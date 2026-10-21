from collections.abc import Iterator
from uuid import UUID

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.engine import Engine

from app.core.config import settings
from app.core.database import get_database_engine
from app.core.errors import AppError
from app.main import app
from app.services.read_data import get_public_config

WEST_AREA = "MULTIPOLYGON(((105 10,105.01 10,105.01 10.01,105 10.01,105 10)))"
EAST_AREA = "MULTIPOLYGON(((105.03 10,105.04 10,105.04 10.01,105.03 10.01,105.03 10)))"
WEST_BBOX = "105,10,105.01,10.01"
ORIGIN_ID = UUID("00000000-0000-0000-0000-000000000001")
NORTH_ID = UUID("00000000-0000-0000-0000-000000000002")
SOUTH_ID = UUID("00000000-0000-0000-0000-000000000003")
EAST_ID = UUID("00000000-0000-0000-0000-000000000004")
WEST_ID = UUID("00000000-0000-0000-0000-000000000005")
CONTRIBUTOR_ID = UUID("00000000-0000-0000-0000-000000000010")


@pytest.fixture
def read_api_client(
    postgis_engine: Engine, read_api_schema: None
) -> Iterator[TestClient]:
    del read_api_schema
    with postgis_engine.begin() as connection:
        connection.execute(text("DELETE FROM photos"))
        connection.execute(text("DELETE FROM user_roads"))
        connection.execute(text("DELETE FROM users"))
        connection.execute(text("DELETE FROM osm.roads"))
        connection.execute(text("DELETE FROM service_areas"))
        connection.execute(
            text(
                """
                INSERT INTO service_areas (slug, name, geom)
                VALUES
                    ('west', 'Vùng Tây', ST_GeomFromText(:west, 4326)),
                    ('east', 'Vùng Đông', ST_GeomFromText(:east, 4326))
                """
            ),
            {"west": WEST_AREA, "east": EAST_AREA},
        )
    app.dependency_overrides[get_database_engine] = lambda: postgis_engine
    client = TestClient(app)
    yield client
    client.close()
    app.dependency_overrides.pop(get_database_engine, None)


def _add_user(engine: Engine) -> None:
    with engine.begin() as connection:
        connection.execute(
            text(
                """
                INSERT INTO users (id, display_name)
                VALUES (:id, 'Người đóng góp')
                ON CONFLICT (id) DO NOTHING
                """
            ),
            {"id": CONTRIBUTOR_ID},
        )


def _add_photo(
    engine: Engine,
    photo_id: UUID,
    longitude: float,
    latitude: float,
    *,
    heading: float | None = None,
    status: str = "approved",
    deleted: bool = False,
) -> None:
    _add_user(engine)
    with engine.begin() as connection:
        connection.execute(
            text(
                """
                INSERT INTO photos (
                    id, contributor_id, location, heading, display_key, mobile_key,
                    thumbnail_key, exif_data, status, deleted_at
                )
                VALUES (
                    :id, :contributor, ST_SetSRID(ST_MakePoint(:lon, :lat), 4326),
                    :heading, 'photos/test/display.jpg', 'photos/test/mobile.jpg',
                    'photos/test/thumb.jpg', '{"gps":"private"}'::jsonb, :status,
                    CASE WHEN :deleted THEN now() ELSE NULL END
                )
                """
            ),
            {
                "id": photo_id,
                "contributor": CONTRIBUTOR_ID,
                "lon": longitude,
                "lat": latitude,
                "heading": heading,
                "status": status,
                "deleted": deleted,
            },
        )


def test_config_returns_bounds_center_terms_and_optional_satellite(
    read_api_client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(settings, "SAT_TILE_URL", "")
    response = read_api_client.get("/api/v1/config")

    assert response.status_code == 200
    config = response.json()
    areas = {area["slug"]: area for area in config["areas"]}
    assert set(areas) == {"west", "east"}
    assert areas["west"]["bbox"] == [105.0, 10.0, 105.01, 10.01]
    assert config["center"] == {"lat": 10.005, "lng": 105.02}
    assert config["zoom"] >= 1
    assert config["terms_version"] == settings.TERMS_VERSION
    assert config["satellite"] is None

    monkeypatch.setattr(settings, "SAT_TILE_URL", "https://tiles.example.invalid/{z}/{x}/{y}.png")
    monkeypatch.setattr(settings, "SAT_ATTRIBUTION", "Test attribution")
    monkeypatch.setattr(settings, "SAT_MAX_ZOOM", 17)
    configured = read_api_client.get("/api/v1/config").json()["satellite"]
    assert configured == {
        "url": "https://tiles.example.invalid/{z}/{x}/{y}.png",
        "attribution": "Test attribution",
        "max_zoom": 17,
    }


def test_config_rejects_satellite_url_without_attribution(
    read_api_client: TestClient,
    postgis_engine: Engine,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    del read_api_client
    monkeypatch.setattr(settings, "SAT_TILE_URL", "https://tiles.example.invalid/{z}/{x}/{y}.png")
    monkeypatch.setattr(settings, "SAT_ATTRIBUTION", "")

    with pytest.raises(AppError, match="ghi công"):
        get_public_config(postgis_engine)


@pytest.mark.parametrize("bbox", ["bad", "105,10,105,10.01", "181,10,182,11"])
def test_rejects_invalid_bbox(read_api_client: TestClient, bbox: str) -> None:
    response = read_api_client.get("/api/v1/roads", params={"bbox": bbox})

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "invalid_bbox"


def test_rejects_bbox_outside_service_bounds(read_api_client: TestClient) -> None:
    response = read_api_client.get(
        "/api/v1/roads",
        params={"bbox": "100,5,101,6"},
    )

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "bbox_out_of_bounds"


def test_roads_separate_osm_and_approved_community_layers(
    read_api_client: TestClient, postgis_engine: Engine
) -> None:
    with postgis_engine.begin() as connection:
        connection.execute(
            text(
                """
                INSERT INTO osm.roads (id, name, highway, geometry)
                VALUES (
                    1, 'Đường OSM', 'residential',
                    ST_GeomFromText('LINESTRING(105.001 10.001,105.009 10.009)', 4326)
                )
                """
            )
        )
        connection.execute(
            text(
                """
                INSERT INTO user_roads (id, geometry, name, road_type, status)
                VALUES
                    ('00000000-0000-0000-0000-000000000021',
                     ST_GeomFromText('LINESTRING(105.002 10.002,105.008 10.008)', 4326),
                     'Đường cộng đồng', 'path', 'approved'),
                    ('00000000-0000-0000-0000-000000000022',
                     ST_GeomFromText('LINESTRING(105.002 10.008,105.008 10.002)', 4326),
                     'Chưa duyệt', 'path', 'pending')
                """
            )
        )

    all_roads = read_api_client.get(
        "/api/v1/roads", params={"bbox": WEST_BBOX, "layer": "all"}
    ).json()
    assert len(all_roads["features"]) == 2
    assert {feature["properties"]["source"] for feature in all_roads["features"]} == {
        "osm",
        "community",
    }
    osm_roads = read_api_client.get(
        "/api/v1/roads", params={"bbox": WEST_BBOX, "layer": "osm"}
    ).json()
    assert [feature["properties"]["name"] for feature in osm_roads["features"]] == ["Đường OSM"]
    community_roads = read_api_client.get(
        "/api/v1/roads", params={"bbox": WEST_BBOX, "layer": "community"}
    ).json()
    assert [feature["properties"]["name"] for feature in community_roads["features"]] == [
        "Đường cộng đồng"
    ]


def test_roads_limit_is_5000_and_reports_truncation(
    read_api_client: TestClient, postgis_engine: Engine
) -> None:
    with postgis_engine.begin() as connection:
        connection.execute(
            text(
                """
                INSERT INTO osm.roads (id, highway, geometry)
                SELECT
                    value,
                    'residential',
                    ST_MakeLine(
                        ST_SetSRID(ST_MakePoint(105.001 + value * 0.0000001, 10.005), 4326),
                        ST_SetSRID(ST_MakePoint(105.002 + value * 0.0000001, 10.005), 4326)
                    )
                FROM generate_series(1, 5001) AS value
                """
            )
        )

    response = read_api_client.get(
        "/api/v1/roads", params={"bbox": WEST_BBOX, "layer": "osm", "zoom": 13}
    )

    assert response.status_code == 200
    assert len(response.json()["features"]) == 5000
    assert response.json()["truncated"] is True


def test_photos_only_include_approved_non_deleted_points(
    read_api_client: TestClient, postgis_engine: Engine
) -> None:
    _add_photo(postgis_engine, ORIGIN_ID, 105.005, 10.005)
    _add_photo(
        postgis_engine,
        UUID("00000000-0000-0000-0000-000000000011"),
        105.006,
        10.006,
        status="pending",
    )
    _add_photo(
        postgis_engine,
        UUID("00000000-0000-0000-0000-000000000012"),
        105.007,
        10.007,
        deleted=True,
    )

    response = read_api_client.get("/api/v1/photos", params={"bbox": WEST_BBOX})

    assert response.status_code == 200
    features = response.json()["features"]
    assert [feature["properties"]["id"] for feature in features] == [str(ORIGIN_ID)]
    assert features[0]["properties"]["thumbnail_url"] == "/media/photos/test/thumb.jpg"


def test_photos_limit_is_2000_and_reports_truncation(
    read_api_client: TestClient, postgis_engine: Engine
) -> None:
    _add_user(postgis_engine)
    with postgis_engine.begin() as connection:
        connection.execute(
            text(
                """
                INSERT INTO photos (id, contributor_id, location, status)
                SELECT
                    gen_random_uuid(),
                    :contributor,
                    ST_SetSRID(
                        ST_MakePoint(105.001 + value * 0.0000001, 10.005),
                        4326
                    ),
                    'approved'
                FROM generate_series(1, 2001) AS value
                """
            ),
            {"contributor": CONTRIBUTOR_ID},
        )

    response = read_api_client.get("/api/v1/photos", params={"bbox": WEST_BBOX})

    assert response.status_code == 200
    assert len(response.json()["features"]) == 2000
    assert response.json()["truncated"] is True


def test_photo_detail_hides_exif_and_returns_public_media_urls(
    read_api_client: TestClient, postgis_engine: Engine
) -> None:
    _add_photo(postgis_engine, ORIGIN_ID, 105.005, 10.005, heading=35)

    response = read_api_client.get(f"/api/v1/photos/{ORIGIN_ID}")

    assert response.status_code == 200
    detail = response.json()
    assert detail["display_url"] == "/media/photos/test/display.jpg"
    assert detail["mobile_url"] == "/media/photos/test/mobile.jpg"
    assert detail["thumbnail_url"] == "/media/photos/test/thumb.jpg"
    assert detail["location"] == {"lat": 10.005, "lng": 105.005}
    assert detail["contributor"]["display_name"] == "Người đóng góp"
    assert "exif_data" not in detail
    assert "gps" not in response.text


def test_photo_detail_hides_pending_photos(
    read_api_client: TestClient, postgis_engine: Engine
) -> None:
    _add_photo(postgis_engine, ORIGIN_ID, 105.005, 10.005, status="pending")

    response = read_api_client.get(f"/api/v1/photos/{ORIGIN_ID}")

    assert response.status_code == 404


def _add_directional_neighbors(engine: Engine, heading: float | None) -> None:
    origin_lon, origin_lat = 105.005, 10.005
    _add_photo(engine, ORIGIN_ID, origin_lon, origin_lat, heading=heading)
    with engine.begin() as connection:
        for photo_id, direction in (
            (NORTH_ID, 0),
            (SOUTH_ID, 180),
            (EAST_ID, 90),
            (WEST_ID, 270),
        ):
            connection.execute(
                text(
                    """
                    INSERT INTO photos (
                        id, contributor_id, location, status, thumbnail_key
                    )
                    VALUES (
                        :id, :contributor,
                        ST_Project(
                            ST_SetSRID(ST_MakePoint(:lon, :lat), 4326)::geography,
                            20,
                            radians(:direction)
                        )::geometry,
                        'approved',
                        'photos/test/thumb.jpg'
                    )
                    """
                ),
                {
                    "id": photo_id,
                    "contributor": CONTRIBUTOR_ID,
                    "lon": origin_lon,
                    "lat": origin_lat,
                    "direction": direction,
                },
            )


def test_neighbors_use_photo_heading_when_bearing_is_omitted(
    read_api_client: TestClient, postgis_engine: Engine
) -> None:
    _add_directional_neighbors(postgis_engine, heading=0)

    response = read_api_client.get(f"/api/v1/photos/{ORIGIN_ID}/neighbors")

    assert response.status_code == 200
    neighbors = response.json()
    assert neighbors["forward"]["id"] == str(NORTH_ID)
    assert neighbors["backward"]["id"] == str(SOUTH_ID)
    assert {item["id"] for item in neighbors["nearby"]} == {str(EAST_ID), str(WEST_ID)}


def test_neighbors_without_heading_are_nearby_unless_bearing_is_given(
    read_api_client: TestClient, postgis_engine: Engine
) -> None:
    _add_directional_neighbors(postgis_engine, heading=None)

    no_bearing = read_api_client.get(f"/api/v1/photos/{ORIGIN_ID}/neighbors").json()
    assert no_bearing["forward"] is None
    assert no_bearing["backward"] is None
    assert len(no_bearing["nearby"]) == 4

    with_bearing = read_api_client.get(
        f"/api/v1/photos/{ORIGIN_ID}/neighbors",
        params={"bearing": 90},
    ).json()
    assert with_bearing["forward"]["id"] == str(EAST_ID)
    assert with_bearing["backward"]["id"] == str(WEST_ID)
    assert {item["id"] for item in with_bearing["nearby"]} == {str(NORTH_ID), str(SOUTH_ID)}

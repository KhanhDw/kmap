import json
from pathlib import Path

import pytest
from sqlalchemy import text
from sqlalchemy.engine import Engine

from app.services.areas import is_within_service_area, sync_service_areas


def _feature(slug: str, name: str, west: float, east: float) -> dict:
    return {
        "type": "Feature",
        "properties": {"slug": slug, "name": name},
        "geometry": {
            "type": "Polygon",
            "coordinates": [
                [
                    [west, 0],
                    [east, 0],
                    [east, 0.01],
                    [west, 0.01],
                    [west, 0],
                ]
            ],
        },
    }


@pytest.fixture
def areas_file(tmp_path: Path) -> Path:
    path = tmp_path / "areas.geojson"
    path.write_text(
        json.dumps(
            {
                "type": "FeatureCollection",
                "features": [
                    _feature("west", "Vùng Tây", 0, 0.01),
                    _feature("east", "Vùng Đông", 0.03, 0.04),
                ],
            }
        ),
        encoding="utf-8",
    )
    return path


@pytest.fixture(autouse=True)
def clean_areas(postgis_engine: Engine):
    with postgis_engine.begin() as connection:
        connection.execute(text("DELETE FROM service_areas"))
    yield
    with postgis_engine.begin() as connection:
        connection.execute(text("DELETE FROM service_areas"))


def test_sync_is_idempotent_and_tracks_geojson_features(
    postgis_engine: Engine, areas_file: Path
) -> None:
    sync_service_areas(postgis_engine, areas_file)
    sync_service_areas(postgis_engine, areas_file)
    with postgis_engine.connect() as connection:
        assert connection.execute(text("SELECT count(*) FROM service_areas")).scalar_one() == 2

    data = json.loads(areas_file.read_text(encoding="utf-8"))
    data["features"].append(_feature("extra", "Vùng thử", 0.06, 0.07))
    areas_file.write_text(json.dumps(data), encoding="utf-8")
    sync_service_areas(postgis_engine, areas_file)
    with postgis_engine.connect() as connection:
        assert connection.execute(text("SELECT count(*) FROM service_areas")).scalar_one() == 3


def test_accepts_point_inside_service_area(postgis_engine: Engine, areas_file: Path) -> None:
    sync_service_areas(postgis_engine, areas_file)
    assert is_within_service_area(postgis_engine, "POINT(0.005 0.005)")


@pytest.mark.parametrize(("distance_m", "expected"), [(99, True), (101, False)])
def test_applies_metre_buffer(
    postgis_engine: Engine, areas_file: Path, distance_m: float, expected: bool
) -> None:
    sync_service_areas(postgis_engine, areas_file)
    with postgis_engine.connect() as connection:
        point_wkt = connection.execute(
            text(
                """
                SELECT ST_AsText(
                    ST_Project(
                        ST_SetSRID(ST_MakePoint(0.01, 0.005), 4326)::geography,
                        :distance_m,
                        pi() / 2
                    )::geometry
                )
                """
            ),
            {"distance_m": distance_m},
        ).scalar_one()
    assert is_within_service_area(postgis_engine, point_wkt) is expected


def test_rejects_point_between_disjoint_service_areas(
    postgis_engine: Engine, areas_file: Path
) -> None:
    sync_service_areas(postgis_engine, areas_file)
    assert not is_within_service_area(postgis_engine, "POINT(0.02 0.005)")


def test_rejects_line_crossing_the_gap_between_service_areas(
    postgis_engine: Engine, areas_file: Path
) -> None:
    sync_service_areas(postgis_engine, areas_file)
    line = "LINESTRING(0.005 0.005, 0.035 0.005)"
    assert not is_within_service_area(postgis_engine, line)


def test_rejects_negative_buffer(postgis_engine: Engine) -> None:
    with pytest.raises(ValueError, match="non-negative"):
        is_within_service_area(postgis_engine, "POINT(0 0)", buffer_m=-1)

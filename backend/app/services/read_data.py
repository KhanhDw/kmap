import json
import math
from typing import Any, Literal
from urllib.parse import quote
from uuid import UUID

from sqlalchemy import Engine, text

from app.core.config import settings
from app.core.errors import AppError

Layer = Literal["osm", "community", "all"]
BBox = tuple[float, float, float, float]
MAX_ROADS = 5000
MAX_PHOTOS = 2000


def parse_bbox(value: str) -> BBox:
    try:
        coordinates = tuple(float(part.strip()) for part in value.split(","))
    except ValueError as error:
        raise AppError(
            "invalid_bbox",
            "bbox phải có dạng minLon,minLat,maxLon,maxLat.",
            422,
        ) from error

    if (
        len(coordinates) != 4
        or not all(math.isfinite(coordinate) for coordinate in coordinates)
        or not (-180 <= coordinates[0] <= 180)
        or not (-90 <= coordinates[1] <= 90)
        or not (-180 <= coordinates[2] <= 180)
        or not (-90 <= coordinates[3] <= 90)
        or coordinates[0] >= coordinates[2]
        or coordinates[1] >= coordinates[3]
    ):
        raise AppError(
            "invalid_bbox",
            "bbox phải có tọa độ hợp lệ và min nhỏ hơn max.",
            422,
        )
    return coordinates[0], coordinates[1], coordinates[2], coordinates[3]


def _service_bounds(engine: Engine) -> BBox:
    with engine.connect() as connection:
        row = connection.execute(
            text(
                """
                SELECT
                    min(ST_XMin(Box3D(geom))),
                    min(ST_YMin(Box3D(geom))),
                    max(ST_XMax(Box3D(geom))),
                    max(ST_YMax(Box3D(geom)))
                FROM service_areas
                """
            )
        ).one()
    if row[0] is None:
        raise AppError("service_areas_unavailable", "Chưa cấu hình vùng phục vụ.", 503)
    return float(row[0]), float(row[1]), float(row[2]), float(row[3])


def _validate_bbox(engine: Engine, bbox: BBox) -> None:
    west, south, east, north = _service_bounds(engine)
    margin_x = (east - west) * 0.1
    margin_y = (north - south) * 0.1
    if (
        bbox[0] < west - margin_x
        or bbox[1] < south - margin_y
        or bbox[2] > east + margin_x
        or bbox[3] > north + margin_y
    ):
        raise AppError(
            "bbox_out_of_bounds",
            "Khu vực yêu cầu vượt quá vùng phục vụ cho phép.",
            422,
        )


def _envelope_params(bbox: BBox) -> dict[str, float]:
    return dict(zip(("min_lon", "min_lat", "max_lon", "max_lat"), bbox, strict=True))


def get_public_config(engine: Engine) -> dict[str, Any]:
    with engine.connect() as connection:
        rows = connection.execute(
            text(
                """
                SELECT
                    slug,
                    name,
                    ST_XMin(Box3D(geom)) AS west,
                    ST_YMin(Box3D(geom)) AS south,
                    ST_XMax(Box3D(geom)) AS east,
                    ST_YMax(Box3D(geom)) AS north
                FROM service_areas
                ORDER BY name
                """
            )
        ).mappings().all()
    if not rows:
        raise AppError("service_areas_unavailable", "Chưa cấu hình vùng phục vụ.", 503)

    west = min(float(row["west"]) for row in rows)
    south = min(float(row["south"]) for row in rows)
    east = max(float(row["east"]) for row in rows)
    north = max(float(row["north"]) for row in rows)
    width = max(east - west, 1e-9)
    height = max(north - south, 1e-9)
    zoom_x = math.log2((800 / 256) * 360 / width)
    zoom_y = math.log2((600 / 256) * 180 / height)
    satellite_url = settings.SAT_TILE_URL.strip()
    satellite_attribution = settings.SAT_ATTRIBUTION.strip()
    if bool(satellite_url) != bool(satellite_attribution):
        raise AppError(
            "invalid_satellite_configuration",
            "Cần cấu hình đồng thời URL và ghi công cho nền vệ tinh.",
            500,
        )
    satellite = None
    if satellite_url:
        satellite = {
            "url": satellite_url,
            "attribution": satellite_attribution,
            "max_zoom": settings.SAT_MAX_ZOOM,
        }

    return {
        "areas": [
            {
                "slug": row["slug"],
                "name": row["name"],
                "bbox": [
                    float(row["west"]),
                    float(row["south"]),
                    float(row["east"]),
                    float(row["north"]),
                ],
            }
            for row in rows
        ],
        "center": {
            "lat": round((south + north) / 2, 7),
            "lng": round((west + east) / 2, 7),
        },
        "zoom": max(1, min(18, math.floor(min(zoom_x, zoom_y)))),
        "terms_version": settings.TERMS_VERSION,
        "satellite": satellite,
    }


def get_roads(engine: Engine, bbox: BBox, layer: Layer, zoom: int) -> dict[str, Any]:
    _validate_bbox(engine, bbox)
    tolerance = max(1e-8, (360 / (256 * (2**zoom))) * 0.5)
    osm_select = """
        SELECT
            r.id::text AS id,
            'osm'::text AS source,
            r.highway::text AS highway,
            NULL::text AS road_type,
            r.name::text AS name,
            ST_AsGeoJSON(
                ST_SimplifyPreserveTopology(r.geometry, :tolerance)
            ) AS geometry
        FROM osm.roads AS r
        WHERE ST_Intersects(
            r.geometry,
            ST_MakeEnvelope(:min_lon, :min_lat, :max_lon, :max_lat, 4326)
        )
    """
    community_select = """
        SELECT
            r.id::text AS id,
            'community'::text AS source,
            NULL::text AS highway,
            r.road_type::text AS road_type,
            r.name::text AS name,
            ST_AsGeoJSON(
                ST_SimplifyPreserveTopology(r.geometry, :tolerance)
            ) AS geometry
        FROM user_roads AS r
        WHERE r.status = 'approved'
            AND r.deleted_at IS NULL
            AND ST_Intersects(
                r.geometry,
                ST_MakeEnvelope(:min_lon, :min_lat, :max_lon, :max_lat, 4326)
            )
    """
    selects = {
        "osm": osm_select,
        "community": community_select,
        "all": f"{osm_select} UNION ALL {community_select}",
    }
    query = text(
        f"""
        SELECT id, source, highway, road_type, name, geometry
        FROM ({selects[layer]}) AS roads
        ORDER BY source, id
        LIMIT :limit
        """
    )
    params = {
        **_envelope_params(bbox),
        "tolerance": tolerance,
        "limit": MAX_ROADS + 1,
    }
    with engine.connect() as connection:
        rows = connection.execute(query, params).mappings().all()
    truncated = len(rows) > MAX_ROADS
    features = [
        {
            "type": "Feature",
            "geometry": json.loads(row["geometry"]),
            "properties": {
                "id": row["id"],
                "source": row["source"],
                "highway": row["highway"],
                "road_type": row["road_type"],
                "name": row["name"],
            },
        }
        for row in rows[:MAX_ROADS]
    ]
    return {"type": "FeatureCollection", "features": features, "truncated": truncated}


def _media_url(key: str | None) -> str | None:
    if key is None:
        return None
    path = quote(key.lstrip("/"), safe="/")
    return f"{settings.MEDIA_URL_PREFIX.rstrip('/')}/{path}"


def get_photos(engine: Engine, bbox: BBox) -> dict[str, Any]:
    _validate_bbox(engine, bbox)
    with engine.connect() as connection:
        rows = connection.execute(
            text(
                """
                SELECT
                    id::text AS id,
                    ST_AsGeoJSON(location) AS geometry,
                    thumbnail_key,
                    heading
                FROM photos
                WHERE status = 'approved'
                    AND deleted_at IS NULL
                    AND ST_Intersects(
                        location,
                        ST_MakeEnvelope(:min_lon, :min_lat, :max_lon, :max_lat, 4326)
                    )
                ORDER BY id
                LIMIT :limit
                """
            ),
            {**_envelope_params(bbox), "limit": MAX_PHOTOS + 1},
        ).mappings().all()
    truncated = len(rows) > MAX_PHOTOS
    features = [
        {
            "type": "Feature",
            "geometry": json.loads(row["geometry"]),
            "properties": {
                "id": row["id"],
                "thumbnail_url": _media_url(row["thumbnail_key"]),
                "heading": row["heading"],
            },
        }
        for row in rows[:MAX_PHOTOS]
    ]
    return {"type": "FeatureCollection", "features": features, "truncated": truncated}


def get_photo(engine: Engine, photo_id: UUID) -> dict[str, Any]:
    with engine.connect() as connection:
        row = connection.execute(
            text(
                """
                SELECT
                    p.id::text AS id,
                    ST_X(p.location) AS longitude,
                    ST_Y(p.location) AS latitude,
                    p.heading,
                    p.captured_at,
                    p.display_key,
                    p.mobile_key,
                    p.thumbnail_key,
                    u.display_name
                FROM photos AS p
                JOIN users AS u ON u.id = p.contributor_id
                WHERE p.id = :photo_id
                    AND p.status = 'approved'
                    AND p.deleted_at IS NULL
                """
            ),
            {"photo_id": photo_id},
        ).mappings().one_or_none()
    if row is None:
        raise AppError("photo_not_found", "Không tìm thấy ảnh công khai.", 404)
    return {
        "id": row["id"],
        "display_url": _media_url(row["display_key"]),
        "mobile_url": _media_url(row["mobile_key"]),
        "thumbnail_url": _media_url(row["thumbnail_key"]),
        "location": {"lat": row["latitude"], "lng": row["longitude"]},
        "heading": row["heading"],
        "captured_at": row["captured_at"],
        "contributor": {"display_name": row["display_name"]},
    }


def _angle_difference(angle: float, target: float) -> float:
    return (angle - target + 180) % 360 - 180


def get_photo_neighbors(
    engine: Engine,
    photo_id: UUID,
    bearing: float | None,
) -> dict[str, Any]:
    with engine.connect() as connection:
        origin = connection.execute(
            text(
                """
                SELECT ST_AsText(location) AS location_wkt, heading
                FROM photos
                WHERE id = :photo_id
                    AND status = 'approved'
                    AND deleted_at IS NULL
                """
            ),
            {"photo_id": photo_id},
        ).mappings().one_or_none()
        if origin is None:
            raise AppError("photo_not_found", "Không tìm thấy ảnh công khai.", 404)
        rows = connection.execute(
            text(
                """
                WITH origin AS (
                    SELECT ST_GeomFromText(:origin_wkt, 4326)::geography AS location
                )
                SELECT
                    p.id::text AS id,
                    p.thumbnail_key,
                    ST_Distance(p.location::geography, origin.location) AS distance,
                    degrees(ST_Azimuth(origin.location, p.location::geography)) AS bearing
                FROM photos AS p
                CROSS JOIN origin
                WHERE p.id <> :photo_id
                    AND p.status = 'approved'
                    AND p.deleted_at IS NULL
                    AND ST_DWithin(p.location::geography, origin.location, 60)
                ORDER BY distance, p.id
                """
            ),
            {"photo_id": photo_id, "origin_wkt": origin["location_wkt"]},
        ).mappings().all()

    candidates = [
        {
            "id": row["id"],
            "thumbnail_url": _media_url(row["thumbnail_key"]),
            "distance": round(float(row["distance"]), 2),
            "bearing": (
                round(float(row["bearing"]) % 360, 2)
                if row["bearing"] is not None
                else None
            ),
        }
        for row in rows
    ]
    effective_bearing = bearing if bearing is not None else origin["heading"]
    if effective_bearing is None:
        return {"forward": None, "backward": None, "nearby": candidates}

    forward = [
        candidate
        for candidate in candidates
        if candidate["bearing"] is not None
        and abs(_angle_difference(candidate["bearing"], effective_bearing)) <= 60
    ]
    backward_heading = (effective_bearing + 180) % 360
    backward = [
        candidate
        for candidate in candidates
        if candidate["bearing"] is not None
        and abs(_angle_difference(candidate["bearing"], backward_heading)) <= 60
    ]
    selected = {
        min(forward, key=lambda item: item["distance"])["id"] if forward else None,
        min(backward, key=lambda item: item["distance"])["id"] if backward else None,
    }
    return {
        "forward": min(forward, key=lambda item: item["distance"]) if forward else None,
        "backward": min(backward, key=lambda item: item["distance"]) if backward else None,
        "nearby": [item for item in candidates if item["id"] not in selected],
    }

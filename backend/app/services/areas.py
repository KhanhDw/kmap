import json
from pathlib import Path
from typing import Any

from sqlalchemy import Engine, bindparam, text


def _load_features(path: Path) -> list[dict[str, Any]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("type") != "FeatureCollection" or not isinstance(data.get("features"), list):
        raise ValueError("areas file must contain a GeoJSON FeatureCollection")

    features: list[dict[str, Any]] = []
    slugs: set[str] = set()
    for feature in data["features"]:
        properties = feature.get("properties") or {}
        slug = properties.get("slug")
        name = properties.get("name")
        geometry = feature.get("geometry") or {}
        if (
            not isinstance(slug, str)
            or not slug
            or slug in slugs
            or not isinstance(name, str)
            or not name
            or geometry.get("type") not in {"Polygon", "MultiPolygon"}
        ):
            raise ValueError("each area must have a unique slug, name, and polygon geometry")
        slugs.add(slug)
        features.append(
            {
                "slug": slug,
                "name": name,
                "geometry": json.dumps(geometry, separators=(",", ":")),
            }
        )
    if not features:
        raise ValueError("areas file must contain at least one feature")
    return features


def sync_service_areas(engine: Engine, path: Path) -> None:
    features = _load_features(path)
    with engine.begin() as connection:
        for feature in features:
            connection.execute(
                text(
                    """
                    INSERT INTO service_areas (slug, name, geom)
                    VALUES (
                        :slug,
                        :name,
                        ST_Multi(
                            ST_SetSRID(ST_GeomFromGeoJSON(:geometry), 4326)
                        )
                    )
                    ON CONFLICT (slug) DO UPDATE
                    SET name = EXCLUDED.name, geom = EXCLUDED.geom
                    """
                ),
                feature,
            )
        connection.execute(
            text("DELETE FROM service_areas WHERE slug NOT IN :slugs").bindparams(
                bindparam("slugs", expanding=True)
            ),
            {"slugs": tuple(feature["slug"] for feature in features)},
        )


def is_within_service_area(
    engine: Engine,
    geom_wkt: str,
    buffer_m: float = 100,
) -> bool:
    if buffer_m < 0:
        raise ValueError("buffer_m must be non-negative")
    with engine.connect() as connection:
        result = connection.execute(
            text(
                """
                WITH service_area AS (
                    SELECT ST_UnaryUnion(
                        ST_Collect(ST_Buffer(geom::geography, :buffer_m)::geometry)
                    ) AS geom
                    FROM service_areas
                )
                SELECT COALESCE(
                    ST_CoveredBy(
                        ST_SetSRID(ST_GeomFromText(:geom_wkt), 4326),
                        service_area.geom
                    ),
                    FALSE
                )
                FROM service_area
                """
            ),
            {"geom_wkt": geom_wkt, "buffer_m": buffer_m},
        ).scalar_one()
    return bool(result)

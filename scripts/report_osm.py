import json
import os
from datetime import UTC, datetime
from pathlib import Path

import psycopg

CONTAINER_AREAS_PATH = Path("/config/areas.geojson")
AREAS_PATH = (
    CONTAINER_AREAS_PATH
    if CONTAINER_AREAS_PATH.is_file()
    else Path(__file__).resolve().parents[1] / "config" / "areas.geojson"
)


def bbox_sql(geometry_sql: str) -> str:
    return (
        f"ST_XMin(Box3D({geometry_sql})), ST_YMin(Box3D({geometry_sql})), "
        f"ST_XMax(Box3D({geometry_sql})), ST_YMax(Box3D({geometry_sql}))"
    )


def fmt_bbox(values: tuple[float, float, float, float]) -> str:
    return "[" + ", ".join(f"{value:.7f}" for value in values) + "]"


def main() -> None:
    area_data = json.loads(AREAS_PATH.read_text(encoding="utf-8"))
    areas = area_data["features"]
    if len(areas) != 2:
        raise ValueError("The M1 OSM report requires exactly two service areas.")

    connection = psycopg.connect(
        host=os.environ.get("OSM_DB_HOST", "db"),
        port=os.environ.get("OSM_DB_PORT", "5432"),
        dbname=os.environ["POSTGRES_DB"],
        user=os.environ["POSTGRES_USER"],
        password=os.environ["POSTGRES_PASSWORD"],
    )
    rows: list[str] = []
    warning = False
    with connection:
        with connection.cursor() as cursor:
            cursor.execute(
                f"SELECT {bbox_sql('ST_Collect(geom)')}, "
                "round((ST_Area(ST_UnaryUnion(ST_Collect(geom))::geography) "
                "/ 1000000)::numeric, 2) "
                "FROM service_areas"
            )
            merged_row = cursor.fetchone()
            if merged_row is None:
                raise RuntimeError(
                    "service_areas is empty; start the API after running migrations."
                )
            merged_bbox = tuple(float(value) for value in merged_row[:4])

            rows.extend(
                [
                    "# Báo cáo dữ liệu OSM M1",
                    "",
                    f"- Tạo lúc (UTC): {datetime.now(UTC).isoformat(timespec='seconds')}",
                    "- Nguồn: OpenStreetMap contributors, ODbL 1.0.",
                    "- Nguồn tải: "
                    + os.environ.get("OSM_SOURCE_REASON", "Geofabrik Vietnam extract"),
                    "",
                ]
            )
            cursor.execute("SELECT count(*) FROM osm.roads")
            rows.extend(
                [
                    f"- Tổng số bản ghi `osm.roads`: {cursor.fetchone()[0]}",
                    f"- Bbox hợp nhất (WGS84): {fmt_bbox(merged_bbox)}",
                    "",
                ]
            )

            for feature in areas:
                props = feature["properties"]
                cursor.execute(
                    f"""
                    SELECT
                        count(r.id),
                        round((COALESCE(sum(
                            ST_Length(
                                ST_CollectionExtract(
                                    ST_Intersection(r.geometry, a.geom), 2
                                )::geography
                            )
                        ), 0) / 1000)::numeric, 2),
                        {bbox_sql("a.geom")},
                        round((ST_Area(a.geom::geography) / 1000000)::numeric, 2)
                    FROM service_areas AS a
                    LEFT JOIN osm.roads AS r ON ST_Intersects(r.geometry, a.geom)
                    WHERE a.slug = %s
                    GROUP BY a.geom
                    """,
                    (props["slug"],),
                )
                stats = cursor.fetchone()
                if stats is None:
                    raise RuntimeError(f"Service area missing from the database: {props['slug']}")
                road_count = int(stats[0])
                warning = warning or road_count < 50
                rows.extend(
                    [
                        f"## {props['name']}",
                        "",
                        f"- Slug: `{props['slug']}`",
                        f"- OSM relation: `{props.get('osm_id', 'unknown')}` "
                        f"(admin_level={props.get('admin_level', 'unknown')}, "
                        f"last modified {props.get('last_modified', 'unknown')})",
                        f"- Diện tích: {stats[6]} km²",
                        f"- Bbox (WGS84): {fmt_bbox(tuple(float(value) for value in stats[2:6]))}",
                        f"- Số đoạn đường OSM: {road_count}",
                        f"- Tổng chiều dài nằm trong vùng: {stats[1]} km",
                        "",
                        "| Loại highway | Số đoạn |",
                        "| :-- | --: |",
                    ]
                )
                cursor.execute(
                    """
                    SELECT r.highway, count(*)
                    FROM osm.roads AS r
                    JOIN service_areas AS a ON a.slug = %s
                    WHERE ST_Intersects(r.geometry, a.geom)
                    GROUP BY r.highway
                    ORDER BY count(*) DESC, r.highway
                    """,
                    (props["slug"],),
                )
                rows.extend(f"| `{highway}` | {count} |" for highway, count in cursor.fetchall())
                rows.append("")
    connection.close()

    if warning:
        rows.extend(
            [
                "> CẢNH BÁO: Có vùng dưới 50 đoạn đường OSM; "
                "cần chủ dự án kiểm tra trước khi tiếp tục.",
                "",
            ]
        )

    print("\n".join(rows))
    if warning:
        raise SystemExit(3)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Seed four synthetic panoramas along an existing in-area OSM road."""

import hashlib
import io
import secrets
import sys
from pathlib import Path
from uuid import UUID

from argon2 import PasswordHasher
from PIL import Image
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

sys.path.insert(0, str(Path(__file__).resolve().parent))

from make_test_panorama import create_test_panorama

from app.core.config import settings

DEMO_USER_ID = UUID("00000000-0000-0000-0000-00000000d300")
DEMO_PHOTO_IDS = [
    UUID(f"00000000-0000-0000-0000-00000000d30{index}")
    for index in range(1, 5)
]

DEMO_LOCATIONS_SQL = text(
    """
    WITH candidates AS (
        SELECT
            area.slug,
            road.id,
            ST_LineMerge(
                ST_CollectionExtract(ST_Intersection(road.geometry, area.geom), 2)
            ) AS line
        FROM osm.roads AS road
        JOIN service_areas AS area ON ST_Intersects(road.geometry, area.geom)
    ),
    lines AS (
        SELECT
            candidate.slug,
            candidate.id,
            dumped.geom::geometry(LineString, 4326) AS line
        FROM candidates AS candidate
        CROSS JOIN LATERAL ST_Dump(candidate.line) AS dumped
        WHERE ST_GeometryType(dumped.geom) = 'ST_LineString'
            AND ST_Length(dumped.geom::geography) >= 100
    ),
    chosen AS (
        SELECT
            slug,
            id,
            line,
            ST_Length(line::geography) AS meters
        FROM lines
        ORDER BY meters DESC, id
        LIMIT 1
    ),
    locations AS (
        SELECT
            chosen.*,
            step,
            0.5 + ((step - 1.5) * 12 / meters) AS fraction
        FROM chosen
        CROSS JOIN generate_series(0, 3) AS step
    )
    SELECT
        slug,
        id AS osm_road_id,
        ST_X(ST_LineInterpolatePoint(line, fraction)) AS longitude,
        ST_Y(ST_LineInterpolatePoint(line, fraction)) AS latitude,
        degrees(
            ST_Azimuth(
                ST_LineInterpolatePoint(line, GREATEST(0, fraction - 5 / meters)),
                ST_LineInterpolatePoint(line, LEAST(1, fraction + 5 / meters))
            )
        ) AS heading
    FROM locations
    ORDER BY step
    """
)


def save_variant(
    image: Image.Image,
    destination: Path,
    *,
    thumbnail: bool = False,
) -> bytes:
    variant = image.copy()
    if thumbnail:
        variant.thumbnail((400, 200), Image.Resampling.LANCZOS)
    output = io.BytesIO()
    variant.save(output, "JPEG", quality=85, optimize=True)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(output.getvalue())
    return output.getvalue()


def seed(engine: Engine) -> int:
    media_root = Path(settings.MEDIA_DIR)
    created_files: list[Path] = []
    with engine.connect() as connection:
        locations = connection.execute(DEMO_LOCATIONS_SQL).mappings().all()
        if len(locations) != len(DEMO_PHOTO_IDS):
            raise RuntimeError(
                "Không tìm được đường OSM phù hợp để tạo đủ bốn ảnh demo."
            )
        existing = set(
            connection.execute(
                text("SELECT id FROM photos WHERE id = ANY(:photo_ids)"),
                {"photo_ids": DEMO_PHOTO_IDS},
            ).scalars()
        )
    pending = [
        (photo_id, location)
        for photo_id, location in zip(DEMO_PHOTO_IDS, locations, strict=True)
        if photo_id not in existing
    ]
    if not pending:
        print("Bốn ảnh demo đã tồn tại; không thay đổi dữ liệu.")
        return 0

    hasher = PasswordHasher()
    try:
        with engine.begin() as connection:
            connection.execute(
                text(
                    """
                    INSERT INTO users (id, email, password_hash, display_name)
                    VALUES (:id, :email, :password_hash, :display_name)
                    ON CONFLICT (id) DO NOTHING
                    """
                ),
                {
                    "id": DEMO_USER_ID,
                    "email": "demo-viewer@kmap.invalid",
                    "password_hash": hasher.hash(secrets.token_urlsafe(32)),
                    "display_name": "Người đóng góp thử nghiệm",
                },
            )
            for photo_id, location in pending:
                image = create_test_panorama(
                    float(location["heading"] or 0),
                    f"DEMO {str(photo_id)[-1]}",
                )
                source = io.BytesIO()
                image.save(source, "JPEG", quality=90)
                source_bytes = source.getvalue()
                display_key = f"photos/{photo_id}/display.jpg"
                mobile_key = f"photos/{photo_id}/mobile.jpg"
                thumbnail_key = f"photos/{photo_id}/thumb.jpg"
                for key, thumbnail in (
                    (display_key, False),
                    (mobile_key, False),
                    (thumbnail_key, True),
                ):
                    destination = media_root / key
                    save_variant(image, destination, thumbnail=thumbnail)
                    created_files.append(destination)
                connection.execute(
                    text(
                        """
                        INSERT INTO photos (
                            id, contributor_id, location, heading, captured_at,
                            display_key, mobile_key, thumbnail_key, sha256,
                            orig_width, orig_height, width, height, file_size,
                            status, exif_data
                        )
                        VALUES (
                            :id, :contributor_id,
                            ST_SetSRID(ST_MakePoint(:longitude, :latitude), 4326),
                            :heading, NULL, :display_key, :mobile_key, :thumbnail_key,
                            :sha256, :width, :height, :width, :height, :file_size,
                            'approved', NULL
                        )
                        ON CONFLICT (id) DO NOTHING
                        """
                    ),
                    {
                        "id": photo_id,
                        "contributor_id": DEMO_USER_ID,
                        "longitude": location["longitude"],
                        "latitude": location["latitude"],
                        "heading": location["heading"],
                        "display_key": display_key,
                        "mobile_key": mobile_key,
                        "thumbnail_key": thumbnail_key,
                        "sha256": hashlib.sha256(source_bytes).hexdigest(),
                        "width": image.width,
                        "height": image.height,
                        "file_size": len(source_bytes),
                    },
                )
        return len(pending)
    except BaseException:
        for path in created_files:
            path.unlink(missing_ok=True)
        raise


def main() -> None:
    engine = create_engine(settings.DATABASE_URL)
    try:
        count = seed(engine)
        print(f"Đã tạo {count} ảnh 360° thử nghiệm (ảnh giả).")
    finally:
        engine.dispose()


if __name__ == "__main__":
    main()

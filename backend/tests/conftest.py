from collections.abc import Iterator

import pytest
from sqlalchemy import create_engine, make_url, text
from sqlalchemy.engine import Engine

from app.core.config import settings


@pytest.fixture(scope="session")
def postgis_engine() -> Iterator[Engine]:
    base_url = make_url(settings.DATABASE_URL)
    admin_engine = create_engine(base_url)
    with admin_engine.connect().execution_options(isolation_level="AUTOCOMMIT") as connection:
        exists = connection.execute(
            text("SELECT 1 FROM pg_database WHERE datname = 'kmap_test'")
        ).scalar_one_or_none()
        if exists is None:
            connection.exec_driver_sql("CREATE DATABASE kmap_test")
    admin_engine.dispose()

    engine = create_engine(base_url.set(database="kmap_test"))
    with engine.begin() as connection:
        connection.execute(text("CREATE EXTENSION IF NOT EXISTS postgis"))
        connection.execute(text("DROP TABLE IF EXISTS service_areas"))
        connection.execute(
            text(
                """
                CREATE TABLE service_areas (
                    slug text PRIMARY KEY,
                    name text NOT NULL,
                    geom geometry(MultiPolygon, 4326) NOT NULL
                )
                """
            )
        )
    yield engine
    with engine.begin() as connection:
        connection.execute(text("DROP TABLE service_areas"))
    engine.dispose()


@pytest.fixture(scope="session")
def read_api_schema(postgis_engine: Engine) -> Iterator[None]:
    with postgis_engine.begin() as connection:
        connection.execute(text("CREATE SCHEMA IF NOT EXISTS osm"))
        for statement in (
            """
            CREATE TABLE users (
                id uuid PRIMARY KEY,
                display_name text NOT NULL
            )
            """,
            """
            CREATE TABLE photos (
                id uuid PRIMARY KEY,
                contributor_id uuid NOT NULL REFERENCES users(id),
                location geometry(Point, 4326) NOT NULL,
                heading real,
                captured_at timestamptz,
                display_key text,
                mobile_key text,
                thumbnail_key text,
                exif_data jsonb,
                status text NOT NULL,
                deleted_at timestamptz
            )
            """,
            """
            CREATE TABLE user_roads (
                id uuid PRIMARY KEY,
                geometry geometry(LineString, 4326) NOT NULL,
                name text,
                road_type text NOT NULL,
                status text NOT NULL,
                deleted_at timestamptz
            )
            """,
            """
            CREATE TABLE osm.roads (
                id bigint PRIMARY KEY,
                name text,
                highway text NOT NULL,
                geometry geometry(Geometry, 4326) NOT NULL
            )
            """,
        ):
            connection.execute(text(statement))
    yield
    with postgis_engine.begin() as connection:
        connection.execute(text("DROP TABLE photos, user_roads, users, osm.roads"))
        connection.execute(text("DROP SCHEMA osm"))

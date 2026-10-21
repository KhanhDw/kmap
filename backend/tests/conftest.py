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

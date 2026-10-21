from fastapi import Request
from sqlalchemy.engine import Engine


def get_database_engine(request: Request) -> Engine:
    engine = getattr(request.app.state, "database_engine", None)
    if engine is None:
        raise RuntimeError("Database engine is unavailable outside the application lifespan.")
    return engine

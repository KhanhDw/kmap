from typing import Annotated, Literal
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.engine import Engine

from app.core.database import get_database_engine
from app.services import read_data

router = APIRouter(tags=["map"])


@router.get("/config")
def public_config(engine: Annotated[Engine, Depends(get_database_engine)]) -> dict:
    return read_data.get_public_config(engine)


@router.get("/roads")
def roads(
    bbox: str,
    engine: Annotated[Engine, Depends(get_database_engine)],
    layer: Literal["osm", "community", "all"] = "all",
    zoom: Annotated[int, Query(ge=0, le=24)] = 12,
) -> dict:
    return read_data.get_roads(engine, read_data.parse_bbox(bbox), layer, zoom)


@router.get("/photos")
def photos(
    bbox: str,
    engine: Annotated[Engine, Depends(get_database_engine)],
) -> dict:
    return read_data.get_photos(engine, read_data.parse_bbox(bbox))


@router.get("/photos/{photo_id}")
def photo_detail(
    photo_id: UUID,
    engine: Annotated[Engine, Depends(get_database_engine)],
) -> dict:
    return read_data.get_photo(engine, photo_id)


@router.get("/photos/{photo_id}/neighbors")
def photo_neighbors(
    photo_id: UUID,
    engine: Annotated[Engine, Depends(get_database_engine)],
    bearing: Annotated[float | None, Query(ge=0, lt=360)] = None,
) -> dict:
    return read_data.get_photo_neighbors(engine, photo_id, bearing)

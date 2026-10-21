from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import create_engine
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.middleware.base import RequestResponseEndpoint
from starlette.responses import Response
from starlette.staticfiles import StaticFiles

from app.core.config import settings
from app.core.errors import AppError
from app.routers import health, read_data
from app.services.areas import sync_service_areas


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    engine = create_engine(settings.DATABASE_URL)
    app.state.database_engine = engine
    try:
        sync_service_areas(engine, settings.AREAS_FILE)
        yield
    finally:
        engine.dispose()
        del app.state.database_engine


app = FastAPI(
    title="KMap API",
    version="0.1.0",
    docs_url="/api/v1/docs" if settings.ENV != "production" else None,
    redoc_url=None,
    openapi_url="/api/v1/openapi.json" if settings.ENV != "production" else None,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_ORIGIN],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(GZipMiddleware, minimum_size=1000, compresslevel=5)


@app.middleware("http")
async def media_cache_headers(
    request: Request,
    call_next: RequestResponseEndpoint,
) -> Response:
    response = await call_next(request)
    media_prefix = f"{settings.MEDIA_URL_PREFIX.rstrip('/')}/"
    if request.url.path.startswith(media_prefix) and response.status_code == 200:
        response.headers["Cache-Control"] = "public, max-age=31536000, immutable"
    return response


@app.exception_handler(AppError)
async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": {"code": exc.code, "message": exc.message}},
    )


@app.exception_handler(StarletteHTTPException)
async def http_error_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": {"code": "http_error", "message": str(exc.detail)}},
    )


@app.exception_handler(RequestValidationError)
async def validation_error_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    return JSONResponse(
        status_code=422,
        content={
            "error": {
                "code": "validation_error",
                "message": "Dữ liệu không hợp lệ.",
                "details": exc.errors(),
            }
        },
    )


app.include_router(health.router, prefix="/api/v1")
app.include_router(read_data.router, prefix="/api/v1")
app.mount(
    settings.MEDIA_URL_PREFIX,
    StaticFiles(directory=settings.MEDIA_DIR),
    name="media",
)

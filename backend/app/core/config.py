from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=Path(__file__).resolve().parents[3] / ".env",
        extra="ignore",
        case_sensitive=True,
    )

    ENV: str = "development"
    DOMAIN: str = "localhost"
    FRONTEND_ORIGIN: str = "http://localhost"
    BACKEND_ORIGIN: str = "http://localhost"

    DATABASE_URL: str

    JWT_SECRET: str
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30

    MEDIA_DIR: str = "/data/media"
    MEDIA_URL_PREFIX: str = "/media"

    TILE_URL: str = ""
    TILE_ATTRIBUTION: str = ""


settings = Settings()

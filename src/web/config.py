from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Optional

from pydantic import BaseModel, Field
try:
    # Prefer pydantic-settings when available for robust env parsing
    from pydantic_settings import BaseSettings
except Exception:  # pragma: no cover
    # Fallback to simple BaseModel if pydantic-settings is unavailable
    BaseSettings = BaseModel  # type: ignore


class Settings(BaseSettings):
    """Application configuration loaded from environment variables.

    Uses pydantic-settings when available. Otherwise behaves like a regular model.
    """

    app_title: str = Field(default="Table Database")

    # Storage
    db_storage_dir: str = Field(default="databases")

    # Redis / background sync
    redis_url: str = Field(default="redis://localhost:6379/0")

    # Google services configuration (optional, autodetection also supported)
    google_oauth_client_id: Optional[str] = Field(default=None)
    google_oauth_client_secret: Optional[str] = Field(default=None)
    google_api_key: Optional[str] = Field(default=None)
    google_picker_app_id: Optional[str] = Field(default=None)
    google_refresh_token: Optional[str] = Field(default=None)
    google_service_account_info: Optional[str] = Field(default=None)
    google_service_account_file: Optional[str] = Field(default=None)
    drive_folder_id: Optional[str] = Field(default=None)

    class Config:
        env_file = ".env"
        extra = "ignore"


@lru_cache()
def get_settings() -> Settings:
    return Settings()


def get_templates_dir() -> Path:
    return Path(__file__).resolve().parent / "templates"


def get_static_dir() -> Path:
    return Path(__file__).resolve().parent / "static"



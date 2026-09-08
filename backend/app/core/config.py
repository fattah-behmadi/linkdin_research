"""Application settings, loaded from environment / `.env` (pydantic-settings)."""

from __future__ import annotations

from enum import StrEnum
from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_ROOT = Path(__file__).resolve().parents[2]
REPO_ROOT = BACKEND_ROOT.parent


class SearchBackend(StrEnum):
    """Which adapter satisfies the search port."""

    ELASTICSEARCH = "elasticsearch"
    SQL = "sql"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=BACKEND_ROOT / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "LinkedIn Profile Search API"
    api_v1_prefix: str = "/api/v1"
    debug: bool = False

    # --- Persistence -------------------------------------------------------
    database_url: str = f"sqlite+aiosqlite:///{(REPO_ROOT / 'data' / 'linkedin.db').as_posix()}"

    # --- Search ------------------------------------------------------------
    # `elasticsearch` is the primary adapter; `sql` (SQLite FTS5) keeps the app
    # fully functional when no Docker/ES is available.
    search_backend: SearchBackend = SearchBackend.SQL
    elasticsearch_url: str = "http://localhost:9200"
    elasticsearch_index: str = "linkedin-profiles"
    elasticsearch_request_timeout: float = 10.0

    # --- HTTP --------------------------------------------------------------
    cors_origins: list[str] = Field(default_factory=lambda: ["http://localhost:3000"])

    # --- Search behaviour --------------------------------------------------
    max_page_size: int = 100
    facet_size: int = 25

    # --- ETL ---------------------------------------------------------------
    dataset_path: Path = REPO_ROOT / "user_linkedin.txt"


@lru_cache
def get_settings() -> Settings:
    """Cached settings instance (safe to use as a FastAPI dependency)."""
    return Settings()

"""Async engine / session factory and schema bootstrap."""

from __future__ import annotations

from collections.abc import AsyncIterator
from functools import lru_cache
from pathlib import Path

from sqlalchemy import event, text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.config import Settings, get_settings
from app.db import models  # noqa: F401  (import registers the mappers)
from app.db.base import Base

# Full-text index used by the SQL search adapter. Contentless (`content=''`):
# it stores only the inverted index, rows are joined back through `rowid`.
FTS_TABLE_DDL = """
CREATE VIRTUAL TABLE IF NOT EXISTS profiles_fts USING fts5(
    full_name,
    job_title,
    company,
    summary,
    skills,
    education,
    content='',
    tokenize='unicode61 remove_diacritics 2'
)
"""


def _ensure_sqlite_dir(database_url: str) -> None:
    marker = ":///"
    if database_url.startswith("sqlite") and marker in database_url:
        path = Path(database_url.split(marker, 1)[1])
        if path.name != ":memory:":
            path.parent.mkdir(parents=True, exist_ok=True)


def create_engine(settings: Settings | None = None) -> AsyncEngine:
    settings = settings or get_settings()
    _ensure_sqlite_dir(settings.database_url)
    engine = create_async_engine(settings.database_url, echo=settings.debug, future=True)

    @event.listens_for(engine.sync_engine, "connect")
    def _set_sqlite_pragmas(dbapi_connection, _record) -> None:  # type: ignore[no-untyped-def]
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.close()

    return engine


@lru_cache
def get_engine() -> AsyncEngine:
    return create_engine()


@lru_cache
def get_session_factory() -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(get_engine(), expire_on_commit=False, autoflush=False)


async def get_session() -> AsyncIterator[AsyncSession]:
    """FastAPI dependency: one session per request."""
    async with get_session_factory()() as session:
        yield session


async def create_schema(engine: AsyncEngine) -> None:
    """Create tables + the FTS5 index. Idempotent."""
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
        await connection.execute(text(FTS_TABLE_DDL))


async def drop_schema(engine: AsyncEngine) -> None:
    async with engine.begin() as connection:
        await connection.execute(text("DROP TABLE IF EXISTS profiles_fts"))
        await connection.run_sync(Base.metadata.drop_all)

"""Relational read repository: the canonical source for a single profile."""

from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Profile
from app.repositories.mappers import profile_to_detail
from app.schemas.profile import ProfileDetail


class SqlProfileRepository:
    """Implements `ProfileRepositoryPort`."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, profile_id: int) -> ProfileDetail | None:
        profile = await self._session.get(Profile, profile_id)
        return profile_to_detail(profile) if profile else None

    async def count(self) -> int:
        return await self._session.scalar(select(func.count()).select_from(Profile)) or 0

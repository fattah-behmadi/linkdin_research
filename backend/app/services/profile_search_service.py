"""Application service: the only place the API talks to.

It depends on the ports, never on Elasticsearch or SQLAlchemy, so swapping the
search backend (or faking it in tests) needs no change here.
"""

from __future__ import annotations

from app.core.exceptions import ProfileNotFoundError
from app.domain.ports import ProfileRepositoryPort, ProfileSearchPort
from app.schemas.facets import Facets
from app.schemas.profile import ProfileDetail
from app.schemas.search import SearchQuery, SearchResult


class ProfileSearchService:
    def __init__(self, search: ProfileSearchPort, profiles: ProfileRepositoryPort) -> None:
        self._search = search
        self._profiles = profiles

    async def search(self, query: SearchQuery) -> SearchResult:
        return await self._search.search(query)

    async def facets(self) -> Facets:
        """Filter options with hit counts, so the UI never invents its own values."""
        return await self._search.facets()

    async def get_profile(self, profile_id: int) -> ProfileDetail:
        """Full record, always read from the relational store (the source of truth)."""
        profile = await self._profiles.get_by_id(profile_id)
        if profile is None:
            raise ProfileNotFoundError(profile_id)
        return profile

    async def health(self) -> dict[str, object]:
        return {
            "profiles": await self._profiles.count(),
            "search_backend": self._search.name,
            "search_backend_ready": await self._search.ping(),
        }

"""Ports (interfaces) the service layer depends on.

Dependency Inversion: `ProfileSearchService` is written against these Protocols,
never against Elasticsearch or SQLAlchemy. Adapters live in `app.repositories`
and are chosen at composition time in `app.api.deps`.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from app.schemas.facets import Facets
from app.schemas.profile import ProfileDetail
from app.schemas.search import SearchQuery, SearchResult


@runtime_checkable
class ProfileSearchPort(Protocol):
    """Keyword search + filtering + facet aggregation over profiles."""

    name: str

    async def search(self, query: SearchQuery) -> SearchResult: ...

    async def facets(self) -> Facets: ...

    async def ping(self) -> bool:
        """Report whether the backing store is reachable (used by /health)."""
        ...


@runtime_checkable
class ProfileRepositoryPort(Protocol):
    """Canonical record lookup, always served by the relational store."""

    async def get_by_id(self, profile_id: int) -> ProfileDetail | None: ...

    async def count(self) -> int: ...

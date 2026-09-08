"""Composition root: wires concrete adapters into the service via `Depends`.

This is the single place that knows which implementation satisfies which port.
"""

from __future__ import annotations

from typing import Annotated

from elasticsearch import AsyncElasticsearch
from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import SearchBackend, Settings, get_settings
from app.db.session import get_session
from app.domain.ports import ProfileRepositoryPort, ProfileSearchPort
from app.repositories.es_search_repository import ElasticsearchSearchRepository
from app.repositories.sql_profile_repository import SqlProfileRepository
from app.repositories.sql_search_repository import SqlSearchRepository
from app.services.profile_search_service import ProfileSearchService

SettingsDep = Annotated[Settings, Depends(get_settings)]
SessionDep = Annotated[AsyncSession, Depends(get_session)]


def get_elasticsearch(request: Request) -> AsyncElasticsearch:
    """The client created once by the app lifespan."""
    client = getattr(request.app.state, "elasticsearch", None)
    if client is None:  # pragma: no cover - only when misconfigured
        raise RuntimeError("Elasticsearch client is not initialised")
    return client


def get_profile_repository(session: SessionDep) -> ProfileRepositoryPort:
    return SqlProfileRepository(session)


def get_search_repository(
    request: Request,
    session: SessionDep,
    settings: SettingsDep,
) -> ProfileSearchPort:
    if settings.search_backend is SearchBackend.ELASTICSEARCH:
        return ElasticsearchSearchRepository(
            client=get_elasticsearch(request),
            index=settings.elasticsearch_index,
            facet_size=settings.facet_size,
        )
    return SqlSearchRepository(session, facet_size=settings.facet_size)


def get_search_service(
    search: Annotated[ProfileSearchPort, Depends(get_search_repository)],
    profiles: Annotated[ProfileRepositoryPort, Depends(get_profile_repository)],
) -> ProfileSearchService:
    return ProfileSearchService(search=search, profiles=profiles)


ServiceDep = Annotated[ProfileSearchService, Depends(get_search_service)]

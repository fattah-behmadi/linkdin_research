"""Profile search endpoints."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Path, Query

from app.api.deps import ServiceDep
from app.schemas.facets import Facets
from app.schemas.profile import ProfileDetail
from app.schemas.search import SearchQuery, SearchResult

router = APIRouter(prefix="/profiles", tags=["profiles"])


@router.get("/search", response_model=SearchResult, summary="Keyword search with filters")
async def search_profiles(
    service: ServiceDep,
    query: Annotated[SearchQuery, Query()],
) -> SearchResult:
    """Free-text search over names, titles, companies, skills, education and summaries.

    Filters are AND-ed with each other; values within one filter are OR-ed,
    except `skills`, where a profile must have every requested skill.
    """
    return await service.search(query)


@router.get("/facets", response_model=Facets, summary="Available filter values")
async def get_facets(service: ServiceDep) -> Facets:
    return await service.facets()


@router.get("/{profile_id}", response_model=ProfileDetail, summary="Full profile")
async def get_profile(
    service: ServiceDep,
    profile_id: Annotated[int, Path(ge=1)],
) -> ProfileDetail:
    return await service.get_profile(profile_id)

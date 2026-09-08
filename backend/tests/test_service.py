"""The service is written against the ports, so it can be tested without any I/O.

These stubs are also the proof that the port abstraction actually holds: nothing
here imports SQLAlchemy or Elasticsearch.
"""

from __future__ import annotations

import pytest

from app.core.exceptions import ProfileNotFoundError
from app.repositories.sql_search_repository import to_match_expression
from app.schemas.facets import Facets, FacetValue
from app.schemas.profile import ProfileDetail
from app.schemas.search import SearchQuery, SearchResult
from app.services.profile_search_service import ProfileSearchService


class StubSearch:
    name = "stub"

    def __init__(self) -> None:
        self.received: SearchQuery | None = None

    async def search(self, query: SearchQuery) -> SearchResult:
        self.received = query
        return SearchResult(items=[], total=0, page=query.page, size=query.size, backend=self.name)

    async def facets(self) -> Facets:
        return Facets(skills=[FacetValue(value="python", count=3)])

    async def ping(self) -> bool:
        return True


class StubRepository:
    def __init__(self, profile: ProfileDetail | None = None) -> None:
        self._profile = profile

    async def get_by_id(self, profile_id: int) -> ProfileDetail | None:
        return self._profile if self._profile and self._profile.id == profile_id else None

    async def count(self) -> int:
        return 1 if self._profile else 0


PROFILE = ProfileDetail(id=7, full_name="ada lovelace")


async def test_search_is_delegated_to_the_configured_backend() -> None:
    search = StubSearch()
    service = ProfileSearchService(search=search, profiles=StubRepository())

    result = await service.search(SearchQuery(q="python", page=2, size=5))

    assert search.received is not None
    assert search.received.q == "python"
    assert result.backend == "stub"


async def test_facets_come_from_the_search_backend() -> None:
    service = ProfileSearchService(search=StubSearch(), profiles=StubRepository())

    assert (await service.facets()).skills[0].value == "python"


async def test_profile_detail_is_read_from_the_relational_store() -> None:
    service = ProfileSearchService(search=StubSearch(), profiles=StubRepository(PROFILE))

    assert (await service.get_profile(7)).full_name == "ada lovelace"


async def test_missing_profile_raises_a_domain_error() -> None:
    service = ProfileSearchService(search=StubSearch(), profiles=StubRepository())

    with pytest.raises(ProfileNotFoundError) as error:
        await service.get_profile(7)

    assert error.value.status_code == 404


async def test_health_combines_both_ports() -> None:
    service = ProfileSearchService(search=StubSearch(), profiles=StubRepository(PROFILE))

    assert await service.health() == {
        "profiles": 1,
        "search_backend": "stub",
        "search_backend_ready": True,
    }


@pytest.mark.parametrize(
    ("keywords", "expected"),
    [
        ("data science", '"data"* "science"*'),
        ('  "quoted" OR (dropped)  ', '"quoted"* "OR"* "dropped"*'),
        ("c++", '"c++"*'),  # kept whole: FTS5 tokenises inside the quoted phrase
        ("***", None),
        ("", None),
    ],
)
def test_fts_expressions_are_sanitised(keywords: str, expected: str | None) -> None:
    """User input must never reach FTS5 as syntax."""
    assert to_match_expression(keywords) == expected

"""End-to-end API tests against the SQLite/FTS5 search backend."""

from __future__ import annotations

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncEngine

from app.etl.load_sql import load
from tests.conftest import SAMPLE_PROFILES

SEARCH = "/api/v1/profiles/search"


async def names(client: AsyncClient, **params: object) -> list[str]:
    response = await client.get(SEARCH, params=params)
    assert response.status_code == 200, response.text
    return [item["full_name"] for item in response.json()["items"]]


async def test_lists_everything_when_no_query_is_given(client: AsyncClient) -> None:
    response = await client.get(SEARCH)
    body = response.json()

    assert body["total"] == 4
    assert body["pages"] == 1
    assert body["backend"] == "sql"
    assert [item["full_name"] for item in body["items"]] == [
        "ada lovelace",
        "grace hopper",
        "linus torvalds",
        "marie curie",
    ]


async def test_keyword_search_covers_skills_titles_and_education(client: AsyncClient) -> None:
    assert set(await names(client, q="python")) == {"ada lovelace", "grace hopper"}
    assert await names(client, q="kernel") == ["linus torvalds"]
    assert await names(client, q="sorbonne") == ["marie curie"]
    assert await names(client, q="tu berlin") == ["ada lovelace"]


async def test_keyword_search_matches_prefixes(client: AsyncClient) -> None:
    assert await names(client, q="compil") == ["grace hopper"]


async def test_keyword_search_is_scored(client: AsyncClient) -> None:
    body = (await client.get(SEARCH, params={"q": "engineer"})).json()
    scores = [item["score"] for item in body["items"]]

    assert all(score is not None for score in scores)
    assert scores == sorted(scores, reverse=True)


@pytest.mark.parametrize(
    ("params", "expected"),
    [
        ({"countries": "germany"}, ["ada lovelace"]),
        ({"industries": "research"}, ["marie curie"]),
        ({"seniorities": "director"}, ["grace hopper", "marie curie"]),
        ({"company_sizes": ["1-10", "10001+"]}, ["grace hopper", "linus torvalds"]),
        ({"min_years": 20}, ["grace hopper", "linus torvalds"]),
        ({"min_years": 10, "max_years": 20}, ["marie curie"]),
        ({"skills": "python"}, ["ada lovelace", "grace hopper"]),
    ],
)
async def test_filters(client: AsyncClient, params: dict[str, object], expected: list[str]) -> None:
    assert sorted(await names(client, **params)) == sorted(expected)


async def test_multiple_skills_are_required_together(client: AsyncClient) -> None:
    assert await names(client, skills=["python", "cobol"]) == ["grace hopper"]
    assert await names(client, skills=["python", "linux"]) == []


async def test_filters_combine_with_keywords(client: AsyncClient) -> None:
    assert await names(client, q="engineer", countries="germany") == ["ada lovelace"]


async def test_filter_values_are_normalised(client: AsyncClient) -> None:
    assert await names(client, countries="  GERMANY ") == ["ada lovelace"]


async def test_sorting(client: AsyncClient) -> None:
    assert (await names(client, sort="experience_desc"))[0] == "linus torvalds"
    assert (await names(client, sort="experience_asc"))[0] == "ada lovelace"
    assert (await names(client, sort="name"))[0] == "ada lovelace"


async def test_pagination(client: AsyncClient) -> None:
    body = (await client.get(SEARCH, params={"size": 3, "page": 2})).json()

    assert body["total"] == 4
    assert body["pages"] == 2
    assert [item["full_name"] for item in body["items"]] == ["marie curie"]


async def test_facets_expose_filter_values_with_counts(client: AsyncClient) -> None:
    facets = (await client.get("/api/v1/profiles/facets")).json()

    assert {"value": "python", "count": 2} in facets["skills"]
    assert {"value": "computer software", "count": 3} in facets["industries"]
    assert {"value": "director", "count": 2} in facets["seniorities"]
    assert len(facets["countries"]) == 4


async def test_profile_detail(client: AsyncClient) -> None:
    profile_id = (await client.get(SEARCH, params={"q": "ada"})).json()["items"][0]["id"]
    body = (await client.get(f"/api/v1/profiles/{profile_id}")).json()

    assert body["full_name"] == "ada lovelace"
    assert body["headline"] == "senior backend engineer at acme corp"
    assert body["experiences"][0]["company_name"] == "acme corp"
    assert body["educations"][0]["majors"] == ["computer science"]


async def test_unknown_profile_returns_a_typed_error(client: AsyncClient) -> None:
    response = await client.get("/api/v1/profiles/424242")

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "profile_not_found"


@pytest.mark.parametrize(
    "params",
    [
        {"unknown_filter": "x"},
        {"page": 0},
        {"size": 500},
        {"min_years": 10, "max_years": 5},
        {"sort": "salary"},
    ],
)
async def test_invalid_requests_are_rejected(client: AsyncClient, params: dict) -> None:
    assert (await client.get(SEARCH, params=params)).status_code == 422


async def test_health_reports_the_active_backend(client: AsyncClient) -> None:
    body = (await client.get("/api/v1/health")).json()

    assert body == {
        "status": "ok",
        "profiles": 4,
        "search_backend": "sql",
        "search_backend_ready": True,
    }


async def test_reloading_the_dataset_is_idempotent(
    engine: AsyncEngine, client: AsyncClient
) -> None:
    """A second ETL run must replace the data, including the FTS index."""
    await load(engine, SAMPLE_PROFILES)

    body = (await client.get(SEARCH, params={"q": "python"})).json()
    assert body["total"] == 2
    assert (await client.get("/api/v1/health")).json()["profiles"] == 4

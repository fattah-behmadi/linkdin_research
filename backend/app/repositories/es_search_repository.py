"""Elasticsearch search adapter: keyword search, filters and facet aggregations."""

from __future__ import annotations

import logging
from typing import Any

from elastic_transport import TransportError
from elasticsearch import AsyncElasticsearch

from app.core.exceptions import SearchBackendUnavailableError
from app.repositories.mappers import source_to_summary
from app.schemas.facets import Facets, FacetValue
from app.schemas.search import SearchQuery, SearchResult, SortOption

logger = logging.getLogger(__name__)

SEARCH_FIELDS = [
    "full_name^8",
    "job_title^6",
    "skills^4",
    "experience_titles^3",
    "company_name^3",
    "headline^2",
    "education^2",
    "location_name",
    "summary",
]

# facet name -> aggregated field
FACET_FIELDS = {
    "skills": "skills.keyword",
    "industries": "industry",
    "countries": "country",
    "seniorities": "seniority",
    "company_sizes": "company_size",
}

TERM_FILTERS = {
    "industries": "industry",
    "countries": "country",
    "seniorities": "seniority",
    "company_sizes": "company_size",
}


class ElasticsearchSearchRepository:
    """Implements `ProfileSearchPort` on top of Elasticsearch 8."""

    name = "elasticsearch"

    def __init__(self, client: AsyncElasticsearch, index: str, facet_size: int = 25) -> None:
        self._client = client
        self._index = index
        self._facet_size = facet_size

    # -- port ---------------------------------------------------------------
    async def search(self, query: SearchQuery) -> SearchResult:
        response = await self._execute(
            query=self._build_query(query),
            sort=self._build_sort(query),
            from_=query.offset,
            size=query.size,
            track_total_hits=True,
        )
        hits = response["hits"]
        return SearchResult(
            items=[source_to_summary(hit["_source"], hit.get("_score")) for hit in hits["hits"]],
            total=hits["total"]["value"],
            page=query.page,
            size=query.size,
            took_ms=response.get("took", 0),
            backend=self.name,
        )

    async def facets(self) -> Facets:
        response = await self._execute(
            size=0,
            aggs={
                name: {"terms": {"field": field, "size": self._facet_size}}
                for name, field in FACET_FIELDS.items()
            },
        )
        aggregations = response.get("aggregations", {})
        return Facets(
            **{
                name: [
                    FacetValue(value=bucket["key"], count=bucket["doc_count"])
                    for bucket in aggregations.get(name, {}).get("buckets", [])
                ]
                for name in FACET_FIELDS
            }
        )

    async def ping(self) -> bool:
        try:
            return bool(await self._client.ping())
        except TransportError:
            return False

    # -- query building -----------------------------------------------------
    def _build_query(self, query: SearchQuery) -> dict[str, Any]:
        must: list[dict[str, Any]] = []
        if query.q:
            must.append(
                {
                    "multi_match": {
                        "query": query.q,
                        "fields": SEARCH_FIELDS,
                        "type": "best_fields",
                        "operator": "and",
                        "fuzziness": "AUTO",
                    }
                }
            )

        filters: list[dict[str, Any]] = [
            {"terms": {field: getattr(query, name)}}
            for name, field in TERM_FILTERS.items()
            if getattr(query, name)
        ]
        # Every requested skill must be present (AND), not just any of them.
        filters += [{"term": {"skills.keyword": skill}} for skill in query.skills]

        if query.min_years is not None or query.max_years is not None:
            bounds = {}
            if query.min_years is not None:
                bounds["gte"] = query.min_years
            if query.max_years is not None:
                bounds["lte"] = query.max_years
            filters.append({"range": {"years_experience": bounds}})

        if not must and not filters:
            return {"match_all": {}}
        return {"bool": {"must": must or [{"match_all": {}}], "filter": filters}}

    def _build_sort(self, query: SearchQuery) -> list[Any]:
        match query.sort:
            case SortOption.EXPERIENCE_DESC:
                return [{"years_experience": {"order": "desc", "missing": "_last"}}, {"id": "asc"}]
            case SortOption.EXPERIENCE_ASC:
                return [{"years_experience": {"order": "asc", "missing": "_last"}}, {"id": "asc"}]
            case SortOption.NAME:
                return [{"full_name.keyword": "asc"}, {"id": "asc"}]
            case _:
                return ["_score", {"id": "asc"}] if query.q else [{"full_name.keyword": "asc"}]

    async def _execute(self, **body: Any) -> dict[str, Any]:
        try:
            response = await self._client.search(index=self._index, **body)
        except TransportError as error:  # connection refused, index missing, ...
            logger.warning("Elasticsearch request failed: %s", error)
            raise SearchBackendUnavailableError(
                "Elasticsearch is not reachable. Start it with `docker compose up -d` "
                "and run the indexer, or set SEARCH_BACKEND=sql."
            ) from error
        return response.body

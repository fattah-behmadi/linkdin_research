"""SQLite search adapter: FTS5 for keywords, plain SQL for filters and facets.

This is the "simple database search" option. It implements the same
`ProfileSearchPort` as the Elasticsearch adapter, so the API behaves identically
with or without a running Elasticsearch container.
"""

from __future__ import annotations

import re
import time
from typing import Any

from sqlalchemy import Float, Integer, Select, func, select, text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql.elements import ColumnElement
from sqlalchemy.sql.selectable import Subquery

from app.db.models import Profile, Skill, profile_skills
from app.repositories.mappers import profile_to_summary
from app.schemas.facets import Facets, FacetValue
from app.schemas.search import SearchQuery, SearchResult, SortOption

# Keep only token characters FTS5 is happy with; quoting each token then makes
# the MATCH expression injection-proof.
TOKEN = re.compile(r"[^\W_]+[\w'&+.#-]*", re.UNICODE)
MAX_TOKENS = 12

# bm25 column weights, in the order the FTS table declares them:
# full_name, job_title, company, summary, skills, education.
BM25 = "bm25(profiles_fts, 8.0, 5.0, 3.0, 1.0, 4.0, 2.0)"


def to_match_expression(keywords: str) -> str | None:
    """Turn free text into a safe FTS5 MATCH expression with prefix matching."""
    tokens = TOKEN.findall(keywords)[:MAX_TOKENS]
    return " ".join(f'"{token}"*' for token in tokens) or None


class SqlSearchRepository:
    """Implements `ProfileSearchPort` on top of SQLite."""

    name = "sql"

    def __init__(self, session: AsyncSession, facet_size: int = 25) -> None:
        self._session = session
        self._facet_size = facet_size

    # -- port ---------------------------------------------------------------
    async def search(self, query: SearchQuery) -> SearchResult:
        started = time.perf_counter()
        fts = self._fts_subquery(query)
        rank = fts.c.rank if fts is not None else None

        filtered = self._apply_filters(select(Profile.id), query, fts)
        total = await self._session.scalar(select(func.count()).select_from(filtered.subquery()))

        columns: list[Any] = [Profile] if rank is None else [Profile, rank]
        statement = self._apply_filters(select(*columns), query, fts)
        statement = self._apply_sort(statement, query, rank)
        rows = await self._session.execute(statement.offset(query.offset).limit(query.size))

        items = [
            profile_to_summary(row[0], score=None if rank is None else -float(row[1]))
            for row in rows.all()
        ]
        return SearchResult(
            items=items,
            total=total or 0,
            page=query.page,
            size=query.size,
            took_ms=int((time.perf_counter() - started) * 1000),
            backend=self.name,
        )

    async def facets(self) -> Facets:
        return Facets(
            skills=await self._skill_facet(),
            industries=await self._column_facet(Profile.industry),
            countries=await self._column_facet(Profile.country),
            seniorities=await self._column_facet(Profile.seniority),
            company_sizes=await self._column_facet(Profile.company_size),
        )

    async def ping(self) -> bool:
        await self._session.execute(select(1))
        return True

    # -- query building -----------------------------------------------------
    def _fts_subquery(self, query: SearchQuery) -> Subquery | None:
        """Materialise the FTS hit list as a joinable subquery carrying its bm25 rank."""
        match = to_match_expression(query.q) if query.q else None
        if match is None:
            return None
        return (
            text(
                f"SELECT rowid AS profile_id, {BM25} AS rank "
                "FROM profiles_fts WHERE profiles_fts MATCH :match"
            )
            .bindparams(match=match)
            .columns(profile_id=Integer, rank=Float)
            .subquery("fts")
        )

    def _apply_filters(
        self,
        statement: Select[Any],
        query: SearchQuery,
        fts: Subquery | None,
    ) -> Select[Any]:
        if fts is not None:
            statement = statement.join(fts, fts.c.profile_id == Profile.id)

        if query.industries:
            statement = statement.where(Profile.industry.in_(query.industries))
        if query.countries:
            statement = statement.where(Profile.country.in_(query.countries))
        if query.seniorities:
            statement = statement.where(Profile.seniority.in_(query.seniorities))
        if query.company_sizes:
            statement = statement.where(Profile.company_size.in_(query.company_sizes))
        if query.min_years is not None:
            statement = statement.where(Profile.years_experience >= query.min_years)
        if query.max_years is not None:
            statement = statement.where(Profile.years_experience <= query.max_years)
        # Every requested skill must be present (AND), not just any of them.
        for skill in query.skills:
            statement = statement.where(Profile.skills.any(Skill.name == skill))
        return statement

    def _apply_sort(
        self,
        statement: Select[Any],
        query: SearchQuery,
        rank: ColumnElement[float] | None,
    ) -> Select[Any]:
        match query.sort:
            case SortOption.EXPERIENCE_DESC:
                return statement.order_by(Profile.years_experience.desc().nullslast(), Profile.id)
            case SortOption.EXPERIENCE_ASC:
                return statement.order_by(Profile.years_experience.asc().nullslast(), Profile.id)
            case SortOption.NAME:
                return statement.order_by(Profile.full_name.asc(), Profile.id)
            case _:
                # bm25 returns a negative score where "more negative" is better.
                if rank is not None:
                    return statement.order_by(rank.asc(), Profile.id)
                return statement.order_by(Profile.full_name.asc(), Profile.id)

    # -- facets -------------------------------------------------------------
    async def _column_facet(self, column: ColumnElement[str | None]) -> list[FacetValue]:
        total = func.count().label("total")
        rows = await self._session.execute(
            select(column, total)
            .where(column.is_not(None))
            .group_by(column)
            .order_by(total.desc(), column.asc())
            .limit(self._facet_size)
        )
        return [FacetValue(value=value, count=count) for value, count in rows.all()]

    async def _skill_facet(self) -> list[FacetValue]:
        total = func.count(profile_skills.c.profile_id).label("total")
        rows = await self._session.execute(
            select(Skill.name, total)
            .join(profile_skills, profile_skills.c.skill_id == Skill.id)
            .group_by(Skill.name)
            .order_by(total.desc(), Skill.name.asc())
            .limit(self._facet_size)
        )
        return [FacetValue(value=name, count=count) for name, count in rows.all()]

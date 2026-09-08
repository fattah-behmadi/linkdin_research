"""Search request/response contract.

`SearchQuery` doubles as the FastAPI query-parameter model and as the input of
the search port, so route, service and adapters all agree on one validated shape.
"""

from __future__ import annotations

from enum import StrEnum
from typing import Annotated, Self

from pydantic import BaseModel, ConfigDict, Field, computed_field, field_validator, model_validator

from app.schemas.profile import ProfileSummary


class SortOption(StrEnum):
    RELEVANCE = "relevance"
    EXPERIENCE_DESC = "experience_desc"
    EXPERIENCE_ASC = "experience_asc"
    NAME = "name"


def _normalize(values: list[str]) -> list[str]:
    """Dataset values are lower-cased and trimmed; align user input with them."""
    seen: dict[str, None] = {}
    for value in values:
        cleaned = value.strip().lower()
        if cleaned:
            seen.setdefault(cleaned, None)
    return list(seen)


class SearchQuery(BaseModel):
    """Validated search request. Unknown query parameters are rejected."""

    model_config = ConfigDict(extra="forbid")

    q: Annotated[str | None, Field(default=None, max_length=200, description="Free-text keywords.")]

    # --- Filters (all are AND-ed together; values inside one filter are OR-ed,
    #     except `skills`, where every requested skill must be present) -------
    skills: Annotated[list[str], Field(default_factory=list)]
    industries: Annotated[list[str], Field(default_factory=list)]
    countries: Annotated[list[str], Field(default_factory=list)]
    seniorities: Annotated[list[str], Field(default_factory=list)]
    company_sizes: Annotated[list[str], Field(default_factory=list)]
    min_years: Annotated[float | None, Field(default=None, ge=0, le=60)]
    max_years: Annotated[float | None, Field(default=None, ge=0, le=60)]

    # --- Paging & ordering -------------------------------------------------
    page: Annotated[int, Field(default=1, ge=1, le=1000)]
    size: Annotated[int, Field(default=20, ge=1, le=100)]
    sort: SortOption = SortOption.RELEVANCE

    @field_validator(
        "skills", "industries", "countries", "seniorities", "company_sizes", mode="after"
    )
    @classmethod
    def _normalize_lists(cls, values: list[str]) -> list[str]:
        return _normalize(values)

    @field_validator("q", mode="after")
    @classmethod
    def _clean_q(cls, value: str | None) -> str | None:
        cleaned = (value or "").strip()
        return cleaned or None

    @model_validator(mode="after")
    def _check_years_range(self) -> Self:
        both_set = self.min_years is not None and self.max_years is not None
        if both_set and self.min_years > self.max_years:  # type: ignore[operator]
            raise ValueError("min_years must be less than or equal to max_years")
        return self

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.size

    @property
    def has_filters(self) -> bool:
        return bool(
            self.skills
            or self.industries
            or self.countries
            or self.seniorities
            or self.company_sizes
            or self.min_years is not None
            or self.max_years is not None
        )


class SearchResult(BaseModel):
    """Adapter-agnostic search result — also the wire response of `/profiles/search`."""

    items: list[ProfileSummary]
    total: int
    page: int
    size: int
    took_ms: int = 0
    backend: str = "sql"

    @computed_field  # type: ignore[prop-decorator]
    @property
    def pages(self) -> int:
        return max(1, -(-self.total // self.size))

"""Facet DTOs — the values the UI renders as filter options, with hit counts."""

from __future__ import annotations

from pydantic import BaseModel, Field


class FacetValue(BaseModel):
    value: str
    count: int


class Facets(BaseModel):
    skills: list[FacetValue] = Field(default_factory=list)
    industries: list[FacetValue] = Field(default_factory=list)
    countries: list[FacetValue] = Field(default_factory=list)
    seniorities: list[FacetValue] = Field(default_factory=list)
    company_sizes: list[FacetValue] = Field(default_factory=list)

"""Read-side DTOs. These are the contract shared by every search adapter."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class ExperienceOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    title: str | None = None
    company_name: str | None = None
    company_industry: str | None = None
    location_name: str | None = None
    start_date: str | None = None
    end_date: str | None = None
    is_current: bool = False


class EducationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    school_name: str | None = None
    degrees: list[str] = Field(default_factory=list)
    majors: list[str] = Field(default_factory=list)
    start_date: str | None = None
    end_date: str | None = None


class ProfileSummary(BaseModel):
    """Shape returned by search hits — cheap to build from SQL rows or ES `_source`."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    full_name: str
    headline: str | None = None
    job_title: str | None = None
    company_name: str | None = None
    industry: str | None = None
    location_name: str | None = None
    country: str | None = None
    seniority: str | None = None
    years_experience: float | None = None
    linkedin_url: str | None = None
    skills: list[str] = Field(default_factory=list)
    score: float | None = Field(default=None, description="Relevance score of the search hit.")


class ProfileDetail(ProfileSummary):
    """Full profile, served by `GET /profiles/{id}` from the relational store."""

    summary: str | None = None
    company_size: str | None = None
    company_industry: str | None = None
    connections: int | None = None
    inferred_salary: str | None = None
    experiences: list[ExperienceOut] = Field(default_factory=list)
    educations: list[EducationOut] = Field(default_factory=list)

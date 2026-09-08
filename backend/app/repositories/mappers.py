"""ORM/Elasticsearch -> DTO mapping, kept in one place so both adapters agree."""

from __future__ import annotations

from typing import Any

from app.db.models import Profile
from app.schemas.profile import EducationOut, ExperienceOut, ProfileDetail, ProfileSummary


def _split(value: str | None) -> list[str]:
    return [part.strip() for part in (value or "").split(",") if part.strip()]


def profile_to_summary(profile: Profile, score: float | None = None) -> ProfileSummary:
    return ProfileSummary(
        id=profile.id,
        full_name=profile.full_name,
        headline=profile.headline,
        job_title=profile.job_title,
        company_name=profile.company_name,
        industry=profile.industry,
        location_name=profile.location_name,
        country=profile.country,
        seniority=profile.seniority,
        years_experience=profile.years_experience,
        linkedin_url=profile.linkedin_url,
        skills=[skill.name for skill in profile.skills],
        score=score,
    )


def profile_to_detail(profile: Profile) -> ProfileDetail:
    return ProfileDetail(
        **profile_to_summary(profile).model_dump(),
        summary=profile.summary,
        company_size=profile.company_size,
        company_industry=profile.company_industry,
        connections=profile.connections,
        inferred_salary=profile.inferred_salary,
        experiences=[
            ExperienceOut(
                title=item.title,
                company_name=item.company_name,
                company_industry=item.company_industry,
                location_name=item.location_name,
                start_date=item.start_date,
                end_date=item.end_date,
                is_current=item.is_current,
            )
            for item in profile.experiences
        ],
        educations=[
            EducationOut(
                school_name=item.school_name,
                degrees=_split(item.degrees),
                majors=_split(item.majors),
                start_date=item.start_date,
                end_date=item.end_date,
            )
            for item in profile.educations
        ],
    )


def source_to_summary(source: dict[str, Any], score: float | None = None) -> ProfileSummary:
    """Map an Elasticsearch `_source` document back to the shared DTO."""
    return ProfileSummary(
        id=int(source["id"]),
        full_name=source.get("full_name", ""),
        headline=source.get("headline"),
        job_title=source.get("job_title"),
        company_name=source.get("company_name"),
        industry=source.get("industry"),
        location_name=source.get("location_name"),
        country=source.get("country"),
        seniority=source.get("seniority"),
        years_experience=source.get("years_experience"),
        linkedin_url=source.get("linkedin_url"),
        skills=list(source.get("skills") or []),
        score=score,
    )

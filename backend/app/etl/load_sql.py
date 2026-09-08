"""Load parsed profiles into SQLite and rebuild the FTS5 index.

The load is a full refresh: the dataset is a static snapshot, so replacing the
content is simpler (and safer) than diffing it.
"""

from __future__ import annotations

import logging
from collections.abc import Sequence

from sqlalchemy import delete, insert, select, text
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession

from app.db.models import Education, Experience, Profile, Skill, profile_skills
from app.db.session import create_schema
from app.etl.parse import ProfileRecord

logger = logging.getLogger(__name__)


def _fts_row(profile: Profile, record: ProfileRecord) -> dict[str, object]:
    """One FTS5 row per profile, keyed by `rowid` so it joins back to `profiles`."""
    education = " ".join(
        " ".join(filter(None, [item.school_name, *item.degrees, *item.majors]))
        for item in record.educations
    )
    return {
        "rowid": profile.id,
        "full_name": record.full_name,
        "job_title": " ".join(
            filter(None, [record.job_title, *(item.title or "" for item in record.experiences)])
        ),
        "company": " ".join(
            filter(
                None,
                [
                    record.company_name or "",
                    record.industry or "",
                    *(item.company_name or "" for item in record.experiences),
                ],
            )
        ),
        "summary": record.summary or "",
        "skills": " ".join(record.skills),
        "education": education,
    }


async def _upsert_skills(session: AsyncSession, records: Sequence[ProfileRecord]) -> dict[str, int]:
    names = sorted({skill for record in records for skill in record.skills})
    if names:
        await session.execute(insert(Skill), [{"name": name} for name in names])
        await session.flush()
    rows = await session.execute(select(Skill.name, Skill.id))
    return dict(rows.all())


async def clear(session: AsyncSession) -> None:
    """Truncate every table this ETL owns, including the FTS index."""
    await session.execute(delete(profile_skills))
    await session.execute(delete(Education))
    await session.execute(delete(Experience))
    await session.execute(delete(Profile))
    await session.execute(delete(Skill))
    # A contentless FTS5 table rejects DELETE; this is its documented reset command.
    await session.execute(text("INSERT INTO profiles_fts(profiles_fts) VALUES('delete-all')"))


async def load(
    engine: AsyncEngine, records: Sequence[ProfileRecord]
) -> list[tuple[int, ProfileRecord]]:
    """Replace the relational content with `records`.

    Returns each record with the primary key it was stored under, so the search
    index can be built with the same ids the API serves.
    """
    await create_schema(engine)

    async with AsyncSession(engine, expire_on_commit=False) as session, session.begin():
        await clear(session)
        skill_ids = await _upsert_skills(session, records)

        profiles = [
            Profile(
                full_name=record.full_name,
                first_name=record.first_name,
                last_name=record.last_name,
                linkedin_url=record.linkedin_url,
                linkedin_username=record.linkedin_username,
                job_title=record.job_title,
                seniority=record.seniority,
                industry=record.industry,
                company_name=record.company_name,
                company_size=record.company_size,
                company_industry=record.company_industry,
                location_name=record.location_name,
                country=record.country,
                region=record.region,
                years_experience=record.years_experience,
                connections=record.connections,
                inferred_salary=record.inferred_salary,
                summary=record.summary,
                experiences=[
                    Experience(
                        position=position,
                        title=item.title,
                        company_name=item.company_name,
                        company_industry=item.company_industry,
                        location_name=item.location_name,
                        start_date=item.start_date,
                        end_date=item.end_date,
                        is_current=item.is_current,
                    )
                    for position, item in enumerate(record.experiences)
                ],
                educations=[
                    Education(
                        position=position,
                        school_name=item.school_name,
                        degrees=", ".join(item.degrees) or None,
                        majors=", ".join(item.majors) or None,
                        start_date=item.start_date,
                        end_date=item.end_date,
                    )
                    for position, item in enumerate(record.educations)
                ],
            )
            for record in records
        ]
        session.add_all(profiles)
        await session.flush()

        links = [
            {"profile_id": profile.id, "skill_id": skill_ids[skill]}
            for profile, record in zip(profiles, records, strict=True)
            for skill in record.skills
        ]
        if links:
            await session.execute(insert(profile_skills), links)

        await session.execute(
            text(
                "INSERT INTO profiles_fts(rowid, full_name, job_title, company, summary,"
                " skills, education)"
                " VALUES (:rowid, :full_name, :job_title, :company, :summary,"
                " :skills, :education)"
            ),
            [_fts_row(profile, record) for profile, record in zip(profiles, records, strict=True)],
        )

    logger.info("Loaded %d profiles into the relational store", len(records))
    return [(profile.id, record) for profile, record in zip(profiles, records, strict=True)]

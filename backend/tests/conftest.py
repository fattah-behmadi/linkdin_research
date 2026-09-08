"""Test fixtures: a throwaway SQLite database seeded with a known set of profiles."""

from __future__ import annotations

from collections.abc import AsyncIterator
from pathlib import Path

import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncEngine, async_sessionmaker, create_async_engine

from app.core.config import SearchBackend, Settings, get_settings
from app.db.session import create_schema, get_session
from app.etl.load_sql import load
from app.etl.parse import EducationRecord, ExperienceRecord, ProfileRecord
from app.main import create_app

FIXTURES = Path(__file__).parent / "fixtures"

SAMPLE_PROFILES = [
    ProfileRecord(
        full_name="ada lovelace",
        linkedin_url="linkedin.com/in/ada-lovelace",
        job_title="senior backend engineer",
        seniority="senior",
        industry="computer software",
        company_name="acme corp",
        company_size="51-200",
        location_name="berlin, berlin, germany",
        country="germany",
        region="berlin",
        years_experience=9.0,
        summary="Builds distributed systems and APIs.",
        skills=["python", "fastapi", "sql"],
        experiences=[
            ExperienceRecord(
                title="backend engineer", company_name="acme corp", start_date="2019-01"
            )
        ],
        educations=[
            EducationRecord(
                school_name="tu berlin", degrees=["bachelors"], majors=["computer science"]
            )
        ],
    ),
    ProfileRecord(
        full_name="grace hopper",
        linkedin_url="linkedin.com/in/grace-hopper",
        job_title="director of engineering",
        seniority="director",
        industry="computer software",
        company_name="globex",
        company_size="10001+",
        location_name="new york, new york, united states",
        country="united states",
        region="new york",
        years_experience=21.0,
        summary="Compiler pioneer.",
        skills=["python", "cobol"],
    ),
    ProfileRecord(
        full_name="linus torvalds",
        linkedin_url="linkedin.com/in/linus-torvalds",
        job_title="principal kernel engineer",
        seniority="owner",
        industry="computer software",
        company_name="initech",
        company_size="1-10",
        location_name="helsinki, uusimaa, finland",
        country="finland",
        region="uusimaa",
        years_experience=30.0,
        skills=["c", "git", "linux"],
    ),
    ProfileRecord(
        full_name="marie curie",
        linkedin_url="linkedin.com/in/marie-curie",
        job_title="research director",
        seniority="director",
        industry="research",
        company_name="sorbonne",
        company_size="201-500",
        location_name="paris, ile-de-france, france",
        country="france",
        region="ile-de-france",
        years_experience=15.0,
        skills=["research", "physics"],
        educations=[EducationRecord(school_name="university of paris", degrees=["phd"])],
    ),
]


@pytest_asyncio.fixture
async def engine(tmp_path: Path) -> AsyncIterator[AsyncEngine]:
    engine = create_async_engine(f"sqlite+aiosqlite:///{(tmp_path / 'test.db').as_posix()}")
    await create_schema(engine)
    await load(engine, SAMPLE_PROFILES)
    yield engine
    await engine.dispose()


@pytest_asyncio.fixture
async def client(engine: AsyncEngine) -> AsyncIterator[AsyncClient]:
    """API client bound to the seeded test database.

    The SQL backend is forced so the suite never depends on a developer's local
    `.env` (or on a running Elasticsearch); the Elasticsearch adapter is
    exercised separately against a live container.
    """
    settings = Settings(search_backend=SearchBackend.SQL)
    app = create_app(settings)
    app.dependency_overrides[get_settings] = lambda: settings
    session_factory = async_sessionmaker(engine, expire_on_commit=False)

    async def override_session() -> AsyncIterator[object]:
        async with session_factory() as session:
            yield session

    app.dependency_overrides[get_session] = override_session
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as http:
        yield http

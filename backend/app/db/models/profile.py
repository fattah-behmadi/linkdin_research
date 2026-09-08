"""Relational schema for the LinkedIn dataset.

Denormalised "current position" columns live on `profiles` because every filter
and every list row needs them; the repeating parts of a profile (skills,
experience, education) are normalised into their own tables.
"""

from __future__ import annotations

from sqlalchemy import (
    Boolean,
    Column,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Table,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

profile_skills = Table(
    "profile_skills",
    Base.metadata,
    Column("profile_id", ForeignKey("profiles.id", ondelete="CASCADE"), primary_key=True),
    Column("skill_id", ForeignKey("skills.id", ondelete="CASCADE"), primary_key=True),
)


class Skill(Base):
    __tablename__ = "skills"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(120), unique=True, index=True)

    profiles: Mapped[list[Profile]] = relationship(
        secondary=profile_skills, back_populates="skills"
    )


class Profile(Base):
    __tablename__ = "profiles"
    __table_args__ = (
        UniqueConstraint("linkedin_url", name="uq_profiles_linkedin_url"),
        Index("ix_profiles_filters", "industry", "country", "seniority"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    # Identity
    full_name: Mapped[str] = mapped_column(String(200), index=True)
    first_name: Mapped[str | None] = mapped_column(String(100))
    last_name: Mapped[str | None] = mapped_column(String(100))
    linkedin_url: Mapped[str | None] = mapped_column(String(300))
    linkedin_username: Mapped[str | None] = mapped_column(String(160))

    # Current position (denormalised for filtering / list rendering)
    job_title: Mapped[str | None] = mapped_column(String(200), index=True)
    seniority: Mapped[str | None] = mapped_column(String(40), index=True)
    industry: Mapped[str | None] = mapped_column(String(120), index=True)
    company_name: Mapped[str | None] = mapped_column(String(200), index=True)
    company_size: Mapped[str | None] = mapped_column(String(40), index=True)
    company_industry: Mapped[str | None] = mapped_column(String(120))

    # Location
    location_name: Mapped[str | None] = mapped_column(String(200))
    country: Mapped[str | None] = mapped_column(String(80), index=True)
    region: Mapped[str | None] = mapped_column(String(120))

    # Signals
    years_experience: Mapped[float | None] = mapped_column(Float, index=True)
    connections: Mapped[int | None] = mapped_column(Integer)
    inferred_salary: Mapped[str | None] = mapped_column(String(40))
    summary: Mapped[str | None] = mapped_column(Text)

    skills: Mapped[list[Skill]] = relationship(
        secondary=profile_skills, back_populates="profiles", lazy="selectin", order_by=Skill.name
    )
    experiences: Mapped[list[Experience]] = relationship(
        back_populates="profile",
        cascade="all, delete-orphan",
        lazy="selectin",
        order_by="Experience.position",
    )
    educations: Mapped[list[Education]] = relationship(
        back_populates="profile",
        cascade="all, delete-orphan",
        lazy="selectin",
        order_by="Education.position",
    )

    @property
    def headline(self) -> str | None:
        """`job title at company` - what the result list shows under the name."""
        if self.job_title and self.company_name:
            return f"{self.job_title} at {self.company_name}"
        return self.job_title or self.company_name


class Experience(Base):
    __tablename__ = "experiences"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    profile_id: Mapped[int] = mapped_column(
        ForeignKey("profiles.id", ondelete="CASCADE"), index=True
    )
    position: Mapped[int] = mapped_column(Integer, default=0)

    title: Mapped[str | None] = mapped_column(String(200))
    company_name: Mapped[str | None] = mapped_column(String(200))
    company_industry: Mapped[str | None] = mapped_column(String(120))
    location_name: Mapped[str | None] = mapped_column(String(200))
    start_date: Mapped[str | None] = mapped_column(String(10))
    end_date: Mapped[str | None] = mapped_column(String(10))
    is_current: Mapped[bool] = mapped_column(Boolean, default=False)

    profile: Mapped[Profile] = relationship(back_populates="experiences")


class Education(Base):
    __tablename__ = "educations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    profile_id: Mapped[int] = mapped_column(
        ForeignKey("profiles.id", ondelete="CASCADE"), index=True
    )
    position: Mapped[int] = mapped_column(Integer, default=0)

    school_name: Mapped[str | None] = mapped_column(String(200), index=True)
    degrees: Mapped[str | None] = mapped_column(String(300))  # comma-separated
    majors: Mapped[str | None] = mapped_column(String(300))  # comma-separated
    start_date: Mapped[str | None] = mapped_column(String(10))
    end_date: Mapped[str | None] = mapped_column(String(10))

    profile: Mapped[Profile] = relationship(back_populates="educations")

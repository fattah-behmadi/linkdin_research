"""The parser is the riskiest part of this project: the source file is malformed
and its column layout varies per row. These tests pin that behaviour down."""

from __future__ import annotations

from app.etl.parse import load_profiles
from tests.conftest import FIXTURES

DATASET = FIXTURES / "sample_dataset.csv"


def test_both_column_layouts_produce_the_same_fields() -> None:
    """`ada` is stored in header order, `grace` in the compact layout."""
    records, _ = load_profiles(DATASET)
    by_name = {record.full_name: record for record in records}

    assert set(by_name) == {"ada lovelace", "grace hopper"}
    for record in by_name.values():
        assert record.industry == "computer software"
        assert record.company_name == "acme corp"
        assert record.company_size == "51-200"
        assert record.company_industry == "software"
        assert record.country == "germany"
        assert record.region == "berlin"
        assert record.location_name == "berlin, berlin, germany"
        assert record.seniority == "senior"
        assert record.skills == ["python", "fastapi", "sql"]
        assert record.experiences[0].title == "backend engineer"
        assert record.educations[0].school_name == "tu berlin"
        assert record.educations[0].majors == ["computer science"]

    assert by_name["ada lovelace"].job_title == "senior backend engineer"
    assert by_name["ada lovelace"].years_experience == 9.0
    assert by_name["grace hopper"].job_title == "principal engineer"
    assert by_name["grace hopper"].years_experience == 21.0


def test_broken_rows_are_reported_not_silently_shifted() -> None:
    records, report = load_profiles(DATASET)

    assert report.parsed == len(records) == 2
    assert report.skipped_malformed == 1  # the truncated `alan turing` row
    assert report.skipped_duplicate == 1
    assert "alan turing" not in {record.full_name for record in records}


def test_duplicates_keep_the_richest_record() -> None:
    """The fixture holds a second, emptier `ada lovelace` row."""
    records, _ = load_profiles(DATASET)
    ada = next(record for record in records if record.full_name == "ada lovelace")

    assert ada.job_title == "senior backend engineer"
    assert ada.skills

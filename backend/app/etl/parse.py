r"""Tolerant reader for the supplied LinkedIn export.

The delivered file is *not* a well-formed CSV, and the header line lies:

* stray CRLFs are injected inside unquoted values (``linkedin_id,\r\n47878127``);
* the export concatenates two dumps, so the header line appears twice;
* a few records have an unrelated grep dump spliced into the middle of a field;
* nested columns hold Python reprs, sometimes with backslash-escaped quotes;
* **rows do not share one column layout.** Optional blocks (the three
  ``facebook_*`` columns, the ``job_company_*`` block, ``location_metro``) are
  present in some rows and absent in others, while every row is padded back to
  77 fields. Mapping by header position silently shifts columns - dates land in
  ``country``, languages land in ``skills``.

So positions are not trusted. Every row is located structurally instead: the
``experience`` column is found by content, and the surrounding columns are read
at their fixed offsets from it (the source schema keeps
``summary, phone_numbers, emails, interests, skills, location_names, regions,
countries, street_addresses, experience, education, ...`` contiguous). The
job block is anchored on ``job_title_levels``, the first list-shaped column of
a row. Candidates that cannot be located are reported as skipped rather than
silently producing shifted columns.
"""

from __future__ import annotations

import ast
import csv
import io
import logging
import re
from collections.abc import Iterator
from dataclasses import dataclass, field
from pathlib import Path

logger = logging.getLogger(__name__)

csv.field_size_limit(1 << 24)

# A record starts on a new line with `full_name,first_name,` - plain name-ish text.
RECORD_START = re.compile(r"\r?\n *(?=[A-Za-z][A-Za-z .'\-]{1,50},[A-Za-z][A-Za-z .'\-]{0,30},)")
INJECTED_NEWLINE = re.compile(r"\r?\n *")
DATE = re.compile(r"^\d{4}-\d{2}(-\d{2})?$")
HEADER_PREFIX = "full_name,first_name,last_name"

NULLISH = {"", "none", "null", "nan", "[]", "{}"}

# LinkedIn's closed set of company-size buckets. Matching against the set (and
# not a `\d+-\d+` pattern) keeps dates like `2018-03` out of the column.
COMPANY_SIZES = {
    "1-10",
    "11-50",
    "51-200",
    "201-500",
    "501-1000",
    "1001-5000",
    "5001-10000",
    "10001+",
}

# `job_title_levels` values in this dataset (used to validate the job anchor).
SENIORITY_LEVELS = {
    "cxo",
    "director",
    "entry",
    "manager",
    "owner",
    "partner",
    "senior",
    "training",
    "unpaid",
    "vp",
}

# `job_title_role` values in this dataset (a closed vocabulary; used to tell
# whether a row actually carries that column).
JOB_ROLES = {
    "advisory",
    "analyst",
    "customer_service",
    "design",
    "education",
    "engineering",
    "finance",
    "health",
    "human_resources",
    "information_technology",
    "legal",
    "marketing",
    "media",
    "operations",
    "partnerships",
    "product",
    "professional_service",
    "public_relations",
    "real_estate",
    "research",
    "sales",
    "trades",
    "unemployed",
}

# Offsets of the columns we consume, relative to the `experience` column.
OFFSETS_FROM_EXPERIENCE = {
    "location_region": -17,
    "location_country": -16,
    "regions": -3,
    "countries": -2,
    "linkedin_connections": -12,
    "inferred_salary": -11,
    "inferred_years_experience": -10,
    "summary": -9,
    "skills": -5,
    "location_names": -4,
    "experience": 0,
    "education": 1,
}


@dataclass(slots=True)
class ExperienceRecord:
    title: str | None = None
    company_name: str | None = None
    company_industry: str | None = None
    location_name: str | None = None
    start_date: str | None = None
    end_date: str | None = None
    is_current: bool = False


@dataclass(slots=True)
class EducationRecord:
    school_name: str | None = None
    degrees: list[str] = field(default_factory=list)
    majors: list[str] = field(default_factory=list)
    start_date: str | None = None
    end_date: str | None = None


@dataclass(slots=True)
class ProfileRecord:
    """One cleaned profile, ready for the relational loader and the ES indexer."""

    full_name: str
    first_name: str | None = None
    last_name: str | None = None
    linkedin_url: str | None = None
    linkedin_username: str | None = None
    job_title: str | None = None
    seniority: str | None = None
    industry: str | None = None
    company_name: str | None = None
    company_size: str | None = None
    company_industry: str | None = None
    location_name: str | None = None
    country: str | None = None
    region: str | None = None
    years_experience: float | None = None
    connections: int | None = None
    inferred_salary: str | None = None
    summary: str | None = None
    skills: list[str] = field(default_factory=list)
    experiences: list[ExperienceRecord] = field(default_factory=list)
    educations: list[EducationRecord] = field(default_factory=list)

    @property
    def dedupe_key(self) -> str:
        return (self.linkedin_url or self.linkedin_username or self.full_name).strip().lower()

    @property
    def completeness(self) -> int:
        """How many useful fields are populated - used to pick the best duplicate."""
        scalars = sum(
            1
            for value in (
                self.job_title,
                self.industry,
                self.company_name,
                self.country,
                self.summary,
                self.years_experience,
            )
            if value not in (None, "")
        )
        return scalars + len(self.skills) + len(self.experiences) + len(self.educations)


@dataclass(slots=True)
class ParseReport:
    total_candidates: int = 0
    parsed: int = 0
    skipped_malformed: int = 0
    skipped_unlocatable: int = 0
    skipped_duplicate: int = 0

    def as_dict(self) -> dict[str, int]:
        return {
            "candidates": self.total_candidates,
            "parsed": self.parsed,
            "skipped_malformed": self.skipped_malformed,
            "skipped_unlocatable": self.skipped_unlocatable,
            "skipped_duplicate": self.skipped_duplicate,
        }


# --------------------------------------------------------------------------- #
# Field coercion
# --------------------------------------------------------------------------- #
def _text(value: str | None, limit: int | None = None) -> str | None:
    if value is None:
        return None
    cleaned = " ".join(value.split()).strip()
    if cleaned.lower() in NULLISH:
        return None
    return cleaned[:limit] if limit else cleaned


def _number(value: str | None) -> float | None:
    try:
        return float(value) if value not in (None, "") else None
    except (TypeError, ValueError):
        return None


def _integer(value: str | None) -> int | None:
    number = _number(value)
    return int(number) if number is not None else None


def _literal(value: str | None) -> object:
    """Nested columns hold Python reprs; some rows escape their quotes."""
    if not value or value.strip().lower() in NULLISH:
        return None
    for candidate in (value, value.replace("\\'", "'").replace('\\"', '"')):
        try:
            return ast.literal_eval(candidate)
        except (ValueError, SyntaxError, MemoryError, RecursionError):
            continue
    return None


def _string_list(value: str | None, limit: int | None = None) -> list[str]:
    parsed = _literal(value)
    if not isinstance(parsed, list):
        return []
    cleaned = (_text(str(item)) for item in parsed if isinstance(item, str | int | float))
    unique = list(dict.fromkeys(item.lower() for item in cleaned if item))
    return unique[:limit] if limit else unique


def _dict_list(value: str | None) -> list[dict[str, object]]:
    parsed = _literal(value)
    if not isinstance(parsed, list):
        return []
    return [item for item in parsed if isinstance(item, dict)]


def _as_str_list(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    return [item.strip().lower() for item in value if isinstance(item, str) and item.strip()]


def _nested(source: dict[str, object], *path: str) -> str | None:
    cursor: object = source
    for key in path:
        if not isinstance(cursor, dict):
            return None
        cursor = cursor.get(key)
    return _text(cursor) if isinstance(cursor, str) else None


# --------------------------------------------------------------------------- #
# Structural location of a row's columns
# --------------------------------------------------------------------------- #
def _head(value: str, size: int = 400) -> str:
    return value[:size].replace("\\'", "'")


def _find(values: list[str], predicate) -> int:
    return next((index for index, value in enumerate(values) if predicate(value)), -1)


def _experience_index(values: list[str]) -> int:
    """Locate `experience`, falling back to its two immediate neighbours."""
    index = _find(values, lambda v: v.startswith("[{") and "'company':" in _head(v))
    if index >= 0:
        return index
    index = _find(values, lambda v: v.startswith("[{") and "'school':" in _head(v))
    if index >= 0:
        return index - 1
    index = _find(values, lambda v: v.startswith("[{") and "'network':" in _head(v))
    return index - 2 if index >= 0 else -1


def _levels_index(values: list[str], upper: int) -> int:
    """`job_title_levels` is the first list-shaped column of a row."""
    for index in range(6, min(upper, len(values))):
        value = values[index].strip()
        if not value.startswith("["):
            continue
        items = _string_list(value)
        if not items or set(items) <= SENIORITY_LEVELS:
            return index
    return -1


def _company_columns(values: list[str], levels: int, upper: int) -> dict[str, str]:
    """The company block is optional and reshuffled; read what is identifiable."""
    if levels < 0 or levels + 2 >= len(values):
        return {}
    # Layout with the company block inline puts `job_company_id` first; the
    # compact layout puts the name straight after the levels column.
    name = values[levels + 1] if DATE.match(values[levels + 2].strip()) else values[levels + 2]
    columns = {"job_company_name": name}

    # The company block is inline in one layout and moved to the tail in another,
    # so the size bucket is located by value rather than by position.
    size_index = next(
        (index for index, value in enumerate(values) if value.strip() in COMPANY_SIZES),
        -1,
    )
    if size_index >= 0:
        columns["job_company_size"] = values[size_index]
        if size_index + 2 < len(values):
            columns["job_company_industry"] = values[size_index + 2]
    return columns


def _current_location(values: list[str], experience: int) -> str | None:
    """`location_name` sits ~19 columns before `experience`, but the exact gap
    depends on whether the row carries `location_metro`. Accept the candidate
    that actually reads as "city, region, <one of the row's own countries>".
    """
    countries = _string_list(values[experience - 2]) if experience >= 2 else []
    for offset in (-19, -20, -18):
        index = experience + offset
        if index < 0:
            continue
        candidate = values[index].strip()
        if "," in candidate and any(candidate.lower().endswith(c) for c in countries):
            return candidate
    return None


def locate_columns(values: list[str]) -> dict[str, str] | None:
    """Map one positional row onto canonical field names, or ``None`` if unlocatable."""
    experience = _experience_index(values)
    if experience < 18 or experience >= len(values) - 1:
        return None

    columns = {
        name: values[experience + offset]
        for name, offset in OFFSETS_FROM_EXPERIENCE.items()
        if 0 <= experience + offset < len(values)
    }
    columns["full_name"] = values[0]
    columns["first_name"] = values[1]
    columns["last_name"] = values[2]
    columns["linkedin_url"] = next(
        (v for v in values[:8] if v.startswith("linkedin.com/in/")), values[4]
    )
    columns["linkedin_username"] = values[5]

    columns["location_name"] = _current_location(values, experience) or ""

    levels = _levels_index(values, upper=experience - 17)
    if levels >= 3:
        columns["job_title_levels"] = values[levels]
        # `job_title_role` is not present in every layout: keep it only when the
        # column right before the levels holds one of its known values.
        previous = values[levels - 1].strip().lower()
        has_role = previous == "" or previous in JOB_ROLES
        title = levels - 2 if has_role else levels - 1
        # A role slug sitting in the title column means the row did carry the
        # role after all (the empty-column guess above was wrong); shift back.
        if title >= 1 and values[title].strip().lower() in JOB_ROLES:
            title -= 1
        columns["job_title"] = values[title]
        # A bare number here is a facebook/linkedin id from a shorter layout.
        industry = values[title - 1] if title >= 1 else ""
        columns["industry"] = "" if industry.strip().isdigit() else industry
    columns.update(_company_columns(values, levels, upper=experience - 17))
    return columns


# --------------------------------------------------------------------------- #
# Row -> record
# --------------------------------------------------------------------------- #
def _build_experiences(raw: str | None) -> list[ExperienceRecord]:
    records = [
        ExperienceRecord(
            title=_nested(item, "title", "name"),
            company_name=_nested(item, "company", "name"),
            company_industry=_nested(item, "company", "industry"),
            location_name=_nested(item, "company", "location", "name"),
            start_date=_text(str(item.get("start_date") or "")),
            end_date=_text(str(item.get("end_date") or "")),
            is_current=not item.get("end_date") and bool(item.get("start_date")),
        )
        for item in _dict_list(raw)
    ]
    records.sort(key=lambda record: record.start_date or "", reverse=True)
    return records


def _build_educations(raw: str | None) -> list[EducationRecord]:
    records = [
        EducationRecord(
            school_name=_nested(item, "school", "name"),
            degrees=list(dict.fromkeys(_as_str_list(item.get("degrees")))),
            majors=list(dict.fromkeys(_as_str_list(item.get("majors")))),
            start_date=_text(str(item.get("start_date") or "")),
            end_date=_text(str(item.get("end_date") or "")),
        )
        for item in _dict_list(raw)
    ]
    records.sort(key=lambda record: record.end_date or "", reverse=True)
    return records


def _location_name(columns: dict[str, str], country: str | None, region: str | None) -> str | None:
    located = _text(columns.get("location_name"), 200)
    if located:
        return located
    names = _string_list(columns.get("location_names"))
    if names:
        best = next((name for name in names if region and region in name), names[0])
        return _text(best, 200)
    return _text(", ".join(part for part in (region, country) if part), 200)


def _pick(value: str | None, allowed: list[str], limit: int) -> str | None:
    """Cross-check a positional value against the row's own list column.

    `countries`/`regions` sit right next to `experience`, so they are the most
    reliably located columns in a row; they are used to reject a `location_*`
    value that a shifted layout put in the wrong place.
    """
    cleaned = _text(value, limit)
    if cleaned and (not allowed or cleaned.lower() in allowed):
        return cleaned
    return _text(allowed[0], limit) if allowed else None


def row_to_record(columns: dict[str, str]) -> ProfileRecord | None:
    full_name = _text(columns.get("full_name"), 200)
    if not full_name:
        return None

    levels = _string_list(columns.get("job_title_levels"))
    country = _pick(columns.get("location_country"), _string_list(columns.get("countries")), 80)
    region = _pick(
        columns.get("location_region"),
        [entry.split(",")[0] for entry in _string_list(columns.get("regions"))],
        120,
    )
    return ProfileRecord(
        full_name=full_name,
        first_name=_text(columns.get("first_name"), 100),
        last_name=_text(columns.get("last_name"), 100),
        linkedin_url=_text(columns.get("linkedin_url"), 300),
        linkedin_username=_text(columns.get("linkedin_username"), 160),
        job_title=_text(columns.get("job_title"), 200),
        seniority=levels[0] if levels else None,
        industry=_text(columns.get("industry"), 120),
        company_name=_text(columns.get("job_company_name"), 200),
        company_size=_text(columns.get("job_company_size"), 40),
        company_industry=_text(columns.get("job_company_industry"), 120),
        location_name=_location_name(columns, country, region),
        country=country,
        region=region,
        years_experience=_number(columns.get("inferred_years_experience")),
        connections=_integer(columns.get("linkedin_connections")),
        inferred_salary=_text(columns.get("inferred_salary"), 40),
        summary=_text(columns.get("summary")),
        skills=_string_list(columns.get("skills")),
        experiences=_build_experiences(columns.get("experience")),
        educations=_build_educations(columns.get("education")),
    )


# --------------------------------------------------------------------------- #
# File -> records
# --------------------------------------------------------------------------- #
def read_header(text: str) -> list[str]:
    first_line = text.split("\n", 1)[0]
    return next(csv.reader(io.StringIO(first_line.rstrip("\r"))))


def _scan(chunk: str, in_quotes: bool) -> tuple[int, bool]:
    """Count top-level commas in `chunk`, carrying the quote state across pieces."""
    commas = 0
    for char in chunk:
        if char == '"':
            in_quotes = not in_quotes
        elif char == "," and not in_quotes:
            commas += 1
    return commas, in_quotes


def iter_candidates(text: str, expected: int) -> Iterator[str]:
    """Split the file into record candidates.

    `RECORD_START` is deliberately permissive, so it also fires inside values
    such as ``"berlin, berlin, germany"``. Pieces are accumulated until they
    hold exactly one record worth of fields, which repairs those false splits;
    when a run overshoots, its first piece is the broken one and is emitted on
    its own (the caller reports it as malformed) instead of swallowing the
    records that follow it.
    """
    pending: list[tuple[str, int]] = []
    total = 0
    in_quotes = False

    for raw in RECORD_START.split(text)[1:]:
        if raw.startswith(HEADER_PREFIX):  # the second dump's header line
            continue
        piece = INJECTED_NEWLINE.sub("", raw)
        commas, in_quotes = _scan(piece, in_quotes)
        pending.append((piece, commas))
        total += commas

        while pending and not in_quotes and total + 1 >= expected:
            if total + 1 == expected:
                yield "".join(part for part, _ in pending)
                pending, total = [], 0
                break
            head, head_commas = pending.pop(0)  # overshoot: this piece is broken
            total -= head_commas
            yield head

    if pending:
        yield "".join(part for part, _ in pending)


def iter_rows(text: str, report: ParseReport | None = None) -> Iterator[dict[str, str] | None]:
    """Yield one canonical-key column map per record candidate (``None`` if unusable)."""
    expected = len(read_header(text))

    for candidate in iter_candidates(text, expected):
        single_line = INJECTED_NEWLINE.sub("", candidate)
        try:
            values = next(csv.reader(io.StringIO(single_line)))
        except (csv.Error, StopIteration):
            values = []
        if len(values) != expected:
            if report is not None:
                report.skipped_malformed += 1
            yield None
            continue

        columns = locate_columns(values)
        if columns is None and report is not None:
            report.skipped_unlocatable += 1
        yield columns


def load_profiles(path: Path) -> tuple[list[ProfileRecord], ParseReport]:
    """Parse the dataset file into deduplicated profile records."""
    text = path.read_text(encoding="utf-8", errors="replace", newline="")
    report = ParseReport()
    best: dict[str, ProfileRecord] = {}

    for columns in iter_rows(text, report):
        report.total_candidates += 1
        record = row_to_record(columns) if columns is not None else None
        if record is None:
            continue
        key = record.dedupe_key
        existing = best.get(key)
        if existing is None:
            best[key] = record
            continue
        report.skipped_duplicate += 1
        if record.completeness > existing.completeness:
            best[key] = record

    report.parsed = len(best)
    logger.info("Parsed dataset %s: %s", path.name, report.as_dict())
    return list(best.values()), report

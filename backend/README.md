# Backend — LinkedIn Profile Search API

FastAPI + SQLAlchemy 2 (async) + SQLite, with two interchangeable search
backends: **SQLite FTS5** (default, no Docker) and **Elasticsearch 8**.

Architecture and design notes live in the [root README](../README.md); this file
is about running and using the API.

---

## Run

```bash
python -m venv .venv
.venv\Scripts\activate            # Windows;  source .venv/bin/activate elsewhere
pip install -e ".[dev]"
cp .env.example .env

python -m app.etl                 # import the dataset (required once)
uvicorn app.main:app --reload --port 8000
```

- API: <http://localhost:8000>
- Swagger UI: <http://localhost:8000/docs>
- OpenAPI JSON: <http://localhost:8000/openapi.json>

---

## Configuration (`.env`)

| Variable                | Default                        | Purpose                                        |
| ----------------------- | ------------------------------ | ---------------------------------------------- |
| `SEARCH_BACKEND`        | `sql`                          | `sql` (SQLite FTS5) or `elasticsearch`          |
| `DATABASE_URL`          | `<repo>/data/linkedin.db`      | async SQLAlchemy URL; override to move the file |
| `ELASTICSEARCH_URL`     | `http://localhost:9200`        | only used by the `elasticsearch` backend        |
| `ELASTICSEARCH_INDEX`   | `linkedin-profiles`            | index name                                      |
| `CORS_ORIGINS`          | `["http://localhost:3000"]`    | JSON array of allowed frontend origins          |
| `DEBUG`                 | `false`                        | debug logging and SQL echo                      |

Settings are read by `pydantic-settings` (`app/core/config.py`); every variable
can also be supplied as a real environment variable.

---

## ETL

```bash
python -m app.etl                 # SQLite, plus ES when it is the configured backend
python -m app.etl --es            # force Elasticsearch indexing
python -m app.etl --no-es         # relational store only
python -m app.etl --dataset path/to/file.csv
```

The load is a **full refresh**: the dataset is a static snapshot, so the tables
and the FTS index are replaced rather than diffed. It is safe to re-run.

Every run prints what it imported and what it refused to import:

```
Parsed dataset user_linkedin.txt: {'candidates': 297, 'parsed': 246,
 'skipped_malformed': 16, 'skipped_unlocatable': 0, 'skipped_duplicate': 35}
```

---

## Endpoints

| Method | Path                      | Purpose                                     |
| ------ | ------------------------- | ------------------------------------------- |
| GET    | `/api/v1/profiles/search` | keyword search + filters + paging + sorting |
| GET    | `/api/v1/profiles/facets` | filter values with hit counts               |
| GET    | `/api/v1/profiles/{id}`   | full profile (experience, education, …)     |
| GET    | `/api/v1/health`          | row count and search-backend status         |

### `GET /api/v1/profiles/search`

| Parameter        | Type            | Notes                                                          |
| ---------------- | --------------- | -------------------------------------------------------------- |
| `q`              | string          | free text over name, title, company, skills, school, summary    |
| `skills`         | repeatable      | a profile must have **every** requested skill (AND)             |
| `industries`     | repeatable      | OR within the filter                                            |
| `countries`      | repeatable      | OR within the filter                                            |
| `seniorities`    | repeatable      | OR within the filter                                            |
| `company_sizes`  | repeatable      | OR within the filter                                            |
| `min_years`      | number, 0–60    | inferred years of experience                                    |
| `max_years`      | number, 0–60    | must be ≥ `min_years`                                           |
| `page`           | int, ≥ 1        | default 1                                                       |
| `size`           | int, 1–100      | default 20                                                      |
| `sort`           | enum            | `relevance` \| `experience_desc` \| `experience_asc` \| `name`  |

Different filters are AND-ed together. Filter values are lower-cased and trimmed
before matching. **Unknown query parameters are rejected with `422`** rather
than silently ignored.

```bash
curl "http://localhost:8000/api/v1/profiles/search?q=engineer&skills=leadership&countries=united%20states&min_years=10&sort=experience_desc"
```

```jsonc
{
  "items": [
    {
      "id": 42,
      "full_name": "…",
      "headline": "director of operations at …",
      "job_title": "director of operations",
      "company_name": "…",
      "industry": "biotechnology",
      "location_name": "rochester, new york, united states",
      "country": "united states",
      "seniority": "director",
      "years_experience": 13.0,
      "linkedin_url": "linkedin.com/in/…",
      "skills": ["leadership", "operational planning", "…"],
      "score": 12.4
    }
  ],
  "total": 23,
  "page": 1,
  "size": 20,
  "pages": 2,
  "took_ms": 25,
  "backend": "elasticsearch"
}
```

`backend` and `took_ms` are returned so the client can show which store answered
and how fast — handy when comparing the two adapters.

### Errors

Domain errors use one envelope:

```json
{ "error": { "code": "profile_not_found", "message": "Profile 999 was not found." } }
```

| Status | `code`                        | When                                          |
| ------ | ----------------------------- | --------------------------------------------- |
| 404    | `profile_not_found`           | unknown profile id                            |
| 422    | (FastAPI validation)          | bad or unknown query parameters               |
| 503    | `search_backend_unavailable`  | `SEARCH_BACKEND=elasticsearch` but ES is down |

---

## Tests

```bash
pytest                     # 39 tests
pytest tests/test_parse.py -v
ruff check .
black --check .
```

- `test_parse.py` — the malformed-CSV parser, against a synthetic fixture that
  reproduces both column layouts, the stray newlines, a duplicate and a
  truncated row.
- `test_search_api.py` — the API end to end against a real SQLite/FTS5 database
  seeded with four known profiles: keyword search, prefix matching, scoring,
  every filter, AND-ed skills, ranges, sorting, paging, facet counts, validation
  and the error envelope.
- `test_service.py` — the service against stub ports (no SQLAlchemy, no
  Elasticsearch imported), plus FTS query sanitisation.

The suite forces `SEARCH_BACKEND=sql` and its own temporary database, so it
never depends on your `.env` or on a running Elasticsearch.

---

## Layout

```
app/
├── api/
│   ├── deps.py            composition root: which adapter satisfies which port
│   └── v1/routes/         profiles.py, health.py
├── core/                  config (pydantic-settings), exceptions, logging
├── db/
│   ├── models/profile.py  Profile, Skill, Experience, Education
│   └── session.py         async engine, schema + FTS5 DDL
├── domain/ports.py        ProfileSearchPort, ProfileRepositoryPort (Protocols)
├── etl/
│   ├── parse.py           tolerant reader for the supplied dataset
│   ├── load_sql.py        full-refresh loader + FTS index build
│   └── __main__.py        the `python -m app.etl` CLI
├── repositories/          sql_search, es_search, sql_profile, mappers
├── schemas/               request/response DTOs (the shared contract)
├── search/                ES client + index mapping
├── services/              ProfileSearchService
└── main.py                app factory, lifespan, error handlers
```

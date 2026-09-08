# LinkedIn Profile Search

A small search engine over a LinkedIn profile dataset: keyword search, five
facet filters and an experience range, served by a FastAPI backend and a
Next.js frontend.

Two apps, run separately:

| App          | Stack                                             | Runs on                   | Docs                                 |
| ------------ | ------------------------------------------------- | ------------------------- | ------------------------------------ |
| **backend**  | Python 3.11+, FastAPI, SQLAlchemy 2, Elasticsearch | <http://localhost:8000>   | [backend/README.md](backend/README.md)   |
| **frontend** | Node 20+, Next.js (App Router), TypeScript, Tailwind | <http://localhost:3000> | [frontend/README.md](frontend/README.md) |

```
.
├── backend/            API + ETL + search adapters
├── frontend/           search UI
├── data/               generated SQLite database (git-ignored)
├── docker-compose.yml  Elasticsearch only - everything else runs natively
└── user_linkedin.txt   the supplied dataset
```

---

## 1. Prerequisites

- **Python 3.11+** and **Node 20+**
- **Docker** — optional. Only needed for the Elasticsearch backend; the app is
  fully functional without it (SQLite FTS5).

---

## 2. Run it

Open two terminals. The whole thing takes about three minutes from a clean
checkout.

### Terminal 1 — backend

```bash
cd backend

python -m venv .venv
.venv\Scripts\activate            # Windows (PowerShell/CMD)
# source .venv/bin/activate       # macOS / Linux

pip install -e ".[dev]"
cp .env.example .env

python -m app.etl                 # parse the dataset -> SQLite + FTS5 index
uvicorn app.main:app --reload --port 8000
```

`python -m app.etl` prints what it imported:

```
Parsed dataset user_linkedin.txt: {'candidates': 297, 'parsed': 246,
 'skipped_malformed': 16, 'skipped_unlocatable': 0, 'skipped_duplicate': 35}
Loaded 246 profiles into the relational store
```

Check it is alive:

```bash
curl http://localhost:8000/api/v1/health
# {"status":"ok","profiles":246,"search_backend":"sql","search_backend_ready":true}
```

Interactive API docs: <http://localhost:8000/docs>

### Terminal 2 — frontend

```bash
cd frontend

npm install
cp .env.example .env.local
npm run dev
```

Open <http://localhost:3000>.

That is the whole app. **No Docker is required** — with the default
`SEARCH_BACKEND=sql`, keyword search runs on SQLite's FTS5 index.

### Optional — switch to Elasticsearch

```bash
docker compose up -d              # single-node ES 8.15, security disabled
```

Wait for it to report green (about 30 s):

```bash
curl http://localhost:9200/_cluster/health
```

Then point the backend at it and rebuild the index:

```bash
# backend/.env
SEARCH_BACKEND=elasticsearch

cd backend
python -m app.etl                 # reloads SQLite and rebuilds the ES index
# restart uvicorn
```

`GET /api/v1/health` now reports `"search_backend":"elasticsearch"`, and the UI
shows the active backend next to the result count. Switching back is one line in
`.env` plus a restart — no re-import needed, both stores stay loaded.

Stop Elasticsearch with `docker compose down` (add `-v` to delete its volume).

---

## 3. Use it

Everything happens on one page.

**Search box** — free text across name, job title, company, skills, school and
summary. Typing is debounced by 300 ms, and matching is prefix-based, so
`engin` already finds engineers. Results are ranked by relevance; the previous
results stay on screen while the next ones load.

**Filters** (left column, collapsed behind a *Filters* button on mobile):

| Filter                | Behaviour                                                       |
| --------------------- | --------------------------------------------------------------- |
| Skills                | a profile must have **every** skill you tick (AND)               |
| Industry              | any of the ticked values (OR)                                    |
| Country               | any of the ticked values (OR)                                    |
| Seniority             | manager, director, senior, cxo, vp, owner, …                     |
| Company size          | 1-10 … 10001+                                                    |
| Years of experience   | numeric min/max range                                            |

Different filters are combined with AND. Every value shows how many profiles
match it, and the counts come from the search backend, so the UI never offers a
filter that returns nothing.

**Other things you can do:**

- Click any skill chip on a result card to filter by that skill.
- Skills matching your current filter are pulled to the front of each card and
  highlighted.
- Remove a filter from the chips under the search box, or use *Clear all*.
- Sort by best match, most/least experience, or name.
- *View details* expands a card and fetches the full profile — summary, the
  full work history, education and every skill. It is only fetched when you
  open it, and cached afterwards.
- The URL always mirrors the search, so any result set can be bookmarked or
  shared:
  `http://localhost:3000/?q=engineer&skills=leadership&countries=united+states&min_years=10&sort=experience_desc`

### Using the API directly

```bash
# keyword + filters + sorting
curl "http://localhost:8000/api/v1/profiles/search?q=engineer&skills=leadership&countries=united%20states&min_years=10&sort=experience_desc"

# the filter values the UI renders, with counts
curl "http://localhost:8000/api/v1/profiles/facets"

# one full profile
curl "http://localhost:8000/api/v1/profiles/1"
```

Full endpoint and parameter reference: [backend/README.md](backend/README.md).

---

## 4. Troubleshooting

**"The API is unreachable. Is the backend running?"**
The backend is not on `:8000`, or `NEXT_PUBLIC_API_BASE_URL` in
`frontend/.env.local` points elsewhere. Check `curl
http://localhost:8000/api/v1/health`.

**Results appear but the browser console shows a CORS error.**
Add the frontend's origin to `CORS_ORIGINS` in `backend/.env` and restart
uvicorn.

**`503 search_backend_unavailable`.**
`SEARCH_BACKEND=elasticsearch` but Elasticsearch is not reachable. Start it
(`docker compose up -d`), or set `SEARCH_BACKEND=sql`.

**Search returns nothing and `/health` reports `"profiles":0`.**
The ETL has not run. `cd backend && python -m app.etl`.

**`listen EACCES` on port 3000, or Docker cannot bind port 9200 (Windows).**
Hyper-V/WinNAT reserves port ranges. List them with:

```powershell
netsh interface ipv4 show excludedportrange protocol=tcp
```

On this machine both 3000 and 9200 fall inside reserved ranges, so use free
ports instead:

```bash
# frontend
npm run dev -- -p 5173

# Elasticsearch: root .env
ELASTICSEARCH_HOST_PORT=9301
```

and match them in `backend/.env`:

```
ELASTICSEARCH_URL=http://localhost:9301
CORS_ORIGINS=["http://localhost:5173"]
```

The `.env` files in this checkout are already set up this way.

---

## 5. Architecture

### Backend

```
API route  ->  ProfileSearchService  ->  ports (Protocols)  ->  adapters
                                          ProfileSearchPort  ->  ElasticsearchSearchRepository
                                                             ->  SqlSearchRepository
                                          ProfileRepositoryPort -> SqlProfileRepository
```

- **Ports** (`app/domain/ports.py`) are `typing.Protocol` interfaces. The
  service is written against them and imports neither SQLAlchemy nor
  Elasticsearch, which is what lets `tests/test_service.py` run the whole
  service against stubs.
- **`app/api/deps.py` is the composition root** — the single place that decides
  which adapter satisfies which port, wired with FastAPI `Depends`.
- **Two search adapters, one contract.** Elasticsearch is the primary one;
  SQLite FTS5 is a complete fallback so the project runs, and is testable,
  without Docker. Both return the same `SearchResult` DTO and both compute
  facets (ES `terms` aggregations vs. SQL `GROUP BY`).
- **Detail lookups always come from the relational store**, which stays the
  source of truth; the index only serves search.
- **Errors** are domain exceptions (`AppError`) translated once, in
  `app/main.py`, into `{"error": {"code", "message"}}`.

### Data model (SQLite)

```
profiles ──< experiences
    │    ──< educations
    └──< profile_skills >── skills

profiles_fts   FTS5 virtual table (full_name, job_title, company, summary,
               skills, education), rowid = profiles.id
```

Current-position fields (`job_title`, `company_name`, `company_size`,
`industry`, `seniority`, `country`, `years_experience`) are denormalised onto
`profiles` because every filter and every result row needs them; the repeating
parts of a profile are normalised into their own tables. Skills are a proper
many-to-many, so the skill facet is a `GROUP BY`, not a `LIKE`.

Keyword search uses **FTS5 with bm25 column weights** (name 8, title 5, skills
4, company 3, education 2, summary 1). User input is tokenised and each token is
quoted and prefixed (`"data"* "engineer"*`), so no user text ever reaches FTS5
as query syntax.

### Frontend

```
components  ->  React Query hooks  ->  service  ->  mapper  ->  proxy  ->  typed fetch
```

- **Proxy** (`api/profile.proxy.ts`) knows endpoints and parameter names.
- **DTOs** (`api/profile.dto.ts`) are Zod schemas — the API response is
  validated at runtime, so nothing downstream needs `any`.
- **Mapper** (`mappers/profile.mapper.ts`) is the only place that knows both the
  snake_case wire shape and the camelCase domain model.
- **Service** (`services/profile.service.ts`) composes proxy + mapper.
- **Hooks** (`hooks/use-profiles.ts`) own caching, `keepPreviousData` while
  paging, and centralised query keys.
- **Components** follow Atomic Design: `atoms/`, `molecules/`, `organisms/`,
  `templates/`.

Search state lives in the URL, parsed and serialised in
`hooks/use-search-criteria.ts`.

---

## 6. Parsing the dataset

The supplied `user_linkedin.txt` is not a well-formed CSV, and this was the
largest single piece of work. `backend/app/etl/parse.py` handles:

1. **Stray newlines inside unquoted values** (`linkedin_id,\r\n47878127`) —
   ~20 000 line breaks for ~300 records.
2. **A repeated header**: the file concatenates two dumps.
3. **A grep dump spliced into the middle of some records.**
4. **Python `repr` in the nested columns**, sometimes with escaped quotes.
5. **Rows that do not share one column layout.** Optional blocks (the three
   `facebook_*` columns, the whole `job_company_*` block, `location_metro`) are
   present in some rows and absent in others, while every row is padded back to
   77 fields. *Mapping by header position silently shifts columns* — dates land
   in `country`, languages land in `skills`.

So positions are not trusted. Each row is located structurally: the `experience`
column is found by its content and neighbouring columns are read at their fixed
offsets from it; the job block is anchored on `job_title_levels` (the first
list-shaped column) and validated against the closed vocabularies for
`job_title_role` and company size. Anything that cannot be located is counted as
skipped rather than imported with shifted columns.

246 unique profiles are imported from 297 record candidates: 35 are duplicates
(the richer copy wins) and 16 are records destroyed by the spliced-in grep dump.
`tests/test_parse.py` pins this down with a synthetic fixture reproducing both
layouts, the stray newlines, a duplicate and a truncated row.

---

## 7. Quality gates

```bash
cd backend
pytest              # 39 tests
ruff check .
black --check .

cd ../frontend
npm run lint
npm run typecheck   # tsc --noEmit, strict
npm run build
```

The backend suite covers the parser, the search API end to end against a real
SQLite/FTS5 database (filters, AND-ed skills, ranges, sorting, paging, facets,
validation, error envelopes) and the service against stub ports.

---

## 8. Deliberate scope decisions

- **shadcn/ui components without Radix.** The components in
  `components/atoms/` follow the shadcn convention (owned source, `cva`
  variants, `cn` merging) but are built on native controls — `<input
  type="checkbox">`, `<select>`, `<input type="number">`. For a checkbox list
  and a sort dropdown, the platform already provides the keyboard behaviour and
  screen-reader semantics a headless library would re-implement.
- **No frontend test runner.** The specified stack lists a testing framework for
  the backend only, so the frontend relies on strict TypeScript, Zod validation
  at the boundary, ESLint and a passing production build.
- **Full-refresh ETL.** The dataset is a static snapshot, so the loader replaces
  the content instead of diffing it, and there are no migrations (`create_all`
  plus the FTS DDL).
- **The 16 unrecoverable rows are dropped, not guessed.** They are reported in
  the parse report; importing them would mean inventing values.

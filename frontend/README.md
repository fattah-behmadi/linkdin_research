# Frontend — LinkedIn Profile Search UI

Next.js (App Router) + TypeScript (strict) + Tailwind v4 + TanStack React Query,
with shadcn/ui-style components organised by Atomic Design.

Architecture and design notes live in the [root README](../README.md); this file
is about running and working on the UI.

---

## Run

```bash
npm install
cp .env.example .env.local
npm run dev                       # http://localhost:3000
```

The backend must be running first — see [backend/README.md](../backend/README.md).

| Script                 | What it does                        |
| ---------------------- | ----------------------------------- |
| `npm run dev`          | dev server with hot reload          |
| `npm run build`        | production build                    |
| `npm run start`        | serve the production build          |
| `npm run lint`         | ESLint (`eslint-config-next`)       |
| `npm run typecheck`    | `tsc --noEmit`, strict mode         |
| `npm run format`       | Prettier write                      |
| `npm run format:check` | Prettier check                      |

If port 3000 is taken (or reserved — see the root README's troubleshooting
section on Windows), use `npm run dev -- -p 5173` and add that origin to
`CORS_ORIGINS` in `backend/.env`.

---

## Configuration

`.env.local`:

```
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000/api/v1
```

It is validated at startup by `src/lib/config/env.ts`, so a missing or malformed
URL fails loudly instead of producing confusing fetch errors.

---

## Using the page

- **Search box** — debounced 300 ms, prefix matching, covers name, title,
  company, skills, school and summary.
- **Filters** — skills (AND: a profile must have all ticked skills), industry,
  country, seniority, company size, and a years-of-experience range. Each value
  shows its hit count, fetched from `/profiles/facets`.
- **Filter chips** under the search box remove individual filters; *Clear all*
  resets them while keeping the keyword.
- **Skill chips** on a card are clickable — clicking one filters by it. Skills
  matching the active filter are pulled to the front and highlighted.
- **Sort** by best match, most/least experience, or name.
- **View details** expands a card and fetches the full profile (summary, work
  history, education, all skills) only at that moment; it is cached afterwards.
- **The URL mirrors the search**, so any result set is shareable and the back
  button works.

---

## Layout

```
src/
├── app/
│   ├── layout.tsx           root layout + fonts
│   ├── page.tsx             the single route
│   ├── providers.tsx        React Query client
│   └── globals.css          design tokens (light/dark) + Tailwind theme
├── components/              Atomic Design
│   ├── atoms/               button, input, badge, checkbox, select, card, skeleton
│   ├── molecules/           search field, facet group, chips, pagination, states
│   ├── organisms/           filter panel, result list, result card
│   └── templates/           page layout, owns the search state
├── features/profiles/       the feature's data layers
│   ├── api/profile.dto.ts   Zod schemas = the wire contract
│   ├── api/profile.proxy.ts endpoints and parameter names
│   ├── mappers/             DTO (snake_case) -> domain (camelCase)
│   ├── services/            proxy + mapper composed
│   ├── hooks/use-profiles.ts        React Query hooks + query keys
│   ├── hooks/use-search-criteria.ts URL <-> search state
│   └── types.ts             the domain model
├── hooks/use-debounced-value.ts
└── lib/
    ├── config/env.ts        validated public config
    ├── http/http-client.ts  the only place that calls fetch
    └── utils/cn.ts          class merging
```

### The data flow, in one line

```
component -> React Query hook -> service -> mapper -> proxy -> typed fetch -> API
```

Each layer has one job, and only the mapper knows both shapes. Adding an
endpoint means touching the proxy, the DTO schema, the mapper and a hook — never
a component.

---

## Conventions

- **No `any`.** API responses are parsed with Zod at the boundary
  (`http-client.ts`), so everything downstream is typed from real data.
- **One failure mode.** Network errors, non-2xx responses and unexpected shapes
  all surface as `HttpError` with a `status` and a `code`, which is what the
  error state renders.
- **Native controls where they suffice** — the checkbox, select and number
  inputs are the platform's, styled. That keeps keyboard and screen-reader
  behaviour for free.
- **Theme tokens, not hard-coded colours.** `globals.css` defines semantic CSS
  variables and maps them into Tailwind via `@theme inline`; dark mode swaps the
  variables and nothing else.

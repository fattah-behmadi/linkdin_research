# Tech Stack

## Backend

| Category | Technology |
|---|---|
| Language | Python 3.11+ |
| Web Framework | FastAPI |
| Data Validation / DTOs | Pydantic v2 |
| ORM | SQLAlchemy 2.x |
| Relational Database | SQLite |
| Search Engine | Elasticsearch 8.x |
| Architecture Pattern | Repository Pattern |
| Architecture Pattern | Service Layer |
| Dependency Management | FastAPI `Depends` (Dependency Injection) |
| Design Principles | SOLID (especially Dependency Inversion) |
| Testing Framework | pytest |
| Testing (Async support) | pytest-asyncio |
| Testing (API client) | httpx / FastAPI `TestClient` |
| Settings Management | pydantic-settings (.env based config) |
| Linting | ruff / flake8 |
| Formatting | black |
| Containerization (ES only) | Docker + Docker Compose |

## Frontend

| Category | Technology |
|---|---|
| Framework | Next.js (App Router) |
| Language | TypeScript (strict mode) |
| UI Component Library | shadcn/ui | Tailwindcss
| Design System Methodology | Atomic Design (atoms, molecules, organisms, templates) |
| Development Methodology | Component-Driven Development (CDD) |
| Server State / Data Fetching | TanStack React Query |
| Architecture Layers | Proxy Layer → Mapper Layer → Service Layer → React Query Hooks → Components |
| Design Principles | SOLID |
| Type Safety | Fully typesafe (no `any`, strict TypeScript) |
| Runtime Validation (optional) | Zod |
| HTTP Client | fetch API (typed wrapper) |
| Linting | ESLint |
| Formatting | Prettier |

## Infrastructure / Tooling

| Category | Technology |
|---|---|
| Search Infra | Elasticsearch (Docker container only) |
| Backend Runtime | Native (uvicorn), no Docker |
| Frontend Runtime | Native (`next dev` / `next start`), no Docker |
| Environment Config | `.env` / `.env.example` (backend & frontend separately) |
| Version Control | Git |

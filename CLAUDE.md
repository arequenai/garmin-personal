# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Health & performance dashboard that syncs data from Garmin Connect into PostgreSQL and displays it via a Next.js frontend. Monorepo with two apps:
- `apps/sync/` -- Python FastAPI backend + Garmin sync service
- `apps/web/` -- Next.js 16 (App Router) + Tailwind v4 frontend

## Commands

```bash
# Development
make setup          # install deps, start DB, run migrations
make dev-db         # start PostgreSQL (Docker, port 5435)
make dev-api        # FastAPI on :8000 with hot reload
make dev-web        # Next.js on :3000
make sync           # trigger manual sync (yesterday's data)
make migrate        # run Alembic migrations

# Quality
make lint           # Ruff (backend) + ESLint (frontend)
make format         # Ruff (backend) + Prettier (frontend)
make test           # pytest all tests
make check          # lint + test + next build

# Single test
cd apps/sync && uv run pytest tests/test_sync_service.py -v
cd apps/sync && uv run pytest tests/test_sync_service.py::test_sync_daily_summary -v
```

## Architecture

### Data Flow

```
Garmin Cloud → GarminClient → SyncService.sync_all() → PostgreSQL
                                    ↓
                             PerformanceUpdater (ATL/CTL/TSB/recovery)
                                    ↓
                             FastAPI endpoints (/api/*)
                                    ↓
                             Next.js server components (fetchApi<T>)
```

### Backend (`apps/sync/app/`)

- **`main.py`** -- FastAPI app with CORS, lifespan scheduler, 8 routers
- **`routers/`** -- API endpoints: dashboard, activities, sleep, daily, nutrition, performance, sync, settings. All prefixed `/api/`
- **`services/garmin_client.py`** -- Wrapper around `garminconnect` library
- **`services/sync_service.py`** -- Orchestrates data sync for a target date. Uses upsert pattern (find by unique key, update or insert)
- **`services/performance_updater.py`** -- Post-sync calculations: daily TSS aggregation, ATL (7d EWMA), CTL (42d EWMA), TSB (CTL−ATL), recovery score
- **`services/calculations.py`** -- TSS formulas (HR-based and strength), EWMA, recovery score (TSB 35% + sleep 40% + HRV 25%)
- **`models/`** -- SQLAlchemy ORM. 7 tables: users, daily_summaries, sleep_sessions, activities, strength_sessions, nutrition_daily, performance_metrics
- **`schemas/`** -- Pydantic response models with `from_attributes = True`
- **`config.py`** -- Pydantic BaseSettings loading from `../../.env`
- **`scheduler.py`** -- APScheduler runs `daily_sync_job()` at 5:00 AM

Key API endpoints:
- `POST /api/sync/trigger?days_back=N` -- manual sync (runs as background task)
- `GET /api/dashboard/today` -- unified snapshot (daily + sleep + activity + nutrition + performance)
- `GET /api/activities`, `GET /api/activities/{id}` -- activity list/detail
- `GET /api/daily`, `GET /api/sleep`, `GET /api/performance`, `GET /api/nutrition` -- date-range queries (`from_date`, `to_date`)

### Frontend (`apps/web/src/`)

- **`app/(dashboard)/`** -- Route group with sidebar layout. Pages: dashboard home, activities/[id], sleep, nutrition, performance, body
- **`lib/api.ts`** -- Single `fetchApi<T>(path)` function; base URL from `NEXT_PUBLIC_API_URL` (default `http://localhost:8000`)
- **`lib/types.ts`** -- TypeScript interfaces mirroring backend Pydantic schemas
- **`lib/format.ts`** -- Duration, distance, number formatters
- **`components/layout/`** -- AppLayout + Sidebar (fixed 72px)
- **`components/dashboard/`** -- Recovery score, body battery, today summary, latest activity, macro split
- **`components/ui/`** -- Reusable: ScoreRing (SVG gauge), MetricCard, Gauge, TrendChart

All pages are async **server components** fetching data at render time via `fetchApi`. Client components (`"use client"`) only for interactive features. Charts use Recharts.

### Database

PostgreSQL 16 in Docker on port 5435. Unique constraints on date columns for upsert logic. Foreign key: `strength_sessions.activity_id → activities.id`.

## Conventions

- **Tailwind v4**: Theme defined via `@theme inline` in `globals.css` (NOT tailwind.config.ts)
- **Custom CSS tokens**: `bg-bg-primary`, `bg-bg-card`, `text-text-primary`, `text-text-secondary`, `text-recovery`, `text-strain`, `text-sleep`, `text-alert`
- **Fonts**: Inter (body, `font-body`), Space Grotesk (headings, `font-heading`)
- **Path alias**: `@/*` → `./src/*` in frontend
- **Python**: Ruff linting/formatting, line length 100
- **Commits**: Conventional Commits format
- **Tests**: pytest with SQLite in-memory, mock GarminClient fixtures
- **API**: All endpoints prefixed `/api/`

## Tech Stack

- **Frontend**: Next.js 16, React 19, TypeScript, Tailwind CSS v4, Recharts, Lucide icons, date-fns
- **Backend**: Python 3.12+, FastAPI, SQLAlchemy 2.0, Alembic, garminconnect, APScheduler, Pydantic
- **Database**: PostgreSQL 16 (Docker)
- **Tooling**: pnpm (frontend), uv (Python), Ruff, ESLint, Prettier

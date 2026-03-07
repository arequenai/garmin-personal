# Garmin Personal -- Health & Performance Dashboard

## Project Structure

Monorepo with two apps:
- `apps/web/` -- Next.js 16 (App Router) + Tailwind v4 frontend
- `apps/sync/` -- Python FastAPI backend + Garmin sync service

## Quick Start

1. `cp .env.example .env` and fill in credentials
2. `make setup` -- installs deps, starts DB, runs migrations
3. Terminal 1: `make dev-api` -- starts backend on port 8000
4. Terminal 2: `make dev-web` -- starts frontend on port 3000
5. `make sync` -- trigger manual data sync

## Key Commands

- `make test` -- run Python tests
- `make lint` -- lint both projects
- `make format` -- format both projects
- `make check` -- full pre-commit check (lint + test + build)
- `make migrate` -- run database migrations

## Tech Stack

- **Frontend:** Next.js 16, TypeScript, Tailwind CSS v4, Recharts, Lucide icons
- **Backend:** Python 3.13, FastAPI, SQLAlchemy, Alembic, garminconnect
- **Database:** PostgreSQL 16 (Docker, port 5435)
- **Tooling:** pnpm (frontend), uv (Python), Ruff (Python linting), ESLint + Prettier (frontend)

## Conventions

- Tailwind v4 uses `@theme inline` in globals.css (NOT tailwind.config.ts)
- Custom colors: bg-bg-primary, bg-bg-card, text-text-primary, text-text-secondary, text-recovery, text-strain, text-sleep, text-alert
- Fonts: Inter (body, font-body), Space Grotesk (headings, font-heading)
- Python code: Ruff for linting and formatting, line length 100
- Commits: Conventional Commits format
- Tests: pytest with SQLite in-memory for unit tests
- API endpoints all prefixed with /api/

## Database

PostgreSQL runs in Docker on port 5435. Migrations managed by Alembic.
Models in `apps/sync/app/models/`. 7 tables: users, daily_summaries, sleep_sessions, activities, strength_sessions, nutrition_daily, performance_metrics.

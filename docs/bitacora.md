# Bitácora

Running log of sprint-level work. Latest entry on top.

---

## 2026-05-08 — Coach Briefing V1, Sprint 1

**Objective**: First `coach.*` push — daily pre-dinner health briefing at 20:30 Europe/Madrid.

**Delivered**:
- `coach.briefings` table + Alembic migration `a8c1d2e3f4a5_create_coach_schema`.
- `app/coach/` package: `briefing` orchestrator, `config` loader (CSV + cache + defaults), `classifier`, 7 rule engines (`wake_time`, `bedtime`, `calorie_target`, `macro_split`, `dinner_macros`, `category_picker`, `semaphore`), `formatter`, `inputs`, `llm`, `ntfy`, `persistence`.
- `POST /api/coach/trigger-briefing` (Bearer auth) and `GET /api/coach/last-briefing` (public, minimal payload).
- APScheduler job `coach_pre_dinner` registered for `0 30 20 * * *` Europe/Madrid.
- Anthropic SDK added (`anthropic>=0.40.0`) for the optional closing-line LLM call (Sonnet 4, 5s timeout, fail-soft).
- 78 coach tests (unit + integration + idempotency + LLM fallback) — all green. Total project test suite: pre-existing failures unrelated to this sprint.
- Smoke workflow `.github/workflows/smoke-coach.yml` — daily 06:00 UTC against production.
- `.env.example` updated with new vars.

**Deviations from brief**:
- Brief referenced `/api/tp/summary` and `/api/nutrition/{date}` HTTP endpoints; neither exists in the actual repo. Replaced with direct Postgres reads (`app/coach/inputs.py`) — cleaner, avoids self-HTTP, matches existing conventions.
- Router lives at `app/routers/coach.py` (not `app/api/coach.py`) to match the repo's `routers/` directory pattern.
- HRV baseline computed inline from the last 7 days of `sleep_sessions.avg_hrv`. No separate `hrv_baseline.compute_last_7d` helper since it's a 4-line query.
- `CoachBriefing` model uses `TypeDecorator` shims (`_UUIDType`, `_StringArray`) so the same model works against Postgres (UUID + ARRAY) and SQLite (CHAR(36) + JSON-encoded list) without a separate test schema. The `coach` schema is suppressed via `COACH_TEST_NO_SCHEMA=1` set in `tests/conftest.py` so SQLite `Base.metadata.create_all` works.

**Sprint 2 candidates surfaced**:
- A unified `/api/tp/summary` endpoint would let the coach share input plumbing with the dashboard.
- Move `dinner_fat_cap_g` to the config sheet.
- Replace the crude `-5ms` HRV proxy with rolling stddev once we have enough history.
- Persist the LLM prompt template alongside `inputs_json` for prompt-version tracking.

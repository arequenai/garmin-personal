# TrainingPeaks Integration -- Backend Design

**Date:** 2026-04-04
**Status:** Approved
**Scope:** Backend only (models, sync, API). Frontend deferred.

## Goal

Pull PMC fitness data (CTL/ATL/TSB) and workout data (planned + completed with HR/power zone breakdown) from TrainingPeaks into PostgreSQL via their internal API, using cookie-based authentication. Expose via new REST endpoints.

## Approach

New tables and services dedicated to TrainingPeaks, fully separate from existing Garmin-based `PerformanceMetric` and `PerformanceUpdater`. Nothing existing is removed or modified beyond wiring in the new sync and router.

## Authentication

TrainingPeaks has no public API. We use the same technique as tp2intervals and trainingpeaks-mcp:

1. User extracts `Production_tpAuth` cookie from browser (DevTools > Network > any request to `tpapi.trainingpeaks.com` > Cookie header)
2. Cookie stored in `.env` as `TP_AUTH_COOKIE`
3. Client exchanges cookie for a short-lived OAuth token via `POST tpapi.trainingpeaks.com/users/v3/token`
4. Token cached in memory, auto-renewed on expiry (~1 hour)

## Data Models

### `tp_fitness_data`

Daily PMC snapshot from TrainingPeaks.

| Column | Type | Notes |
|---|---|---|
| id | Integer PK | Auto |
| date | Date, unique | |
| ctl | Float | Chronic Training Load (fitness) |
| atl | Float | Acute Training Load (fatigue) |
| tsb | Float | Training Stress Balance (form) |
| tss_day | Float | Daily TSS total |
| training_load_7d | Float | 7-day rolling load |
| training_load_28d | Float | 28-day rolling load |
| intensity_factor | Float | Average IF for the day |
| ramp_rate | Float | CTL rate of change |
| synced_at | DateTime | Last sync timestamp |

### `tp_planned_workouts`

Future workouts from the TP calendar/coaching plan.

| Column | Type | Notes |
|---|---|---|
| id | Integer PK | Auto |
| tp_workout_id | String, unique | TrainingPeaks workout ID |
| date | Date | Scheduled date |
| title | String | Workout name |
| workout_type | String | e.g. "Run", "Bike", "Swim", "Strength" |
| description | Text | Coach notes / workout description |
| duration_sec_planned | Integer | Planned duration |
| tss_planned | Float | Planned TSS |
| distance_m_planned | Float | Planned distance in meters |
| structure_json | JSON | Structured intervals (warmup, work, cooldown) |
| completed | Boolean | Whether it was completed |
| synced_at | DateTime | Last sync timestamp |

### `tp_completed_workouts`

Completed workouts with detailed metrics and zone data.

| Column | Type | Notes |
|---|---|---|
| id | Integer PK | Auto |
| tp_workout_id | String, unique | TrainingPeaks workout ID |
| date | Date | Completion date |
| title | String | Workout name |
| workout_type | String | Sport type |
| duration_sec | Integer | Actual duration |
| distance_m | Float | Actual distance |
| tss | Float | Actual TSS |
| intensity_factor | Float | Actual IF |
| avg_hr | Integer | Average heart rate |
| max_hr | Integer | Max heart rate |
| avg_power | Float | Average power (watts) |
| max_power | Float | Max power |
| normalized_power | Float | Normalized power |
| calories | Integer | Calories burned |
| hr_zone1_sec | Integer | Time in HR zone 1 (seconds) |
| hr_zone2_sec | Integer | Time in HR zone 2 |
| hr_zone3_sec | Integer | Time in HR zone 3 |
| hr_zone4_sec | Integer | Time in HR zone 4 |
| hr_zone5_sec | Integer | Time in HR zone 5 |
| power_zone1_sec | Integer | Time in power zone 1 (seconds) |
| power_zone2_sec | Integer | Time in power zone 2 |
| power_zone3_sec | Integer | Time in power zone 3 |
| power_zone4_sec | Integer | Time in power zone 4 |
| power_zone5_sec | Integer | Time in power zone 5 |
| power_zone6_sec | Integer | Time in power zone 6 |
| power_zone7_sec | Integer | Time in power zone 7 (Coggan zones) |
| laps_json | JSON | Lap/interval detail |
| synced_at | DateTime | Last sync timestamp |

## Services

### `TrainingPeaksClient` (`app/services/trainingpeaks_client.py`)

HTTP client wrapping `tpapi.trainingpeaks.com`. Uses `requests` library.

```python
class TrainingPeaksClient:
    def __init__(self, auth_cookie: str): ...
    def login(self) -> None:
        # POST /users/v3/token with cookie → cache OAuth token
    def get_athlete_id(self) -> str:
        # Extract from token response
    def get_fitness(self, start_date: str, end_date: str) -> list[dict]:
        # GET fitness/v3/athletes/{id}/fitness → CTL/ATL/TSB series
    def get_workouts(self, start_date: str, end_date: str) -> list[dict]:
        # GET fitness/v1/athletes/{id}/workouts → planned + completed
    def get_workout_analysis(self, workout_id: str) -> dict:
        # GET fitness/v1/athletes/{id}/workouts/{id}/analysis → zones, laps
```

### `TPSyncService` (`app/services/tp_sync_service.py`)

Orchestrates TrainingPeaks sync for a target date.

```python
class TPSyncService:
    def __init__(self, db: Session, tp_client: TrainingPeaksClient): ...
    def sync_fitness(self, target_date: date) -> None:
        # Upsert tp_fitness_data for target_date
    def sync_planned_workouts(self, target_date: date) -> None:
        # Upsert planned workouts for next 30 days
    def sync_completed_workouts(self, target_date: date) -> None:
        # Upsert completed workouts for last 7 days
        # For each completed workout, fetch analysis for zone data
    def sync_all(self, target_date: date) -> None:
        self.sync_fitness(target_date)
        self.sync_planned_workouts(target_date)
        self.sync_completed_workouts(target_date)
```

## Config Changes

In `app/config.py`, add:

```python
tp_auth_cookie: str = ""
tp_enabled: bool = False
```

In `.env.example`, add:

```
TP_AUTH_COOKIE=
TP_ENABLED=false
```

## Sync Integration

In `app/services/sync_orchestrator.py`, after Garmin sync:

```python
if settings.tp_enabled and settings.tp_auth_cookie:
    tp_client = TrainingPeaksClient(auth_cookie=settings.tp_auth_cookie)
    tp_client.login()
    tp_sync = TPSyncService(db=db, tp_client=tp_client)
    tp_sync.sync_all(target_date)
```

Wrapped in try/except so TP failures don't break the Garmin sync.

## API Endpoints

New router `app/routers/tp.py`, prefix `/api/tp`:

| Method | Path | Response | Description |
|---|---|---|---|
| GET | `/api/tp/fitness` | `list[TPFitnessResponse]` | PMC data with `from_date`, `to_date` query params |
| GET | `/api/tp/workouts/planned` | `list[TPPlannedWorkoutResponse]` | Planned workouts with date range |
| GET | `/api/tp/workouts/completed` | `list[TPCompletedWorkoutResponse]` | Completed workouts with zone data |
| GET | `/api/tp/workouts/{tp_workout_id}` | `TPCompletedWorkoutResponse` | Single workout detail |
| POST | `/api/tp/sync/trigger` | `{"status": "started"}` | Manual sync with `days_back` param |

## Files

### New
- `app/models/tp_fitness_data.py`
- `app/models/tp_planned_workout.py`
- `app/models/tp_completed_workout.py`
- `app/services/trainingpeaks_client.py`
- `app/services/tp_sync_service.py`
- `app/routers/tp.py`
- `app/schemas/tp.py`
- `alembic/versions/..._add_tp_tables.py`

### Modified
- `app/config.py` -- add `tp_auth_cookie`, `tp_enabled`
- `app/models/__init__.py` -- export new models
- `app/main.py` -- include TP router
- `app/services/sync_orchestrator.py` -- call TP sync after Garmin
- `.env.example` -- document new env vars

### Not touched
- `PerformanceUpdater`, `PerformanceMetric`, all frontend code, Overview page
- These will be deprecated/replaced when the frontend is redesigned

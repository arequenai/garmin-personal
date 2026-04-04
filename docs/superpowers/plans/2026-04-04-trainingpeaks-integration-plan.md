# TrainingPeaks Backend Integration Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Pull PMC fitness data and workout data (planned + completed with HR/power zones) from TrainingPeaks into PostgreSQL, exposed via REST endpoints.

**Architecture:** Cookie-based auth against `tpapi.trainingpeaks.com` internal API. Three new tables (`tp_fitness_data`, `tp_planned_workouts`, `tp_completed_workouts`), a `TrainingPeaksClient` HTTP service, a `TPSyncService` orchestrator, and a new `/api/tp/` router. Fully separate from existing Garmin pipeline.

**Tech Stack:** Python 3.12, FastAPI, SQLAlchemy 2.0, Alembic, httpx, Pydantic, pytest

**Spec:** `docs/superpowers/specs/2026-04-04-trainingpeaks-integration-design.md`

---

## File Map

| File | Action | Responsibility |
|---|---|---|
| `apps/sync/app/models/tp_fitness_data.py` | Create | SQLAlchemy model for daily PMC data |
| `apps/sync/app/models/tp_planned_workout.py` | Create | SQLAlchemy model for planned workouts |
| `apps/sync/app/models/tp_completed_workout.py` | Create | SQLAlchemy model for completed workouts with zones |
| `apps/sync/app/models/__init__.py` | Modify | Export 3 new models |
| `apps/sync/app/schemas/tp.py` | Create | Pydantic response schemas |
| `apps/sync/app/services/trainingpeaks_client.py` | Create | HTTP client for TP internal API |
| `apps/sync/app/services/tp_sync_service.py` | Create | Sync orchestrator for TP data |
| `apps/sync/app/routers/tp.py` | Create | API endpoints under /api/tp/ |
| `apps/sync/app/config.py` | Modify | Add `tp_auth_cookie`, `tp_enabled` |
| `apps/sync/app/main.py` | Modify | Include TP router |
| `apps/sync/app/services/sync_orchestrator.py` | Modify | Call TP sync after Garmin sync |
| `apps/sync/.env.example` (root `.env.example`) | Modify | Document new env vars |
| `apps/sync/alembic/versions/e5f6g7h8i9j0_add_tp_tables.py` | Create | Migration for 3 new tables |
| `apps/sync/tests/test_tp_sync_service.py` | Create | Tests for TP sync service |
| `apps/sync/tests/test_trainingpeaks_client.py` | Create | Tests for TP client |

---

## Chunk 1: Models, Schemas & Config

### Task 1: Config — add TP settings

**Files:**
- Modify: `apps/sync/app/config.py`
- Modify: `.env.example`

- [ ] **Step 1: Add TP fields to Settings**

In `apps/sync/app/config.py`, add after `cors_origins`:

```python
tp_auth_cookie: str = ""
tp_enabled: bool = False
```

- [ ] **Step 2: Update .env.example**

Append to `.env.example`:

```
TP_AUTH_COOKIE=
TP_ENABLED=false
```

- [ ] **Step 3: Commit**

```bash
cd apps/sync && git add app/config.py ../../.env.example
git commit -m "feat(tp): add TrainingPeaks config settings"
```

### Task 2: Model — tp_fitness_data

**Files:**
- Create: `apps/sync/app/models/tp_fitness_data.py`

- [ ] **Step 1: Create the model**

```python
from sqlalchemy import Date, Float, Integer
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class TPFitnessData(Base):
    __tablename__ = "tp_fitness_data"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    date: Mapped[Date] = mapped_column(Date, unique=True, nullable=False)
    ctl: Mapped[float | None] = mapped_column(Float, nullable=True)
    atl: Mapped[float | None] = mapped_column(Float, nullable=True)
    tsb: Mapped[float | None] = mapped_column(Float, nullable=True)
    tss_day: Mapped[float | None] = mapped_column(Float, nullable=True)
    training_load_7d: Mapped[float | None] = mapped_column(Float, nullable=True)
    training_load_28d: Mapped[float | None] = mapped_column(Float, nullable=True)
    intensity_factor: Mapped[float | None] = mapped_column(Float, nullable=True)
    ramp_rate: Mapped[float | None] = mapped_column(Float, nullable=True)
```

- [ ] **Step 2: Commit**

```bash
git add apps/sync/app/models/tp_fitness_data.py
git commit -m "feat(tp): add TPFitnessData model"
```

### Task 3: Model — tp_planned_workout

**Files:**
- Create: `apps/sync/app/models/tp_planned_workout.py`

- [ ] **Step 1: Create the model**

```python
from sqlalchemy import Boolean, Date, Float, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class TPPlannedWorkout(Base):
    __tablename__ = "tp_planned_workouts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    tp_workout_id: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    date: Mapped[Date] = mapped_column(Date, nullable=False, index=True)
    title: Mapped[str | None] = mapped_column(String(255), nullable=True)
    workout_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    duration_sec_planned: Mapped[int | None] = mapped_column(Integer, nullable=True)
    tss_planned: Mapped[float | None] = mapped_column(Float, nullable=True)
    distance_m_planned: Mapped[float | None] = mapped_column(Float, nullable=True)
    structure_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    completed: Mapped[bool | None] = mapped_column(Boolean, nullable=True, default=False)
```

- [ ] **Step 2: Commit**

```bash
git add apps/sync/app/models/tp_planned_workout.py
git commit -m "feat(tp): add TPPlannedWorkout model"
```

### Task 4: Model — tp_completed_workout

**Files:**
- Create: `apps/sync/app/models/tp_completed_workout.py`

- [ ] **Step 1: Create the model**

```python
from sqlalchemy import Date, Float, Integer, String
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class TPCompletedWorkout(Base):
    __tablename__ = "tp_completed_workouts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    tp_workout_id: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    date: Mapped[Date] = mapped_column(Date, nullable=False, index=True)
    title: Mapped[str | None] = mapped_column(String(255), nullable=True)
    workout_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    duration_sec: Mapped[int | None] = mapped_column(Integer, nullable=True)
    distance_m: Mapped[float | None] = mapped_column(Float, nullable=True)
    tss: Mapped[float | None] = mapped_column(Float, nullable=True)
    intensity_factor: Mapped[float | None] = mapped_column(Float, nullable=True)
    avg_hr: Mapped[int | None] = mapped_column(Integer, nullable=True)
    max_hr: Mapped[int | None] = mapped_column(Integer, nullable=True)
    avg_power: Mapped[float | None] = mapped_column(Float, nullable=True)
    max_power: Mapped[float | None] = mapped_column(Float, nullable=True)
    normalized_power: Mapped[float | None] = mapped_column(Float, nullable=True)
    calories: Mapped[int | None] = mapped_column(Integer, nullable=True)
    hr_zone1_sec: Mapped[int | None] = mapped_column(Integer, nullable=True)
    hr_zone2_sec: Mapped[int | None] = mapped_column(Integer, nullable=True)
    hr_zone3_sec: Mapped[int | None] = mapped_column(Integer, nullable=True)
    hr_zone4_sec: Mapped[int | None] = mapped_column(Integer, nullable=True)
    hr_zone5_sec: Mapped[int | None] = mapped_column(Integer, nullable=True)
    power_zone1_sec: Mapped[int | None] = mapped_column(Integer, nullable=True)
    power_zone2_sec: Mapped[int | None] = mapped_column(Integer, nullable=True)
    power_zone3_sec: Mapped[int | None] = mapped_column(Integer, nullable=True)
    power_zone4_sec: Mapped[int | None] = mapped_column(Integer, nullable=True)
    power_zone5_sec: Mapped[int | None] = mapped_column(Integer, nullable=True)
    power_zone6_sec: Mapped[int | None] = mapped_column(Integer, nullable=True)
    power_zone7_sec: Mapped[int | None] = mapped_column(Integer, nullable=True)
    laps_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
```

- [ ] **Step 2: Commit**

```bash
git add apps/sync/app/models/tp_completed_workout.py
git commit -m "feat(tp): add TPCompletedWorkout model"
```

### Task 5: Export models and create schemas

**Files:**
- Modify: `apps/sync/app/models/__init__.py`
- Create: `apps/sync/app/schemas/tp.py`

- [ ] **Step 1: Add imports to models/__init__.py**

Add these imports and exports:

```python
from app.models.tp_fitness_data import TPFitnessData
from app.models.tp_planned_workout import TPPlannedWorkout
from app.models.tp_completed_workout import TPCompletedWorkout
```

Add to `__all__`: `"TPFitnessData"`, `"TPPlannedWorkout"`, `"TPCompletedWorkout"`

- [ ] **Step 2: Create Pydantic schemas**

Create `apps/sync/app/schemas/tp.py`:

```python
from datetime import date

from pydantic import BaseModel


class TPFitnessResponse(BaseModel):
    id: int
    date: date
    ctl: float | None
    atl: float | None
    tsb: float | None
    tss_day: float | None
    training_load_7d: float | None
    training_load_28d: float | None
    intensity_factor: float | None
    ramp_rate: float | None

    model_config = {"from_attributes": True}


class TPPlannedWorkoutResponse(BaseModel):
    id: int
    tp_workout_id: str
    date: date
    title: str | None
    workout_type: str | None
    description: str | None
    duration_sec_planned: int | None
    tss_planned: float | None
    distance_m_planned: float | None
    structure_json: dict | None
    completed: bool | None

    model_config = {"from_attributes": True}


class TPCompletedWorkoutResponse(BaseModel):
    id: int
    tp_workout_id: str
    date: date
    title: str | None
    workout_type: str | None
    duration_sec: int | None
    distance_m: float | None
    tss: float | None
    intensity_factor: float | None
    avg_hr: int | None
    max_hr: int | None
    avg_power: float | None
    max_power: float | None
    normalized_power: float | None
    calories: int | None
    hr_zone1_sec: int | None
    hr_zone2_sec: int | None
    hr_zone3_sec: int | None
    hr_zone4_sec: int | None
    hr_zone5_sec: int | None
    power_zone1_sec: int | None
    power_zone2_sec: int | None
    power_zone3_sec: int | None
    power_zone4_sec: int | None
    power_zone5_sec: int | None
    power_zone6_sec: int | None
    power_zone7_sec: int | None
    laps_json: dict | None

    model_config = {"from_attributes": True}
```

- [ ] **Step 3: Commit**

```bash
git add apps/sync/app/models/__init__.py apps/sync/app/schemas/tp.py
git commit -m "feat(tp): export models and add Pydantic schemas"
```

### Task 6: Alembic migration

**Files:**
- Create: `apps/sync/alembic/versions/e5f6g7h8i9j0_add_tp_tables.py`

- [ ] **Step 1: Create migration**

Create `apps/sync/alembic/versions/e5f6g7h8i9j0_add_tp_tables.py`:

```python
"""add trainingpeaks tables

Revision ID: e5f6g7h8i9j0
Revises: d4e5f6g7h8i9
Create Date: 2026-04-04 12:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "e5f6g7h8i9j0"
down_revision: str | Sequence[str] | None = "d4e5f6g7h8i9"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "tp_fitness_data",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("ctl", sa.Float(), nullable=True),
        sa.Column("atl", sa.Float(), nullable=True),
        sa.Column("tsb", sa.Float(), nullable=True),
        sa.Column("tss_day", sa.Float(), nullable=True),
        sa.Column("training_load_7d", sa.Float(), nullable=True),
        sa.Column("training_load_28d", sa.Float(), nullable=True),
        sa.Column("intensity_factor", sa.Float(), nullable=True),
        sa.Column("ramp_rate", sa.Float(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("date"),
    )

    op.create_table(
        "tp_planned_workouts",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("tp_workout_id", sa.String(50), nullable=False),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("title", sa.String(255), nullable=True),
        sa.Column("workout_type", sa.String(100), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("duration_sec_planned", sa.Integer(), nullable=True),
        sa.Column("tss_planned", sa.Float(), nullable=True),
        sa.Column("distance_m_planned", sa.Float(), nullable=True),
        sa.Column("structure_json", postgresql.JSON(), nullable=True),
        sa.Column("completed", sa.Boolean(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tp_workout_id"),
    )
    op.create_index("ix_tp_planned_workouts_date", "tp_planned_workouts", ["date"])

    op.create_table(
        "tp_completed_workouts",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("tp_workout_id", sa.String(50), nullable=False),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("title", sa.String(255), nullable=True),
        sa.Column("workout_type", sa.String(100), nullable=True),
        sa.Column("duration_sec", sa.Integer(), nullable=True),
        sa.Column("distance_m", sa.Float(), nullable=True),
        sa.Column("tss", sa.Float(), nullable=True),
        sa.Column("intensity_factor", sa.Float(), nullable=True),
        sa.Column("avg_hr", sa.Integer(), nullable=True),
        sa.Column("max_hr", sa.Integer(), nullable=True),
        sa.Column("avg_power", sa.Float(), nullable=True),
        sa.Column("max_power", sa.Float(), nullable=True),
        sa.Column("normalized_power", sa.Float(), nullable=True),
        sa.Column("calories", sa.Integer(), nullable=True),
        sa.Column("hr_zone1_sec", sa.Integer(), nullable=True),
        sa.Column("hr_zone2_sec", sa.Integer(), nullable=True),
        sa.Column("hr_zone3_sec", sa.Integer(), nullable=True),
        sa.Column("hr_zone4_sec", sa.Integer(), nullable=True),
        sa.Column("hr_zone5_sec", sa.Integer(), nullable=True),
        sa.Column("power_zone1_sec", sa.Integer(), nullable=True),
        sa.Column("power_zone2_sec", sa.Integer(), nullable=True),
        sa.Column("power_zone3_sec", sa.Integer(), nullable=True),
        sa.Column("power_zone4_sec", sa.Integer(), nullable=True),
        sa.Column("power_zone5_sec", sa.Integer(), nullable=True),
        sa.Column("power_zone6_sec", sa.Integer(), nullable=True),
        sa.Column("power_zone7_sec", sa.Integer(), nullable=True),
        sa.Column("laps_json", postgresql.JSON(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tp_workout_id"),
    )
    op.create_index("ix_tp_completed_workouts_date", "tp_completed_workouts", ["date"])


def downgrade() -> None:
    op.drop_index("ix_tp_completed_workouts_date", "tp_completed_workouts")
    op.drop_table("tp_completed_workouts")
    op.drop_index("ix_tp_planned_workouts_date", "tp_planned_workouts")
    op.drop_table("tp_planned_workouts")
    op.drop_table("tp_fitness_data")
```

- [ ] **Step 2: Run migration**

```bash
cd apps/sync && uv run alembic upgrade head
```

Expected: 3 tables created successfully.

- [ ] **Step 3: Commit**

```bash
git add apps/sync/alembic/versions/e5f6g7h8i9j0_add_tp_tables.py
git commit -m "feat(tp): add Alembic migration for TP tables"
```

---

## Chunk 2: TrainingPeaksClient

### Task 7: Write tests for TrainingPeaksClient

**Files:**
- Create: `apps/sync/tests/test_trainingpeaks_client.py`

- [ ] **Step 1: Write tests**

```python
from unittest.mock import MagicMock, patch

import pytest

from app.services.trainingpeaks_client import TrainingPeaksClient


@pytest.fixture
def mock_httpx_client():
    with patch("app.services.trainingpeaks_client.httpx") as mock_httpx:
        yield mock_httpx


def test_login_exchanges_cookie_for_token(mock_httpx_client):
    """login() should POST to /users/v3/token with cookie and cache the token."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "access_token": "test_token_123",
        "expires_in": 3600,
        "userId": 12345,
    }
    mock_response.raise_for_status = MagicMock()
    mock_httpx_client.post.return_value = mock_response

    client = TrainingPeaksClient(auth_cookie="Production_tpAuth=abc123")
    client.login()

    assert client._token == "test_token_123"
    assert client._athlete_id == "12345"
    mock_httpx_client.post.assert_called_once()


def test_get_athlete_id_returns_cached_id(mock_httpx_client):
    """get_athlete_id() should return the ID from login."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "access_token": "tok",
        "expires_in": 3600,
        "userId": 99,
    }
    mock_response.raise_for_status = MagicMock()
    mock_httpx_client.post.return_value = mock_response

    client = TrainingPeaksClient(auth_cookie="Production_tpAuth=abc")
    client.login()
    assert client.get_athlete_id() == "99"


def test_get_fitness_calls_correct_endpoint(mock_httpx_client):
    """get_fitness() should GET the fitness endpoint with date params."""
    # Setup login
    login_resp = MagicMock()
    login_resp.status_code = 200
    login_resp.json.return_value = {
        "access_token": "tok",
        "expires_in": 3600,
        "userId": 42,
    }
    login_resp.raise_for_status = MagicMock()

    fitness_resp = MagicMock()
    fitness_resp.status_code = 200
    fitness_resp.json.return_value = [{"date": "2026-04-01", "ctl": 55.0}]
    fitness_resp.raise_for_status = MagicMock()

    mock_httpx_client.post.return_value = login_resp
    mock_httpx_client.get.return_value = fitness_resp

    client = TrainingPeaksClient(auth_cookie="Production_tpAuth=abc")
    client.login()
    result = client.get_fitness("2026-04-01", "2026-04-04")

    assert len(result) == 1
    assert result[0]["ctl"] == 55.0
    mock_httpx_client.get.assert_called_once()
    call_url = mock_httpx_client.get.call_args[0][0]
    assert "/fitness" in call_url


def test_get_workout_analysis_returns_none_on_failure(mock_httpx_client):
    """get_workout_analysis() should return None on HTTP errors."""
    login_resp = MagicMock()
    login_resp.status_code = 200
    login_resp.json.return_value = {
        "access_token": "tok",
        "expires_in": 3600,
        "userId": 42,
    }
    login_resp.raise_for_status = MagicMock()
    mock_httpx_client.post.return_value = login_resp

    mock_httpx_client.get.side_effect = Exception("API error")

    client = TrainingPeaksClient(auth_cookie="Production_tpAuth=abc")
    client.login()
    result = client.get_workout_analysis("999")

    assert result is None


def test_login_raises_on_bad_cookie(mock_httpx_client):
    """login() should raise if the token endpoint returns an error."""
    mock_response = MagicMock()
    mock_response.status_code = 401
    mock_response.raise_for_status.side_effect = Exception("401 Unauthorized")
    mock_httpx_client.post.return_value = mock_response

    client = TrainingPeaksClient(auth_cookie="bad_cookie")
    with pytest.raises(Exception, match="401"):
        client.login()
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd apps/sync && uv run pytest tests/test_trainingpeaks_client.py -v
```

Expected: FAIL — `ModuleNotFoundError: No module named 'app.services.trainingpeaks_client'`

- [ ] **Step 3: Commit test file**

```bash
git add apps/sync/tests/test_trainingpeaks_client.py
git commit -m "test(tp): add TrainingPeaksClient tests (red)"
```

### Task 8: Implement TrainingPeaksClient

**Files:**
- Create: `apps/sync/app/services/trainingpeaks_client.py`

- [ ] **Step 1: Implement the client**

```python
import logging
import time

import httpx

logger = logging.getLogger(__name__)

BASE_URL = "https://tpapi.trainingpeaks.com"


class TrainingPeaksClient:
    def __init__(self, auth_cookie: str):
        self.auth_cookie = auth_cookie
        self._token: str | None = None
        self._athlete_id: str | None = None
        self._token_expires_at: float = 0

    def login(self) -> None:
        """Exchange auth cookie for an OAuth token."""
        resp = httpx.post(
            f"{BASE_URL}/users/v3/token",
            headers={"Cookie": self.auth_cookie},
        )
        resp.raise_for_status()
        data = resp.json()
        self._token = data["access_token"]
        self._athlete_id = str(data["userId"])
        self._token_expires_at = time.time() + data.get("expires_in", 3600) - 60

    def _ensure_token(self) -> None:
        """Re-login if token is expired."""
        if time.time() >= self._token_expires_at:
            self.login()

    def _headers(self) -> dict[str, str]:
        self._ensure_token()
        return {"Authorization": f"Bearer {self._token}"}

    def get_athlete_id(self) -> str:
        """Return cached athlete ID from login response."""
        if self._athlete_id is None:
            raise RuntimeError("Must call login() first")
        return self._athlete_id

    def get_fitness(self, start_date: str, end_date: str) -> list[dict]:
        """Get daily CTL/ATL/TSB fitness data."""
        url = f"{BASE_URL}/fitness/v3/athletes/{self._athlete_id}/fitness"
        resp = httpx.get(url, headers=self._headers(), params={
            "startDate": start_date,
            "endDate": end_date,
        })
        resp.raise_for_status()
        return resp.json()

    def get_workouts(self, start_date: str, end_date: str) -> list[dict]:
        """Get workouts (both planned and completed) in a date range."""
        url = f"{BASE_URL}/fitness/v1/athletes/{self._athlete_id}/workouts"
        resp = httpx.get(url, headers=self._headers(), params={
            "startDate": start_date,
            "endDate": end_date,
        })
        resp.raise_for_status()
        return resp.json()

    def get_workout_analysis(self, workout_id: str) -> dict | None:
        """Get detailed analysis (zones, laps) for a workout. Returns None on failure."""
        try:
            url = (
                f"{BASE_URL}/fitness/v1/athletes/{self._athlete_id}"
                f"/workouts/{workout_id}"
            )
            resp = httpx.get(url, headers=self._headers())
            resp.raise_for_status()
            return resp.json()
        except Exception:
            logger.debug("Failed to fetch workout analysis for %s", workout_id, exc_info=True)
            return None
```

- [ ] **Step 2: Run tests to verify they pass**

```bash
cd apps/sync && uv run pytest tests/test_trainingpeaks_client.py -v
```

Expected: All 5 tests PASS.

- [ ] **Step 3: Commit**

```bash
git add apps/sync/app/services/trainingpeaks_client.py
git commit -m "feat(tp): implement TrainingPeaksClient with cookie auth"
```

---

## Chunk 3: TPSyncService

### Task 9: Write tests for TPSyncService

**Files:**
- Create: `apps/sync/tests/test_tp_sync_service.py`

- [ ] **Step 1: Write tests**

```python
from datetime import date
from unittest.mock import MagicMock

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base
from app.models.tp_completed_workout import TPCompletedWorkout
from app.models.tp_fitness_data import TPFitnessData
from app.models.tp_planned_workout import TPPlannedWorkout
from app.services.tp_sync_service import TPSyncService


@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine)
    session = session_factory()
    yield session
    session.close()


def make_mock_tp_client():
    mock = MagicMock()
    mock.get_fitness.return_value = [
        {
            "date": "2026-04-04",
            "ctl": 55.2,
            "atl": 72.1,
            "tsb": -16.9,
            "tpiTssActual": 85.0,
        },
    ]
    mock.get_workouts.return_value = [
        {
            "workoutId": 111,
            "workoutDay": "2026-04-04",
            "title": "Easy Run",
            "workoutTypeValueId": 3,
            "description": "Recovery jog",
            "totalTimePlanned": 2400,
            "tssPlanned": 40.0,
            "distancePlanned": 8000.0,
            "structure": {"warmup": [], "intervals": [], "cooldown": []},
            "completed": True,
            "totalTime": 2500,
            "distance": 8200.0,
            "tpiTssActual": 42.0,
            "heartRateAverage": 140,
            "heartRateMaximum": 165,
            "powerAverage": None,
            "powerMaximum": None,
            "normalizedPower": None,
            "caloriesUsed": 450,
            "ifActual": 0.85,
        },
        {
            "workoutId": 222,
            "workoutDay": "2026-04-06",
            "title": "Tempo Run",
            "workoutTypeValueId": 3,
            "description": "Tempo intervals",
            "totalTimePlanned": 3600,
            "tssPlanned": 80.0,
            "distancePlanned": 12000.0,
            "structure": None,
            "completed": False,
        },
    ]
    mock.get_workout_analysis.return_value = {
        "heartRateZones": [
            {"zoneName": "Z1", "timeInZone": 300},
            {"zoneName": "Z2", "timeInZone": 900},
            {"zoneName": "Z3", "timeInZone": 600},
            {"zoneName": "Z4", "timeInZone": 400},
            {"zoneName": "Z5", "timeInZone": 100},
        ],
        "powerZones": [],
        "laps": [{"lapIndex": 1, "distance": 8200}],
    }
    return mock


def test_sync_fitness(db_session):
    tp = make_mock_tp_client()
    service = TPSyncService(db=db_session, tp_client=tp)
    service.sync_fitness(date(2026, 4, 4))

    records = db_session.query(TPFitnessData).all()
    assert len(records) == 1
    assert records[0].ctl == 55.2
    assert records[0].atl == 72.1
    assert records[0].tsb == -16.9


def test_sync_fitness_upsert(db_session):
    tp = make_mock_tp_client()
    service = TPSyncService(db=db_session, tp_client=tp)
    service.sync_fitness(date(2026, 4, 4))

    # Change CTL and sync again
    tp.get_fitness.return_value[0]["ctl"] = 60.0
    service.sync_fitness(date(2026, 4, 4))

    records = db_session.query(TPFitnessData).all()
    assert len(records) == 1
    assert records[0].ctl == 60.0


def test_sync_planned_workouts(db_session):
    tp = make_mock_tp_client()
    service = TPSyncService(db=db_session, tp_client=tp)
    service.sync_planned_workouts(date(2026, 4, 4))

    planned = db_session.query(TPPlannedWorkout).all()
    # Both workouts (completed=True and completed=False) go into planned
    assert len(planned) == 2


def test_sync_completed_workouts(db_session):
    tp = make_mock_tp_client()
    service = TPSyncService(db=db_session, tp_client=tp)
    service.sync_completed_workouts(date(2026, 4, 4))

    completed = db_session.query(TPCompletedWorkout).all()
    # Only the completed workout (111)
    assert len(completed) == 1
    assert completed[0].tp_workout_id == "111"
    assert completed[0].avg_hr == 140
    assert completed[0].hr_zone1_sec == 300
    assert completed[0].hr_zone3_sec == 600


def test_sync_completed_workout_analysis_failure(db_session):
    """Zone data should be null if analysis call fails."""
    tp = make_mock_tp_client()
    tp.get_workout_analysis.return_value = None
    service = TPSyncService(db=db_session, tp_client=tp)
    service.sync_completed_workouts(date(2026, 4, 4))

    completed = db_session.query(TPCompletedWorkout).all()
    assert len(completed) == 1
    assert completed[0].hr_zone1_sec is None


def test_sync_all(db_session):
    tp = make_mock_tp_client()
    service = TPSyncService(db=db_session, tp_client=tp)
    service.sync_all(date(2026, 4, 4))

    assert db_session.query(TPFitnessData).count() == 1
    assert db_session.query(TPPlannedWorkout).count() == 2
    assert db_session.query(TPCompletedWorkout).count() == 1
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd apps/sync && uv run pytest tests/test_tp_sync_service.py -v
```

Expected: FAIL — `ModuleNotFoundError: No module named 'app.services.tp_sync_service'`

- [ ] **Step 3: Commit**

```bash
git add apps/sync/tests/test_tp_sync_service.py
git commit -m "test(tp): add TPSyncService tests (red)"
```

### Task 10: Implement TPSyncService

**Files:**
- Create: `apps/sync/app/services/tp_sync_service.py`

- [ ] **Step 1: Implement the service**

```python
import logging
from datetime import date, timedelta

from sqlalchemy.orm import Session

from app.models.tp_completed_workout import TPCompletedWorkout
from app.models.tp_fitness_data import TPFitnessData
from app.models.tp_planned_workout import TPPlannedWorkout
from app.services.trainingpeaks_client import TrainingPeaksClient

logger = logging.getLogger(__name__)


class TPSyncService:
    def __init__(self, db: Session, tp_client: TrainingPeaksClient):
        self.db = db
        self.tp = tp_client

    def _upsert(self, model_class, unique_field: str, unique_value, values: dict):
        """Generic upsert: find by unique field, update or create."""
        record = (
            self.db.query(model_class)
            .filter(getattr(model_class, unique_field) == unique_value)
            .first()
        )
        if record:
            for key, val in values.items():
                setattr(record, key, val)
        else:
            record = model_class(**values)
            self.db.add(record)
        self.db.commit()
        self.db.refresh(record)
        return record

    def sync_fitness(self, target_date: date) -> None:
        """Sync daily PMC data from TrainingPeaks."""
        date_str = target_date.isoformat()
        data = self.tp.get_fitness(date_str, date_str)
        for entry in data:
            entry_date_str = entry.get("date") or entry.get("calendarDate")
            if not entry_date_str:
                continue
            entry_date = date.fromisoformat(entry_date_str)
            values = {
                "date": entry_date,
                "ctl": entry.get("ctl"),
                "atl": entry.get("atl"),
                "tsb": entry.get("tsb"),
                "tss_day": entry.get("tpiTssActual") or entry.get("tssActual"),
                "training_load_7d": entry.get("trainingLoad7d"),
                "training_load_28d": entry.get("trainingLoad28d"),
                "intensity_factor": entry.get("ifActual"),
                "ramp_rate": entry.get("rampRate"),
            }
            self._upsert(TPFitnessData, "date", entry_date, values)

    def sync_planned_workouts(self, target_date: date) -> None:
        """Sync planned workouts for the next 30 days."""
        start = target_date
        end = target_date + timedelta(days=30)
        workouts = self.tp.get_workouts(start.isoformat(), end.isoformat())
        for w in workouts:
            workout_id = str(w.get("workoutId", ""))
            if not workout_id:
                continue
            values = {
                "tp_workout_id": workout_id,
                "date": date.fromisoformat(w["workoutDay"]),
                "title": w.get("title"),
                "workout_type": self._resolve_workout_type(w),
                "description": w.get("description"),
                "duration_sec_planned": w.get("totalTimePlanned"),
                "tss_planned": w.get("tssPlanned"),
                "distance_m_planned": w.get("distancePlanned"),
                "structure_json": w.get("structure"),
                "completed": w.get("completed", False),
            }
            self._upsert(TPPlannedWorkout, "tp_workout_id", workout_id, values)

    def sync_completed_workouts(self, target_date: date) -> None:
        """Sync completed workouts for the last 7 days with zone data."""
        start = target_date - timedelta(days=7)
        end = target_date
        workouts = self.tp.get_workouts(start.isoformat(), end.isoformat())
        for w in workouts:
            if not w.get("completed"):
                continue
            workout_id = str(w.get("workoutId", ""))
            if not workout_id:
                continue

            values = {
                "tp_workout_id": workout_id,
                "date": date.fromisoformat(w["workoutDay"]),
                "title": w.get("title"),
                "workout_type": self._resolve_workout_type(w),
                "duration_sec": w.get("totalTime"),
                "distance_m": w.get("distance"),
                "tss": w.get("tpiTssActual") or w.get("tssActual"),
                "intensity_factor": w.get("ifActual"),
                "avg_hr": w.get("heartRateAverage"),
                "max_hr": w.get("heartRateMaximum"),
                "avg_power": w.get("powerAverage"),
                "max_power": w.get("powerMaximum"),
                "normalized_power": w.get("normalizedPower"),
                "calories": w.get("caloriesUsed"),
            }

            # Fetch zone data
            analysis = self.tp.get_workout_analysis(workout_id)
            if analysis:
                values.update(self._extract_zones(analysis))
                values["laps_json"] = analysis.get("laps")

            self._upsert(TPCompletedWorkout, "tp_workout_id", workout_id, values)

    def sync_all(self, target_date: date) -> None:
        """Run all TP sync steps."""
        self.sync_fitness(target_date)
        self.sync_planned_workouts(target_date)
        self.sync_completed_workouts(target_date)

    @staticmethod
    def _resolve_workout_type(workout: dict) -> str | None:
        """Extract workout type string from TP workout data."""
        wt = workout.get("workoutType")
        if isinstance(wt, dict):
            return wt.get("description") or wt.get("name")
        if isinstance(wt, str):
            return wt
        return None

    @staticmethod
    def _extract_zones(analysis: dict) -> dict:
        """Extract HR and power zone seconds from workout analysis."""
        result = {}
        hr_zones = analysis.get("heartRateZones", [])
        for i, zone in enumerate(hr_zones[:5], 1):
            result[f"hr_zone{i}_sec"] = zone.get("timeInZone")

        power_zones = analysis.get("powerZones", [])
        for i, zone in enumerate(power_zones[:7], 1):
            result[f"power_zone{i}_sec"] = zone.get("timeInZone")

        return result
```

- [ ] **Step 2: Run tests to verify they pass**

```bash
cd apps/sync && uv run pytest tests/test_tp_sync_service.py -v
```

Expected: All 6 tests PASS.

- [ ] **Step 3: Commit**

```bash
git add apps/sync/app/services/tp_sync_service.py
git commit -m "feat(tp): implement TPSyncService with upsert pattern"
```

---

## Chunk 4: Router, Wiring & Integration

### Task 11: Create TP router

**Files:**
- Create: `apps/sync/app/routers/tp.py`

- [ ] **Step 1: Implement the router**

```python
import logging
from datetime import date, timedelta

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.models.tp_completed_workout import TPCompletedWorkout
from app.models.tp_fitness_data import TPFitnessData
from app.models.tp_planned_workout import TPPlannedWorkout
from app.schemas.tp import (
    TPCompletedWorkoutResponse,
    TPFitnessResponse,
    TPPlannedWorkoutResponse,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/tp", tags=["trainingpeaks"])


@router.get("/fitness", response_model=list[TPFitnessResponse])
def list_fitness(
    from_date: date = Query(default_factory=lambda: date.today() - timedelta(days=90)),
    to_date: date = Query(default_factory=lambda: date.today()),
    db: Session = Depends(get_db),
):
    return (
        db.query(TPFitnessData)
        .filter(TPFitnessData.date >= from_date, TPFitnessData.date <= to_date)
        .order_by(TPFitnessData.date.desc())
        .all()
    )


@router.get("/workouts/planned", response_model=list[TPPlannedWorkoutResponse])
def list_planned_workouts(
    from_date: date = Query(default_factory=lambda: date.today()),
    to_date: date = Query(default_factory=lambda: date.today() + timedelta(days=30)),
    db: Session = Depends(get_db),
):
    return (
        db.query(TPPlannedWorkout)
        .filter(TPPlannedWorkout.date >= from_date, TPPlannedWorkout.date <= to_date)
        .order_by(TPPlannedWorkout.date)
        .all()
    )


@router.get("/workouts/completed", response_model=list[TPCompletedWorkoutResponse])
def list_completed_workouts(
    from_date: date = Query(default_factory=lambda: date.today() - timedelta(days=30)),
    to_date: date = Query(default_factory=lambda: date.today()),
    db: Session = Depends(get_db),
):
    return (
        db.query(TPCompletedWorkout)
        .filter(TPCompletedWorkout.date >= from_date, TPCompletedWorkout.date <= to_date)
        .order_by(TPCompletedWorkout.date.desc())
        .all()
    )


@router.get("/workouts/{tp_workout_id}", response_model=TPCompletedWorkoutResponse)
def get_completed_workout(tp_workout_id: str, db: Session = Depends(get_db)):
    record = (
        db.query(TPCompletedWorkout)
        .filter(TPCompletedWorkout.tp_workout_id == tp_workout_id)
        .first()
    )
    if not record:
        raise HTTPException(status_code=404, detail="Workout not found")
    return record


def _run_tp_sync(days_back: int) -> None:
    """Run TP sync for a date range."""
    from app.database import SessionLocal
    from app.services.tp_sync_service import TPSyncService
    from app.services.trainingpeaks_client import TrainingPeaksClient

    db = SessionLocal()
    try:
        tp_client = TrainingPeaksClient(auth_cookie=settings.tp_auth_cookie)
        tp_client.login()
        tp_sync = TPSyncService(db=db, tp_client=tp_client)
        today = date.today()
        for i in range(days_back, -1, -1):
            target = today - timedelta(days=i)
            try:
                tp_sync.sync_all(target)
                logger.info("TP sync completed for %s", target)
            except Exception:
                logger.error("TP sync failed for %s", target, exc_info=True)
    finally:
        db.close()


@router.post("/sync/trigger")
def trigger_tp_sync(
    background_tasks: BackgroundTasks,
    days_back: int = 7,
):
    if not settings.tp_enabled or not settings.tp_auth_cookie:
        raise HTTPException(status_code=400, detail="TrainingPeaks not configured")
    background_tasks.add_task(_run_tp_sync, days_back)
    return {"status": "tp_sync_started", "days_back": days_back}
```

- [ ] **Step 2: Commit**

```bash
git add apps/sync/app/routers/tp.py
git commit -m "feat(tp): add /api/tp/ router with endpoints"
```

### Task 12: Wire into main.py and sync_orchestrator.py

**Files:**
- Modify: `apps/sync/app/main.py`
- Modify: `apps/sync/app/services/sync_orchestrator.py`

- [ ] **Step 1: Add TP router to main.py**

In `apps/sync/app/main.py`, add import:

```python
from app.routers import tp
```

Add after the last `app.include_router(...)`:

```python
app.include_router(tp.router)
```

- [ ] **Step 2: Add TP sync to sync_orchestrator.py**

In `apps/sync/app/services/sync_orchestrator.py`, add after the existing sync code (after `updater.update(target_date)`), before the `finally:`:

```python
        if settings.tp_enabled and settings.tp_auth_cookie:
            try:
                from app.services.tp_sync_service import TPSyncService
                from app.services.trainingpeaks_client import TrainingPeaksClient

                tp_client = TrainingPeaksClient(auth_cookie=settings.tp_auth_cookie)
                tp_client.login()
                tp_sync = TPSyncService(db=db, tp_client=tp_client)
                tp_sync.sync_all(target_date)
            except Exception:
                logger.exception("TrainingPeaks sync failed")
```

- [ ] **Step 3: Run lint**

```bash
cd apps/sync && uv run ruff check .
```

Expected: No errors.

- [ ] **Step 4: Run all tests**

```bash
cd apps/sync && uv run pytest tests/ -v
```

Expected: All tests pass (existing + new).

- [ ] **Step 5: Commit**

```bash
git add apps/sync/app/main.py apps/sync/app/services/sync_orchestrator.py
git commit -m "feat(tp): wire TP router and sync into app"
```

### Task 13: Run migration and verify API

- [ ] **Step 1: Run migration against local DB**

```bash
cd apps/sync && uv run alembic upgrade head
```

Expected: Migration applies successfully.

- [ ] **Step 2: Verify API endpoints load**

```bash
curl -s http://localhost:8000/api/tp/fitness | head -c 100
curl -s http://localhost:8000/api/tp/workouts/planned | head -c 100
curl -s http://localhost:8000/api/tp/workouts/completed | head -c 100
```

Expected: Empty arrays `[]` (no data yet, but no errors).

- [ ] **Step 3: Verify health check still works**

```bash
curl -s http://localhost:8000/api/health
```

Expected: `{"status":"ok"}`

- [ ] **Step 4: Final commit**

```bash
git add -A && git commit -m "feat(tp): TrainingPeaks backend integration complete"
```

# Plan Dashboard — Phase 1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the Daily Dashboard (`/plan`) with top strip (6 live metrics) and 5 expandable pillar rows, powered by a frequent sync job and new API endpoint.

**Architecture:** New `stress_readings` table stores raw Garmin stress data for last-hour computation. New `frequent_sync_job` runs every 15 min (7:00-23:00) to update nutrition (MFP) and stress for today. New `/api/plan/daily` endpoint assembles all strip + pillar data in a single response. Frontend is a new Next.js page at `/plan` with a client component that polls for updates every 60s.

**Tech Stack:** Python/FastAPI/SQLAlchemy (backend), Next.js 16/React 19/TypeScript/Tailwind v4 (frontend), Alembic (migrations), pytest with SQLite in-memory (tests)

**Spec:** `docs/superpowers/specs/2026-04-04-plan-dashboard-design.md`

---

### Task 1: StressReading model + migration

**Files:**
- Create: `apps/sync/app/models/stress_reading.py`
- Modify: `apps/sync/app/models/__init__.py`
- Test: `apps/sync/tests/test_models.py`

- [ ] **Step 1: Write the failing test**

Add to `apps/sync/tests/test_models.py`:

```python
from app.models.stress_reading import StressReading

def test_stress_reading_creation(db_session):
    from datetime import date, datetime

    reading = StressReading(
        date=date(2026, 4, 4),
        timestamp=datetime(2026, 4, 4, 10, 30, 0),
        value=42,
    )
    db_session.add(reading)
    db_session.commit()

    result = db_session.query(StressReading).first()
    assert result.value == 42
    assert result.date == date(2026, 4, 4)
    assert result.timestamp == datetime(2026, 4, 4, 10, 30, 0)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd apps/sync && uv run pytest tests/test_models.py::test_stress_reading_creation -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'app.models.stress_reading'`

- [ ] **Step 3: Create the model**

Create `apps/sync/app/models/stress_reading.py`:

```python
from sqlalchemy import Date, DateTime, Integer
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class StressReading(Base):
    __tablename__ = "stress_readings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    date: Mapped[Date] = mapped_column(Date, nullable=False, index=True)
    timestamp: Mapped[DateTime] = mapped_column(DateTime, nullable=False)
    value: Mapped[int] = mapped_column(Integer, nullable=False)
```

- [ ] **Step 4: Register in `__init__.py`**

Add to `apps/sync/app/models/__init__.py`:

```python
from app.models.stress_reading import StressReading
```

And add `"StressReading"` to the `__all__` list.

- [ ] **Step 5: Run test to verify it passes**

Run: `cd apps/sync && uv run pytest tests/test_models.py::test_stress_reading_creation -v`
Expected: PASS

- [ ] **Step 6: Generate Alembic migration**

Run: `cd apps/sync && uv run alembic revision --autogenerate -m "add stress_readings table"`
Verify the generated migration creates the `stress_readings` table with columns `id`, `date`, `timestamp`, `value` and an index on `date`.

- [ ] **Step 7: Commit**

```bash
git add apps/sync/app/models/stress_reading.py apps/sync/app/models/__init__.py apps/sync/tests/test_models.py apps/sync/alembic/versions/
git commit -m "feat(plan): add StressReading model and migration"
```

---

### Task 2: Stress sync method + last-hour calculation

**Files:**
- Modify: `apps/sync/app/services/sync_service.py`
- Modify: `apps/sync/app/services/calculations.py`
- Test: `apps/sync/tests/test_calculations.py`
- Test: `apps/sync/tests/test_sync_service.py`

- [ ] **Step 1: Write the failing test for stress_last_hour calculation**

Add to `apps/sync/tests/test_calculations.py`:

```python
from datetime import datetime
from app.services.calculations import calculate_stress_last_hour


def test_stress_last_hour_basic():
    """Average stress from readings in the last 60 minutes."""
    now = datetime(2026, 4, 4, 14, 0, 0)
    readings = [
        # 50 min ago — included
        (datetime(2026, 4, 4, 13, 10, 0), 30),
        # 30 min ago — included
        (datetime(2026, 4, 4, 13, 30, 0), 40),
        # 10 min ago — included
        (datetime(2026, 4, 4, 13, 50, 0), 50),
        # 70 min ago — excluded
        (datetime(2026, 4, 4, 12, 50, 0), 90),
    ]
    result = calculate_stress_last_hour(readings, now)
    assert result == 40  # (30+40+50) / 3


def test_stress_last_hour_no_readings():
    now = datetime(2026, 4, 4, 14, 0, 0)
    result = calculate_stress_last_hour([], now)
    assert result is None


def test_stress_last_hour_skips_negative():
    """Negative values (-1=activity, -2=unusable) are excluded."""
    now = datetime(2026, 4, 4, 14, 0, 0)
    readings = [
        (datetime(2026, 4, 4, 13, 30, 0), 40),
        (datetime(2026, 4, 4, 13, 40, 0), -1),
        (datetime(2026, 4, 4, 13, 50, 0), 60),
    ]
    result = calculate_stress_last_hour(readings, now)
    assert result == 50  # (40+60) / 2
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd apps/sync && uv run pytest tests/test_calculations.py::test_stress_last_hour_basic -v`
Expected: FAIL with `ImportError: cannot import name 'calculate_stress_last_hour'`

- [ ] **Step 3: Implement `calculate_stress_last_hour`**

Add to `apps/sync/app/services/calculations.py`:

```python
from datetime import datetime, timedelta


def calculate_stress_last_hour(
    readings: list[tuple[datetime, int]],
    now: datetime,
) -> int | None:
    """Average stress from readings within the last 60 minutes.

    Skips negative values (-1=activity, -2=unusable).
    """
    cutoff = now - timedelta(hours=1)
    valid = [val for ts, val in readings if ts >= cutoff and val > 0]
    if not valid:
        return None
    return round(sum(valid) / len(valid))
```

- [ ] **Step 4: Run calculation tests**

Run: `cd apps/sync && uv run pytest tests/test_calculations.py -k stress_last_hour -v`
Expected: all 3 PASS

- [ ] **Step 5: Write the failing test for sync_stress_readings**

Add to `apps/sync/tests/test_sync_service.py`:

```python
from app.models.stress_reading import StressReading


def test_sync_stress_readings(db_session):
    mock_garmin = make_mock_garmin()
    mock_garmin.get_stress_data.return_value = {
        "stressValuesArray": [
            [1712234400000, 30],  # 10:00
            [1712234580000, -1],  # 10:03 (activity)
            [1712234760000, 45],  # 10:06
        ],
        "overallStressLevel": 35,
        "maxStressLevel": 45,
    }
    sync = SyncService(db=db_session, garmin=mock_garmin)
    sync.sync_stress_readings(date(2026, 4, 4))

    readings = db_session.query(StressReading).all()
    assert len(readings) == 3
    assert readings[0].value == 30
    assert readings[1].value == -1
    assert readings[2].value == 45
```

- [ ] **Step 6: Run test to verify it fails**

Run: `cd apps/sync && uv run pytest tests/test_sync_service.py::test_sync_stress_readings -v`
Expected: FAIL with `AttributeError: 'SyncService' object has no attribute 'sync_stress_readings'`

- [ ] **Step 7: Implement `sync_stress_readings`**

Add method to `SyncService` in `apps/sync/app/services/sync_service.py`:

```python
from app.models.stress_reading import StressReading
from datetime import datetime

def sync_stress_readings(self, target_date: date) -> int:
    """Sync raw stress data points into stress_readings table.

    Returns number of readings stored.
    """
    date_str = target_date.isoformat()
    stress = self.garmin.get_stress_data(date_str)
    values_array = stress.get("stressValuesArray", [])
    if not values_array:
        return 0

    # Delete existing readings for this date (idempotent re-sync)
    self.db.query(StressReading).filter(StressReading.date == target_date).delete()

    count = 0
    for ts_ms, value in values_array:
        reading = StressReading(
            date=target_date,
            timestamp=datetime.fromtimestamp(ts_ms / 1000),
            value=value,
        )
        self.db.add(reading)
        count += 1

    self.db.commit()
    return count
```

- [ ] **Step 8: Run test to verify it passes**

Run: `cd apps/sync && uv run pytest tests/test_sync_service.py::test_sync_stress_readings -v`
Expected: PASS

- [ ] **Step 9: Commit**

```bash
git add apps/sync/app/services/calculations.py apps/sync/app/services/sync_service.py apps/sync/tests/test_calculations.py apps/sync/tests/test_sync_service.py
git commit -m "feat(plan): add stress readings sync and last-hour calculation"
```

---

### Task 3: Frequent sync job

**Files:**
- Modify: `apps/sync/app/scheduler.py`
- Modify: `apps/sync/app/services/sync_orchestrator.py`
- Test: `apps/sync/tests/test_sync_orchestrator.py` (new)

- [ ] **Step 1: Write the failing test**

Create `apps/sync/tests/test_sync_orchestrator.py`:

```python
from unittest.mock import patch, MagicMock
from datetime import date

from app.services.sync_orchestrator import run_frequent_sync


def test_run_frequent_sync_calls_nutrition_and_stress():
    """Frequent sync only syncs nutrition and stress readings for today."""
    mock_db = MagicMock()
    mock_sync = MagicMock()

    with (
        patch("app.services.sync_orchestrator.SessionLocal", return_value=mock_db),
        patch("app.services.sync_orchestrator.GarminClient") as mock_garmin_cls,
        patch("app.services.sync_orchestrator.SyncService", return_value=mock_sync),
        patch("app.services.sync_orchestrator.settings") as mock_settings,
    ):
        mock_settings.garmin_email = "test@test.com"
        mock_settings.garmin_password = "pass"
        mock_settings.mfp_cookies = '{"key": "val"}'
        mock_settings.nightscout_url = ""
        mock_settings.nightscout_token = ""

        run_frequent_sync()

        mock_sync.sync_nutrition.assert_called_once_with(date.today())
        mock_sync.sync_stress_readings.assert_called_once_with(date.today())
        # Should NOT call full sync methods
        mock_sync.sync_all.assert_not_called()
        mock_sync.sync_sleep.assert_not_called()
        mock_sync.sync_activities.assert_not_called()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd apps/sync && uv run pytest tests/test_sync_orchestrator.py -v`
Expected: FAIL with `ImportError: cannot import name 'run_frequent_sync'`

- [ ] **Step 3: Implement `run_frequent_sync`**

Add to `apps/sync/app/services/sync_orchestrator.py`:

```python
def run_frequent_sync() -> None:
    """Lightweight sync for intraday data: nutrition (MFP) + stress readings."""
    db = SessionLocal()
    try:
        garmin = GarminClient(email=settings.garmin_email, password=settings.garmin_password)
        garmin.login()

        user = db.query(User).first()
        mfp_cookies = (
            user.mfp_cookies if user and user.mfp_cookies else None
        ) or settings.mfp_cookies

        mfp = None
        if mfp_cookies:
            from app.services.mfp_client import MFPClient

            mfp = MFPClient(cookies_json=mfp_cookies)
            mfp.login()

        sync = SyncService(db=db, garmin=garmin, mfp=mfp)
        today = date.today()
        sync.sync_nutrition(today)
        sync.sync_stress_readings(today)
        logger.info(f"Frequent sync completed for {today}")
    except Exception:
        logger.exception("Frequent sync failed")
    finally:
        db.close()
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd apps/sync && uv run pytest tests/test_sync_orchestrator.py -v`
Expected: PASS

- [ ] **Step 5: Add frequent sync to scheduler**

Modify `apps/sync/app/scheduler.py`:

```python
import logging
from datetime import date

from apscheduler.schedulers.background import BackgroundScheduler

from app.services.sync_orchestrator import run_sync_for_date, run_frequent_sync

logger = logging.getLogger(__name__)


def daily_sync_job():
    logger.info("Starting daily sync job")
    try:
        target = date.today()
        run_sync_for_date(target)
        logger.info(f"Daily sync completed for {target}")
    except Exception:
        logger.exception("Daily sync failed")


def frequent_sync_job():
    logger.info("Starting frequent sync job")
    try:
        run_frequent_sync()
    except Exception:
        logger.exception("Frequent sync failed")


scheduler = BackgroundScheduler()
scheduler.add_job(daily_sync_job, "cron", hour=5, minute=0, id="daily_sync")
scheduler.add_job(
    frequent_sync_job,
    "cron",
    minute="*/15",
    hour="7-23",
    id="frequent_sync",
)
```

- [ ] **Step 6: Commit**

```bash
git add apps/sync/app/scheduler.py apps/sync/app/services/sync_orchestrator.py apps/sync/tests/test_sync_orchestrator.py
git commit -m "feat(plan): add frequent sync job (nutrition + stress every 15min)"
```

---

### Task 4: Plan daily API schema

**Files:**
- Create: `apps/sync/app/schemas/plan.py`
- Test: (schema validation tested implicitly by endpoint test in Task 5)

- [ ] **Step 1: Create the Pydantic schemas**

Create `apps/sync/app/schemas/plan.py`:

```python
from datetime import date

from pydantic import BaseModel


class StripMetric(BaseModel):
    label: str
    value: str
    secondary_value: str | None = None
    unit: str
    target: str | None = None
    pct: int | None = None
    trend: str | None = None  # "up", "down", "flat"


class PillarKPI(BaseModel):
    label: str
    value: str
    unit: str
    target: str | None = None
    status: str | None = None  # "on_track", "behind", "met"
    spark: list[float] = []


class PillarDriver(BaseModel):
    label: str
    value: str
    unit: str


class PillarData(BaseModel):
    id: str
    name: str
    color: str
    collapsed_kpis: list[PillarKPI]
    expanded_kpis: list[PillarKPI] = []
    drivers: list[PillarDriver] = []


class PlanDailyResponse(BaseModel):
    date: date
    strip: list[StripMetric]
    pillars: list[PillarData]
```

- [ ] **Step 2: Commit**

```bash
git add apps/sync/app/schemas/plan.py
git commit -m "feat(plan): add Pydantic schemas for plan daily endpoint"
```

---

### Task 5: Plan daily API endpoint

**Files:**
- Create: `apps/sync/app/routers/plan.py`
- Modify: `apps/sync/app/main.py`
- Test: `apps/sync/tests/test_plan_router.py` (new)

- [ ] **Step 1: Write the failing test**

Create `apps/sync/tests/test_plan_router.py`:

```python
from datetime import date, datetime

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base, get_db
from app.main import app
from app.models import (
    Activity,
    BodyComposition,
    DailySummary,
    NutritionDaily,
    PerformanceMetric,
    SleepSession,
)
from app.models.stress_reading import StressReading
from app.models.training_readiness import TrainingReadiness
from app.models.user_goal import UserGoal

engine = create_engine("sqlite:///:memory:")
TestSession = sessionmaker(bind=engine)


@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.create_all(engine)
    yield
    Base.metadata.drop_all(engine)


@pytest.fixture
def db():
    session = TestSession()
    yield session
    session.close()


@pytest.fixture
def client(db):
    def override():
        yield db

    app.dependency_overrides[get_db] = override
    yield TestClient(app)
    app.dependency_overrides.clear()


def seed_data(db, target=date(2026, 4, 4)):
    db.add(DailySummary(date=target, resting_hr=48, stress_avg=28, body_battery_high=72))
    db.add(SleepSession(date=target, total_sleep_min=452, deep_min=81, avg_hrv=52.0, sleep_score=85))
    db.add(NutritionDaily(date=target, calories=1420, protein_g=82.0, carbs_g=180.0, fat_g=55.0))
    db.add(PerformanceMetric(
        date=target, tss=65.0, atl=78.0, ctl=62.0, tsb=-16.0,
        vo2max=48.3, recovery_score=68.0,
    ))
    db.add(UserGoal(metric_key="calories", target_value=2200, target_unit="kcal", category="nutrition"))
    db.add(UserGoal(metric_key="protein", target_value=125, target_unit="g", category="nutrition"))
    # Stress readings for last hour test
    now = datetime(2026, 4, 4, 14, 0, 0)
    db.add(StressReading(date=target, timestamp=datetime(2026, 4, 4, 13, 30), value=30))
    db.add(StressReading(date=target, timestamp=datetime(2026, 4, 4, 13, 45), value=40))
    db.add(StressReading(date=target, timestamp=datetime(2026, 4, 4, 13, 55), value=38))
    db.commit()


def test_plan_daily_returns_strip_and_pillars(client, db):
    seed_data(db)
    resp = client.get("/api/plan/daily")
    assert resp.status_code == 200
    data = resp.json()
    assert "strip" in data
    assert "pillars" in data
    assert len(data["strip"]) == 6
    assert len(data["pillars"]) == 5
    # Check strip labels
    labels = [s["label"] for s in data["strip"]]
    assert "Calories" in labels
    assert "Protein" in labels
    assert "Stress 1h" in labels
    assert "HRV" in labels
    assert "TSB" in labels
    assert "Sleep" in labels


def test_plan_daily_calories_show_consumed_and_target(client, db):
    seed_data(db)
    resp = client.get("/api/plan/daily")
    data = resp.json()
    cal = next(s for s in data["strip"] if s["label"] == "Calories")
    assert cal["value"] == "1,420"
    assert cal["target"] == "2,200"
    assert cal["pct"] == 65  # 1420/2200 ~ 64.5 -> 65


def test_plan_daily_empty_db(client, db):
    resp = client.get("/api/plan/daily")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["strip"]) == 6
    assert len(data["pillars"]) == 5
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd apps/sync && uv run pytest tests/test_plan_router.py -v`
Expected: FAIL (router does not exist yet)

- [ ] **Step 3: Implement the router**

Create `apps/sync/app/routers/plan.py`:

```python
from datetime import date, datetime, timedelta

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.constants import RUNNING_TYPES, STRENGTH_TYPE
from app.database import get_db
from app.models import (
    Activity,
    BodyComposition,
    DailySummary,
    NutritionDaily,
    PerformanceMetric,
    SleepSession,
)
from app.models.exercise_set import ExerciseSet
from app.models.stress_reading import StressReading
from app.models.training_readiness import TrainingReadiness
from app.models.user_goal import UserGoal
from app.schemas.plan import (
    PillarData,
    PillarDriver,
    PillarKPI,
    PlanDailyResponse,
    StripMetric,
)
from app.services.calculations import calculate_stress_last_hour

router = APIRouter(prefix="/api/plan", tags=["plan"])


def _fmt(val, decimals: int = 0) -> str:
    if val is None:
        return "--"
    if decimals == 0:
        return f"{int(round(val)):,}"
    return f"{val:.{decimals}f}"


def _fmt_duration_min(minutes: int | None) -> str:
    if minutes is None:
        return "--"
    h = minutes // 60
    m = minutes % 60
    return f"{h}:{m:02d}"


def _pct(value: float | None, target: float | None) -> int | None:
    if value is None or target is None or target == 0:
        return None
    return min(100, round(value / target * 100))


def _spark_7d(db: Session, model, column: str, target_date: date) -> list[float]:
    start = target_date - timedelta(days=6)
    rows = (
        db.query(getattr(model, column))
        .filter(model.date >= start, model.date <= target_date)
        .order_by(model.date)
        .all()
    )
    return [float(r[0]) for r in rows if r[0] is not None]


def _hrv_trend(db: Session, target_date: date, current_hrv: float | None) -> str:
    if current_hrv is None:
        return "flat"
    avg_7d = _spark_7d(db, SleepSession, "avg_hrv", target_date)
    if len(avg_7d) < 3:
        return "flat"
    recent_avg = sum(avg_7d) / len(avg_7d)
    if current_hrv > recent_avg * 1.03:
        return "up"
    if current_hrv < recent_avg * 0.97:
        return "down"
    return "flat"


def _tsb_label(tsb: float | None) -> str:
    if tsb is None:
        return ""
    if tsb > 10:
        return "fresh"
    if tsb > -10:
        return "neutral"
    if tsb > -30:
        return "building load"
    return "overreaching"


def _goal_val(goals: dict[str, UserGoal], key: str) -> float | None:
    g = goals.get(key)
    return g.target_value if g else None


def _build_strip(
    db: Session,
    target_date: date,
    daily: DailySummary | None,
    sleep: SleepSession | None,
    nutrition: NutritionDaily | None,
    perf: PerformanceMetric | None,
    goals: dict[str, UserGoal],
) -> list[StripMetric]:
    # Calories
    cal_val = nutrition.calories if nutrition else None
    cal_target = _goal_val(goals, "calories")

    # Protein
    prot_val = nutrition.protein_g if nutrition else None
    prot_target = _goal_val(goals, "protein")

    # Stress last hour
    readings = (
        db.query(StressReading.timestamp, StressReading.value)
        .filter(StressReading.date == target_date)
        .order_by(StressReading.timestamp)
        .all()
    )
    stress_1h = calculate_stress_last_hour(readings, datetime.now())
    stress_day_avg = daily.stress_avg if daily else None

    # HRV
    hrv_val = sleep.avg_hrv if sleep else None
    hrv_trend = _hrv_trend(db, target_date, hrv_val)
    hrv_7d = _spark_7d(db, SleepSession, "avg_hrv", target_date)
    hrv_7d_avg = round(sum(hrv_7d) / len(hrv_7d)) if hrv_7d else None

    # TSB
    tsb_val = perf.tsb if perf else None

    # Sleep
    sleep_min = sleep.total_sleep_min if sleep else None
    deep_pct = None
    if sleep and sleep.deep_min and sleep.total_sleep_min and sleep.total_sleep_min > 0:
        deep_pct = round(sleep.deep_min / sleep.total_sleep_min * 100)

    return [
        StripMetric(
            label="Calories",
            value=_fmt(cal_val),
            unit="kcal",
            target=_fmt(cal_target) if cal_target else None,
            pct=_pct(cal_val, cal_target),
        ),
        StripMetric(
            label="Protein",
            value=_fmt(prot_val),
            unit="g",
            target=_fmt(prot_target) if prot_target else None,
            pct=_pct(prot_val, prot_target),
        ),
        StripMetric(
            label="Stress 1h",
            value=_fmt(stress_1h),
            unit="avg",
            secondary_value=f"day avg: {_fmt(stress_day_avg)}" if stress_day_avg else None,
        ),
        StripMetric(
            label="HRV",
            value=_fmt(hrv_val),
            unit="ms",
            trend=hrv_trend,
            secondary_value=f"7d avg: {_fmt(hrv_7d_avg)}" if hrv_7d_avg else None,
        ),
        StripMetric(
            label="TSB",
            value=_fmt(tsb_val),
            unit="form",
            secondary_value=_tsb_label(tsb_val),
        ),
        StripMetric(
            label="Sleep",
            value=_fmt_duration_min(sleep_min),
            unit="hrs",
            secondary_value=f"deep {deep_pct}%" if deep_pct else None,
        ),
    ]


def _build_p1_aerobic(
    db: Session, target_date: date, perf: PerformanceMetric | None
) -> PillarData:
    vo2 = perf.vo2max if perf else None
    ctl = perf.ctl if perf else None
    atl = perf.atl if perf else None
    tsb = perf.tsb if perf else None

    # Weekly running stats
    start = target_date - timedelta(days=6)
    acts = (
        db.query(Activity)
        .filter(Activity.date >= start, Activity.date <= target_date, Activity.type.in_(RUNNING_TYPES))
        .all()
    )
    weekly_km = round(sum((a.distance_m or 0) / 1000 for a in acts), 1)
    weekly_tss = round(sum(a.tss or 0 for a in acts), 0)

    return PillarData(
        id="aerobic",
        name="P1 Motor Aeróbico",
        color="#00d68f",
        collapsed_kpis=[
            PillarKPI(label="VO2max", value=_fmt(vo2, 1), unit="ml/kg"),
            PillarKPI(label="CTL", value=_fmt(ctl), unit=""),
            PillarKPI(label="VT1 pace", value="--", unit="min/km"),
        ],
        expanded_kpis=[
            PillarKPI(
                label="VO2max", value=_fmt(vo2, 1), unit="ml/kg",
                target=">52", spark=_spark_7d(db, PerformanceMetric, "vo2max", target_date),
            ),
            PillarKPI(
                label="CTL", value=_fmt(ctl), unit="",
                target=">100", spark=_spark_7d(db, PerformanceMetric, "ctl", target_date),
            ),
            PillarKPI(label="VT1 pace", value="--", unit="min/km", target="<5:00"),
        ],
        drivers=[
            PillarDriver(label="km/week", value=_fmt(weekly_km, 1), unit="km"),
            PillarDriver(label="TSS/week", value=_fmt(weekly_tss), unit=""),
            PillarDriver(label="ATL", value=_fmt(atl), unit=""),
        ],
    )


def _build_p2_strength(db: Session, target_date: date) -> PillarData:
    start_7d = target_date - timedelta(days=6)
    start_30d = target_date - timedelta(days=30)

    # Weekly strength stats
    str_acts = (
        db.query(Activity)
        .filter(Activity.date >= start_7d, Activity.date <= target_date, Activity.type == STRENGTH_TYPE)
        .all()
    )
    sess_count = len(str_acts)
    str_hours = round(sum((a.duration_sec or 0) / 3600 for a in str_acts), 1)

    # Days since last strength
    last = (
        db.query(Activity.date)
        .filter(Activity.type == STRENGTH_TYPE, Activity.date <= target_date)
        .order_by(Activity.date.desc())
        .first()
    )
    days_since = (target_date - last[0]).days if last else None

    # Pull-ups max from last 30 days
    str_act_ids = [a.id for a in db.query(Activity.id).filter(
        Activity.date >= start_30d, Activity.date <= target_date, Activity.type == STRENGTH_TYPE
    ).all()]
    pullups = None
    if str_act_ids:
        result = (
            db.query(ExerciseSet.reps)
            .filter(
                ExerciseSet.activity_id.in_(str_act_ids),
                ExerciseSet.exercise_name.ilike("%pull%up%"),
                ExerciseSet.reps.isnot(None),
            )
            .order_by(ExerciseSet.reps.desc())
            .first()
        )
        pullups = result[0] if result else None

    return PillarData(
        id="strength",
        name="P2 Durabilidad Muscular",
        color="#00c4b4",
        collapsed_kpis=[
            PillarKPI(label="Pull-ups", value=_fmt(pullups), unit="reps"),
            PillarKPI(label="DL 5RM", value="--", unit="kg"),
            PillarKPI(label="Calf raises", value="--", unit="reps"),
        ],
        expanded_kpis=[
            PillarKPI(label="Pull-ups", value=_fmt(pullups), unit="reps", target="15"),
            PillarKPI(label="DL 5RM", value="--", unit="kg", target="103"),
            PillarKPI(label="Calf raises", value="--", unit="reps", target="30"),
        ],
        drivers=[
            PillarDriver(label="Sessions/wk", value=str(sess_count), unit="/2"),
            PillarDriver(label="Days since", value=_fmt(days_since), unit="days"),
            PillarDriver(label="Strength time", value=_fmt(str_hours, 1), unit="hrs"),
        ],
    )


def _build_p3_fueling(
    db: Session, target_date: date, nutrition: NutritionDaily | None, body_comp: BodyComposition | None
) -> PillarData:
    weight = body_comp.weight_kg if body_comp else None
    bf = body_comp.body_fat_pct if body_comp else None

    # Glucose (latest)
    from app.models.glucose_daily import GlucoseDaily

    glucose = db.query(GlucoseDaily).filter_by(date=target_date).first()
    gluc_val = glucose.mean_glucose if glucose else None

    # 7d avg protein
    start = target_date - timedelta(days=6)
    prot_rows = (
        db.query(NutritionDaily.protein_g)
        .filter(NutritionDaily.date >= start, NutritionDaily.date <= target_date)
        .all()
    )
    prot_vals = [r[0] for r in prot_rows if r[0] is not None]
    prot_7d = round(sum(prot_vals) / len(prot_vals)) if prot_vals else None

    # 7d avg calories
    cal_rows = (
        db.query(NutritionDaily.calories)
        .filter(NutritionDaily.date >= start, NutritionDaily.date <= target_date)
        .all()
    )
    cal_vals = [r[0] for r in cal_rows if r[0] is not None]
    cal_7d = round(sum(cal_vals) / len(cal_vals)) if cal_vals else None

    return PillarData(
        id="fueling",
        name="P3 Fueling y Metabolismo",
        color="#b388ff",
        collapsed_kpis=[
            PillarKPI(label="Weight", value=_fmt(weight, 1), unit="kg"),
            PillarKPI(label="Body fat", value=_fmt(bf, 1) if bf else "--", unit="%"),
            PillarKPI(label="Glucose", value=_fmt(gluc_val), unit="mg/dL"),
        ],
        expanded_kpis=[
            PillarKPI(
                label="Weight", value=_fmt(weight, 1), unit="kg",
                spark=_spark_7d(db, BodyComposition, "weight_kg", target_date),
            ),
            PillarKPI(label="Body fat", value=_fmt(bf, 1) if bf else "--", unit="%", target="<15%"),
            PillarKPI(label="Glucose", value=_fmt(gluc_val), unit="mg/dL"),
        ],
        drivers=[
            PillarDriver(label="Cal avg 7d", value=_fmt(cal_7d), unit="kcal"),
            PillarDriver(label="Prot avg 7d", value=_fmt(prot_7d), unit="g"),
        ],
    )


def _build_p4_recovery(
    db: Session, target_date: date, daily: DailySummary | None, sleep: SleepSession | None, perf: PerformanceMetric | None
) -> PillarData:
    hrv = sleep.avg_hrv if sleep else None
    sleep_min = sleep.total_sleep_min if sleep else None
    rhr = daily.resting_hr if daily else None
    sleep_score = sleep.sleep_score if sleep else None
    bb = daily.body_battery_high if daily else None
    stress = daily.stress_avg if daily else None

    deep_pct = None
    if sleep and sleep.deep_min and sleep.total_sleep_min and sleep.total_sleep_min > 0:
        deep_pct = round(sleep.deep_min / sleep.total_sleep_min * 100)

    bedtime = "--"
    if sleep and sleep.sleep_start:
        bedtime = sleep.sleep_start.strftime("%H:%M")

    return PillarData(
        id="recovery",
        name="P4 Recuperación",
        color="#f5c542",
        collapsed_kpis=[
            PillarKPI(label="HRV", value=_fmt(hrv), unit="ms"),
            PillarKPI(label="Sleep", value=_fmt_duration_min(sleep_min), unit="hrs"),
            PillarKPI(label="RHR", value=_fmt(rhr), unit="bpm"),
        ],
        expanded_kpis=[
            PillarKPI(
                label="Sleep total", value=_fmt_duration_min(sleep_min), unit="hrs",
                target=">7:30", spark=_spark_7d(db, SleepSession, "total_sleep_min", target_date),
            ),
            PillarKPI(
                label="Deep sleep", value=f"{deep_pct}%" if deep_pct else "--", unit="",
                target=">15%",
            ),
            PillarKPI(
                label="HRV baseline", value=_fmt(hrv), unit="ms",
                spark=_spark_7d(db, SleepSession, "avg_hrv", target_date),
            ),
        ],
        drivers=[
            PillarDriver(label="Sleep score", value=_fmt(sleep_score), unit=""),
            PillarDriver(label="Bedtime", value=bedtime, unit=""),
            PillarDriver(label="Body battery", value=_fmt(bb), unit="%"),
            PillarDriver(label="Stress avg", value=_fmt(stress), unit=""),
        ],
    )


def _build_p5_clinical(db: Session) -> PillarData:
    return PillarData(
        id="clinical",
        name="P5 Salud Clínica",
        color="#ff4d4d",
        collapsed_kpis=[
            PillarKPI(label="Screenings", value="✓", unit=""),
            PillarKPI(label="LDL", value="72", unit="mg/dL"),
            PillarKPI(label="Next", value="Ca coronario", unit=""),
        ],
        expanded_kpis=[
            PillarKPI(label="LDL", value="72", unit="mg/dL", target="<70"),
            PillarKPI(label="HDL", value="63", unit="mg/dL", target=">60", status="met"),
            PillarKPI(label="BP", value="--", unit="mmHg", target="<120/80"),
        ],
        drivers=[
            PillarDriver(label="Ca coronario", value="Pending", unit="before Sep 2026"),
            PillarDriver(label="Dermatología", value="Pending", unit="2026"),
        ],
    )


def _get_latest_date(db: Session) -> date:
    latest = db.query(DailySummary).order_by(DailySummary.date.desc()).first()
    return latest.date if latest else date.today()


@router.get("/daily", response_model=PlanDailyResponse)
def get_plan_daily(db: Session = Depends(get_db)):
    target = _get_latest_date(db)

    daily = db.query(DailySummary).filter_by(date=target).first()
    sleep = db.query(SleepSession).filter_by(date=target).first()
    nutrition = db.query(NutritionDaily).filter_by(date=target).first()
    perf = db.query(PerformanceMetric).filter_by(date=target).first()
    body_comp = db.query(BodyComposition).filter_by(date=target).first()

    all_goals = db.query(UserGoal).all()
    goals = {g.metric_key: g for g in all_goals}

    strip = _build_strip(db, target, daily, sleep, nutrition, perf, goals)

    pillars = [
        _build_p1_aerobic(db, target, perf),
        _build_p2_strength(db, target),
        _build_p3_fueling(db, target, nutrition, body_comp),
        _build_p4_recovery(db, target, daily, sleep, perf),
        _build_p5_clinical(db),
    ]

    return PlanDailyResponse(date=target, strip=strip, pillars=pillars)
```

- [ ] **Step 4: Register router in main.py**

Add to `apps/sync/app/main.py`:

```python
from app.routers import plan
```

And:

```python
app.include_router(plan.router)
```

- [ ] **Step 5: Run tests**

Run: `cd apps/sync && uv run pytest tests/test_plan_router.py -v`
Expected: all 3 PASS

- [ ] **Step 6: Run full test suite**

Run: `cd apps/sync && uv run pytest -v`
Expected: all tests PASS

- [ ] **Step 7: Commit**

```bash
git add apps/sync/app/routers/plan.py apps/sync/app/main.py apps/sync/tests/test_plan_router.py
git commit -m "feat(plan): add /api/plan/daily endpoint with strip and pillar data"
```

---

### Task 6: Frontend types and API

**Files:**
- Modify: `apps/web/src/lib/types.ts`
- (No test — types are verified by TypeScript compiler)

- [ ] **Step 1: Add plan types**

Add to `apps/web/src/lib/types.ts`:

```typescript
// ── Plan dashboard types ──

export interface StripMetric {
  label: string;
  value: string;
  secondary_value: string | null;
  unit: string;
  target: string | null;
  pct: number | null;
  trend: string | null;
}

export interface PillarKPI {
  label: string;
  value: string;
  unit: string;
  target: string | null;
  status: string | null;
  spark: number[];
}

export interface PillarDriver {
  label: string;
  value: string;
  unit: string;
}

export interface PillarData {
  id: string;
  name: string;
  color: string;
  collapsed_kpis: PillarKPI[];
  expanded_kpis: PillarKPI[];
  drivers: PillarDriver[];
}

export interface PlanDailyData {
  date: string;
  strip: StripMetric[];
  pillars: PillarData[];
}

export function emptyPlanDailyData(): PlanDailyData {
  return {
    date: new Date().toISOString().split("T")[0],
    strip: [],
    pillars: [],
  };
}
```

- [ ] **Step 2: Verify TypeScript compiles**

Run: `cd apps/web && npx tsc --noEmit`
Expected: no errors

- [ ] **Step 3: Commit**

```bash
git add apps/web/src/lib/types.ts
git commit -m "feat(plan): add TypeScript types for plan daily dashboard"
```

---

### Task 7: Frontend daily-strip component

**Files:**
- Create: `apps/web/src/components/plan/daily-strip.tsx`

- [ ] **Step 1: Create the component**

Create `apps/web/src/components/plan/daily-strip.tsx`:

```tsx
"use client";

import { useEffect, useState } from "react";
import type { StripMetric, PlanDailyData } from "@/lib/types";
import { fetchApi } from "@/lib/api";

function TrendArrow({ trend }: { trend: string | null }) {
  if (!trend || trend === "flat") return null;
  const color = trend === "up" ? "text-green-400" : "text-red-400";
  const arrow = trend === "up" ? "↑" : "↓";
  return <span className={`ml-1 text-xs ${color}`}>{arrow}</span>;
}

function MetricCard({ metric }: { metric: StripMetric }) {
  const hasProgress = metric.pct != null && metric.target;

  return (
    <div className="rounded-xl border border-whoop-border bg-whoop-card p-3 text-center">
      <div className="text-[9px] font-semibold uppercase tracking-wider text-whoop-text-muted">
        {metric.label}
      </div>
      <div className="mt-1.5">
        <span className="text-xl font-extrabold text-whoop-text">{metric.value}</span>
        <TrendArrow trend={metric.trend} />
        {metric.target && (
          <>
            <span className="mx-1 text-xs text-whoop-text-muted">/</span>
            <span className="text-sm text-whoop-text-secondary">{metric.target}</span>
          </>
        )}
      </div>
      <div className="text-[9px] text-whoop-text-muted">{metric.unit}</div>
      {hasProgress && (
        <div className="mx-auto mt-1.5 h-[3px] w-full rounded-full bg-whoop-surface">
          <div
            className="h-[3px] rounded-full bg-whoop-green"
            style={{ width: `${Math.min(metric.pct!, 100)}%` }}
          />
        </div>
      )}
      {metric.secondary_value && (
        <div className="mt-1 text-[9px] text-whoop-text-secondary">
          {metric.secondary_value}
        </div>
      )}
    </div>
  );
}

interface DailyStripProps {
  initialStrip: StripMetric[];
}

export function DailyStrip({ initialStrip }: DailyStripProps) {
  const [strip, setStrip] = useState(initialStrip);

  useEffect(() => {
    const interval = setInterval(async () => {
      try {
        const data = await fetchApi<PlanDailyData>("/api/plan/daily");
        setStrip(data.strip);
      } catch {
        // Keep showing stale data on fetch failure
      }
    }, 60_000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="grid grid-cols-6 gap-2">
      {strip.map((m) => (
        <MetricCard key={m.label} metric={m} />
      ))}
    </div>
  );
}
```

- [ ] **Step 2: Commit**

```bash
git add apps/web/src/components/plan/daily-strip.tsx
git commit -m "feat(plan): add DailyStrip component with 60s polling"
```

---

### Task 8: Frontend pillar-accordion component

**Files:**
- Create: `apps/web/src/components/plan/pillar-row.tsx`
- Create: `apps/web/src/components/plan/pillar-accordion.tsx`
- Create: `apps/web/src/components/plan/sparkline-7d.tsx`

- [ ] **Step 1: Create sparkline component**

Create `apps/web/src/components/plan/sparkline-7d.tsx`:

```tsx
export function Sparkline7d({
  data,
  color,
  width = 100,
  height = 24,
}: {
  data: number[];
  color: string;
  width?: number;
  height?: number;
}) {
  if (data.length < 2) return null;

  const min = Math.min(...data);
  const max = Math.max(...data);
  const range = max - min || 1;
  const padding = 2;

  const points = data
    .map((v, i) => {
      const x = (i / (data.length - 1)) * width;
      const y = padding + (1 - (v - min) / range) * (height - 2 * padding);
      return `${x},${y}`;
    })
    .join(" ");

  return (
    <svg viewBox={`0 0 ${width} ${height}`} style={{ width, height }}>
      <polyline
        points={points}
        fill="none"
        stroke={color}
        strokeWidth="1.5"
        opacity="0.7"
      />
    </svg>
  );
}
```

- [ ] **Step 2: Create pillar-row component**

Create `apps/web/src/components/plan/pillar-row.tsx`:

```tsx
"use client";

import type { PillarData } from "@/lib/types";
import { Sparkline7d } from "./sparkline-7d";

interface PillarRowProps {
  pillar: PillarData;
  expanded: boolean;
  onToggle: () => void;
}

export function PillarRow({ pillar, expanded, onToggle }: PillarRowProps) {
  return (
    <div
      className="overflow-hidden rounded-xl border transition-colors"
      style={{ borderColor: expanded ? pillar.color : "var(--color-whoop-border)" }}
    >
      {/* Collapsed header — always visible */}
      <button
        onClick={onToggle}
        className="flex w-full items-center justify-between px-3.5 py-2.5"
      >
        <div className="flex items-center gap-2.5">
          <div
            className="h-2.5 w-2.5 rounded-full"
            style={{ background: pillar.color }}
          />
          <span
            className="text-[11px] font-bold tracking-widest"
            style={{ color: pillar.color }}
          >
            {pillar.name.toUpperCase()}
          </span>
        </div>
        <div className="flex items-center gap-5">
          <div className="flex gap-4 text-[11px]">
            {pillar.collapsed_kpis.map((kpi) => (
              <span key={kpi.label}>
                <span className="text-whoop-text-muted">{kpi.label}</span>{" "}
                <span className="font-bold text-whoop-text">{kpi.value}</span>
              </span>
            ))}
          </div>
          <span
            className="text-sm transition-transform"
            style={{
              color: expanded ? pillar.color : "var(--color-whoop-text-muted)",
              transform: expanded ? "rotate(90deg)" : "none",
            }}
          >
            ▸
          </span>
        </div>
      </button>

      {/* Expanded content */}
      {expanded && (
        <div className="border-t border-whoop-border px-3.5 pb-3.5">
          {/* KPI cards with sparklines */}
          <div className="mt-3 grid grid-cols-3 gap-2.5">
            {pillar.expanded_kpis.map((kpi) => (
              <div
                key={kpi.label}
                className="rounded-lg bg-whoop-surface p-2.5"
              >
                <div className="text-[9px] uppercase tracking-wider text-whoop-text-muted">
                  {kpi.label}
                </div>
                <div className="mt-1 flex items-baseline gap-1.5">
                  <span className="text-lg font-extrabold text-whoop-text">
                    {kpi.value}
                  </span>
                  {kpi.target && (
                    <span className="text-[10px] text-whoop-text-muted">
                      target {kpi.target}
                    </span>
                  )}
                </div>
                {kpi.spark.length > 1 && (
                  <div className="mt-1.5">
                    <Sparkline7d data={kpi.spark} color={pillar.color} />
                    <div className="text-right text-[8px] text-whoop-text-muted">
                      7d trend
                    </div>
                  </div>
                )}
              </div>
            ))}
          </div>

          {/* Drivers */}
          {pillar.drivers.length > 0 && (
            <div className="mt-2.5 flex gap-2">
              {pillar.drivers.map((d) => (
                <div
                  key={d.label}
                  className="flex flex-1 items-center justify-between rounded-md bg-whoop-surface px-2 py-1.5"
                >
                  <span className="text-[9px] text-whoop-text-muted">
                    {d.label}
                  </span>
                  <span
                    className="text-[11px] font-bold"
                    style={{ color: pillar.color }}
                  >
                    {d.value}
                    {d.unit && (
                      <span className="ml-0.5 text-[8px] text-whoop-text-secondary">
                        {d.unit}
                      </span>
                    )}
                  </span>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
```

- [ ] **Step 3: Create pillar-accordion component**

Create `apps/web/src/components/plan/pillar-accordion.tsx`:

```tsx
"use client";

import { useState } from "react";
import type { PillarData } from "@/lib/types";
import { PillarRow } from "./pillar-row";

interface PillarAccordionProps {
  pillars: PillarData[];
}

export function PillarAccordion({ pillars }: PillarAccordionProps) {
  const [expandedId, setExpandedId] = useState<string | null>(null);

  return (
    <div className="flex flex-col gap-1">
      {pillars.map((p) => (
        <PillarRow
          key={p.id}
          pillar={p}
          expanded={expandedId === p.id}
          onToggle={() =>
            setExpandedId((prev) => (prev === p.id ? null : p.id))
          }
        />
      ))}
    </div>
  );
}
```

- [ ] **Step 4: Commit**

```bash
git add apps/web/src/components/plan/sparkline-7d.tsx apps/web/src/components/plan/pillar-row.tsx apps/web/src/components/plan/pillar-accordion.tsx
git commit -m "feat(plan): add PillarAccordion, PillarRow, and Sparkline7d components"
```

---

### Task 9: Frontend plan page

**Files:**
- Create: `apps/web/src/app/(dashboard)/plan/page.tsx`

- [ ] **Step 1: Create the page**

Create `apps/web/src/app/(dashboard)/plan/page.tsx`:

```tsx
import { DM_Sans } from "next/font/google";
import { fetchApi } from "@/lib/api";
import { emptyPlanDailyData, type PlanDailyData } from "@/lib/types";
import { DailyStrip } from "@/components/plan/daily-strip";
import { PillarAccordion } from "@/components/plan/pillar-accordion";

export const dynamic = "force-dynamic";

const dmSans = DM_Sans({ subsets: ["latin"], variable: "--font-dm-sans" });

export default async function PlanPage() {
  let data: PlanDailyData;
  try {
    data = await fetchApi<PlanDailyData>("/api/plan/daily");
  } catch {
    data = emptyPlanDailyData();
  }

  const today = new Date();
  const dateStr = today.toLocaleDateString("en-US", {
    weekday: "long",
    month: "short",
    day: "numeric",
  });

  return (
    <div className={`${dmSans.variable} min-h-screen bg-whoop-bg text-whoop-text`}>
      {/* Header */}
      <div className="sticky top-0 z-50 flex items-center justify-between border-b border-whoop-border bg-whoop-bg/90 px-6 py-3 backdrop-blur-xl">
        <div>
          <div
            className="text-lg font-extrabold tracking-tight"
            style={{ fontFamily: "'DM Sans', sans-serif" }}
          >
            <span className="text-whoop-green">P</span>LAN ESTRATÉGICO
          </div>
          <div className="text-[11px] tracking-wider text-whoop-text-muted">
            {dateStr.toUpperCase()}
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="mx-auto max-w-[1200px] px-6 py-6 pb-16">
        {/* Top strip */}
        <DailyStrip initialStrip={data.strip} />

        {/* Pillar rows */}
        <div className="mt-6">
          <PillarAccordion pillars={data.pillars} />
        </div>
      </div>
    </div>
  );
}
```

- [ ] **Step 2: Verify build**

Run: `cd apps/web && npx next build`
Expected: build succeeds

- [ ] **Step 3: Commit**

```bash
git add apps/web/src/app/\(dashboard\)/plan/page.tsx
git commit -m "feat(plan): add /plan page with daily strip and pillar accordion"
```

---

### Task 10: Run migration, smoke test, final commit

**Files:**
- No new files

- [ ] **Step 1: Run migration**

Run: `cd apps/sync && uv run alembic upgrade head`
Expected: migration applies successfully, `stress_readings` table created.

- [ ] **Step 2: Run full backend tests**

Run: `cd apps/sync && uv run pytest -v`
Expected: all tests PASS

- [ ] **Step 3: Run frontend build**

Run: `cd apps/web && npx next build`
Expected: build succeeds

- [ ] **Step 4: Run lint**

Run: `cd apps/sync && uv run ruff check . && uv run ruff format --check .`
Expected: no issues

- [ ] **Step 5: Manual smoke test**

Start both services:
```bash
make dev-api   # terminal 1
make dev-web   # terminal 2
```

Visit `http://localhost:3000/plan`. Verify:
- Top strip shows 6 metric cards (values may be "--" if no data)
- 5 pillar rows render with names and colors
- Clicking a pillar expands it (shows KPIs + drivers)
- Clicking another collapses the first
- No console errors

- [ ] **Step 6: Commit any lint fixes if needed**

```bash
git add -A
git commit -m "chore(plan): lint fixes and finalize phase 1"
```

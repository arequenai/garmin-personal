# Aerobico Tab Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a detail page at `/aerobico` for aerobic training data with a PMC chart, training calendar, HR zone distribution, and weekly volume chart.

**Architecture:** New FastAPI router with 4 read-only endpoints querying existing TP/Garmin models. Next.js client page with global date range state, 4 data-fetching hooks, and 4 chart components (2 using Lightweight Charts, 1 custom calendar, 1 pure CSS). Sidebar restored for two-tab navigation.

**Tech Stack:** Python/FastAPI (backend), Next.js 16/React 19/TypeScript (frontend), Lightweight Charts (TradingView), Tailwind v4, Lucide icons.

---

## File Structure

### Backend (apps/sync/)

| File | Action | Responsibility |
|------|--------|----------------|
| `app/schemas/aerobico.py` | Create | Pydantic response models for all 4 endpoints |
| `app/routers/aerobico.py` | Create | 4 GET endpoints: pmc, calendar, volume, hr-zones |
| `app/main.py` | Modify | Register aerobico router |
| `tests/test_aerobico_router.py` | Create | Integration tests for all 4 endpoints |

### Frontend (apps/web/)

| File | Action | Responsibility |
|------|--------|----------------|
| `src/lib/types.ts` | Modify | Add aerobico TypeScript interfaces |
| `src/lib/hooks/use-aerobic-pmc.ts` | Create | Fetch hook for PMC data |
| `src/lib/hooks/use-aerobic-volume.ts` | Create | Fetch hook for weekly volume |
| `src/lib/hooks/use-aerobic-hr-zones.ts` | Create | Fetch hook for HR zone data |
| `src/lib/hooks/use-aerobic-calendar.ts` | Create | Fetch hook for calendar data |
| `src/components/aerobico/pmc-chart.tsx` | Create | Lightweight Charts PMC visualization |
| `src/components/aerobico/training-calendar.tsx` | Create | Custom month grid calendar |
| `src/components/aerobico/hr-zone-chart.tsx` | Create | CSS horizontal stacked bar |
| `src/components/aerobico/weekly-volume-chart.tsx` | Create | Lightweight Charts combo chart |
| `src/components/aerobico/aerobico-page.tsx` | Create | Client wrapper with date state + layout |
| `src/app/(dashboard)/aerobico/page.tsx` | Create | Server component shell |
| `src/components/layout/sidebar.tsx` | Create | Restored sidebar with 2 nav items |
| `src/components/layout/app-layout.tsx` | Modify | Re-add sidebar to layout |
| `src/components/plan/pillar-row.tsx` | Modify | Add link to /aerobico on aerobic pillar |
| `package.json` | Modify | Add lightweight-charts and lucide-react |

---

### Task 1: Backend Schemas

**Files:**
- Create: `apps/sync/app/schemas/aerobico.py`

- [ ] **Step 1: Create the schema file**

```python
from datetime import date

from pydantic import BaseModel


class PMCDataPoint(BaseModel):
    date: date
    ctl: float | None
    atl: float | None
    tsb: float | None
    tss_day: float | None

    model_config = {"from_attributes": True}


class CalendarPlannedWorkout(BaseModel):
    date: date
    title: str | None
    workout_type: str | None
    duration_sec_planned: int | None
    tss_planned: float | None
    distance_m_planned: float | None

    model_config = {"from_attributes": True}


class CalendarCompletedWorkout(BaseModel):
    date: date
    title: str | None
    workout_type: str | None
    tss: float | None
    distance_m: float | None
    duration_sec: int | None

    model_config = {"from_attributes": True}


class CalendarResponse(BaseModel):
    planned: list[CalendarPlannedWorkout]
    completed: list[CalendarCompletedWorkout]


class WeeklyVolume(BaseModel):
    week_start: date
    km: float
    elevation_m: float


class HRZonesResponse(BaseModel):
    zone1_sec: int
    zone2_sec: int
    zone3_sec: int
    zone4_sec: int
    zone5_sec: int
```

- [ ] **Step 2: Commit**

```bash
cd apps/sync
git add app/schemas/aerobico.py
git commit -m "feat(api): add Pydantic schemas for aerobico endpoints"
```

---

### Task 2: Backend Router — PMC Endpoint

**Files:**
- Create: `apps/sync/app/routers/aerobico.py`
- Create: `apps/sync/tests/test_aerobico_router.py`
- Modify: `apps/sync/app/main.py`

- [ ] **Step 1: Write the failing test for PMC endpoint**

Create `apps/sync/tests/test_aerobico_router.py`:

```python
from datetime import date, timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app
from app.models.tp_fitness_data import TPFitnessData

engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
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


def test_pmc_returns_fitness_data(client, db):
    db.add(TPFitnessData(date=date(2026, 3, 1), ctl=80.0, atl=65.0, tsb=15.0, tss_day=50.0))
    db.add(TPFitnessData(date=date(2026, 3, 2), ctl=81.0, atl=66.0, tsb=15.0, tss_day=60.0))
    db.commit()

    resp = client.get("/api/aerobico/pmc?from_date=2026-03-01&to_date=2026-03-02")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 2
    assert data[0]["date"] == "2026-03-01"
    assert data[0]["ctl"] == 80.0
    assert data[1]["date"] == "2026-03-02"


def test_pmc_default_range(client, db):
    db.add(TPFitnessData(date=date.today(), ctl=80.0, atl=65.0, tsb=15.0, tss_day=50.0))
    db.commit()

    resp = client.get("/api/aerobico/pmc")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1


def test_pmc_empty(client, db):
    resp = client.get("/api/aerobico/pmc?from_date=2026-01-01&to_date=2026-01-31")
    assert resp.status_code == 200
    assert resp.json() == []
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd apps/sync && uv run pytest tests/test_aerobico_router.py::test_pmc_returns_fitness_data -v`
Expected: FAIL (404 — route not registered yet)

- [ ] **Step 3: Create the router with PMC endpoint**

Create `apps/sync/app/routers/aerobico.py`:

```python
from datetime import date, timedelta

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.constants import RUNNING_TYPES
from app.database import get_db
from app.models.activity import Activity
from app.models.tp_completed_workout import TPCompletedWorkout
from app.models.tp_fitness_data import TPFitnessData
from app.models.tp_planned_workout import TPPlannedWorkout
from app.schemas.aerobico import (
    CalendarCompletedWorkout,
    CalendarPlannedWorkout,
    CalendarResponse,
    HRZonesResponse,
    PMCDataPoint,
    WeeklyVolume,
)

router = APIRouter(prefix="/api/aerobico", tags=["aerobico"])


@router.get("/pmc", response_model=list[PMCDataPoint])
def get_pmc(
    from_date: date = Query(default_factory=lambda: date.today() - timedelta(days=365)),
    to_date: date = Query(default_factory=lambda: date.today()),
    db: Session = Depends(get_db),
):
    return (
        db.query(TPFitnessData)
        .filter(TPFitnessData.date >= from_date, TPFitnessData.date <= to_date)
        .order_by(TPFitnessData.date)
        .all()
    )
```

- [ ] **Step 4: Register the router in main.py**

In `apps/sync/app/main.py`, add the import and include:

Add to imports:
```python
from app.routers import (
    ...existing imports...,
    aerobico,
)
```

Add after the last `include_router` call:
```python
app.include_router(aerobico.router)
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `cd apps/sync && uv run pytest tests/test_aerobico_router.py -v`
Expected: 3 tests PASS

- [ ] **Step 6: Commit**

```bash
git add apps/sync/app/routers/aerobico.py apps/sync/app/main.py tests/test_aerobico_router.py
git commit -m "feat(api): add /api/aerobico/pmc endpoint"
```

---

### Task 3: Backend Router — Calendar Endpoint

**Files:**
- Modify: `apps/sync/app/routers/aerobico.py`
- Modify: `apps/sync/tests/test_aerobico_router.py`

- [ ] **Step 1: Write failing tests**

Add to `apps/sync/tests/test_aerobico_router.py`:

```python
from app.models.tp_completed_workout import TPCompletedWorkout
from app.models.tp_planned_workout import TPPlannedWorkout


def test_calendar_returns_planned_and_completed(client, db):
    db.add(TPPlannedWorkout(
        tp_workout_id="plan-1", date=date(2026, 4, 10),
        title="Easy Run", workout_type="run",
        duration_sec_planned=3600, tss_planned=50, distance_m_planned=10000,
    ))
    db.add(TPCompletedWorkout(
        tp_workout_id="done-1", date=date(2026, 4, 3),
        title="Intervals", workout_type="run",
        tss=85, distance_m=12000, duration_sec=4200,
    ))
    db.commit()

    resp = client.get("/api/aerobico/calendar?from_date=2026-04-01&to_date=2026-04-15")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["planned"]) == 1
    assert data["planned"][0]["title"] == "Easy Run"
    assert len(data["completed"]) == 1
    assert data["completed"][0]["title"] == "Intervals"


def test_calendar_empty(client, db):
    resp = client.get("/api/aerobico/calendar?from_date=2026-01-01&to_date=2026-01-31")
    assert resp.status_code == 200
    data = resp.json()
    assert data["planned"] == []
    assert data["completed"] == []
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd apps/sync && uv run pytest tests/test_aerobico_router.py::test_calendar_returns_planned_and_completed -v`
Expected: FAIL (404 — endpoint doesn't exist yet)

- [ ] **Step 3: Add calendar endpoint to router**

Append to `apps/sync/app/routers/aerobico.py`:

```python
@router.get("/calendar", response_model=CalendarResponse)
def get_calendar(
    from_date: date = Query(default_factory=lambda: date.today() - timedelta(days=30)),
    to_date: date = Query(default_factory=lambda: date.today() + timedelta(days=30)),
    db: Session = Depends(get_db),
):
    planned = (
        db.query(TPPlannedWorkout)
        .filter(TPPlannedWorkout.date >= from_date, TPPlannedWorkout.date <= to_date)
        .order_by(TPPlannedWorkout.date)
        .all()
    )
    completed = (
        db.query(TPCompletedWorkout)
        .filter(TPCompletedWorkout.date >= from_date, TPCompletedWorkout.date <= to_date)
        .order_by(TPCompletedWorkout.date)
        .all()
    )
    return CalendarResponse(planned=planned, completed=completed)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd apps/sync && uv run pytest tests/test_aerobico_router.py -v`
Expected: 5 tests PASS

- [ ] **Step 5: Commit**

```bash
git add apps/sync/app/routers/aerobico.py apps/sync/tests/test_aerobico_router.py
git commit -m "feat(api): add /api/aerobico/calendar endpoint"
```

---

### Task 4: Backend Router �� Volume Endpoint

**Files:**
- Modify: `apps/sync/app/routers/aerobico.py`
- Modify: `apps/sync/tests/test_aerobico_router.py`

- [ ] **Step 1: Write failing tests**

Add to `apps/sync/tests/test_aerobico_router.py`:

```python
from app.models.activity import Activity


def test_volume_aggregates_by_week(client, db):
    # Two runs in the same ISO week (Mon 2026-03-30 to Sun 2026-04-05)
    db.add(Activity(
        garmin_id="r1", date=date(2026, 3, 30), type="running",
        distance_m=10000, elevation_gain=100,
    ))
    db.add(Activity(
        garmin_id="r2", date=date(2026, 4, 1), type="trail_running",
        distance_m=15000, elevation_gain=250,
    ))
    # Non-running activity — should be excluded
    db.add(Activity(
        garmin_id="s1", date=date(2026, 4, 1), type="strength_training",
        distance_m=0, elevation_gain=0,
    ))
    db.commit()

    resp = client.get("/api/aerobico/volume?from_date=2026-03-30&to_date=2026-04-05")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]["km"] == 25.0
    assert data[0]["elevation_m"] == 350.0


def test_volume_empty(client, db):
    resp = client.get("/api/aerobico/volume?from_date=2026-01-01&to_date=2026-01-31")
    assert resp.status_code == 200
    assert resp.json() == []
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd apps/sync && uv run pytest tests/test_aerobico_router.py::test_volume_aggregates_by_week -v`
Expected: FAIL (404)

- [ ] **Step 3: Add volume endpoint to router**

Append to `apps/sync/app/routers/aerobico.py`:

```python
@router.get("/volume", response_model=list[WeeklyVolume])
def get_volume(
    from_date: date = Query(default_factory=lambda: date.today() - timedelta(weeks=12)),
    to_date: date = Query(default_factory=lambda: date.today()),
    db: Session = Depends(get_db),
):
    activities = (
        db.query(Activity)
        .filter(
            Activity.date >= from_date,
            Activity.date <= to_date,
            Activity.type.in_(RUNNING_TYPES),
        )
        .all()
    )

    weeks: dict[date, dict] = {}
    for a in activities:
        # ISO week: Monday as start
        week_start = a.date - timedelta(days=a.date.weekday())
        if week_start not in weeks:
            weeks[week_start] = {"km": 0.0, "elevation_m": 0.0}
        weeks[week_start]["km"] += round((a.distance_m or 0) / 1000, 2)
        weeks[week_start]["elevation_m"] += float(a.elevation_gain or 0)

    result = [
        WeeklyVolume(
            week_start=ws,
            km=round(vals["km"], 1),
            elevation_m=round(vals["elevation_m"], 0),
        )
        for ws, vals in sorted(weeks.items())
    ]
    return result
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd apps/sync && uv run pytest tests/test_aerobico_router.py -v`
Expected: 7 tests PASS

- [ ] **Step 5: Commit**

```bash
git add apps/sync/app/routers/aerobico.py apps/sync/tests/test_aerobico_router.py
git commit -m "feat(api): add /api/aerobico/volume endpoint"
```

---

### Task 5: Backend Router — HR Zones Endpoint

**Files:**
- Modify: `apps/sync/app/routers/aerobico.py`
- Modify: `apps/sync/tests/test_aerobico_router.py`

- [ ] **Step 1: Write failing tests**

Add to `apps/sync/tests/test_aerobico_router.py`:

```python
def test_hr_zones_sums_across_workouts(client, db):
    db.add(TPCompletedWorkout(
        tp_workout_id="w1", date=date(2026, 4, 1), workout_type="run",
        hr_zone1_sec=600, hr_zone2_sec=1800, hr_zone3_sec=900,
        hr_zone4_sec=300, hr_zone5_sec=60,
    ))
    db.add(TPCompletedWorkout(
        tp_workout_id="w2", date=date(2026, 4, 3), workout_type="run",
        hr_zone1_sec=400, hr_zone2_sec=1200, hr_zone3_sec=600,
        hr_zone4_sec=200, hr_zone5_sec=40,
    ))
    db.commit()

    resp = client.get("/api/aerobico/hr-zones?from_date=2026-04-01&to_date=2026-04-05")
    assert resp.status_code == 200
    data = resp.json()
    assert data["zone1_sec"] == 1000
    assert data["zone2_sec"] == 3000
    assert data["zone3_sec"] == 1500
    assert data["zone4_sec"] == 500
    assert data["zone5_sec"] == 100


def test_hr_zones_empty(client, db):
    resp = client.get("/api/aerobico/hr-zones?from_date=2026-01-01&to_date=2026-01-31")
    assert resp.status_code == 200
    data = resp.json()
    assert data["zone1_sec"] == 0
    assert data["zone2_sec"] == 0


def test_hr_zones_handles_null_values(client, db):
    db.add(TPCompletedWorkout(
        tp_workout_id="w3", date=date(2026, 4, 1), workout_type="run",
        hr_zone1_sec=600, hr_zone2_sec=None, hr_zone3_sec=900,
        hr_zone4_sec=None, hr_zone5_sec=None,
    ))
    db.commit()

    resp = client.get("/api/aerobico/hr-zones?from_date=2026-04-01&to_date=2026-04-05")
    assert resp.status_code == 200
    data = resp.json()
    assert data["zone1_sec"] == 600
    assert data["zone2_sec"] == 0
    assert data["zone3_sec"] == 900
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd apps/sync && uv run pytest tests/test_aerobico_router.py::test_hr_zones_sums_across_workouts -v`
Expected: FAIL (404)

- [ ] **Step 3: Add HR zones endpoint to router**

Append to `apps/sync/app/routers/aerobico.py`:

```python
@router.get("/hr-zones", response_model=HRZonesResponse)
def get_hr_zones(
    from_date: date = Query(default_factory=lambda: date.today() - timedelta(weeks=4)),
    to_date: date = Query(default_factory=lambda: date.today()),
    db: Session = Depends(get_db),
):
    workouts = (
        db.query(TPCompletedWorkout)
        .filter(TPCompletedWorkout.date >= from_date, TPCompletedWorkout.date <= to_date)
        .all()
    )

    totals = {f"zone{i}_sec": 0 for i in range(1, 6)}
    for w in workouts:
        for i in range(1, 6):
            totals[f"zone{i}_sec"] += getattr(w, f"hr_zone{i}_sec", None) or 0

    return HRZonesResponse(**totals)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd apps/sync && uv run pytest tests/test_aerobico_router.py -v`
Expected: 10 tests PASS

- [ ] **Step 5: Commit**

```bash
git add apps/sync/app/routers/aerobico.py apps/sync/tests/test_aerobico_router.py
git commit -m "feat(api): add /api/aerobico/hr-zones endpoint"
```

---

### Task 6: Frontend Dependencies & Types

**Files:**
- Modify: `apps/web/package.json`
- Modify: `apps/web/src/lib/types.ts`

- [ ] **Step 1: Install dependencies**

```bash
cd apps/web && pnpm add lightweight-charts lucide-react
```

- [ ] **Step 2: Add TypeScript interfaces**

Append to `apps/web/src/lib/types.ts`:

```typescript
// ── Aerobico tab types ──

export interface PMCDataPoint {
  date: string;
  ctl: number | null;
  atl: number | null;
  tsb: number | null;
  tss_day: number | null;
}

export interface CalendarPlannedWorkout {
  date: string;
  title: string | null;
  workout_type: string | null;
  duration_sec_planned: number | null;
  tss_planned: number | null;
  distance_m_planned: number | null;
}

export interface CalendarCompletedWorkout {
  date: string;
  title: string | null;
  workout_type: string | null;
  tss: number | null;
  distance_m: number | null;
  duration_sec: number | null;
}

export interface CalendarData {
  planned: CalendarPlannedWorkout[];
  completed: CalendarCompletedWorkout[];
}

export interface WeeklyVolume {
  week_start: string;
  km: number;
  elevation_m: number;
}

export interface HRZonesData {
  zone1_sec: number;
  zone2_sec: number;
  zone3_sec: number;
  zone4_sec: number;
  zone5_sec: number;
}
```

- [ ] **Step 3: Commit**

```bash
git add apps/web/package.json apps/web/pnpm-lock.yaml apps/web/src/lib/types.ts
git commit -m "feat(web): add aerobico types and chart dependencies"
```

---

### Task 7: Frontend Data Hooks

**Files:**
- Create: `apps/web/src/lib/hooks/use-aerobic-pmc.ts`
- Create: `apps/web/src/lib/hooks/use-aerobic-volume.ts`
- Create: `apps/web/src/lib/hooks/use-aerobic-hr-zones.ts`
- Create: `apps/web/src/lib/hooks/use-aerobic-calendar.ts`

- [ ] **Step 1: Create the PMC hook**

Create `apps/web/src/lib/hooks/use-aerobic-pmc.ts`:

```typescript
"use client";

import { useEffect, useState } from "react";
import { fetchApi } from "@/lib/api";
import type { PMCDataPoint } from "@/lib/types";

export function useAerobicPMC(from: string, to: string) {
  const [data, setData] = useState<PMCDataPoint[] | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError(null);

    fetchApi<PMCDataPoint[]>(`/api/aerobico/pmc?from_date=${from}&to_date=${to}`)
      .then((result) => {
        if (!cancelled) setData(result);
      })
      .catch((err) => {
        if (!cancelled) setError(err.message);
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });

    return () => { cancelled = true; };
  }, [from, to]);

  return { data, loading, error };
}
```

- [ ] **Step 2: Create the volume hook**

Create `apps/web/src/lib/hooks/use-aerobic-volume.ts`:

```typescript
"use client";

import { useEffect, useState } from "react";
import { fetchApi } from "@/lib/api";
import type { WeeklyVolume } from "@/lib/types";

export function useAerobicVolume(from: string, to: string) {
  const [data, setData] = useState<WeeklyVolume[] | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError(null);

    fetchApi<WeeklyVolume[]>(`/api/aerobico/volume?from_date=${from}&to_date=${to}`)
      .then((result) => {
        if (!cancelled) setData(result);
      })
      .catch((err) => {
        if (!cancelled) setError(err.message);
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });

    return () => { cancelled = true; };
  }, [from, to]);

  return { data, loading, error };
}
```

- [ ] **Step 3: Create the HR zones hook**

Create `apps/web/src/lib/hooks/use-aerobic-hr-zones.ts`:

```typescript
"use client";

import { useEffect, useState } from "react";
import { fetchApi } from "@/lib/api";
import type { HRZonesData } from "@/lib/types";

export function useAerobicHRZones(from: string, to: string) {
  const [data, setData] = useState<HRZonesData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    // Always use last 4 weeks of the range
    const toDate = new Date(to);
    const fourWeeksBack = new Date(toDate);
    fourWeeksBack.setDate(fourWeeksBack.getDate() - 28);
    const effectiveFrom = fourWeeksBack.toISOString().split("T")[0];

    let cancelled = false;
    setLoading(true);
    setError(null);

    fetchApi<HRZonesData>(`/api/aerobico/hr-zones?from_date=${effectiveFrom}&to_date=${to}`)
      .then((result) => {
        if (!cancelled) setData(result);
      })
      .catch((err) => {
        if (!cancelled) setError(err.message);
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });

    return () => { cancelled = true; };
  }, [from, to]);

  return { data, loading, error };
}
```

- [ ] **Step 4: Create the calendar hook**

Create `apps/web/src/lib/hooks/use-aerobic-calendar.ts`:

```typescript
"use client";

import { useEffect, useState } from "react";
import { fetchApi } from "@/lib/api";
import type { CalendarData } from "@/lib/types";

export function useAerobicCalendar(from: string, to: string) {
  const [data, setData] = useState<CalendarData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError(null);

    fetchApi<CalendarData>(`/api/aerobico/calendar?from_date=${from}&to_date=${to}`)
      .then((result) => {
        if (!cancelled) setData(result);
      })
      .catch((err) => {
        if (!cancelled) setError(err.message);
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });

    return () => { cancelled = true; };
  }, [from, to]);

  return { data, loading, error };
}
```

- [ ] **Step 5: Commit**

```bash
git add apps/web/src/lib/hooks/
git commit -m "feat(web): add data-fetching hooks for aerobico tab"
```

---

### Task 8: PMC Chart Component

**Files:**
- Create: `apps/web/src/components/aerobico/pmc-chart.tsx`

- [ ] **Step 1: Create the PMC chart**

Create `apps/web/src/components/aerobico/pmc-chart.tsx`:

```tsx
"use client";

import { useEffect, useRef } from "react";
import {
  createChart,
  type IChartApi,
  type ISeriesApi,
  LineStyle,
  ColorType,
} from "lightweight-charts";
import type { PMCDataPoint } from "@/lib/types";

interface PMCChartProps {
  data: PMCDataPoint[];
}

export function PMCChart({ data }: PMCChartProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const chartRef = useRef<IChartApi | null>(null);

  useEffect(() => {
    if (!containerRef.current) return;

    const chart = createChart(containerRef.current, {
      width: containerRef.current.clientWidth,
      height: 350,
      layout: {
        background: { type: ColorType.Solid, color: "#1a1a1a" },
        textColor: "#888888",
      },
      grid: {
        vertLines: { color: "#2a2a2a" },
        horzLines: { color: "#2a2a2a" },
      },
      crosshair: { mode: 0 },
      rightPriceScale: { borderColor: "#2a2a2a" },
      timeScale: { borderColor: "#2a2a2a" },
    });
    chartRef.current = chart;

    // CTL line (blue)
    const ctlSeries = chart.addLineSeries({
      color: "#4da6ff",
      lineWidth: 2,
      title: "CTL",
    });
    ctlSeries.setData(
      data
        .filter((d) => d.ctl != null)
        .map((d) => ({ time: d.date, value: d.ctl! })),
    );

    // ATL line (orange)
    const atlSeries = chart.addLineSeries({
      color: "#f97316",
      lineWidth: 2,
      title: "ATL",
    });
    atlSeries.setData(
      data
        .filter((d) => d.atl != null)
        .map((d) => ({ time: d.date, value: d.atl! })),
    );

    // TSB baseline area (green above 0, red below)
    const tsbSeries = chart.addBaselineSeries({
      baseValue: { type: "price", price: 0 },
      topLineColor: "#00d68f",
      topFillColor1: "rgba(0, 214, 143, 0.2)",
      topFillColor2: "rgba(0, 214, 143, 0.0)",
      bottomLineColor: "#ef4444",
      bottomFillColor1: "rgba(239, 68, 68, 0.0)",
      bottomFillColor2: "rgba(239, 68, 68, 0.2)",
      lineWidth: 2,
      title: "TSB",
    });
    tsbSeries.setData(
      data
        .filter((d) => d.tsb != null)
        .map((d) => ({ time: d.date, value: d.tsb! })),
    );

    chart.timeScale().fitContent();

    const handleResize = () => {
      if (containerRef.current) {
        chart.applyOptions({ width: containerRef.current.clientWidth });
      }
    };
    window.addEventListener("resize", handleResize);

    return () => {
      window.removeEventListener("resize", handleResize);
      chart.remove();
    };
  }, [data]);

  return (
    <div className="rounded-xl border border-whoop-border bg-whoop-card p-4">
      <h2 className="mb-3 text-sm font-semibold text-whoop-text">
        Performance Management Chart
      </h2>
      <div ref={containerRef} />
    </div>
  );
}
```

- [ ] **Step 2: Verify it compiles**

Run: `cd apps/web && npx next build 2>&1 | tail -5`
Expected: Build should compile (page not wired yet, but component itself should have no TS errors)

- [ ] **Step 3: Commit**

```bash
git add apps/web/src/components/aerobico/pmc-chart.tsx
git commit -m "feat(web): add PMC chart component using Lightweight Charts"
```

---

### Task 9: Training Calendar Component

**Files:**
- Create: `apps/web/src/components/aerobico/training-calendar.tsx`

- [ ] **Step 1: Create the training calendar**

Create `apps/web/src/components/aerobico/training-calendar.tsx`:

```tsx
"use client";

import { useState } from "react";
import { ChevronLeft, ChevronRight } from "lucide-react";
import type { CalendarData, CalendarPlannedWorkout, CalendarCompletedWorkout } from "@/lib/types";
import { useAerobicCalendar } from "@/lib/hooks/use-aerobic-calendar";

const DAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"];

const WORKOUT_COLORS: Record<string, string> = {
  run: "#00d68f",
  bike: "#4da6ff",
  swim: "#00c4b4",
};
const DEFAULT_COLOR = "#6b7280";

function getColor(type: string | null): string {
  if (!type) return DEFAULT_COLOR;
  const key = type.toLowerCase();
  for (const [k, v] of Object.entries(WORKOUT_COLORS)) {
    if (key.includes(k)) return v;
  }
  return DEFAULT_COLOR;
}

function formatDuration(sec: number | null): string {
  if (!sec) return "--";
  const h = Math.floor(sec / 3600);
  const m = Math.floor((sec % 3600) / 60);
  return h > 0 ? `${h}h${m}m` : `${m}m`;
}

function formatKm(meters: number | null): string {
  if (!meters) return "--";
  return `${(meters / 1000).toFixed(1)}km`;
}

interface DayPopoverProps {
  planned: CalendarPlannedWorkout[];
  completed: CalendarCompletedWorkout[];
}

function DayPopover({ planned, completed }: DayPopoverProps) {
  return (
    <div className="absolute left-1/2 top-full z-50 mt-1 -translate-x-1/2 rounded-lg border border-whoop-border bg-whoop-card p-2.5 shadow-lg"
         style={{ minWidth: "180px" }}>
      {completed.map((w, i) => (
        <div key={`c-${i}`} className="mb-1.5 last:mb-0">
          <div className="flex items-center gap-1.5">
            <div className="h-2 w-2 rounded-full" style={{ background: getColor(w.workout_type) }} />
            <span className="text-xs font-medium text-whoop-text">{w.title || "Workout"}</span>
          </div>
          <div className="ml-3.5 text-[10px] text-whoop-text-muted">
            TSS {w.tss ?? "--"} · {formatKm(w.distance_m)} · {formatDuration(w.duration_sec)}
          </div>
        </div>
      ))}
      {planned.map((w, i) => (
        <div key={`p-${i}`} className="mb-1.5 last:mb-0 opacity-60">
          <div className="flex items-center gap-1.5">
            <div className="h-2 w-2 rounded-full border border-dashed"
                 style={{ borderColor: getColor(w.workout_type) }} />
            <span className="text-xs font-medium text-whoop-text">{w.title || "Planned"}</span>
          </div>
          <div className="ml-3.5 text-[10px] text-whoop-text-muted">
            TSS {w.tss_planned ?? "--"} · {formatKm(w.distance_m_planned)} · {formatDuration(w.duration_sec_planned)}
          </div>
        </div>
      ))}
    </div>
  );
}

export function TrainingCalendar() {
  const [viewDate, setViewDate] = useState(() => new Date());
  const [selectedDay, setSelectedDay] = useState<string | null>(null);

  // Fetch 2 months around the view date
  const from = new Date(viewDate.getFullYear(), viewDate.getMonth(), 1);
  const to = new Date(viewDate.getFullYear(), viewDate.getMonth() + 1, 0);
  const fromStr = from.toISOString().split("T")[0];
  const toStr = to.toISOString().split("T")[0];

  const { data, loading } = useAerobicCalendar(fromStr, toStr);

  const year = viewDate.getFullYear();
  const month = viewDate.getMonth();
  const firstDay = new Date(year, month, 1);
  // Monday-based: 0=Mon, 6=Sun
  const startOffset = (firstDay.getDay() + 6) % 7;
  const daysInMonth = new Date(year, month + 1, 0).getDate();
  const todayStr = new Date().toISOString().split("T")[0];

  const prevMonth = () => setViewDate(new Date(year, month - 1, 1));
  const nextMonth = () => setViewDate(new Date(year, month + 1, 1));

  // Index workouts by date string
  const plannedByDate: Record<string, CalendarPlannedWorkout[]> = {};
  const completedByDate: Record<string, CalendarCompletedWorkout[]> = {};
  if (data) {
    for (const w of data.planned) {
      (plannedByDate[w.date] ??= []).push(w);
    }
    for (const w of data.completed) {
      (completedByDate[w.date] ??= []).push(w);
    }
  }

  const monthLabel = firstDay.toLocaleDateString("en-US", { month: "long", year: "numeric" });

  return (
    <div className="rounded-xl border border-whoop-border bg-whoop-card p-4">
      {/* Header */}
      <div className="mb-3 flex items-center justify-between">
        <h2 className="text-sm font-semibold text-whoop-text">Training Calendar</h2>
        <div className="flex items-center gap-2">
          <button onClick={prevMonth} className="rounded p-1 text-whoop-text-muted hover:bg-whoop-surface">
            <ChevronLeft size={16} />
          </button>
          <span className="text-xs font-medium text-whoop-text-secondary" style={{ minWidth: "120px", textAlign: "center" }}>
            {monthLabel}
          </span>
          <button onClick={nextMonth} className="rounded p-1 text-whoop-text-muted hover:bg-whoop-surface">
            <ChevronRight size={16} />
          </button>
        </div>
      </div>

      {loading && <div className="py-8 text-center text-xs text-whoop-text-muted">Loading...</div>}

      {!loading && (
        <>
          {/* Day headers */}
          <div className="grid grid-cols-7 gap-px mb-1">
            {DAYS.map((d) => (
              <div key={d} className="text-center text-[9px] font-medium text-whoop-text-muted py-1">
                {d}
              </div>
            ))}
          </div>

          {/* Day cells */}
          <div className="grid grid-cols-7 gap-px">
            {Array.from({ length: startOffset }).map((_, i) => (
              <div key={`empty-${i}`} className="h-10" />
            ))}
            {Array.from({ length: daysInMonth }).map((_, i) => {
              const day = i + 1;
              const dateStr = `${year}-${String(month + 1).padStart(2, "0")}-${String(day).padStart(2, "0")}`;
              const planned = plannedByDate[dateStr] || [];
              const completed = completedByDate[dateStr] || [];
              const hasWorkout = planned.length > 0 || completed.length > 0;
              const isToday = dateStr === todayStr;
              const isSelected = dateStr === selectedDay;

              return (
                <div
                  key={day}
                  className={`relative flex h-10 cursor-pointer flex-col items-center justify-center rounded-md transition-colors ${
                    isToday ? "bg-whoop-surface" : "hover:bg-whoop-surface/50"
                  }`}
                  onClick={() => setSelectedDay(isSelected ? null : hasWorkout ? dateStr : null)}
                >
                  <span className={`text-[11px] ${isToday ? "font-bold text-whoop-text" : "text-whoop-text-secondary"}`}>
                    {day}
                  </span>
                  {hasWorkout && (
                    <div className="mt-0.5 flex gap-0.5">
                      {completed.length > 0 && (
                        <div className="h-1.5 w-1.5 rounded-full" style={{ background: getColor(completed[0].workout_type) }} />
                      )}
                      {planned.length > 0 && (
                        <div className="h-1.5 w-1.5 rounded-full border" style={{ borderColor: getColor(planned[0].workout_type) }} />
                      )}
                    </div>
                  )}
                  {isSelected && hasWorkout && (
                    <DayPopover planned={planned} completed={completed} />
                  )}
                </div>
              );
            })}
          </div>
        </>
      )}
    </div>
  );
}
```

- [ ] **Step 2: Commit**

```bash
git add apps/web/src/components/aerobico/training-calendar.tsx
git commit -m "feat(web): add training calendar component"
```

---

### Task 10: HR Zone Chart Component

**Files:**
- Create: `apps/web/src/components/aerobico/hr-zone-chart.tsx`

- [ ] **Step 1: Create the HR zone chart**

Create `apps/web/src/components/aerobico/hr-zone-chart.tsx`:

```tsx
"use client";

import type { HRZonesData } from "@/lib/types";

interface HRZoneChartProps {
  data: HRZonesData;
}

const ZONES = [
  { key: "zone1_sec" as const, label: "Z1", color: "#6b7280", name: "Recovery" },
  { key: "zone2_sec" as const, label: "Z2", color: "#4da6ff", name: "Endurance" },
  { key: "zone3_sec" as const, label: "Z3", color: "#00d68f", name: "Tempo" },
  { key: "zone4_sec" as const, label: "Z4", color: "#f97316", name: "Threshold" },
  { key: "zone5_sec" as const, label: "Z5", color: "#ef4444", name: "VO2max" },
];

function formatTime(sec: number): string {
  const h = Math.floor(sec / 3600);
  const m = Math.floor((sec % 3600) / 60);
  return h > 0 ? `${h}h ${m}m` : `${m}m`;
}

export function HRZoneChart({ data }: HRZoneChartProps) {
  const total = ZONES.reduce((sum, z) => sum + data[z.key], 0);

  return (
    <div className="rounded-xl border border-whoop-border bg-whoop-card p-4">
      <h2 className="mb-3 text-sm font-semibold text-whoop-text">
        HR Zone Distribution
        <span className="ml-2 text-xs font-normal text-whoop-text-muted">last 4 weeks</span>
      </h2>

      {total === 0 ? (
        <div className="py-8 text-center text-xs text-whoop-text-muted">No HR zone data</div>
      ) : (
        <>
          {/* Stacked bar */}
          <div className="flex h-8 overflow-hidden rounded-md">
            {ZONES.map((z) => {
              const pct = (data[z.key] / total) * 100;
              if (pct < 0.5) return null;
              return (
                <div
                  key={z.key}
                  className="flex items-center justify-center text-[9px] font-bold text-white transition-all"
                  style={{ width: `${pct}%`, backgroundColor: z.color }}
                >
                  {pct >= 8 && z.label}
                </div>
              );
            })}
          </div>

          {/* Legend */}
          <div className="mt-3 space-y-1.5">
            {ZONES.map((z) => {
              const pct = total > 0 ? (data[z.key] / total) * 100 : 0;
              return (
                <div key={z.key} className="flex items-center justify-between text-xs">
                  <div className="flex items-center gap-2">
                    <div className="h-2.5 w-2.5 rounded-sm" style={{ backgroundColor: z.color }} />
                    <span className="text-whoop-text-secondary">
                      {z.label} — {z.name}
                    </span>
                  </div>
                  <span className="text-whoop-text">
                    {pct.toFixed(0)}% · {formatTime(data[z.key])}
                  </span>
                </div>
              );
            })}
          </div>
        </>
      )}
    </div>
  );
}
```

- [ ] **Step 2: Commit**

```bash
git add apps/web/src/components/aerobico/hr-zone-chart.tsx
git commit -m "feat(web): add HR zone distribution chart component"
```

---

### Task 11: Weekly Volume Chart Component

**Files:**
- Create: `apps/web/src/components/aerobico/weekly-volume-chart.tsx`

- [ ] **Step 1: Create the weekly volume chart**

Create `apps/web/src/components/aerobico/weekly-volume-chart.tsx`:

```tsx
"use client";

import { useEffect, useRef } from "react";
import {
  createChart,
  type IChartApi,
  ColorType,
} from "lightweight-charts";
import type { WeeklyVolume } from "@/lib/types";

interface WeeklyVolumeChartProps {
  data: WeeklyVolume[];
}

export function WeeklyVolumeChart({ data }: WeeklyVolumeChartProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const chartRef = useRef<IChartApi | null>(null);

  useEffect(() => {
    if (!containerRef.current || data.length === 0) return;

    const chart = createChart(containerRef.current, {
      width: containerRef.current.clientWidth,
      height: 250,
      layout: {
        background: { type: ColorType.Solid, color: "#1a1a1a" },
        textColor: "#888888",
      },
      grid: {
        vertLines: { color: "#2a2a2a" },
        horzLines: { color: "#2a2a2a" },
      },
      crosshair: { mode: 0 },
      rightPriceScale: {
        borderColor: "#2a2a2a",
        visible: true,
      },
      leftPriceScale: {
        borderColor: "#2a2a2a",
        visible: true,
      },
      timeScale: { borderColor: "#2a2a2a" },
    });
    chartRef.current = chart;

    // Km bars (left axis)
    const kmSeries = chart.addHistogramSeries({
      color: "#4da6ff",
      priceScaleId: "left",
      title: "km",
    });
    kmSeries.setData(
      data.map((d) => ({ time: d.week_start, value: d.km })),
    );

    // Elevation line (right axis)
    const elevSeries = chart.addLineSeries({
      color: "#f97316",
      lineWidth: 2,
      priceScaleId: "right",
      title: "elevation (m)",
    });
    elevSeries.setData(
      data.map((d) => ({ time: d.week_start, value: d.elevation_m })),
    );

    chart.timeScale().fitContent();

    const handleResize = () => {
      if (containerRef.current) {
        chart.applyOptions({ width: containerRef.current.clientWidth });
      }
    };
    window.addEventListener("resize", handleResize);

    return () => {
      window.removeEventListener("resize", handleResize);
      chart.remove();
    };
  }, [data]);

  return (
    <div className="rounded-xl border border-whoop-border bg-whoop-card p-4">
      <h2 className="mb-3 text-sm font-semibold text-whoop-text">
        Weekly Volume
        <span className="ml-2 text-xs font-normal text-whoop-text-muted">
          km (blue) · elevation (orange)
        </span>
      </h2>
      {data.length === 0 ? (
        <div className="py-8 text-center text-xs text-whoop-text-muted">No volume data</div>
      ) : (
        <div ref={containerRef} />
      )}
    </div>
  );
}
```

- [ ] **Step 2: Commit**

```bash
git add apps/web/src/components/aerobico/weekly-volume-chart.tsx
git commit -m "feat(web): add weekly volume chart component"
```

---

### Task 12: Aerobico Page Client Wrapper

**Files:**
- Create: `apps/web/src/components/aerobico/aerobico-page.tsx`
- Create: `apps/web/src/app/(dashboard)/aerobico/page.tsx`

- [ ] **Step 1: Create the client wrapper**

Create `apps/web/src/components/aerobico/aerobico-page.tsx`:

```tsx
"use client";

import { useState } from "react";
import Link from "next/link";
import { ArrowLeft } from "lucide-react";
import { useAerobicPMC } from "@/lib/hooks/use-aerobic-pmc";
import { useAerobicVolume } from "@/lib/hooks/use-aerobic-volume";
import { useAerobicHRZones } from "@/lib/hooks/use-aerobic-hr-zones";
import { PMCChart } from "./pmc-chart";
import { TrainingCalendar } from "./training-calendar";
import { HRZoneChart } from "./hr-zone-chart";
import { WeeklyVolumeChart } from "./weekly-volume-chart";

function defaultFrom(monthsBack: number): string {
  const d = new Date();
  d.setMonth(d.getMonth() - monthsBack);
  return d.toISOString().split("T")[0];
}

function today(): string {
  return new Date().toISOString().split("T")[0];
}

const PRESETS = [
  { label: "3M", months: 3 },
  { label: "6M", months: 6 },
  { label: "1Y", months: 12 },
];

function ChartError({ message, onRetry }: { message: string; onRetry: () => void }) {
  return (
    <div className="flex flex-col items-center justify-center py-8">
      <p className="text-xs text-whoop-text-muted">Could not load data</p>
      <button onClick={onRetry} className="mt-2 text-xs text-whoop-blue hover:underline">
        Retry
      </button>
    </div>
  );
}

export function AerobicoPageClient() {
  const [from, setFrom] = useState(() => defaultFrom(12));
  const [to, setTo] = useState(today);
  const [activePreset, setActivePreset] = useState("1Y");

  const pmc = useAerobicPMC(from, to);
  const volume = useAerobicVolume(from, to);
  const hrZones = useAerobicHRZones(from, to);

  const applyPreset = (months: number, label: string) => {
    setFrom(defaultFrom(months));
    setTo(today());
    setActivePreset(label);
  };

  // Force re-fetch by toggling dates
  const retryPmc = () => { setFrom((f) => f); };
  const retryVolume = () => { setFrom((f) => f); };
  const retryHrZones = () => { setFrom((f) => f); };

  return (
    <div className="min-h-screen bg-whoop-bg text-whoop-text">
      <div className="mx-auto max-w-6xl px-3 pt-4 pb-20 sm:px-6 sm:pt-6 sm:pb-16">
        {/* Header bar */}
        <div className="mb-6 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <Link
            href="/"
            className="flex items-center gap-1.5 text-sm text-whoop-text-muted hover:text-whoop-text transition-colors"
          >
            <ArrowLeft size={16} />
            Plan
          </Link>

          {/* Date range controls */}
          <div className="flex items-center gap-2">
            {PRESETS.map((p) => (
              <button
                key={p.label}
                onClick={() => applyPreset(p.months, p.label)}
                className={`rounded-md px-2.5 py-1 text-xs font-medium transition-colors ${
                  activePreset === p.label
                    ? "bg-whoop-surface text-whoop-text"
                    : "text-whoop-text-muted hover:bg-whoop-surface/50"
                }`}
              >
                {p.label}
              </button>
            ))}
            <input
              type="date"
              value={from}
              onChange={(e) => { setFrom(e.target.value); setActivePreset(""); }}
              className="rounded-md border border-whoop-border bg-whoop-surface px-2 py-1 text-xs text-whoop-text"
            />
            <input
              type="date"
              value={to}
              onChange={(e) => { setTo(e.target.value); setActivePreset(""); }}
              className="rounded-md border border-whoop-border bg-whoop-surface px-2 py-1 text-xs text-whoop-text"
            />
          </div>
        </div>

        {/* PMC Chart */}
        {pmc.loading && (
          <div className="rounded-xl border border-whoop-border bg-whoop-card p-4">
            <div className="h-[350px] animate-pulse rounded bg-whoop-surface" />
          </div>
        )}
        {pmc.error && (
          <div className="rounded-xl border border-whoop-border bg-whoop-card p-4">
            <ChartError message={pmc.error} onRetry={retryPmc} />
          </div>
        )}
        {pmc.data && <PMCChart data={pmc.data} />}

        {/* Calendar + HR Zones row */}
        <div className="mt-4 grid gap-4 md:grid-cols-2">
          <TrainingCalendar />

          <div>
            {hrZones.loading && (
              <div className="rounded-xl border border-whoop-border bg-whoop-card p-4">
                <div className="h-[200px] animate-pulse rounded bg-whoop-surface" />
              </div>
            )}
            {hrZones.error && (
              <div className="rounded-xl border border-whoop-border bg-whoop-card p-4">
                <ChartError message={hrZones.error} onRetry={retryHrZones} />
              </div>
            )}
            {hrZones.data && <HRZoneChart data={hrZones.data} />}
          </div>
        </div>

        {/* Weekly Volume */}
        <div className="mt-4">
          {volume.loading && (
            <div className="rounded-xl border border-whoop-border bg-whoop-card p-4">
              <div className="h-[250px] animate-pulse rounded bg-whoop-surface" />
            </div>
          )}
          {volume.error && (
            <div className="rounded-xl border border-whoop-border bg-whoop-card p-4">
              <ChartError message={volume.error} onRetry={retryVolume} />
            </div>
          )}
          {volume.data && <WeeklyVolumeChart data={volume.data} />}
        </div>
      </div>
    </div>
  );
}
```

- [ ] **Step 2: Create the server component page**

Create `apps/web/src/app/(dashboard)/aerobico/page.tsx`:

```tsx
import { AerobicoPageClient } from "@/components/aerobico/aerobico-page";

export const dynamic = "force-dynamic";

export default function AerobicoPage() {
  return <AerobicoPageClient />;
}
```

- [ ] **Step 3: Commit**

```bash
git add apps/web/src/components/aerobico/aerobico-page.tsx apps/web/src/app/\(dashboard\)/aerobico/page.tsx
git commit -m "feat(web): add aerobico page with date range selector and chart layout"
```

---

### Task 13: Restore Sidebar Navigation

**Files:**
- Create: `apps/web/src/components/layout/sidebar.tsx`
- Modify: `apps/web/src/components/layout/app-layout.tsx`

- [ ] **Step 1: Create the sidebar**

Create `apps/web/src/components/layout/sidebar.tsx`:

```tsx
"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { Activity, Target } from "lucide-react";

const navItems = [
  { href: "/", icon: Target, label: "Plan" },
  { href: "/aerobico", icon: Activity, label: "Aeróbico" },
] as const;

export function Sidebar() {
  const pathname = usePathname();

  return (
    <>
      {/* Desktop sidebar */}
      <aside className="bg-bg-card fixed left-0 top-0 z-40 hidden h-screen w-[72px] flex-col items-center py-6 shadow-[1px_0_0_0_rgba(255,255,255,0.04)] md:flex">
        <Link
          href="/"
          className="font-heading mb-8 flex h-10 w-10 items-center justify-center rounded-lg text-sm font-bold tracking-tight text-text-primary"
        >
          GP
        </Link>

        <nav className="flex flex-1 flex-col items-center gap-1">
          {navItems.map(({ href, icon: Icon, label }) => {
            const isActive =
              href === "/" ? pathname === "/" : pathname.startsWith(href);
            return (
              <Link
                key={href}
                href={href}
                className={`group relative flex h-11 w-11 items-center justify-center rounded-lg transition-all duration-200 ${
                  isActive
                    ? "bg-bg-hover text-text-primary"
                    : "text-text-secondary hover:bg-bg-hover/50 hover:text-text-primary"
                }`}
              >
                <Icon size={20} strokeWidth={isActive ? 2 : 1.5} />
                <span className="pointer-events-none absolute left-full ml-3 rounded-md bg-bg-hover px-2.5 py-1.5 text-xs font-medium text-text-primary opacity-0 shadow-lg transition-opacity duration-150 group-hover:opacity-100">
                  {label}
                </span>
              </Link>
            );
          })}
        </nav>
      </aside>

      {/* Mobile bottom nav */}
      <nav className="bg-bg-card fixed bottom-0 left-0 right-0 z-40 flex items-center justify-around border-t border-white/5 pb-[env(safe-area-inset-bottom)] md:hidden">
        {navItems.map(({ href, icon: Icon, label }) => {
          const isActive =
            href === "/" ? pathname === "/" : pathname.startsWith(href);
          return (
            <Link
              key={href}
              href={href}
              className={`flex flex-col items-center gap-0.5 px-2 py-2 ${
                isActive ? "text-text-primary" : "text-text-secondary"
              }`}
            >
              <Icon size={18} strokeWidth={isActive ? 2 : 1.5} />
              <span className="text-[9px] font-medium">{label}</span>
            </Link>
          );
        })}
      </nav>
    </>
  );
}
```

- [ ] **Step 2: Update app-layout to include sidebar**

Replace the contents of `apps/web/src/components/layout/app-layout.tsx`:

```tsx
import { Sidebar } from "./sidebar";

export function AppLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex min-h-screen">
      <Sidebar />
      <main className="flex min-h-screen flex-1 flex-col p-0 md:ml-[72px] md:p-8">
        {children}
      </main>
    </div>
  );
}
```

- [ ] **Step 3: Build to verify**

Run: `cd apps/web && npx next build 2>&1 | tail -10`
Expected: Compiles successfully, shows `/` and `/aerobico` routes

- [ ] **Step 4: Commit**

```bash
git add apps/web/src/components/layout/sidebar.tsx apps/web/src/components/layout/app-layout.tsx
git commit -m "feat(web): restore sidebar with Plan and Aerobico tabs"
```

---

### Task 14: Pillar Row Link to Aerobico

**Files:**
- Modify: `apps/web/src/components/plan/pillar-row.tsx`

- [ ] **Step 1: Add link and chevron to the aerobic pillar row**

In `apps/web/src/components/plan/pillar-row.tsx`, add the import at the top:

```tsx
import Link from "next/link";
import { ChevronRight } from "lucide-react";
```

Then modify the button element inside the component. Replace the opening `<button` tag and its `onClick`:

Find:
```tsx
      <button
        onClick={onToggle}
        className="flex w-full items-center justify-between gap-2 px-3 py-2.5 sm:px-3.5"
      >
```

Replace with:
```tsx
      <button
        onClick={onToggle}
        className="flex w-full items-center justify-between gap-2 px-3 py-2.5 sm:px-3.5"
      >
```

That stays the same. Instead, add a link chevron after the expand arrow inside the button. Find the expand arrow span:

```tsx
          <span
            className="text-sm transition-transform"
            style={{
              color: expanded
                ? pillar.color
                : "var(--color-whoop-text-muted)",
              transform: expanded ? "rotate(90deg)" : "none",
            }}
          >
            &#9656;
          </span>
```

After the closing `</span>`, before the closing `</div>` of the shrink-0 flex container, add:

```tsx
          {pillar.id === "aerobic" && (
            <Link
              href="/aerobico"
              onClick={(e) => e.stopPropagation()}
              className="ml-1 text-whoop-text-muted hover:text-whoop-text transition-colors"
            >
              <ChevronRight size={14} />
            </Link>
          )}
```

- [ ] **Step 2: Build to verify**

Run: `cd apps/web && npx next build 2>&1 | tail -5`
Expected: Compiles successfully

- [ ] **Step 3: Commit**

```bash
git add apps/web/src/components/plan/pillar-row.tsx
git commit -m "feat(web): add link from aerobic pillar row to /aerobico page"
```

---

### Task 15: Final Integration Test

- [ ] **Step 1: Run all backend tests**

Run: `cd apps/sync && uv run pytest tests/ -v`
Expected: All tests pass, including the new `test_aerobico_router.py` tests

- [ ] **Step 2: Run frontend build**

Run: `cd apps/web && npx next build 2>&1 | tail -15`
Expected: Build succeeds, routes shown: `/`, `/aerobico`

- [ ] **Step 3: Run frontend lint**

Run: `cd apps/web && npx eslint src/`
Expected: No errors

- [ ] **Step 4: Final commit if any fixes were needed**

```bash
git add -A
git commit -m "fix: address integration test findings"
```

(Skip this step if no fixes were needed.)

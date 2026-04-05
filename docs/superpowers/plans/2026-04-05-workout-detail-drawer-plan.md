# Workout Detail Drawer Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a click-to-expand detail drawer to the Aerobico tab's Training Calendar showing coach notes, metrics, zone charts, and planned-vs-actual comparison.

**Architecture:** Backend adds a `workout_details_json` column to store full TP workout details, a new endpoint to serve workout detail + matched planned workout, and updates schemas to include `tp_workout_id` in calendar responses. Frontend adds a drawer component below the calendar with sub-components for completed/planned views, a data-fetching hook, and selection state in the calendar.

**Tech Stack:** Python/FastAPI/SQLAlchemy/Alembic (backend), React/TypeScript/Tailwind (frontend), pytest with SQLite in-memory (tests)

---

### Task 1: Database migration — add `workout_details_json` column

**Files:**
- Modify: `apps/sync/app/models/tp_completed_workout.py:40` (add column after `laps_json`)
- Create: `apps/sync/alembic/versions/xxxx_add_workout_details_json.py` (auto-generated)

- [ ] **Step 1: Add column to SQLAlchemy model**

In `apps/sync/app/models/tp_completed_workout.py`, add after line 40 (`laps_json`):

```python
workout_details_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
```

- [ ] **Step 2: Generate Alembic migration**

Run:
```bash
cd apps/sync && uv run alembic revision --autogenerate -m "add workout_details_json to tp_completed_workouts"
```

Expected: Creates a new migration file in `alembic/versions/`.

- [ ] **Step 3: Run the migration**

Run:
```bash
cd apps/sync && uv run alembic upgrade head
```

Expected: Migration applies successfully, column exists.

- [ ] **Step 4: Verify column exists**

Run:
```bash
cd apps/sync && uv run python -c "
from app.database import SessionLocal
from sqlalchemy import text
db = SessionLocal()
r = db.execute(text(\"SELECT column_name FROM information_schema.columns WHERE table_name='tp_completed_workouts' AND column_name='workout_details_json'\")).fetchone()
print('Column exists:', r is not None)
db.close()
"
```

Expected: `Column exists: True`

- [ ] **Step 5: Commit**

```bash
cd apps/sync
git add app/models/tp_completed_workout.py alembic/versions/*workout_details_json*
git commit -m "feat(db): add workout_details_json column to tp_completed_workouts"
```

---

### Task 2: Store workout details during sync

**Files:**
- Modify: `apps/sync/app/services/tp_sync_service.py:127` (add one line in `sync_completed_workouts_range`)

- [ ] **Step 1: Write the failing test**

Add to `apps/sync/tests/test_tp_sync_service.py`:

```python
def test_sync_completed_stores_workout_details_json(mock_tp, db):
    """sync_completed_workouts_range stores the full details response in workout_details_json."""
    mock_tp.get_workouts.return_value = [{
        "workoutId": "9999",
        "workoutDay": "2026-04-01",
        "workoutTypeValueId": 3,
        "totalTime": 1.0,
        "distance": 10000,
        "tssActual": 80,
    }]
    details_payload = {
        "workoutId": 9999,
        "timeInHeartRateZones": {"timeInZones": [{"seconds": 100, "minimum": 93, "maximum": 142, "label": "Z1"}]},
        "timeInSpeedZones": {"timeInZones": [{"seconds": 200, "minimum": 2.0, "maximum": 3.0, "label": "Recovery Run"}]},
        "meanMaxSpeedsByDistance": {"meanMaxes": [{"label": "MM1Kilometer", "value": 3.5}]},
    }
    mock_tp.get_workout_details.return_value = details_payload

    from app.services.tp_sync_service import TPSyncService
    from datetime import date
    svc = TPSyncService(db=db, tp_client=mock_tp)
    svc.sync_completed_workouts_range(date(2026, 4, 1), date(2026, 4, 1))

    from app.models.tp_completed_workout import TPCompletedWorkout
    w = db.query(TPCompletedWorkout).filter(TPCompletedWorkout.tp_workout_id == "9999").first()
    assert w is not None
    assert w.workout_details_json is not None
    assert "timeInHeartRateZones" in w.workout_details_json
    assert "timeInSpeedZones" in w.workout_details_json
```

- [ ] **Step 2: Run test to verify it fails**

Run:
```bash
cd apps/sync && uv run pytest tests/test_tp_sync_service.py::test_sync_completed_stores_workout_details_json -v
```

Expected: FAIL — `workout_details_json` is not being set yet.

- [ ] **Step 3: Add one line to store details**

In `apps/sync/app/services/tp_sync_service.py`, in `sync_completed_workouts_range()`, after line 127 (`values.update(self._extract_zones(details))`), add:

```python
                values["workout_details_json"] = details
```

- [ ] **Step 4: Run test to verify it passes**

Run:
```bash
cd apps/sync && uv run pytest tests/test_tp_sync_service.py::test_sync_completed_stores_workout_details_json -v
```

Expected: PASS

- [ ] **Step 5: Run all existing TP sync tests to check for regressions**

Run:
```bash
cd apps/sync && uv run pytest tests/test_tp_sync_service.py -v
```

Expected: All tests pass.

- [ ] **Step 6: Commit**

```bash
cd apps/sync
git add app/services/tp_sync_service.py tests/test_tp_sync_service.py
git commit -m "feat(sync): store full workout details JSON during TP sync"
```

---

### Task 3: Backfill endpoint for workout_details_json

**Files:**
- Modify: `apps/sync/app/routers/tp.py:166-200` (extend `_run_tp_zones_backfill` to also store `workout_details_json`)

- [ ] **Step 1: Update the zones backfill to also store details JSON**

In `apps/sync/app/routers/tp.py`, in `_run_tp_zones_backfill()`, replace the existing batch loop body (lines 176-199) with logic that also stores the full details. Change the filter to include workouts missing `workout_details_json`:

Replace the filter on line 177-180:
```python
                batch = (
                    tp_sync.db.query(TPCompletedWorkout)
                    .filter(TPCompletedWorkout.hr_zone1_sec == None)  # noqa: E711
                    .limit(BATCH_SIZE)
                    .all()
                )
```

With:
```python
                from sqlalchemy import or_
                batch = (
                    tp_sync.db.query(TPCompletedWorkout)
                    .filter(
                        or_(
                            TPCompletedWorkout.hr_zone1_sec == None,  # noqa: E711
                            TPCompletedWorkout.workout_details_json == None,  # noqa: E711
                        )
                    )
                    .limit(BATCH_SIZE)
                    .all()
                )
```

And in the inner loop (after `for k, v in zones.items(): setattr(w, k, v)`), add:

```python
                    w.workout_details_json = details
```

- [ ] **Step 2: Test manually by checking the backfill finds workouts missing details**

Run:
```bash
cd apps/sync && uv run python -c "
from app.database import SessionLocal
from app.models.tp_completed_workout import TPCompletedWorkout
from sqlalchemy import text
db = SessionLocal()
count = db.execute(text(\"SELECT COUNT(*) FROM tp_completed_workouts WHERE workout_details_json IS NULL\")).scalar()
print(f'Workouts missing details: {count}')
db.close()
"
```

Expected: Shows how many workouts need backfill (should be ~311, all of them).

- [ ] **Step 3: Commit**

```bash
cd apps/sync
git add app/routers/tp.py
git commit -m "feat(sync): extend zones backfill to also store workout_details_json"
```

---

### Task 4: Add `tp_workout_id` to calendar schemas

**Files:**
- Modify: `apps/sync/app/schemas/aerobico.py:16-35` (add field to both schemas)
- Modify: `apps/sync/tests/test_aerobico_router.py` (verify ID is returned)
- Modify: `apps/web/src/lib/types.ts:71-89` (add field to both TS interfaces)

- [ ] **Step 1: Write the failing test**

Add to `apps/sync/tests/test_aerobico_router.py`:

```python
def test_calendar_returns_tp_workout_id(client, db):
    db.add(TPPlannedWorkout(
        tp_workout_id="plan-99", date=date(2026, 4, 10),
        title="Easy Run", workout_type="run",
        duration_sec_planned=3600, tss_planned=50, distance_m_planned=10000,
    ))
    db.add(TPCompletedWorkout(
        tp_workout_id="done-99", date=date(2026, 4, 3),
        title="Intervals", workout_type="run",
        tss=85, distance_m=12000, duration_sec=4200,
    ))
    db.commit()
    resp = client.get("/api/aerobico/calendar?from_date=2026-04-01&to_date=2026-04-15")
    assert resp.status_code == 200
    data = resp.json()
    assert data["planned"][0]["tp_workout_id"] == "plan-99"
    assert data["completed"][0]["tp_workout_id"] == "done-99"
```

- [ ] **Step 2: Run test to verify it fails**

Run:
```bash
cd apps/sync && uv run pytest tests/test_aerobico_router.py::test_calendar_returns_tp_workout_id -v
```

Expected: FAIL — `tp_workout_id` not in response.

- [ ] **Step 3: Add `tp_workout_id` to Pydantic schemas**

In `apps/sync/app/schemas/aerobico.py`, add `tp_workout_id: str` to both `CalendarPlannedWorkout` and `CalendarCompletedWorkout`:

```python
class CalendarPlannedWorkout(BaseModel):
    tp_workout_id: str
    date: date
    title: str | None
    workout_type: str | None
    description: str | None
    duration_sec_planned: int | None
    tss_planned: float | None
    distance_m_planned: float | None

    model_config = {"from_attributes": True}


class CalendarCompletedWorkout(BaseModel):
    tp_workout_id: str
    date: date
    title: str | None
    workout_type: str | None
    description: str | None
    tss: float | None
    distance_m: float | None
    duration_sec: int | None

    model_config = {"from_attributes": True}
```

- [ ] **Step 4: Run test to verify it passes**

Run:
```bash
cd apps/sync && uv run pytest tests/test_aerobico_router.py::test_calendar_returns_tp_workout_id -v
```

Expected: PASS

- [ ] **Step 5: Update frontend TypeScript types**

In `apps/web/src/lib/types.ts`, add `tp_workout_id: string` to both interfaces:

```typescript
export interface CalendarPlannedWorkout {
  tp_workout_id: string;
  date: string;
  title: string | null;
  workout_type: string | null;
  description: string | null;
  duration_sec_planned: number | null;
  tss_planned: number | null;
  distance_m_planned: number | null;
}

export interface CalendarCompletedWorkout {
  tp_workout_id: string;
  date: string;
  title: string | null;
  workout_type: string | null;
  description: string | null;
  tss: number | null;
  distance_m: number | null;
  duration_sec: number | null;
}
```

- [ ] **Step 6: Run all aerobico router tests**

Run:
```bash
cd apps/sync && uv run pytest tests/test_aerobico_router.py -v
```

Expected: All tests pass.

- [ ] **Step 7: Commit**

```bash
git add apps/sync/app/schemas/aerobico.py apps/sync/tests/test_aerobico_router.py apps/web/src/lib/types.ts
git commit -m "feat(api): add tp_workout_id to calendar workout schemas"
```

---

### Task 5: New workout detail endpoint + schemas

**Files:**
- Modify: `apps/sync/app/schemas/aerobico.py` (add new response models)
- Modify: `apps/sync/app/routers/aerobico.py` (add new endpoint)
- Modify: `apps/sync/tests/test_aerobico_router.py` (add tests)

- [ ] **Step 1: Add Pydantic response models**

Add to `apps/sync/app/schemas/aerobico.py`:

```python
class CompletedWorkoutDetail(BaseModel):
    tp_workout_id: str
    date: date
    title: str | None
    workout_type: str | None
    description: str | None
    duration_sec: int | None
    distance_m: float | None
    tss: float | None
    intensity_factor: float | None
    avg_hr: int | None
    max_hr: int | None
    avg_power: float | None
    calories: int | None
    elevation_gain_m: float | None
    workout_details_json: dict | None

    model_config = {"from_attributes": True}


class PlannedWorkoutDetail(BaseModel):
    tp_workout_id: str
    date: date
    title: str | None
    workout_type: str | None
    description: str | None
    duration_sec_planned: int | None
    distance_m_planned: float | None
    tss_planned: float | None
    structure_json: dict | None

    model_config = {"from_attributes": True}


class WorkoutWithPlannedResponse(BaseModel):
    workout: CompletedWorkoutDetail | PlannedWorkoutDetail
    planned: PlannedWorkoutDetail | None = None
    completed: CompletedWorkoutDetail | None = None
```

- [ ] **Step 2: Write the failing tests**

Add to `apps/sync/tests/test_aerobico_router.py`:

```python
def test_workout_detail_completed(client, db):
    db.add(TPCompletedWorkout(
        tp_workout_id="c-100", date=date(2026, 4, 3),
        title="Tempo Run", workout_type="Run",
        tss=85, distance_m=12000, duration_sec=4200,
        avg_hr=155, max_hr=172, intensity_factor=0.78,
        calories=800,
        workout_details_json={"timeInHeartRateZones": {"timeInZones": []}},
    ))
    db.commit()
    resp = client.get("/api/aerobico/workout/c-100")
    assert resp.status_code == 200
    data = resp.json()
    assert data["workout"]["tp_workout_id"] == "c-100"
    assert data["workout"]["title"] == "Tempo Run"
    assert data["workout"]["workout_details_json"] is not None
    assert data["planned"] is None


def test_workout_detail_completed_with_planned_match(client, db):
    db.add(TPPlannedWorkout(
        tp_workout_id="p-100", date=date(2026, 4, 3),
        title="Tempo Run", workout_type="Run",
        duration_sec_planned=4000, distance_m_planned=11000, tss_planned=80,
        description="Run at tempo pace",
    ))
    db.add(TPCompletedWorkout(
        tp_workout_id="c-100", date=date(2026, 4, 3),
        title="Tempo Run", workout_type="Run",
        tss=85, distance_m=12000, duration_sec=4200,
    ))
    db.commit()
    resp = client.get("/api/aerobico/workout/c-100")
    assert resp.status_code == 200
    data = resp.json()
    assert data["workout"]["tp_workout_id"] == "c-100"
    assert data["planned"] is not None
    assert data["planned"]["tp_workout_id"] == "p-100"
    assert data["planned"]["tss_planned"] == 80


def test_workout_detail_planned(client, db):
    db.add(TPPlannedWorkout(
        tp_workout_id="p-200", date=date(2026, 4, 10),
        title="Easy Run", workout_type="Run",
        duration_sec_planned=3600, tss_planned=40, distance_m_planned=10000,
        description="Easy recovery run",
        structure_json={"polyline": [[0, 0], [1, 0.5]], "structure": []},
    ))
    db.commit()
    resp = client.get("/api/aerobico/workout/p-200?type=planned")
    assert resp.status_code == 200
    data = resp.json()
    assert data["workout"]["tp_workout_id"] == "p-200"
    assert data["workout"]["description"] == "Easy recovery run"
    assert data["workout"]["structure_json"] is not None
    assert data["completed"] is None


def test_workout_detail_not_found(client, db):
    resp = client.get("/api/aerobico/workout/nonexistent")
    assert resp.status_code == 404
```

- [ ] **Step 3: Run tests to verify they fail**

Run:
```bash
cd apps/sync && uv run pytest tests/test_aerobico_router.py::test_workout_detail_completed tests/test_aerobico_router.py::test_workout_detail_not_found -v
```

Expected: FAIL — endpoint doesn't exist yet.

- [ ] **Step 4: Implement the endpoint**

In `apps/sync/app/routers/aerobico.py`, add the import and endpoint:

At the top, add `HTTPException` to the FastAPI import and add the new schema imports:

```python
from fastapi import APIRouter, Depends, HTTPException, Query
```

```python
from app.schemas.aerobico import (
    CalendarResponse,
    CompletedWorkoutDetail,
    PlannedWorkoutDetail,
    PMCDataPoint,
    WeeklyHRZones,
    WeeklyVolume,
    WorkoutWithPlannedResponse,
)
```

Add the endpoint at the end of the file:

```python
@router.get("/workout/{tp_workout_id}", response_model=WorkoutWithPlannedResponse)
def get_workout_detail(
    tp_workout_id: str,
    type: str = Query(default="completed"),
    db: Session = Depends(get_db),
):
    if type == "planned":
        workout = (
            db.query(TPPlannedWorkout)
            .filter(TPPlannedWorkout.tp_workout_id == tp_workout_id)
            .first()
        )
        if not workout:
            raise HTTPException(status_code=404, detail="Workout not found")

        # Try to find a matching completed workout (same date, case-insensitive title)
        completed = None
        if workout.title:
            completed = (
                db.query(TPCompletedWorkout)
                .filter(
                    TPCompletedWorkout.date == workout.date,
                    TPCompletedWorkout.title.ilike(workout.title),
                )
                .first()
            )

        return WorkoutWithPlannedResponse(
            workout=PlannedWorkoutDetail.model_validate(workout),
            completed=CompletedWorkoutDetail.model_validate(completed) if completed else None,
        )

    # Default: completed
    workout = (
        db.query(TPCompletedWorkout)
        .filter(TPCompletedWorkout.tp_workout_id == tp_workout_id)
        .first()
    )
    if not workout:
        raise HTTPException(status_code=404, detail="Workout not found")

    # Try to find a matching planned workout (same date, case-insensitive title)
    planned = None
    if workout.title:
        planned = (
            db.query(TPPlannedWorkout)
            .filter(
                TPPlannedWorkout.date == workout.date,
                TPPlannedWorkout.title.ilike(workout.title),
            )
            .first()
        )

    return WorkoutWithPlannedResponse(
        workout=CompletedWorkoutDetail.model_validate(workout),
        planned=PlannedWorkoutDetail.model_validate(planned) if planned else None,
    )
```

- [ ] **Step 5: Run all workout detail tests**

Run:
```bash
cd apps/sync && uv run pytest tests/test_aerobico_router.py -v -k "workout_detail"
```

Expected: All 4 new tests PASS.

- [ ] **Step 6: Run full aerobico test suite**

Run:
```bash
cd apps/sync && uv run pytest tests/test_aerobico_router.py -v
```

Expected: All tests pass.

- [ ] **Step 7: Commit**

```bash
cd apps/sync
git add app/schemas/aerobico.py app/routers/aerobico.py tests/test_aerobico_router.py
git commit -m "feat(api): add workout detail endpoint with planned/actual matching"
```

---

### Task 6: Frontend types and data hook

**Files:**
- Modify: `apps/web/src/lib/types.ts:61-94` (add new types)
- Create: `apps/web/src/lib/hooks/use-workout-detail.ts`

- [ ] **Step 1: Add TypeScript types**

In `apps/web/src/lib/types.ts`, after the `CalendarData` interface (line 94), add:

```typescript
export interface WorkoutDetailsJSON {
  timeInHeartRateZones?: {
    timeInZones: { seconds: number; minimum: number; maximum: number; label: string }[];
    threshold?: number;
  };
  timeInSpeedZones?: {
    timeInZones: { seconds: number; minimum: number; maximum: number; label: string }[];
    threshold?: number;
  };
  timeInPowerZones?: {
    timeInZones: { seconds: number; minimum: number; maximum: number; label: string }[];
    threshold?: number;
  };
  meanMaxSpeedsByDistance?: {
    meanMaxes: { label: string; value: number | null }[];
  };
  meanMaxSpeeds?: {
    meanMaxes: { label: string; value: number | null }[];
  };
  meanMaxHeartRates?: {
    meanMaxes: { label: string; value: number | null }[];
  };
  meanMaxPowers?: {
    meanMaxes: { label: string; value: number | null }[];
  };
}

export interface WorkoutStructureStep {
  type: "step" | "repetition";
  name?: string;
  intensityClass?: "warmUp" | "active" | "coolDown";
  length: { unit: string; value: number };
  steps?: WorkoutStructureStep[];
  targets?: { minValue: number; maxValue: number }[];
  begin?: number;
  end?: number;
}

export interface WorkoutStructure {
  polyline: [number, number][];
  structure: WorkoutStructureStep[];
  primaryIntensityMetric?: string;
}

export interface CompletedWorkoutDetail {
  tp_workout_id: string;
  date: string;
  title: string | null;
  workout_type: string | null;
  description: string | null;
  duration_sec: number | null;
  distance_m: number | null;
  tss: number | null;
  intensity_factor: number | null;
  avg_hr: number | null;
  max_hr: number | null;
  avg_power: number | null;
  calories: number | null;
  elevation_gain_m: number | null;
  workout_details_json: WorkoutDetailsJSON | null;
}

export interface PlannedWorkoutDetail {
  tp_workout_id: string;
  date: string;
  title: string | null;
  workout_type: string | null;
  description: string | null;
  duration_sec_planned: number | null;
  distance_m_planned: number | null;
  tss_planned: number | null;
  structure_json: WorkoutStructure | null;
}

export interface WorkoutWithPlanned {
  workout: CompletedWorkoutDetail | PlannedWorkoutDetail;
  planned: PlannedWorkoutDetail | null;
  completed: CompletedWorkoutDetail | null;
}
```

- [ ] **Step 2: Create the data-fetching hook**

Create `apps/web/src/lib/hooks/use-workout-detail.ts`:

```typescript
"use client";

import { useEffect, useRef, useState } from "react";
import { fetchApi } from "@/lib/api";
import type { WorkoutWithPlanned } from "@/lib/types";

interface WorkoutSelection {
  id: string;
  type: "completed" | "planned";
}

export function useWorkoutDetail(selection: WorkoutSelection | null) {
  const [data, setData] = useState<WorkoutWithPlanned | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const cacheRef = useRef<Map<string, WorkoutWithPlanned>>(new Map());

  useEffect(() => {
    if (!selection) {
      setData(null);
      setLoading(false);
      return;
    }

    const cacheKey = `${selection.type}:${selection.id}`;
    const cached = cacheRef.current.get(cacheKey);
    if (cached) {
      setData(cached);
      setLoading(false);
      return;
    }

    setLoading(true);
    setError(null);

    let cancelled = false;
    fetchApi<WorkoutWithPlanned>(
      `/api/aerobico/workout/${selection.id}?type=${selection.type}`,
    )
      .then((result) => {
        if (!cancelled) {
          cacheRef.current.set(cacheKey, result);
          setData(result);
          setLoading(false);
        }
      })
      .catch((err) => {
        if (!cancelled) {
          setError(err.message);
          setLoading(false);
        }
      });

    return () => { cancelled = true; };
  }, [selection?.id, selection?.type]);

  return { data, loading, error };
}
```

- [ ] **Step 3: Commit**

```bash
git add apps/web/src/lib/types.ts apps/web/src/lib/hooks/use-workout-detail.ts
git commit -m "feat(web): add workout detail types and data hook"
```

---

### Task 7: Workout detail drawer — main container and header

**Files:**
- Create: `apps/web/src/components/aerobico/workout-detail-drawer.tsx`

- [ ] **Step 1: Create the drawer component**

Create `apps/web/src/components/aerobico/workout-detail-drawer.tsx`:

```typescript
"use client";

import { X } from "lucide-react";
import type {
  CompletedWorkoutDetail,
  PlannedWorkoutDetail,
  WorkoutWithPlanned,
} from "@/lib/types";
import { useWorkoutDetail } from "@/lib/hooks/use-workout-detail";
import { DrawerCompletedBody } from "./drawer-completed-body";
import { DrawerPlannedBody } from "./drawer-planned-body";
import { DrawerComparisonStrip } from "./drawer-comparison-strip";
import { DrawerCharts } from "./drawer-charts";
import { DrawerStructureViz } from "./drawer-structure-viz";

const WORKOUT_COLORS: Record<string, string> = {
  run: "#00d68f",
  bike: "#4da6ff",
  swim: "#00c4b4",
  strength: "#a855f7",
  hike: "#f59e0b",
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

function isCompleted(
  w: CompletedWorkoutDetail | PlannedWorkoutDetail,
): w is CompletedWorkoutDetail {
  return "duration_sec" in w;
}

function formatDate(dateStr: string): string {
  const d = new Date(dateStr + "T00:00:00");
  return d.toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" });
}

interface WorkoutDetailDrawerProps {
  selection: { id: string; type: "completed" | "planned" } | null;
  onClose: () => void;
}

export function WorkoutDetailDrawer({ selection, onClose }: WorkoutDetailDrawerProps) {
  const { data, loading, error } = useWorkoutDetail(selection);
  const isOpen = selection !== null;

  return (
    <div
      className="overflow-hidden transition-all duration-300 ease-out"
      style={{ maxHeight: isOpen ? "600px" : "0px" }}
    >
      {isOpen && (
        <div className="mt-4 rounded-xl border border-whoop-border bg-whoop-card">
          {loading && (
            <div className="p-4">
              <div className="h-[200px] animate-pulse rounded bg-whoop-surface" />
            </div>
          )}

          {error && (
            <div className="flex items-center justify-center p-8">
              <p className="text-xs text-whoop-text-muted">Could not load workout details</p>
            </div>
          )}

          {data && <DrawerContent data={data} onClose={onClose} />}
        </div>
      )}
    </div>
  );
}

function DrawerContent({ data, onClose }: { data: WorkoutWithPlanned; onClose: () => void }) {
  const workout = data.workout;
  const color = getColor(workout.workout_type);
  const completed = isCompleted(workout);
  const title = workout.title || (completed ? "Workout" : "Planned");
  const typeBadge = workout.workout_type || "Workout";

  return (
    <>
      {/* Header bar */}
      <div
        className="flex items-center justify-between px-4 py-3"
        style={{
          borderBottom: "1px solid rgba(255,255,255,0.06)",
          borderLeft: `3px solid ${color}`,
          background: `linear-gradient(90deg, ${color}10, transparent)`,
        }}
      >
        <div className="flex items-center gap-3">
          <span className="text-sm font-semibold text-whoop-text">{title}</span>
          <span className="text-xs text-whoop-text-muted">
            {typeBadge} &bull; {formatDate(workout.date)}
          </span>
          {!completed && (
            <span className="rounded border border-whoop-border px-1.5 py-0.5 text-[10px] font-medium uppercase tracking-wider text-whoop-text-muted"
              style={{ borderStyle: "dashed" }}
            >
              Planned
            </span>
          )}
        </div>
        <button
          onClick={onClose}
          className="rounded p-1 text-whoop-text-muted hover:bg-whoop-surface hover:text-whoop-text transition-colors"
        >
          <X size={16} />
        </button>
      </div>

      {/* Comparison strip (when both planned and completed exist) */}
      {completed && data.planned && (
        <DrawerComparisonStrip
          completed={workout as CompletedWorkoutDetail}
          planned={data.planned}
        />
      )}
      {!completed && data.completed && (
        <DrawerComparisonStrip
          completed={data.completed}
          planned={workout as PlannedWorkoutDetail}
        />
      )}

      {/* Body */}
      {completed ? (
        <DrawerCompletedBody workout={workout as CompletedWorkoutDetail} color={color} />
      ) : (
        <DrawerPlannedBody workout={workout as PlannedWorkoutDetail} color={color} />
      )}

      {/* Charts / Structure */}
      {completed && (
        <DrawerCharts workout={workout as CompletedWorkoutDetail} />
      )}
      {!completed && (workout as PlannedWorkoutDetail).structure_json && (
        <DrawerStructureViz structure={(workout as PlannedWorkoutDetail).structure_json!} />
      )}
    </>
  );
}
```

- [ ] **Step 2: Commit**

```bash
git add apps/web/src/components/aerobico/workout-detail-drawer.tsx
git commit -m "feat(web): add WorkoutDetailDrawer main container and header"
```

---

### Task 8: Drawer body components (completed + planned)

**Files:**
- Create: `apps/web/src/components/aerobico/drawer-completed-body.tsx`
- Create: `apps/web/src/components/aerobico/drawer-planned-body.tsx`

- [ ] **Step 1: Create completed body component**

Create `apps/web/src/components/aerobico/drawer-completed-body.tsx`:

```typescript
"use client";

import type { CompletedWorkoutDetail } from "@/lib/types";

function formatDuration(sec: number | null): string {
  if (!sec) return "—";
  const h = Math.floor(sec / 3600);
  const m = Math.floor((sec % 3600) / 60);
  return h > 0 ? `${h}h ${m.toString().padStart(2, "0")}m` : `${m}m`;
}

function formatPace(distM: number | null, sec: number | null): string {
  if (!distM || !sec || distM < 100) return "—";
  const paceSecPerKm = sec / (distM / 1000);
  const min = Math.floor(paceSecPerKm / 60);
  const s = Math.round(paceSecPerKm % 60);
  return `${min}:${s.toString().padStart(2, "0")} /km`;
}

function formatKm(meters: number | null): string {
  if (!meters || meters < 100) return "—";
  return `${(meters / 1000).toFixed(1)} km`;
}

interface MetricRowProps {
  label: string;
  value: string;
  color?: string;
}

function MetricRow({ label, value, color }: MetricRowProps) {
  return (
    <div className="flex justify-between text-[11px]">
      <span className="text-whoop-text-muted">{label}</span>
      <span className="font-medium" style={{ color: color || "var(--whoop-text)" }}>{value}</span>
    </div>
  );
}

interface DrawerCompletedBodyProps {
  workout: CompletedWorkoutDetail;
  color: string;
}

export function DrawerCompletedBody({ workout, color }: DrawerCompletedBodyProps) {
  return (
    <div className="flex" style={{ borderBottom: "1px solid rgba(255,255,255,0.04)" }}>
      {/* Left: Coach Notes */}
      <div className="flex-1 p-4" style={{ borderRight: "1px solid rgba(255,255,255,0.04)" }}>
        <div
          className="mb-1.5 text-[10px] font-semibold uppercase tracking-wider"
          style={{ color }}
        >
          Coach Notes
        </div>
        {workout.description ? (
          <div className="whitespace-pre-line text-xs leading-relaxed text-whoop-text-secondary">
            {workout.description}
          </div>
        ) : (
          <div className="text-xs text-whoop-text-muted italic">No notes</div>
        )}
      </div>

      {/* Right: Key Metrics */}
      <div className="w-[200px] shrink-0 space-y-1.5 p-4">
        <MetricRow label="Distance" value={formatKm(workout.distance_m)} />
        <MetricRow label="Duration" value={formatDuration(workout.duration_sec)} />
        <MetricRow label="Avg Pace" value={formatPace(workout.distance_m, workout.duration_sec)} />
        <MetricRow label="TSS" value={workout.tss != null ? String(Math.round(workout.tss)) : "—"} color="#4da6ff" />
        <MetricRow label="IF" value={workout.intensity_factor != null ? workout.intensity_factor.toFixed(2) : "—"} />
        <MetricRow
          label="Avg HR"
          value={workout.avg_hr != null ? `${workout.avg_hr} bpm` : "—"}
          color="#ef4444"
        />
        <MetricRow
          label="Max HR"
          value={workout.max_hr != null ? `${workout.max_hr} bpm` : "—"}
          color="#ef4444"
        />
        {workout.elevation_gain_m != null && (
          <MetricRow label="Elevation" value={`${Math.round(workout.elevation_gain_m)}m`} />
        )}
        <MetricRow label="Calories" value={workout.calories != null ? workout.calories.toLocaleString() : "—"} />
      </div>
    </div>
  );
}
```

- [ ] **Step 2: Create planned body component**

Create `apps/web/src/components/aerobico/drawer-planned-body.tsx`:

```typescript
"use client";

import type { PlannedWorkoutDetail } from "@/lib/types";

function formatDuration(sec: number | null): string {
  if (!sec) return "—";
  const h = Math.floor(sec / 3600);
  const m = Math.floor((sec % 3600) / 60);
  return h > 0 ? `${h}h ${m.toString().padStart(2, "0")}m` : `${m}m`;
}

function formatKm(meters: number | null): string {
  if (!meters || meters < 100) return "—";
  return `${(meters / 1000).toFixed(1)} km`;
}

interface DrawerPlannedBodyProps {
  workout: PlannedWorkoutDetail;
  color: string;
}

export function DrawerPlannedBody({ workout, color }: DrawerPlannedBodyProps) {
  return (
    <div className="flex" style={{ borderBottom: "1px solid rgba(255,255,255,0.04)" }}>
      {/* Left: Coach Notes */}
      <div className="flex-1 p-4" style={{ borderRight: "1px solid rgba(255,255,255,0.04)" }}>
        <div
          className="mb-1.5 text-[10px] font-semibold uppercase tracking-wider"
          style={{ color }}
        >
          Coach Notes
        </div>
        {workout.description ? (
          <div className="whitespace-pre-line text-xs leading-relaxed text-whoop-text-secondary">
            {workout.description}
          </div>
        ) : (
          <div className="text-xs text-whoop-text-muted italic">No notes</div>
        )}
      </div>

      {/* Right: Planned Targets */}
      <div className="w-[200px] shrink-0 space-y-1.5 p-4">
        <div className="mb-2 text-[10px] font-semibold uppercase tracking-wider text-whoop-text-muted">
          Planned Targets
        </div>
        <div className="flex justify-between text-[11px]">
          <span className="text-whoop-text-muted">Duration</span>
          <span className="italic text-whoop-text-secondary">{formatDuration(workout.duration_sec_planned)}</span>
        </div>
        <div className="flex justify-between text-[11px]">
          <span className="text-whoop-text-muted">Distance</span>
          <span className="italic text-whoop-text-secondary">{formatKm(workout.distance_m_planned)}</span>
        </div>
        <div className="flex justify-between text-[11px]">
          <span className="text-whoop-text-muted">TSS</span>
          <span className="italic text-whoop-text-secondary">
            {workout.tss_planned != null ? String(Math.round(workout.tss_planned)) : "—"}
          </span>
        </div>
      </div>
    </div>
  );
}
```

- [ ] **Step 3: Commit**

```bash
git add apps/web/src/components/aerobico/drawer-completed-body.tsx apps/web/src/components/aerobico/drawer-planned-body.tsx
git commit -m "feat(web): add drawer body components for completed and planned workouts"
```

---

### Task 9: Comparison strip component

**Files:**
- Create: `apps/web/src/components/aerobico/drawer-comparison-strip.tsx`

- [ ] **Step 1: Create the comparison strip**

Create `apps/web/src/components/aerobico/drawer-comparison-strip.tsx`:

```typescript
"use client";

import type { CompletedWorkoutDetail, PlannedWorkoutDetail } from "@/lib/types";

function formatDuration(sec: number | null): string {
  if (!sec) return "—";
  const h = Math.floor(sec / 3600);
  const m = Math.floor((sec % 3600) / 60);
  return h > 0 ? `${h}h${m.toString().padStart(2, "0")}` : `${m}m`;
}

function formatKm(meters: number | null): string {
  if (!meters || meters < 100) return "—";
  return `${(meters / 1000).toFixed(1)}`;
}

function deltaColor(planned: number, actual: number): string {
  const pct = Math.abs((actual - planned) / planned);
  if (pct <= 0.1) return "#00d68f";  // green
  if (pct <= 0.25) return "#f59e0b"; // yellow
  return "#ef4444";                  // red
}

function formatDelta(planned: number | null, actual: number | null, unit: string): string {
  if (planned == null || actual == null) return "—";
  const diff = actual - planned;
  const sign = diff >= 0 ? "+" : "";
  return `${sign}${Math.round(diff)}${unit}`;
}

interface ComparisonItem {
  label: string;
  planned: string;
  actual: string;
  delta: string;
  color: string;
}

interface DrawerComparisonStripProps {
  completed: CompletedWorkoutDetail;
  planned: PlannedWorkoutDetail;
}

export function DrawerComparisonStrip({ completed, planned }: DrawerComparisonStripProps) {
  const items: ComparisonItem[] = [];

  // Duration
  if (planned.duration_sec_planned != null && completed.duration_sec != null) {
    items.push({
      label: "Duration",
      planned: formatDuration(planned.duration_sec_planned),
      actual: formatDuration(completed.duration_sec),
      delta: (() => {
        const diff = completed.duration_sec! - planned.duration_sec_planned!;
        const m = Math.round(diff / 60);
        return `${m >= 0 ? "+" : ""}${m}min`;
      })(),
      color: deltaColor(planned.duration_sec_planned, completed.duration_sec),
    });
  }

  // Distance
  if (planned.distance_m_planned != null && completed.distance_m != null) {
    const plannedKm = planned.distance_m_planned / 1000;
    const actualKm = completed.distance_m / 1000;
    const diffKm = actualKm - plannedKm;
    items.push({
      label: "Distance",
      planned: `${plannedKm.toFixed(1)} km`,
      actual: `${actualKm.toFixed(1)} km`,
      delta: `${diffKm >= 0 ? "+" : ""}${diffKm.toFixed(1)} km`,
      color: deltaColor(planned.distance_m_planned, completed.distance_m),
    });
  }

  // TSS
  if (planned.tss_planned != null && completed.tss != null) {
    items.push({
      label: "TSS",
      planned: String(Math.round(planned.tss_planned)),
      actual: String(Math.round(completed.tss)),
      delta: formatDelta(planned.tss_planned, completed.tss, ""),
      color: deltaColor(planned.tss_planned, completed.tss),
    });
  }

  if (items.length === 0) return null;

  return (
    <div
      className="flex items-center gap-6 px-4 py-2"
      style={{
        borderBottom: "1px solid rgba(255,255,255,0.04)",
        background: "rgba(255,255,255,0.02)",
      }}
    >
      <span className="text-[10px] font-semibold uppercase tracking-wider text-whoop-text-muted">
        Plan vs Actual
      </span>
      {items.map((item) => (
        <div key={item.label} className="flex items-center gap-2 text-[11px]">
          <span className="text-whoop-text-muted">{item.label}:</span>
          <span className="text-whoop-text-secondary">{item.planned}</span>
          <span className="text-whoop-text-muted">&rarr;</span>
          <span className="text-whoop-text">{item.actual}</span>
          <span className="font-medium" style={{ color: item.color }}>
            ({item.delta})
          </span>
        </div>
      ))}
    </div>
  );
}
```

- [ ] **Step 2: Commit**

```bash
git add apps/web/src/components/aerobico/drawer-comparison-strip.tsx
git commit -m "feat(web): add planned-vs-actual comparison strip component"
```

---

### Task 10: Charts components (HR zones, pace zones, best paces)

**Files:**
- Create: `apps/web/src/components/aerobico/drawer-charts.tsx`

- [ ] **Step 1: Create the charts component**

Create `apps/web/src/components/aerobico/drawer-charts.tsx`:

```typescript
"use client";

import type { CompletedWorkoutDetail } from "@/lib/types";

const HR_ZONE_COLORS = ["#00d68f", "#4da6ff", "#f59e0b", "#ef4444", "#dc2626"];
const HR_ZONE_LABELS = ["Z1", "Z2", "Z3", "Z4", "Z5"];

function formatZoneTime(sec: number): string {
  if (sec < 60) return `${sec}s`;
  const m = Math.floor(sec / 60);
  return `${m}m`;
}

function speedToPace(mps: number): string {
  if (mps <= 0) return "—";
  const secPerKm = 1000 / mps;
  const min = Math.floor(secPerKm / 60);
  const sec = Math.round(secPerKm % 60);
  return `${min}:${sec.toString().padStart(2, "0")}`;
}

const PACE_DISTANCE_LABELS: Record<string, string> = {
  MM400Meter: "400m",
  MM800Meter: "800m",
  MM1Kilometer: "1 km",
  MM1Mile: "1 mi",
  MM5Kilometer: "5 km",
  MM10Kilometer: "10 km",
  MMHalfMarathon: "HM",
  MMMarathon: "Marathon",
};

const PACE_DISTANCE_ORDER = [
  "MM400Meter", "MM800Meter", "MM1Kilometer", "MM5Kilometer", "MM10Kilometer",
];

interface DrawerChartsProps {
  workout: CompletedWorkoutDetail;
}

export function DrawerCharts({ workout }: DrawerChartsProps) {
  const details = workout.workout_details_json;
  if (!details) return null;

  const hrZones = details.timeInHeartRateZones?.timeInZones || [];
  const speedZones = details.timeInSpeedZones?.timeInZones || [];
  const bestPaces = details.meanMaxSpeedsByDistance?.meanMaxes || [];

  const hasHR = hrZones.length > 0 && hrZones.some((z) => z.seconds > 0);
  const hasSpeed = speedZones.length > 0 && speedZones.some((z) => z.seconds > 0);
  const hasBestPaces = bestPaces.some((p) => p.value != null && p.value > 0);

  if (!hasHR && !hasSpeed && !hasBestPaces) return null;

  const maxHRSec = Math.max(...hrZones.map((z) => z.seconds), 1);
  const maxSpeedSec = Math.max(...speedZones.map((z) => z.seconds), 1);

  return (
    <div className="flex" style={{ borderTop: "1px solid rgba(255,255,255,0.04)" }}>
      {/* HR Zones */}
      {hasHR && (
        <div className="flex-1 p-3" style={{ borderRight: hasSpeed || hasBestPaces ? "1px solid rgba(255,255,255,0.04)" : undefined }}>
          <div className="mb-2 text-[10px] font-semibold text-whoop-text-muted">HR Zones</div>
          <div className="flex items-end gap-1" style={{ height: "60px" }}>
            {hrZones.slice(0, 5).map((z, i) => (
              <div key={i} className="flex flex-1 flex-col items-center gap-0.5">
                <div className="text-[9px] text-whoop-text-muted">
                  {z.seconds > 0 ? formatZoneTime(z.seconds) : ""}
                </div>
                <div
                  className="w-full rounded-t"
                  style={{
                    height: `${Math.max((z.seconds / maxHRSec) * 48, 2)}px`,
                    backgroundColor: HR_ZONE_COLORS[i] || "#6b7280",
                  }}
                />
                <div className="text-[9px] text-whoop-text-muted">{HR_ZONE_LABELS[i]}</div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Pace/Speed Zones */}
      {hasSpeed && (
        <div className="flex-1 p-3" style={{ borderRight: hasBestPaces ? "1px solid rgba(255,255,255,0.04)" : undefined }}>
          <div className="mb-2 text-[10px] font-semibold text-whoop-text-muted">Pace Zones</div>
          <div className="flex items-end gap-1" style={{ height: "60px" }}>
            {speedZones.slice(0, 5).map((z, i) => (
              <div key={i} className="flex flex-1 flex-col items-center gap-0.5">
                <div className="text-[9px] text-whoop-text-muted">
                  {z.seconds > 0 ? formatZoneTime(z.seconds) : ""}
                </div>
                <div
                  className="w-full rounded-t"
                  style={{
                    height: `${Math.max((z.seconds / maxSpeedSec) * 48, 2)}px`,
                    backgroundColor: "#a855f7",
                    opacity: 0.5 + (i / 5) * 0.5,
                  }}
                />
                <div className="truncate text-[8px] text-whoop-text-muted" title={z.label}>
                  {z.label.replace(/ Run$/, "").slice(0, 4)}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Best Paces by Distance */}
      {hasBestPaces && (
        <div className="flex-1 p-3">
          <div className="mb-2 text-[10px] font-semibold text-whoop-text-muted">Best Paces</div>
          <div className="space-y-1">
            {PACE_DISTANCE_ORDER.map((key) => {
              const entry = bestPaces.find((p) => p.label === key);
              if (!entry || entry.value == null || entry.value <= 0) return null;
              return (
                <div key={key} className="flex justify-between text-[11px]">
                  <span className="text-whoop-text-muted">{PACE_DISTANCE_LABELS[key] || key}</span>
                  <span className="text-whoop-text">{speedToPace(entry.value)} /km</span>
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}
```

- [ ] **Step 2: Commit**

```bash
git add apps/web/src/components/aerobico/drawer-charts.tsx
git commit -m "feat(web): add HR zones, pace zones, and best paces chart components"
```

---

### Task 11: Structure visualization component

**Files:**
- Create: `apps/web/src/components/aerobico/drawer-structure-viz.tsx`

- [ ] **Step 1: Create the structure visualization**

Create `apps/web/src/components/aerobico/drawer-structure-viz.tsx`:

```typescript
"use client";

import type { WorkoutStructure, WorkoutStructureStep } from "@/lib/types";

const INTENSITY_COLORS: Record<string, string> = {
  warmUp: "#00d68f",
  active: "#ef4444",
  coolDown: "#4da6ff",
};

function formatStepLength(step: WorkoutStructureStep): string {
  const { unit, value } = step.length;
  if (unit === "second") {
    const m = Math.floor(value / 60);
    const s = value % 60;
    return s > 0 ? `${m}:${s.toString().padStart(2, "0")}` : `${m}:00`;
  }
  if (unit === "meter") {
    return value >= 1000 ? `${(value / 1000).toFixed(1)}km` : `${value}m`;
  }
  return `${value}x`;
}

function flattenSteps(structure: WorkoutStructureStep[]): {
  label: string;
  intensityClass: string;
  widthPct: number;
  heightPct: number;
}[] {
  const blocks: { label: string; intensityClass: string; widthPct: number; heightPct: number }[] = [];

  // Compute total duration estimate from begin/end if available
  let totalEnd = 0;
  for (const step of structure) {
    if (step.end != null && step.end > totalEnd) totalEnd = step.end;
  }
  if (totalEnd === 0) totalEnd = 1;

  for (const step of structure) {
    const begin = step.begin ?? 0;
    const end = step.end ?? totalEnd;
    const widthPct = ((end - begin) / totalEnd) * 100;

    if (step.type === "repetition" && step.steps && step.length.value > 1) {
      const reps = step.length.value;
      const subWidth = widthPct / (reps * step.steps.length);
      for (let r = 0; r < reps; r++) {
        for (const sub of step.steps) {
          const intensity = sub.intensityClass || "active";
          const maxTarget = sub.targets?.[0]?.maxValue ?? 5;
          const heightPct = Math.min((maxTarget / 10) * 100, 100);
          const name = sub.name || intensity;
          const len = formatStepLength(sub);
          blocks.push({
            label: r === 0 ? `${reps}x ${len} ${name}` : "",
            intensityClass: intensity,
            widthPct: subWidth,
            heightPct,
          });
        }
      }
    } else {
      const innerStep = step.steps?.[0] || step;
      const intensity = innerStep.intensityClass || "active";
      const maxTarget = innerStep.targets?.[0]?.maxValue ?? 5;
      const heightPct = Math.min((maxTarget / 10) * 100, 100);
      const name = innerStep.name || intensity;
      const len = formatStepLength(innerStep);
      blocks.push({
        label: `${name} ${len}`,
        intensityClass: intensity,
        widthPct,
        heightPct,
      });
    }
  }

  return blocks;
}

interface DrawerStructureVizProps {
  structure: WorkoutStructure;
}

export function DrawerStructureViz({ structure }: DrawerStructureVizProps) {
  if (!structure.structure || structure.structure.length === 0) return null;

  const blocks = flattenSteps(structure.structure);

  return (
    <div className="p-3" style={{ borderTop: "1px solid rgba(255,255,255,0.04)" }}>
      <div className="mb-2 text-[10px] font-semibold text-whoop-text-muted">Workout Structure</div>
      <div className="flex items-end gap-px" style={{ height: "60px" }}>
        {blocks.map((block, i) => (
          <div
            key={i}
            className="relative flex flex-col items-center justify-end"
            style={{ width: `${block.widthPct}%`, height: "100%" }}
          >
            {block.label && (
              <div className="absolute -top-3.5 left-0 truncate text-[8px] text-whoop-text-muted whitespace-nowrap">
                {block.label}
              </div>
            )}
            <div
              className="w-full rounded-t-sm"
              style={{
                height: `${block.heightPct}%`,
                backgroundColor: INTENSITY_COLORS[block.intensityClass] || "#6b7280",
                opacity: block.intensityClass === "active" ? 0.85 : 0.6,
              }}
            />
          </div>
        ))}
      </div>
    </div>
  );
}
```

- [ ] **Step 2: Commit**

```bash
git add apps/web/src/components/aerobico/drawer-structure-viz.tsx
git commit -m "feat(web): add planned workout structure visualization component"
```

---

### Task 12: Wire up calendar selection + drawer in aerobico page

**Files:**
- Modify: `apps/web/src/components/aerobico/training-calendar.tsx` (add selection state, make blocks clickable)
- Modify: `apps/web/src/components/aerobico/aerobico-page.tsx` (render drawer between calendar and HR zones)

- [ ] **Step 1: Update TrainingCalendar to support selection**

In `apps/web/src/components/aerobico/training-calendar.tsx`:

Add to the `TrainingCalendarProps` interface and component signature:

```typescript
interface TrainingCalendarProps {
  from: string;
  to: string;
  selectedWorkoutId: string | null;
  onSelectWorkout: (id: string, type: "completed" | "planned") => void;
}

export function TrainingCalendar({ from, to, selectedWorkoutId, onSelectWorkout }: TrainingCalendarProps) {
```

Update the `WorkoutBlock` component to accept and handle clicks. Change its props and add click handler:

```typescript
function WorkoutBlock({ workout, planned, selectedId, onSelect }: {
  workout: CalendarCompletedWorkout | CalendarPlannedWorkout;
  planned?: boolean;
  selectedId: string | null;
  onSelect: (id: string, type: "completed" | "planned") => void;
}) {
  const [hovered, setHovered] = useState(false);
  const type = workout.workout_type;
  const title = workout.title;
  const color = getColor(type);
  const isSelected = workout.tp_workout_id === selectedId;

  const duration = planned
    ? formatDuration((workout as CalendarPlannedWorkout).duration_sec_planned)
    : formatDuration((workout as CalendarCompletedWorkout).duration_sec);
  const distance = planned
    ? formatKm((workout as CalendarPlannedWorkout).distance_m_planned)
    : formatKm((workout as CalendarCompletedWorkout).distance_m);

  // ... (keep existing tooltip detail lines logic unchanged)

  const handleClick = () => {
    onSelect(workout.tp_workout_id, planned ? "planned" : "completed");
  };

  return (
    <div
      className="relative"
      onMouseEnter={() => setHovered(true)}
      onMouseLeave={() => setHovered(false)}
    >
      <div
        onClick={handleClick}
        className={`cursor-pointer rounded px-1.5 py-0.5 text-[10px] leading-tight transition-all ${
          planned ? "opacity-50 border border-dashed" : ""
        } ${isSelected ? "ring-1" : ""}`}
        style={{
          borderLeft: planned ? undefined : `2px solid ${color}`,
          borderColor: planned ? color : undefined,
          backgroundColor: planned ? "transparent" : `${color}10`,
          boxShadow: isSelected ? `0 0 8px ${color}40` : undefined,
          ringColor: isSelected ? color : undefined,
        }}
      >
```

Update where `WorkoutBlock` is rendered in the calendar grid to pass the new props:

```typescript
{completed.map((w, i) => (
  <WorkoutBlock key={`c-${i}`} workout={w} selectedId={selectedWorkoutId} onSelect={onSelectWorkout} />
))}
{planned.map((w, i) => (
  <WorkoutBlock key={`p-${i}`} workout={w} planned selectedId={selectedWorkoutId} onSelect={onSelectWorkout} />
))}
```

- [ ] **Step 2: Update aerobico-page.tsx to manage selection and render drawer**

In `apps/web/src/components/aerobico/aerobico-page.tsx`, add imports and state:

```typescript
import { useState } from "react";
// ... existing imports
import { WorkoutDetailDrawer } from "./workout-detail-drawer";
```

Inside `AerobicoPageClient`, add:

```typescript
const [selectedWorkout, setSelectedWorkout] = useState<{ id: string; type: "completed" | "planned" } | null>(null);

const handleSelectWorkout = (id: string, type: "completed" | "planned") => {
  setSelectedWorkout((prev) =>
    prev?.id === id ? null : { id, type }
  );
};

const handleCloseDrawer = () => setSelectedWorkout(null);
```

Update the `TrainingCalendar` usage:

```tsx
<TrainingCalendar
  from={from}
  to={to}
  selectedWorkoutId={selectedWorkout?.id ?? null}
  onSelectWorkout={handleSelectWorkout}
/>
```

Add the drawer between the calendar and the HR zones chart:

```tsx
{/* Workout Detail Drawer */}
<WorkoutDetailDrawer
  selection={selectedWorkout}
  onClose={handleCloseDrawer}
/>
```

- [ ] **Step 3: Verify the build compiles**

Run:
```bash
cd apps/web && pnpm build
```

Expected: Build succeeds with no TypeScript errors.

- [ ] **Step 4: Commit**

```bash
git add apps/web/src/components/aerobico/training-calendar.tsx apps/web/src/components/aerobico/aerobico-page.tsx
git commit -m "feat(web): wire up calendar selection and workout detail drawer"
```

---

### Task 13: Run backfill and end-to-end verification

**Files:** No file changes — verification only.

- [ ] **Step 1: Run the backfill to populate workout_details_json**

Run:
```bash
cd apps/sync && uv run python -c "
import httpx
resp = httpx.post('http://localhost:8000/api/tp/sync/zones-backfill', timeout=10)
print(resp.json())
"
```

Expected: `{"status": "tp_zones_backfill_started"}`

Wait a few minutes for the backfill to complete, then verify:

```bash
cd apps/sync && uv run python -c "
from app.database import SessionLocal
from sqlalchemy import text
db = SessionLocal()
total = db.execute(text('SELECT COUNT(*) FROM tp_completed_workouts')).scalar()
filled = db.execute(text(\"SELECT COUNT(*) FROM tp_completed_workouts WHERE workout_details_json IS NOT NULL AND workout_details_json::text != 'null'\")).scalar()
print(f'{filled}/{total} workouts have details JSON')
db.close()
"
```

Expected: Most workouts now have `workout_details_json` populated.

- [ ] **Step 2: Test the workout detail endpoint**

Run:
```bash
cd apps/sync && uv run python -c "
import httpx
# Get a recent completed workout ID from the calendar
cal = httpx.get('http://localhost:8000/api/aerobico/calendar?from_date=2026-04-01&to_date=2026-04-05').json()
if cal['completed']:
    wid = cal['completed'][0]['tp_workout_id']
    print(f'Testing workout ID: {wid}')
    detail = httpx.get(f'http://localhost:8000/api/aerobico/workout/{wid}').json()
    print(f'Title: {detail[\"workout\"][\"title\"]}')
    print(f'Has details JSON: {detail[\"workout\"][\"workout_details_json\"] is not None}')
    print(f'Has planned match: {detail[\"planned\"] is not None}')
else:
    print('No completed workouts in date range')
"
```

Expected: Endpoint returns workout data with details JSON.

- [ ] **Step 3: Test the frontend visually**

Run:
```bash
cd apps/web && pnpm dev
```

Open http://localhost:3000/aerobico and click on a workout in the calendar. The drawer should slide open showing coach notes, metrics, HR zone bars, pace zone bars, and best paces.

- [ ] **Step 4: Run all backend tests**

Run:
```bash
cd apps/sync && uv run pytest -v
```

Expected: All tests pass.

- [ ] **Step 5: Run lint**

Run:
```bash
make lint
```

Expected: No lint errors.

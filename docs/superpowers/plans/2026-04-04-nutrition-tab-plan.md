# Nutrition Tab Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a `/nutricion` page showing daily calorie tracking vs goal, macro composition, alcohol consumption, and body composition trends — with aligned time-series charts and a summary sidebar.

**Architecture:** Backend adds an `alcohol_drinks` column to `nutrition_daily`, extends `MFPClient.get_day()` to return meal entries for alcohol keyword detection, and adds a `/api/body-composition` endpoint. Frontend creates a new `/nutricion` route with four date-aligned charts (calories, macros, alcohol strip, weight/BF) plus a summary sidebar with period KPIs.

**Tech Stack:** Python/FastAPI/SQLAlchemy/Alembic (backend), Next.js/TypeScript/lightweight-charts/custom SVG (frontend)

**Spec:** `docs/superpowers/specs/2026-04-04-nutrition-tab-design.md`

---

## File Map

### Backend (apps/sync/)

| Action | File | Responsibility |
|--------|------|----------------|
| Modify | `app/models/nutrition_daily.py` | Add `alcohol_drinks` column |
| Modify | `app/schemas/nutrition.py` | Add `alcohol_drinks` to response |
| Create | `alembic/versions/f6g7h8i9j0k1_add_alcohol_drinks_to_nutrition_daily.py` | Migration |
| Modify | `app/services/mfp_client.py` | Return meal entries alongside totals |
| Modify | `app/services/sync_service.py` | Count alcohol drinks during nutrition sync |
| Create | `app/routers/body_composition.py` | `GET /api/body-composition` endpoint |
| Create | `app/schemas/body_composition.py` | Pydantic response model |
| Modify | `app/main.py` | Register body_composition router |
| Create | `tests/test_alcohol_detection.py` | Tests for alcohol keyword matching |
| Modify | `tests/test_mfp_client.py` | Tests for entries extraction |

### Frontend (apps/web/src/)

| Action | File | Responsibility |
|--------|------|----------------|
| Modify | `lib/types.ts` | Add `NutritionDay` and `BodyCompositionDay` types |
| Create | `lib/hooks/use-nutrition-data.ts` | Fetch `/api/nutrition` |
| Create | `lib/hooks/use-body-composition.ts` | Fetch `/api/body-composition` |
| Create | `app/(dashboard)/nutricion/page.tsx` | Route entry (server component) |
| Create | `components/nutricion/nutricion-page.tsx` | Main client component with date state |
| Create | `components/nutricion/calories-chart.tsx` | Daily bars + goal line + 7d MA |
| Create | `components/nutricion/macro-stacked-chart.tsx` | Daily 100% stacked bars (custom SVG) |
| Create | `components/nutricion/alcohol-strip.tsx` | Daily dot strip with week boundaries |
| Create | `components/nutricion/weight-bf-chart.tsx` | Dual-axis lightweight-charts |
| Create | `components/nutricion/summary-sidebar.tsx` | Period KPI cards |
| Modify | `components/layout/sidebar.tsx` | Add "Nutrición" nav item |

---

## Task 0: Alcohol Keyword Discovery (One-Time, Interactive)

This task is **interactive** — it requires running a script, reviewing output with the user, and hardcoding the results. It must be done before Task 3.

**Files:**
- Create: `apps/sync/scripts/discover_alcohol_keywords.py`

- [ ] **Step 0.1: Write discovery script**

```python
"""One-time script to extract all unique MFP food entry names for alcohol classification.

Usage: cd apps/sync && uv run python scripts/discover_alcohol_keywords.py
Requires MFP_COOKIES env var or .env file.
"""
import json
import os
import sys
from datetime import date, timedelta

# Add parent so app imports work
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.config import settings
from app.services.mfp_client import MFPClient


def main():
    cookies = settings.mfp_cookies
    if not cookies:
        print("ERROR: MFP_COOKIES not set")
        sys.exit(1)

    client = MFPClient(cookies_json=cookies)
    client.login()
    if not client._authenticated:
        print("ERROR: MFP login failed")
        sys.exit(1)

    today = date.today()
    start = today - timedelta(days=90)
    all_names: set[str] = set()
    day = start

    while day <= today:
        data = client.get_day(day)
        if data and "entries" in data:
            for entry in data["entries"]:
                all_names.add(entry["name"])
        day += timedelta(days=1)
        if (day - start).days % 10 == 0:
            print(f"  scanned {(day - start).days}/90 days, {len(all_names)} unique names")

    print(f"\nTotal unique food entry names: {len(all_names)}\n")
    sorted_names = sorted(all_names)
    for name in sorted_names:
        print(f"  {name}")

    # Save to file for LLM review
    out_path = os.path.join(os.path.dirname(__file__), "mfp_food_names.txt")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write("\n".join(sorted_names))
    print(f"\nSaved to {out_path}")


if __name__ == "__main__":
    main()
```

**Note:** This script depends on `MFPClient.get_day()` returning entries (implemented in Task 2). Run Task 2 first, then this script.

- [ ] **Step 0.2: Run the script**

```bash
cd apps/sync && uv run python scripts/discover_alcohol_keywords.py
```

- [ ] **Step 0.3: Classify with LLM and present to user**

Read `apps/sync/scripts/mfp_food_names.txt`, identify which entries are alcoholic beverages, and present the list to the user for review/correction.

- [ ] **Step 0.4: Hardcode keywords**

After user approval, the final keyword list will be used in Task 3. Delete the script and txt file after use.

---

## Task 1: Add `alcohol_drinks` Column + Migration

**Files:**
- Modify: `apps/sync/app/models/nutrition_daily.py`
- Modify: `apps/sync/app/schemas/nutrition.py`
- Create: `apps/sync/alembic/versions/<auto>_add_alcohol_drinks_to_nutrition_daily.py`

- [ ] **Step 1.1: Add column to model**

In `apps/sync/app/models/nutrition_daily.py`, add after `protein_goal_g`:

```python
alcohol_drinks: Mapped[int | None] = mapped_column(Integer, nullable=True)
```

- [ ] **Step 1.2: Add field to schema**

In `apps/sync/app/schemas/nutrition.py`, add after `protein_goal_g`:

```python
alcohol_drinks: int | None = None
```

- [ ] **Step 1.3: Generate Alembic migration**

```bash
cd apps/sync && uv run alembic revision --autogenerate -m "add alcohol_drinks to nutrition_daily"
```

Expected: A new migration file in `alembic/versions/` with `op.add_column('nutrition_daily', sa.Column('alcohol_drinks', sa.Integer(), nullable=True))`.

- [ ] **Step 1.4: Run migration**

```bash
cd apps/sync && uv run alembic upgrade head
```

Expected: `INFO  [alembic.runtime.migration] Running upgrade ... -> ..., add alcohol_drinks to nutrition_daily`

- [ ] **Step 1.5: Verify existing test still passes**

```bash
cd apps/sync && uv run pytest tests/test_mfp_client.py -v
```

Expected: All existing tests PASS (the new nullable column doesn't break anything).

- [ ] **Step 1.6: Commit**

```bash
cd apps/sync && git add app/models/nutrition_daily.py app/schemas/nutrition.py alembic/versions/ && git commit -m "feat(sync): add alcohol_drinks column to nutrition_daily"
```

---

## Task 2: Extend `MFPClient.get_day()` to Return Entries

**Files:**
- Modify: `apps/sync/app/services/mfp_client.py`
- Modify: `apps/sync/tests/test_mfp_client.py`

- [ ] **Step 2.1: Write failing test for entries**

Add to `apps/sync/tests/test_mfp_client.py`:

```python
def test_sync_nutrition_includes_entries(db_session):
    """get_day() should return entries list alongside totals."""
    mock_garmin = MagicMock()
    mock_garmin.get_activities.return_value = []
    mock_garmin.get_daily_summary.return_value = {}
    mock_garmin.get_heart_rates.return_value = {}
    mock_garmin.get_stress_data.return_value = {}
    mock_garmin.get_body_battery.return_value = []
    mock_garmin.get_spo2_data.return_value = {}
    mock_garmin.get_respiration_data.return_value = {}
    mock_garmin.get_hydration_data.return_value = {}
    mock_garmin.get_sleep_data.return_value = {}

    mock_mfp = MagicMock()
    mock_mfp.get_day.return_value = {
        "calories": 2200,
        "protein_g": 150.0,
        "carbs_g": 250.0,
        "fat_g": 70.0,
        "fiber_g": 30.0,
        "sodium_mg": 2000.0,
        "entries": [
            {"name": "Chicken Breast", "meal": "Lunch"},
            {"name": "Corona Beer", "meal": "Dinner"},
        ],
    }

    service = SyncService(db=db_session, garmin=mock_garmin, mfp=mock_mfp)
    service.sync_nutrition(date(2026, 3, 6))

    record = db_session.query(NutritionDaily).filter_by(date=date(2026, 3, 6)).first()
    assert record is not None
    assert record.calories == 2200
```

- [ ] **Step 2.2: Run test to verify it passes (schema already updated)**

```bash
cd apps/sync && uv run pytest tests/test_mfp_client.py::test_sync_nutrition_includes_entries -v
```

Expected: PASS (the entries key is just extra data the sync ignores for now).

- [ ] **Step 2.3: Extend `MFPClient.get_day()` to include entries**

In `apps/sync/app/services/mfp_client.py`, modify the `get_day` method. Replace the try block body (lines 67-82):

```python
        try:
            day = self._client.get_date(target_date.year, target_date.month, target_date.day)
            if not day or not day.totals:
                return None

            totals = day.totals
            goals = day.goals or {}

            # Extract individual food entries from meals
            entries = []
            for meal in day.meals:
                for entry in meal.entries:
                    entries.append({
                        "name": entry.name,
                        "meal": meal.name,
                    })

            return {
                "calories": totals.get("calories"),
                "protein_g": totals.get("protein"),
                "carbs_g": totals.get("carbohydrates"),
                "fat_g": totals.get("fat"),
                "fiber_g": totals.get("fiber"),
                "sodium_mg": totals.get("sodium"),
                "calories_goal": goals.get("calories"),
                "protein_goal_g": goals.get("protein"),
                "entries": entries,
            }
        except Exception as e:
            logger.warning(f"MFP get_day failed for {target_date}: {e}")
            return None
```

- [ ] **Step 2.4: Run all MFP tests**

```bash
cd apps/sync && uv run pytest tests/test_mfp_client.py -v
```

Expected: All PASS.

- [ ] **Step 2.5: Commit**

```bash
cd apps/sync && git add app/services/mfp_client.py tests/test_mfp_client.py && git commit -m "feat(sync): extend MFPClient.get_day() to return meal entries"
```

---

## Task 3: Alcohol Detection in Sync

**Files:**
- Modify: `apps/sync/app/services/sync_service.py`
- Create: `apps/sync/tests/test_alcohol_detection.py`

- [ ] **Step 3.1: Write failing test for alcohol counting**

Create `apps/sync/tests/test_alcohol_detection.py`:

```python
from datetime import date
from unittest.mock import MagicMock

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base
from app.models import NutritionDaily
from app.services.sync_service import SyncService


@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine)
    session = session_factory()
    yield session
    session.close()


def _make_mfp_mock(entries: list[dict], calories: int = 2000) -> MagicMock:
    mock = MagicMock()
    mock.get_day.return_value = {
        "calories": calories,
        "protein_g": 100.0,
        "carbs_g": 200.0,
        "fat_g": 60.0,
        "fiber_g": 25.0,
        "sodium_mg": 1500.0,
        "calories_goal": 2100,
        "protein_goal_g": 120.0,
        "entries": entries,
    }
    return mock


def test_alcohol_detection_counts_drinks(db_session):
    entries = [
        {"name": "Chicken Breast", "meal": "Lunch"},
        {"name": "Corona Beer", "meal": "Dinner"},
        {"name": "Red Wine - 1 Glass", "meal": "Dinner"},
        {"name": "Brown Rice", "meal": "Dinner"},
    ]
    mock_mfp = _make_mfp_mock(entries)
    mock_garmin = MagicMock()

    service = SyncService(db=db_session, garmin=mock_garmin, mfp=mock_mfp)
    service.sync_nutrition(date(2026, 3, 6))

    record = db_session.query(NutritionDaily).filter_by(date=date(2026, 3, 6)).first()
    assert record is not None
    assert record.alcohol_drinks == 2


def test_alcohol_detection_zero_when_no_drinks(db_session):
    entries = [
        {"name": "Chicken Breast", "meal": "Lunch"},
        {"name": "Brown Rice", "meal": "Dinner"},
    ]
    mock_mfp = _make_mfp_mock(entries)
    mock_garmin = MagicMock()

    service = SyncService(db=db_session, garmin=mock_garmin, mfp=mock_mfp)
    service.sync_nutrition(date(2026, 3, 6))

    record = db_session.query(NutritionDaily).filter_by(date=date(2026, 3, 6)).first()
    assert record is not None
    assert record.alcohol_drinks == 0


def test_alcohol_detection_no_entries_key(db_session):
    """When MFP returns no entries (old format), alcohol_drinks should be None."""
    mock_mfp = MagicMock()
    mock_mfp.get_day.return_value = {
        "calories": 2000,
        "protein_g": 100.0,
        "carbs_g": 200.0,
        "fat_g": 60.0,
        "fiber_g": 25.0,
        "sodium_mg": 1500.0,
    }
    mock_garmin = MagicMock()

    service = SyncService(db=db_session, garmin=mock_garmin, mfp=mock_mfp)
    service.sync_nutrition(date(2026, 3, 6))

    record = db_session.query(NutritionDaily).filter_by(date=date(2026, 3, 6)).first()
    assert record is not None
    assert record.alcohol_drinks is None
```

- [ ] **Step 3.2: Run tests to verify they fail**

```bash
cd apps/sync && uv run pytest tests/test_alcohol_detection.py -v
```

Expected: FAIL — `alcohol_drinks` will be `None` for all tests since sync_nutrition doesn't set it yet.

- [ ] **Step 3.3: Implement alcohol detection in sync_service**

In `apps/sync/app/services/sync_service.py`, add near the top of the file (after the imports):

```python
# Alcohol keywords — determined by one-time analysis of MFP food entry names.
# Each keyword is matched case-insensitively against the food entry name.
ALCOHOL_KEYWORDS = [
    # PLACEHOLDER — replace with actual keywords after Task 0 discovery
    "beer", "wine", "vodka", "whiskey", "gin", "rum", "tequila",
    "cocktail", "margarita", "cerveza", "seltzer", "cider", "sangria",
    "bourbon", "scotch", "champagne", "prosecco", "mezcal", "sake",
    "malbec", "cabernet", "merlot", "ipa", "lager", "ale", "stout",
    "corona", "heineken", "aperol", "spritz", "negroni", "daiquiri",
    "mojito", "piña colada", "michelada", "paloma",
]


def _count_alcohol_drinks(entries: list[dict]) -> int:
    """Count food entries that match alcohol keywords."""
    count = 0
    for entry in entries:
        name = entry.get("name", "").lower()
        if any(kw in name for kw in ALCOHOL_KEYWORDS):
            count += 1
    return count
```

Then modify `sync_nutrition` method (replace lines 220-237):

```python
    def sync_nutrition(self, target_date: date) -> NutritionDaily | None:
        if not self.mfp:
            return None
        data = self.mfp.get_day(target_date)
        if not data:
            return None

        # Count alcohol drinks if entries are available
        entries = data.get("entries")
        alcohol_drinks = _count_alcohol_drinks(entries) if entries else None

        values = {
            "date": target_date,
            "calories": data.get("calories"),
            "protein_g": data.get("protein_g"),
            "carbs_g": data.get("carbs_g"),
            "fat_g": data.get("fat_g"),
            "fiber_g": data.get("fiber_g"),
            "sodium_mg": data.get("sodium_mg"),
            "calories_goal": data.get("calories_goal"),
            "protein_goal_g": data.get("protein_goal_g"),
            "alcohol_drinks": alcohol_drinks,
        }
        return self._upsert(NutritionDaily, "date", target_date, values)
```

- [ ] **Step 3.4: Run alcohol detection tests**

```bash
cd apps/sync && uv run pytest tests/test_alcohol_detection.py -v
```

Expected: All 3 tests PASS.

- [ ] **Step 3.5: Run all sync tests to verify no regressions**

```bash
cd apps/sync && uv run pytest tests/ -v
```

Expected: All PASS.

- [ ] **Step 3.6: Commit**

```bash
cd apps/sync && git add app/services/sync_service.py tests/test_alcohol_detection.py && git commit -m "feat(sync): detect alcohol drinks from MFP food entries"
```

---

## Task 4: Body Composition API Endpoint

**Files:**
- Create: `apps/sync/app/schemas/body_composition.py`
- Create: `apps/sync/app/routers/body_composition.py`
- Modify: `apps/sync/app/main.py`

- [ ] **Step 4.1: Create Pydantic schema**

Create `apps/sync/app/schemas/body_composition.py`:

```python
from datetime import date

from pydantic import BaseModel


class BodyCompositionResponse(BaseModel):
    date: date
    weight_kg: float | None
    body_fat_pct: float | None

    model_config = {"from_attributes": True}
```

- [ ] **Step 4.2: Create router**

Create `apps/sync/app/routers/body_composition.py`:

```python
from datetime import date, timedelta

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.body_composition import BodyComposition
from app.schemas.body_composition import BodyCompositionResponse

router = APIRouter(prefix="/api/body-composition", tags=["body-composition"])


@router.get("", response_model=list[BodyCompositionResponse])
def list_body_composition(
    from_date: date = Query(default_factory=lambda: date.today() - timedelta(days=30)),
    to_date: date = Query(default_factory=lambda: date.today()),
    db: Session = Depends(get_db),
):
    return (
        db.query(BodyComposition)
        .filter(BodyComposition.date >= from_date, BodyComposition.date <= to_date)
        .order_by(BodyComposition.date.asc())
        .all()
    )
```

- [ ] **Step 4.3: Register router in main.py**

In `apps/sync/app/main.py`, add the import:

```python
from app.routers import (
    activities,
    aerobico,
    body_composition,
    daily,
    ...
```

And add after the fitbit router line:

```python
app.include_router(body_composition.router)
```

- [ ] **Step 4.4: Verify the app starts**

```bash
cd apps/sync && uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 &
sleep 2
curl -s http://localhost:8000/api/body-composition | python -m json.tool
kill %1
```

Expected: Returns a JSON array (possibly empty if no data).

- [ ] **Step 4.5: Commit**

```bash
cd apps/sync && git add app/schemas/body_composition.py app/routers/body_composition.py app/main.py && git commit -m "feat(sync): add GET /api/body-composition endpoint"
```

---

## Task 5: Frontend Types and Data Hooks

**Files:**
- Modify: `apps/web/src/lib/types.ts`
- Create: `apps/web/src/lib/hooks/use-nutrition-data.ts`
- Create: `apps/web/src/lib/hooks/use-body-composition.ts`

- [ ] **Step 5.1: Add TypeScript types**

Append to `apps/web/src/lib/types.ts`:

```typescript
// ── Nutrición tab types ──

export interface NutritionDay {
  id: number;
  date: string;
  calories: number | null;
  protein_g: number | null;
  carbs_g: number | null;
  fat_g: number | null;
  fiber_g: number | null;
  sodium_mg: number | null;
  calories_goal: number | null;
  protein_goal_g: number | null;
  alcohol_drinks: number | null;
}

export interface BodyCompositionDay {
  date: string;
  weight_kg: number | null;
  body_fat_pct: number | null;
}
```

- [ ] **Step 5.2: Create nutrition data hook**

Create `apps/web/src/lib/hooks/use-nutrition-data.ts`:

```typescript
"use client";

import { useEffect, useState } from "react";
import { fetchApi } from "@/lib/api";
import type { NutritionDay } from "@/lib/types";

export function useNutritionData(from: string, to: string) {
  const [data, setData] = useState<NutritionDay[] | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [prevKey, setPrevKey] = useState(`${from}-${to}`);

  const key = `${from}-${to}`;
  if (prevKey !== key) {
    setPrevKey(key);
    setLoading(true);
    setError(null);
  }

  useEffect(() => {
    let cancelled = false;

    fetchApi<NutritionDay[]>(`/api/nutrition?from_date=${from}&to_date=${to}`)
      .then((result) => {
        if (!cancelled) {
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
  }, [from, to]);

  return { data, loading, error };
}
```

- [ ] **Step 5.3: Create body composition hook**

Create `apps/web/src/lib/hooks/use-body-composition.ts`:

```typescript
"use client";

import { useEffect, useState } from "react";
import { fetchApi } from "@/lib/api";
import type { BodyCompositionDay } from "@/lib/types";

export function useBodyComposition(from: string, to: string) {
  const [data, setData] = useState<BodyCompositionDay[] | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [prevKey, setPrevKey] = useState(`${from}-${to}`);

  const key = `${from}-${to}`;
  if (prevKey !== key) {
    setPrevKey(key);
    setLoading(true);
    setError(null);
  }

  useEffect(() => {
    let cancelled = false;

    fetchApi<BodyCompositionDay[]>(`/api/body-composition?from_date=${from}&to_date=${to}`)
      .then((result) => {
        if (!cancelled) {
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
  }, [from, to]);

  return { data, loading, error };
}
```

- [ ] **Step 5.4: Verify frontend compiles**

```bash
cd apps/web && pnpm build 2>&1 | head -20
```

Expected: No TypeScript errors (build may warn about unused types, that's fine).

- [ ] **Step 5.5: Commit**

```bash
cd apps/web && git add src/lib/types.ts src/lib/hooks/use-nutrition-data.ts src/lib/hooks/use-body-composition.ts && git commit -m "feat(web): add nutrition and body composition types and hooks"
```

---

## Task 6: Nutrición Page Shell + Sidebar Nav

**Files:**
- Create: `apps/web/src/app/(dashboard)/nutricion/page.tsx`
- Create: `apps/web/src/components/nutricion/nutricion-page.tsx`
- Modify: `apps/web/src/components/layout/sidebar.tsx`

- [ ] **Step 6.1: Create route page**

Create `apps/web/src/app/(dashboard)/nutricion/page.tsx`:

```tsx
import { NutricionPageClient } from "@/components/nutricion/nutricion-page";

export const dynamic = "force-dynamic";

export default function NutricionPage() {
  return <NutricionPageClient />;
}
```

- [ ] **Step 6.2: Create page shell with date controls**

Create `apps/web/src/components/nutricion/nutricion-page.tsx`:

```tsx
"use client";

import { useState } from "react";
import Link from "next/link";
import { ArrowLeft } from "lucide-react";
import { useNutritionData } from "@/lib/hooks/use-nutrition-data";
import { useBodyComposition } from "@/lib/hooks/use-body-composition";

function defaultFrom(monthsBack: number): string {
  const d = new Date();
  d.setMonth(d.getMonth() - monthsBack);
  return d.toISOString().split("T")[0];
}

function defaultFromWeeks(weeksBack: number): string {
  const d = new Date();
  d.setDate(d.getDate() - weeksBack * 7);
  return d.toISOString().split("T")[0];
}

function today(): string {
  return new Date().toISOString().split("T")[0];
}

const PRESETS = [
  { label: "1W", weeks: 1 },
  { label: "1M", months: 1 },
  { label: "3M", months: 3 },
  { label: "6M", months: 6 },
  { label: "1Y", months: 12 },
];

function ChartError({ onRetry }: { onRetry: () => void }) {
  return (
    <div className="flex flex-col items-center justify-center py-8">
      <p className="text-xs text-whoop-text-muted">Could not load data</p>
      <button onClick={onRetry} className="mt-2 text-xs text-whoop-blue hover:underline">
        Retry
      </button>
    </div>
  );
}

function ChartSkeleton({ height = "h-[200px]" }: { height?: string }) {
  return (
    <div className="rounded-xl border border-whoop-border bg-whoop-card p-4">
      <div className={`${height} animate-pulse rounded bg-whoop-surface`} />
    </div>
  );
}

export function NutricionPageClient() {
  const [from, setFrom] = useState(() => defaultFrom(1));
  const [to, setTo] = useState(today);
  const [activePreset, setActivePreset] = useState("1M");

  const nutrition = useNutritionData(from, to);
  const bodyComp = useBodyComposition(from, to);

  const applyPreset = (preset: typeof PRESETS[number]) => {
    const newFrom = preset.weeks
      ? defaultFromWeeks(preset.weeks)
      : defaultFrom(preset.months!);
    setFrom(newFrom);
    setTo(today());
    setActivePreset(preset.label);
  };

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

          <div className="flex items-center gap-2">
            {PRESETS.map((p) => (
              <button
                key={p.label}
                onClick={() => applyPreset(p)}
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

        {/* Main grid: charts left, summary right */}
        <div className="flex flex-col gap-4 md:flex-row">
          {/* Left: charts */}
          <div className="flex flex-1 flex-col gap-4 md:w-3/4">
            {nutrition.loading ? (
              <>
                <ChartSkeleton height="h-[200px]" />
                <ChartSkeleton height="h-[120px]" />
                <ChartSkeleton height="h-[40px]" />
              </>
            ) : nutrition.error ? (
              <div className="rounded-xl border border-whoop-border bg-whoop-card p-4">
                <ChartError onRetry={() => setFrom((f) => f)} />
              </div>
            ) : (
              <>
                {/* Calories chart — Task 7 */}
                <div className="rounded-xl border border-whoop-border bg-whoop-card p-4">
                  <p className="text-xs text-whoop-text-muted">Calories chart placeholder</p>
                </div>
                {/* Macro chart — Task 8 */}
                <div className="rounded-xl border border-whoop-border bg-whoop-card p-4">
                  <p className="text-xs text-whoop-text-muted">Macro chart placeholder</p>
                </div>
                {/* Alcohol strip — Task 9 */}
                <div className="rounded-xl border border-whoop-border bg-whoop-card p-4">
                  <p className="text-xs text-whoop-text-muted">Alcohol strip placeholder</p>
                </div>
              </>
            )}

            {/* Weight/BF chart */}
            {bodyComp.loading ? (
              <ChartSkeleton height="h-[200px]" />
            ) : bodyComp.error ? (
              <div className="rounded-xl border border-whoop-border bg-whoop-card p-4">
                <ChartError onRetry={() => setFrom((f) => f)} />
              </div>
            ) : (
              <div className="rounded-xl border border-whoop-border bg-whoop-card p-4">
                <p className="text-xs text-whoop-text-muted">Weight/BF chart placeholder</p>
              </div>
            )}
          </div>

          {/* Right: summary sidebar */}
          <div className="flex flex-col gap-4 md:w-1/4">
            <div className="rounded-xl border border-whoop-border bg-whoop-card p-4">
              <p className="text-xs text-whoop-text-muted">Summary sidebar placeholder</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
```

- [ ] **Step 6.3: Add nav item to sidebar**

In `apps/web/src/components/layout/sidebar.tsx`, add the import:

```typescript
import { Activity, Target, UtensilsCrossed } from "lucide-react";
```

And add to the `navItems` array:

```typescript
const navItems = [
  { href: "/", icon: Target, label: "Plan" },
  { href: "/aerobico", icon: Activity, label: "Aeróbico" },
  { href: "/nutricion", icon: UtensilsCrossed, label: "Nutrición" },
] as const;
```

- [ ] **Step 6.4: Verify the page loads**

```bash
cd apps/web && pnpm dev &
sleep 5
curl -s http://localhost:3000/nutricion | head -5
kill %1
```

Expected: HTML response (the page renders with placeholders).

- [ ] **Step 6.5: Commit**

```bash
git add apps/web/src/app/\(dashboard\)/nutricion/page.tsx apps/web/src/components/nutricion/nutricion-page.tsx apps/web/src/components/layout/sidebar.tsx && git commit -m "feat(web): add nutricion page shell with date controls and sidebar nav"
```

---

## Task 7: Calories Chart

**Files:**
- Create: `apps/web/src/components/nutricion/calories-chart.tsx`
- Modify: `apps/web/src/components/nutricion/nutricion-page.tsx`

- [ ] **Step 7.1: Create calories chart component**

Create `apps/web/src/components/nutricion/calories-chart.tsx`:

```tsx
"use client";

import { useEffect, useRef } from "react";
import {
  createChart,
  type IChartApi,
  ColorType,
  HistogramSeries as HistogramSeriesDef,
  LineSeries as LineSeriesDef,
} from "lightweight-charts";
import type { NutritionDay } from "@/lib/types";

interface CaloriesChartProps {
  data: NutritionDay[];
}

function compute7dMA(data: NutritionDay[]): { time: string; value: number }[] {
  const sorted = [...data].sort((a, b) => a.date.localeCompare(b.date));
  const result: { time: string; value: number }[] = [];
  for (let i = 0; i < sorted.length; i++) {
    const windowStart = Math.max(0, i - 6);
    let sum = 0;
    let count = 0;
    for (let j = windowStart; j <= i; j++) {
      if (sorted[j].calories != null) {
        sum += sorted[j].calories!;
        count++;
      }
    }
    if (count > 0) {
      result.push({ time: sorted[i].date, value: Math.round(sum / count) });
    }
  }
  return result;
}

export function CaloriesChart({ data }: CaloriesChartProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const chartRef = useRef<IChartApi | null>(null);

  useEffect(() => {
    if (!containerRef.current || data.length === 0) return;

    const chart = createChart(containerRef.current, {
      width: containerRef.current.clientWidth,
      height: 200,
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

    const sorted = [...data].sort((a, b) => a.date.localeCompare(b.date));

    // Determine the goal (use the most common non-null goal value)
    const goals = sorted.map((d) => d.calories_goal).filter((g): g is number => g != null);
    const goalValue = goals.length > 0 ? goals[goals.length - 1] : null;

    // Daily calorie bars — green if ≤ goal, red if > goal
    const barSeries = chart.addSeries(HistogramSeriesDef, {
      title: "Calories",
    });
    barSeries.setData(
      sorted
        .filter((d) => d.calories != null)
        .map((d) => ({
          time: d.date,
          value: d.calories!,
          color:
            goalValue != null && d.calories! > goalValue
              ? "#ef4444"
              : "#00d68f",
        })),
    );

    // Goal line
    if (goalValue != null) {
      const goalSeries = chart.addSeries(LineSeriesDef, {
        color: "#f97316",
        lineWidth: 1,
        lineStyle: 2, // dashed
        title: "Goal",
        crosshairMarkerVisible: false,
      });
      goalSeries.setData(
        sorted
          .filter((d) => d.calories != null)
          .map((d) => ({ time: d.date, value: goalValue })),
      );
    }

    // 7-day moving average
    const maSeries = chart.addSeries(LineSeriesDef, {
      color: "#4da6ff",
      lineWidth: 1,
      title: "7d avg",
      crosshairMarkerVisible: false,
    });
    maSeries.setData(compute7dMA(sorted));

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
        Calories vs Goal
        <span className="ml-2 text-xs font-normal text-whoop-text-muted">
          bars · goal (orange) · 7d avg (blue)
        </span>
      </h2>
      {data.length === 0 ? (
        <div className="py-8 text-center text-xs text-whoop-text-muted">No calorie data</div>
      ) : (
        <div ref={containerRef} />
      )}
    </div>
  );
}
```

- [ ] **Step 7.2: Wire into nutricion-page.tsx**

In `apps/web/src/components/nutricion/nutricion-page.tsx`, add the import:

```tsx
import { CaloriesChart } from "./calories-chart";
```

Replace the calories placeholder:

```tsx
{/* Calories chart — Task 7 */}
<div className="rounded-xl border border-whoop-border bg-whoop-card p-4">
  <p className="text-xs text-whoop-text-muted">Calories chart placeholder</p>
</div>
```

With:

```tsx
<CaloriesChart data={nutrition.data!} />
```

- [ ] **Step 7.3: Verify it compiles**

```bash
cd apps/web && pnpm build 2>&1 | tail -5
```

Expected: Build succeeds.

- [ ] **Step 7.4: Commit**

```bash
git add apps/web/src/components/nutricion/calories-chart.tsx apps/web/src/components/nutricion/nutricion-page.tsx && git commit -m "feat(web): add calories vs goal chart with 7d moving average"
```

---

## Task 8: Macro Stacked Chart

**Files:**
- Create: `apps/web/src/components/nutricion/macro-stacked-chart.tsx`
- Modify: `apps/web/src/components/nutricion/nutricion-page.tsx`

- [ ] **Step 8.1: Create macro stacked chart component**

Create `apps/web/src/components/nutricion/macro-stacked-chart.tsx`:

```tsx
"use client";

import { useMemo, useState } from "react";
import type { NutritionDay } from "@/lib/types";

interface MacroStackedChartProps {
  data: NutritionDay[];
}

interface DayMacro {
  date: string;
  protein_pct: number;
  carbs_pct: number;
  fat_pct: number;
  protein_g: number;
  carbs_g: number;
  fat_g: number;
}

const COLORS = {
  protein: "#4da6ff",
  carbs: "#00d68f",
  fat: "#f97316",
};

export function MacroStackedChart({ data }: MacroStackedChartProps) {
  const [hoveredIndex, setHoveredIndex] = useState<number | null>(null);

  const days = useMemo(() => {
    const sorted = [...data].sort((a, b) => a.date.localeCompare(b.date));
    return sorted
      .filter((d) => d.protein_g != null && d.carbs_g != null && d.fat_g != null)
      .map((d): DayMacro => {
        const p = d.protein_g!;
        const c = d.carbs_g!;
        const f = d.fat_g!;
        const total = p + c + f;
        if (total === 0) {
          return { date: d.date, protein_pct: 0, carbs_pct: 0, fat_pct: 0, protein_g: 0, carbs_g: 0, fat_g: 0 };
        }
        return {
          date: d.date,
          protein_pct: (p / total) * 100,
          carbs_pct: (c / total) * 100,
          fat_pct: (f / total) * 100,
          protein_g: p,
          carbs_g: c,
          fat_g: f,
        };
      });
  }, [data]);

  if (days.length === 0) {
    return (
      <div className="rounded-xl border border-whoop-border bg-whoop-card p-4">
        <h2 className="mb-3 text-sm font-semibold text-whoop-text">Macro Split</h2>
        <div className="py-8 text-center text-xs text-whoop-text-muted">No macro data</div>
      </div>
    );
  }

  const barWidth = Math.max(2, Math.min(12, Math.floor(600 / days.length) - 1));
  const gap = 1;
  const svgWidth = days.length * (barWidth + gap);
  const svgHeight = 120;
  const hovered = hoveredIndex != null ? days[hoveredIndex] : null;

  return (
    <div className="rounded-xl border border-whoop-border bg-whoop-card p-4">
      <h2 className="mb-3 text-sm font-semibold text-whoop-text">
        Macro Split
        <span className="ml-2 text-xs font-normal text-whoop-text-muted">
          <span style={{ color: COLORS.protein }}>■</span> P{" "}
          <span style={{ color: COLORS.carbs }}>■</span> C{" "}
          <span style={{ color: COLORS.fat }}>■</span> F
        </span>
      </h2>

      {hovered && (
        <div className="mb-2 text-xs text-whoop-text-muted">
          {hovered.date}:{" "}
          <span style={{ color: COLORS.protein }}>P {Math.round(hovered.protein_g)}g ({hovered.protein_pct.toFixed(0)}%)</span>{" · "}
          <span style={{ color: COLORS.carbs }}>C {Math.round(hovered.carbs_g)}g ({hovered.carbs_pct.toFixed(0)}%)</span>{" · "}
          <span style={{ color: COLORS.fat }}>F {Math.round(hovered.fat_g)}g ({hovered.fat_pct.toFixed(0)}%)</span>
        </div>
      )}

      <div className="overflow-x-auto">
        <svg
          width={svgWidth}
          height={svgHeight}
          viewBox={`0 0 ${svgWidth} ${svgHeight}`}
          className="block"
        >
          {days.map((d, i) => {
            const x = i * (barWidth + gap);
            const proteinH = (d.protein_pct / 100) * svgHeight;
            const carbsH = (d.carbs_pct / 100) * svgHeight;
            const fatH = (d.fat_pct / 100) * svgHeight;
            return (
              <g
                key={d.date}
                onMouseEnter={() => setHoveredIndex(i)}
                onMouseLeave={() => setHoveredIndex(null)}
                style={{ cursor: "crosshair" }}
              >
                {/* Protein (top) */}
                <rect x={x} y={0} width={barWidth} height={proteinH} fill={COLORS.protein} />
                {/* Carbs (middle) */}
                <rect x={x} y={proteinH} width={barWidth} height={carbsH} fill={COLORS.carbs} />
                {/* Fat (bottom) */}
                <rect x={x} y={proteinH + carbsH} width={barWidth} height={fatH} fill={COLORS.fat} />
              </g>
            );
          })}
        </svg>
      </div>
    </div>
  );
}
```

- [ ] **Step 8.2: Wire into nutricion-page.tsx**

Add import:

```tsx
import { MacroStackedChart } from "./macro-stacked-chart";
```

Replace the macro placeholder with:

```tsx
<MacroStackedChart data={nutrition.data!} />
```

- [ ] **Step 8.3: Verify it compiles**

```bash
cd apps/web && pnpm build 2>&1 | tail -5
```

Expected: Build succeeds.

- [ ] **Step 8.4: Commit**

```bash
git add apps/web/src/components/nutricion/macro-stacked-chart.tsx apps/web/src/components/nutricion/nutricion-page.tsx && git commit -m "feat(web): add daily macro split stacked bar chart"
```

---

## Task 9: Alcohol Strip

**Files:**
- Create: `apps/web/src/components/nutricion/alcohol-strip.tsx`
- Modify: `apps/web/src/components/nutricion/nutricion-page.tsx`

- [ ] **Step 9.1: Create alcohol strip component**

Create `apps/web/src/components/nutricion/alcohol-strip.tsx`:

```tsx
"use client";

import { useMemo } from "react";
import type { NutritionDay } from "@/lib/types";

interface AlcoholStripProps {
  data: NutritionDay[];
}

function getISOWeek(dateStr: string): string {
  const d = new Date(dateStr + "T00:00:00");
  d.setDate(d.getDate() + 3 - ((d.getDay() + 6) % 7));
  const yearStart = new Date(d.getFullYear(), 0, 4);
  const weekNo = Math.ceil(
    ((d.getTime() - yearStart.getTime()) / 86400000 + yearStart.getDay() + 1) / 7,
  );
  return `${d.getFullYear()}-W${String(weekNo).padStart(2, "0")}`;
}

export function AlcoholStrip({ data }: AlcoholStripProps) {
  const sorted = useMemo(
    () => [...data].sort((a, b) => a.date.localeCompare(b.date)),
    [data],
  );

  if (sorted.length === 0) {
    return (
      <div className="rounded-xl border border-whoop-border bg-whoop-card p-4">
        <h2 className="mb-3 text-sm font-semibold text-whoop-text">Alcohol</h2>
        <div className="py-4 text-center text-xs text-whoop-text-muted">No data</div>
      </div>
    );
  }

  const dotSize = Math.max(6, Math.min(12, Math.floor(600 / sorted.length) - 2));
  const gap = 2;
  const svgHeight = 24;
  const cy = svgHeight / 2;

  // Detect week boundaries
  const weekBoundaries: number[] = [];
  for (let i = 1; i < sorted.length; i++) {
    if (getISOWeek(sorted[i].date) !== getISOWeek(sorted[i - 1].date)) {
      weekBoundaries.push(i);
    }
  }

  const svgWidth = sorted.length * (dotSize + gap);

  return (
    <div className="rounded-xl border border-whoop-border bg-whoop-card p-4">
      <h2 className="mb-3 text-sm font-semibold text-whoop-text">
        Alcohol
        <span className="ml-2 text-xs font-normal text-whoop-text-muted">
          <span style={{ color: "#f97316" }}>●</span> drink day{" · "}
          <span style={{ color: "#333" }}>●</span> none{" · "}
          <span style={{ color: "#444" }}>|</span> week
        </span>
      </h2>

      <div className="overflow-x-auto">
        <svg
          width={svgWidth}
          height={svgHeight}
          viewBox={`0 0 ${svgWidth} ${svgHeight}`}
          className="block"
        >
          {/* Week boundary lines */}
          {weekBoundaries.map((idx) => {
            const x = idx * (dotSize + gap) - gap / 2;
            return (
              <line
                key={`wb-${idx}`}
                x1={x}
                y1={0}
                x2={x}
                y2={svgHeight}
                stroke="#444"
                strokeWidth={1}
              />
            );
          })}

          {/* Dots */}
          {sorted.map((d, i) => {
            const cx = i * (dotSize + gap) + dotSize / 2;
            const hasDrinks = (d.alcohol_drinks ?? 0) > 0;
            return (
              <circle
                key={d.date}
                cx={cx}
                cy={cy}
                r={dotSize / 2}
                fill={hasDrinks ? "#f97316" : "#333"}
              >
                <title>
                  {d.date}: {d.alcohol_drinks ?? 0} drink{(d.alcohol_drinks ?? 0) !== 1 ? "s" : ""}
                </title>
              </circle>
            );
          })}
        </svg>
      </div>
    </div>
  );
}
```

- [ ] **Step 9.2: Wire into nutricion-page.tsx**

Add import:

```tsx
import { AlcoholStrip } from "./alcohol-strip";
```

Replace the alcohol placeholder with:

```tsx
<AlcoholStrip data={nutrition.data!} />
```

- [ ] **Step 9.3: Verify it compiles**

```bash
cd apps/web && pnpm build 2>&1 | tail -5
```

Expected: Build succeeds.

- [ ] **Step 9.4: Commit**

```bash
git add apps/web/src/components/nutricion/alcohol-strip.tsx apps/web/src/components/nutricion/nutricion-page.tsx && git commit -m "feat(web): add daily alcohol strip with week boundaries"
```

---

## Task 10: Weight & Body Fat Chart

**Files:**
- Create: `apps/web/src/components/nutricion/weight-bf-chart.tsx`
- Modify: `apps/web/src/components/nutricion/nutricion-page.tsx`

- [ ] **Step 10.1: Create weight/BF chart component**

Create `apps/web/src/components/nutricion/weight-bf-chart.tsx`:

```tsx
"use client";

import { useEffect, useRef } from "react";
import {
  createChart,
  type IChartApi,
  ColorType,
  LineSeries as LineSeriesDef,
} from "lightweight-charts";
import type { BodyCompositionDay } from "@/lib/types";

interface WeightBFChartProps {
  data: BodyCompositionDay[];
}

export function WeightBFChart({ data }: WeightBFChartProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const chartRef = useRef<IChartApi | null>(null);

  useEffect(() => {
    if (!containerRef.current || data.length === 0) return;

    const chart = createChart(containerRef.current, {
      width: containerRef.current.clientWidth,
      height: 200,
      layout: {
        background: { type: ColorType.Solid, color: "#1a1a1a" },
        textColor: "#888888",
      },
      grid: {
        vertLines: { color: "#2a2a2a" },
        horzLines: { color: "#2a2a2a" },
      },
      crosshair: { mode: 0 },
      rightPriceScale: { borderColor: "#2a2a2a", visible: true },
      leftPriceScale: { borderColor: "#2a2a2a", visible: true },
      timeScale: { borderColor: "#2a2a2a" },
    });
    chartRef.current = chart;

    const sorted = [...data].sort((a, b) => a.date.localeCompare(b.date));

    const weightSeries = chart.addSeries(LineSeriesDef, {
      color: "#4da6ff",
      lineWidth: 2,
      priceScaleId: "left",
      title: "Weight (kg)",
    });
    weightSeries.setData(
      sorted.filter((d) => d.weight_kg != null).map((d) => ({ time: d.date, value: d.weight_kg! })),
    );

    const bfSeries = chart.addSeries(LineSeriesDef, {
      color: "#f97316",
      lineWidth: 2,
      priceScaleId: "right",
      title: "Body Fat (%)",
    });
    bfSeries.setData(
      sorted.filter((d) => d.body_fat_pct != null).map((d) => ({ time: d.date, value: d.body_fat_pct! })),
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
        Weight & Body Fat
        <span className="ml-2 text-xs font-normal text-whoop-text-muted">
          weight (blue) · body fat (orange)
        </span>
      </h2>
      {data.length === 0 ? (
        <div className="py-8 text-center text-xs text-whoop-text-muted">No body composition data</div>
      ) : (
        <div ref={containerRef} />
      )}
    </div>
  );
}
```

- [ ] **Step 10.2: Wire into nutricion-page.tsx**

Add import:

```tsx
import { WeightBFChart } from "./weight-bf-chart";
```

Replace the weight/BF placeholder with:

```tsx
<WeightBFChart data={bodyComp.data!} />
```

- [ ] **Step 10.3: Verify it compiles**

```bash
cd apps/web && pnpm build 2>&1 | tail -5
```

Expected: Build succeeds.

- [ ] **Step 10.4: Commit**

```bash
git add apps/web/src/components/nutricion/weight-bf-chart.tsx apps/web/src/components/nutricion/nutricion-page.tsx && git commit -m "feat(web): add weight and body fat dual-axis chart"
```

---

## Task 11: Summary Sidebar

**Files:**
- Create: `apps/web/src/components/nutricion/summary-sidebar.tsx`
- Modify: `apps/web/src/components/nutricion/nutricion-page.tsx`

- [ ] **Step 11.1: Create summary sidebar component**

Create `apps/web/src/components/nutricion/summary-sidebar.tsx`:

```tsx
"use client";

import { useMemo } from "react";
import type { NutritionDay, BodyCompositionDay } from "@/lib/types";

interface SummarySidebarProps {
  nutrition: NutritionDay[];
  bodyComp: BodyCompositionDay[];
}

const ALCOHOL_LIMIT = 3;

function getISOWeekKey(dateStr: string): string {
  const d = new Date(dateStr + "T00:00:00");
  d.setDate(d.getDate() + 3 - ((d.getDay() + 6) % 7));
  const yearStart = new Date(d.getFullYear(), 0, 4);
  const weekNo = Math.ceil(
    ((d.getTime() - yearStart.getTime()) / 86400000 + yearStart.getDay() + 1) / 7,
  );
  return `${d.getFullYear()}-W${String(weekNo).padStart(2, "0")}`;
}

function getCurrentISOWeekKey(): string {
  return getISOWeekKey(new Date().toISOString().split("T")[0]);
}

function alcoholColor(count: number): string {
  if (count >= ALCOHOL_LIMIT) return "#ef4444";
  if (count === 2) return "#eab308";
  return "#00d68f";
}

export function SummarySidebar({ nutrition, bodyComp }: SummarySidebarProps) {
  const stats = useMemo(() => {
    const withCal = nutrition.filter((d) => d.calories != null);
    const avgCal = withCal.length > 0
      ? Math.round(withCal.reduce((s, d) => s + d.calories!, 0) / withCal.length)
      : null;

    const goals = withCal.filter((d) => d.calories_goal != null);
    const avgGoal = goals.length > 0
      ? Math.round(goals.reduce((s, d) => s + d.calories_goal!, 0) / goals.length)
      : null;

    const onTarget = avgGoal != null
      ? withCal.filter((d) => d.calories! <= (d.calories_goal ?? Infinity)).length
      : 0;
    const pctOnTarget = withCal.length > 0 ? Math.round((onTarget / withCal.length) * 100) : 0;
    const avgDeficit = avgCal != null && avgGoal != null ? avgCal - avgGoal : null;

    // Macros
    const withMacros = nutrition.filter(
      (d) => d.protein_g != null && d.carbs_g != null && d.fat_g != null,
    );
    const avgProtein = withMacros.length > 0
      ? Math.round(withMacros.reduce((s, d) => s + d.protein_g!, 0) / withMacros.length)
      : null;
    const avgCarbs = withMacros.length > 0
      ? Math.round(withMacros.reduce((s, d) => s + d.carbs_g!, 0) / withMacros.length)
      : null;
    const avgFat = withMacros.length > 0
      ? Math.round(withMacros.reduce((s, d) => s + d.fat_g!, 0) / withMacros.length)
      : null;
    const macroTotal = (avgProtein ?? 0) + (avgCarbs ?? 0) + (avgFat ?? 0);
    const proteinPct = macroTotal > 0 ? Math.round(((avgProtein ?? 0) / macroTotal) * 100) : 0;
    const carbsPct = macroTotal > 0 ? Math.round(((avgCarbs ?? 0) / macroTotal) * 100) : 0;
    const fatPct = macroTotal > 0 ? Math.round(((avgFat ?? 0) / macroTotal) * 100) : 0;

    // Alcohol by week
    const weekMap = new Map<string, number>();
    for (const d of nutrition) {
      if (d.alcohol_drinks == null) continue;
      const wk = getISOWeekKey(d.date);
      weekMap.set(wk, (weekMap.get(wk) ?? 0) + d.alcohol_drinks);
    }
    const weeks = [...weekMap.entries()].sort((a, b) => a[0].localeCompare(b[0]));
    const currentWeekKey = getCurrentISOWeekKey();
    const currentWeekDrinks = weekMap.get(currentWeekKey) ?? 0;
    const weeksUnderLimit = weeks.filter(([, c]) => c < ALCOHOL_LIMIT).length;

    // Body comp
    const sortedBC = [...bodyComp]
      .filter((d) => d.weight_kg != null || d.body_fat_pct != null)
      .sort((a, b) => a.date.localeCompare(b.date));
    const firstBC = sortedBC[0];
    const lastBC = sortedBC[sortedBC.length - 1];
    const currentWeight = lastBC?.weight_kg ?? null;
    const currentBF = lastBC?.body_fat_pct ?? null;
    const weightDelta = firstBC?.weight_kg != null && lastBC?.weight_kg != null
      ? lastBC.weight_kg - firstBC.weight_kg
      : null;
    const bfDelta = firstBC?.body_fat_pct != null && lastBC?.body_fat_pct != null
      ? lastBC.body_fat_pct - firstBC.body_fat_pct
      : null;

    return {
      avgCal, avgGoal, avgDeficit, pctOnTarget, totalDays: withCal.length,
      avgProtein, avgCarbs, avgFat, proteinPct, carbsPct, fatPct,
      currentWeekDrinks, weeks, weeksUnderLimit,
      currentWeight, currentBF, weightDelta, bfDelta,
    };
  }, [nutrition, bodyComp]);

  return (
    <div className="flex flex-col gap-4">
      {/* Calories */}
      <div className="rounded-xl border border-whoop-border bg-whoop-card p-4">
        <p className="mb-2 text-[9px] uppercase tracking-wider text-whoop-text-muted">Calories</p>
        <p className="text-2xl font-bold text-whoop-text">
          {stats.avgCal != null ? stats.avgCal.toLocaleString() : "--"}
        </p>
        <p className="text-xs text-whoop-text-muted">avg/day</p>

        {stats.avgDeficit != null && (
          <div className="mt-3 border-t border-whoop-border pt-3">
            <p className="text-[9px] text-whoop-text-muted">
              vs goal ({stats.avgGoal?.toLocaleString()})
            </p>
            <p className={`text-sm font-bold ${stats.avgDeficit <= 0 ? "text-green-400" : "text-red-400"}`}>
              {stats.avgDeficit > 0 ? "+" : ""}{stats.avgDeficit}
            </p>
            <p className="text-xs text-whoop-text-muted">
              avg {stats.avgDeficit <= 0 ? "deficit" : "surplus"}
            </p>
          </div>
        )}

        <div className="mt-3 border-t border-whoop-border pt-3">
          <div className="flex items-center justify-between">
            <span className="text-[9px] text-whoop-text-muted">Days on target</span>
            <span className="text-xs font-bold text-green-400">{stats.pctOnTarget}%</span>
          </div>
          <div className="mt-1 h-1 rounded-full bg-whoop-surface">
            <div
              className="h-1 rounded-full bg-green-400"
              style={{ width: `${stats.pctOnTarget}%` }}
            />
          </div>
        </div>
      </div>

      {/* Macros */}
      <div className="rounded-xl border border-whoop-border bg-whoop-card p-4">
        <p className="mb-2 text-[9px] uppercase tracking-wider text-whoop-text-muted">Avg Macros</p>
        <div className="space-y-2">
          {[
            { label: "Protein", g: stats.avgProtein, pct: stats.proteinPct, color: "#4da6ff" },
            { label: "Carbs", g: stats.avgCarbs, pct: stats.carbsPct, color: "#00d68f" },
            { label: "Fat", g: stats.avgFat, pct: stats.fatPct, color: "#f97316" },
          ].map((m) => (
            <div key={m.label}>
              <div className="flex items-baseline justify-between">
                <span className="text-sm font-bold" style={{ color: m.color }}>
                  {m.g != null ? `${m.g}g` : "--"}
                </span>
                <span className="text-[9px] text-whoop-text-muted">{m.pct}%</span>
              </div>
              <p className="text-[9px] text-whoop-text-muted">{m.label}</p>
            </div>
          ))}
        </div>
      </div>

      {/* Alcohol */}
      <div className="rounded-xl border border-whoop-border bg-whoop-card p-4">
        <p className="mb-2 text-[9px] uppercase tracking-wider text-whoop-text-muted">Alcohol</p>
        <div className="flex items-baseline gap-1">
          <span
            className="text-2xl font-bold"
            style={{ color: alcoholColor(stats.currentWeekDrinks) }}
          >
            {stats.currentWeekDrinks}
          </span>
          <span className="text-xs text-whoop-text-muted">/ {ALCOHOL_LIMIT} this week</span>
        </div>

        {stats.weeks.length > 0 && (
          <div className="mt-3 border-t border-whoop-border pt-3">
            <div className="flex items-center justify-between">
              <span className="text-[9px] text-whoop-text-muted">Weeks in range</span>
              <span className="text-xs font-bold text-green-400">
                {stats.weeksUnderLimit}/{stats.weeks.length}
              </span>
            </div>
            <div className="mt-2 flex flex-wrap gap-1">
              {stats.weeks.map(([wk, count]) => (
                <div
                  key={wk}
                  className="flex h-5 w-5 items-center justify-center rounded text-[8px] font-bold"
                  style={{ backgroundColor: alcoholColor(count), color: count >= ALCOHOL_LIMIT ? "#fff" : "#000" }}
                  title={`${wk}: ${count} drinks`}
                >
                  {count}
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Body comp */}
      <div className="rounded-xl border border-whoop-border bg-whoop-card p-4">
        <p className="mb-2 text-[9px] uppercase tracking-wider text-whoop-text-muted">Body Comp</p>
        <div className="space-y-3">
          <div>
            <div className="flex items-baseline justify-between">
              <span className="text-lg font-bold text-whoop-text">
                {stats.currentWeight != null ? stats.currentWeight.toFixed(1) : "--"}
              </span>
              {stats.weightDelta != null && (
                <span className={`text-xs ${stats.weightDelta <= 0 ? "text-green-400" : "text-red-400"}`}>
                  {stats.weightDelta > 0 ? "↑" : "↓"} {Math.abs(stats.weightDelta).toFixed(1)} kg
                </span>
              )}
            </div>
            <p className="text-[9px] text-whoop-text-muted">Weight (kg)</p>
          </div>
          <div>
            <div className="flex items-baseline justify-between">
              <span className="text-lg font-bold text-whoop-text">
                {stats.currentBF != null ? stats.currentBF.toFixed(1) : "--"}
              </span>
              {stats.bfDelta != null && (
                <span className={`text-xs ${stats.bfDelta <= 0 ? "text-green-400" : "text-red-400"}`}>
                  {stats.bfDelta > 0 ? "↑" : "↓"} {Math.abs(stats.bfDelta).toFixed(1)}%
                </span>
              )}
            </div>
            <p className="text-[9px] text-whoop-text-muted">Body Fat (%)</p>
          </div>
        </div>
      </div>
    </div>
  );
}
```

- [ ] **Step 11.2: Wire into nutricion-page.tsx**

Add import:

```tsx
import { SummarySidebar } from "./summary-sidebar";
```

Replace the summary sidebar placeholder:

```tsx
<div className="rounded-xl border border-whoop-border bg-whoop-card p-4">
  <p className="text-xs text-whoop-text-muted">Summary sidebar placeholder</p>
</div>
```

With:

```tsx
<SummarySidebar
  nutrition={nutrition.data ?? []}
  bodyComp={bodyComp.data ?? []}
/>
```

- [ ] **Step 11.3: Verify it compiles**

```bash
cd apps/web && pnpm build 2>&1 | tail -5
```

Expected: Build succeeds.

- [ ] **Step 11.4: Commit**

```bash
git add apps/web/src/components/nutricion/summary-sidebar.tsx apps/web/src/components/nutricion/nutricion-page.tsx && git commit -m "feat(web): add nutrition summary sidebar with KPI cards"
```

---

## Task 12: Final Integration & Polish

**Files:**
- Modify: `apps/web/src/components/nutricion/nutricion-page.tsx` (remove remaining placeholders)

- [ ] **Step 12.1: Verify all placeholders are replaced**

Read through `nutricion-page.tsx` and confirm all placeholder divs have been replaced with actual chart components. After Tasks 7-11, the page should have:
- `<CaloriesChart>` 
- `<MacroStackedChart>`
- `<AlcoholStrip>`
- `<WeightBFChart>`
- `<SummarySidebar>`

- [ ] **Step 12.2: Run full frontend build**

```bash
cd apps/web && pnpm build
```

Expected: Build succeeds with no errors.

- [ ] **Step 12.3: Run full backend test suite**

```bash
cd apps/sync && uv run pytest tests/ -v
```

Expected: All tests pass.

- [ ] **Step 12.4: Run lint**

```bash
cd apps/sync && uv run ruff check app/ tests/ && cd ../web && pnpm lint
```

Expected: No lint errors.

- [ ] **Step 12.5: Final commit if any cleanup was needed**

```bash
git add -A && git commit -m "chore: final nutrition tab integration cleanup"
```

Only if there were changes to commit.

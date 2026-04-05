# Adaptive Calorie Targets Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the flat MFP calorie goal with an adaptive daily target that smooths exercise calories across the week, carries over yesterday's excess/deficit, and pre-loads before long runs.

**Architecture:** New pure-function service (`calorie_target.py`) computes targets from pre-fetched data dicts. The nutrition router batch-fetches data for the full date range and calls the service per-day iteratively (since each day's target feeds the next). Frontend swaps the flat goal line for a per-day adaptive target line.

**Tech Stack:** Python/FastAPI (backend), lightweight-charts (frontend chart), SQLAlchemy queries, pytest with SQLite in-memory.

**Spec:** `docs/superpowers/specs/2026-04-05-adaptive-calorie-targets-design.md`

---

## File Map

| Action | File | Responsibility |
|--------|------|---------------|
| Create | `apps/sync/app/services/calorie_target.py` | Pure computation: `compute_adaptive_target()` and batch helper `compute_adaptive_targets_batch()` |
| Create | `apps/sync/tests/test_calorie_target.py` | Unit tests for the calorie target computation |
| Modify | `apps/sync/app/schemas/nutrition.py` | Add `calories_target_adaptive` field |
| Modify | `apps/sync/app/routers/nutrition.py` | Batch-compute and attach adaptive targets |
| Modify | `apps/sync/app/routers/plan.py:107-110` | Use adaptive target for Calories strip metric |
| Modify | `apps/sync/tests/test_plan_router.py` | Update test expectations for adaptive target |
| Modify | `apps/web/src/lib/types.ts:113-125` | Add `calories_target_adaptive` to `NutritionDay` |
| Modify | `apps/web/src/components/nutricion/calories-chart.tsx:64-102` | Use per-day adaptive target line instead of flat goal |

---

### Task 1: Core computation — base + exercise adjustment

**Files:**
- Create: `apps/sync/app/services/calorie_target.py`
- Create: `apps/sync/tests/test_calorie_target.py`

- [ ] **Step 1: Write failing tests for base and exercise factors**

In `apps/sync/tests/test_calorie_target.py`:

```python
from app.services.calorie_target import compute_adaptive_target, CalorieTargetConfig


def test_rest_day_returns_base():
    """No exercise today, no 7d history -> just base."""
    config = CalorieTargetConfig()
    result = compute_adaptive_target(
        config=config,
        today_active_cal=0,
        prev_7d_active_cals=[],
        yesterday_consumed=None,
        yesterday_target=None,
        tomorrow_has_long_run=False,
    )
    assert result == 1500  # 1800 - 300


def test_exercise_today_adds_half():
    """600 cal exercise today, no 7d history -> base + 0.5*600 = 1800."""
    config = CalorieTargetConfig()
    result = compute_adaptive_target(
        config=config,
        today_active_cal=600,
        prev_7d_active_cals=[],
        yesterday_consumed=None,
        yesterday_target=None,
        tomorrow_has_long_run=False,
    )
    assert result == 1800  # 1500 + 300


def test_exercise_7d_avg_adds_fraction():
    """No exercise today, 7d avg of 400 -> base + 0.3*400 = 1620."""
    config = CalorieTargetConfig()
    result = compute_adaptive_target(
        config=config,
        today_active_cal=0,
        prev_7d_active_cals=[400, 400, 400, 400, 400, 400, 400],
        yesterday_consumed=None,
        yesterday_target=None,
        tomorrow_has_long_run=False,
    )
    assert result == 1620  # 1500 + 120


def test_exercise_combined_today_and_avg():
    """800 cal today, 7d avg of 500 -> base + 0.5*800 + 0.3*500 = 2050."""
    config = CalorieTargetConfig()
    result = compute_adaptive_target(
        config=config,
        today_active_cal=800,
        prev_7d_active_cals=[500, 500, 500, 500, 500, 500, 500],
        yesterday_consumed=None,
        yesterday_target=None,
        tomorrow_has_long_run=False,
    )
    assert result == 2050  # 1500 + 400 + 150
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd C:/Code/garmin-personal/apps/sync && uv run pytest tests/test_calorie_target.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'app.services.calorie_target'`

- [ ] **Step 3: Implement CalorieTargetConfig and compute_adaptive_target**

In `apps/sync/app/services/calorie_target.py`:

```python
from dataclasses import dataclass


@dataclass
class CalorieTargetConfig:
    sedentary: int = 1800
    deficit: int = 300
    exercise_today_weight: float = 0.5
    exercise_avg_weight: float = 0.3
    excess_carryover: float = 0.5
    preload_bonus: int = 200
    preload_threshold_sec: int = 7200
    floor: int = 1200


def compute_adaptive_target(
    config: CalorieTargetConfig,
    today_active_cal: int,
    prev_7d_active_cals: list[int],
    yesterday_consumed: int | None,
    yesterday_target: int | None,
    tomorrow_has_long_run: bool,
) -> int:
    """Compute the adaptive calorie target for a single day.

    All DB access happens outside this function — it receives pre-fetched data.
    """
    base = config.sedentary - config.deficit

    # Factor 2: smoothed exercise add-back
    avg_7d = (
        sum(prev_7d_active_cals) / len(prev_7d_active_cals)
        if prev_7d_active_cals
        else 0
    )
    exercise_adj = (
        config.exercise_today_weight * today_active_cal
        + config.exercise_avg_weight * avg_7d
    )

    # Factor 3: yesterday's excess/deficit carry-over
    excess_adj = 0.0
    if yesterday_consumed is not None and yesterday_target is not None:
        excess_adj = -config.excess_carryover * (yesterday_consumed - yesterday_target)

    # Factor 4: tomorrow pre-load
    preload_adj = config.preload_bonus if tomorrow_has_long_run else 0

    target = base + exercise_adj + excess_adj + preload_adj
    return max(config.floor, round(target))
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd C:/Code/garmin-personal/apps/sync && uv run pytest tests/test_calorie_target.py -v`
Expected: 4 tests PASS

- [ ] **Step 5: Commit**

```bash
git add apps/sync/app/services/calorie_target.py apps/sync/tests/test_calorie_target.py
git commit -m "feat(sync): add adaptive calorie target core computation"
```

---

### Task 2: Excess carry-over, preload, and floor tests

**Files:**
- Modify: `apps/sync/tests/test_calorie_target.py`

- [ ] **Step 1: Write failing tests for factors 3, 4, and floor**

Append to `apps/sync/tests/test_calorie_target.py`:

```python
def test_excess_carryover_overate():
    """Overate 200 yesterday -> today -100."""
    config = CalorieTargetConfig()
    result = compute_adaptive_target(
        config=config,
        today_active_cal=0,
        prev_7d_active_cals=[],
        yesterday_consumed=1700,
        yesterday_target=1500,
        tomorrow_has_long_run=False,
    )
    assert result == 1400  # 1500 + 0 - 100 + 0


def test_excess_carryover_underate():
    """Underate 200 yesterday -> today +100."""
    config = CalorieTargetConfig()
    result = compute_adaptive_target(
        config=config,
        today_active_cal=0,
        prev_7d_active_cals=[],
        yesterday_consumed=1300,
        yesterday_target=1500,
        tomorrow_has_long_run=False,
    )
    assert result == 1600  # 1500 + 0 + 100 + 0


def test_excess_carryover_skipped_when_no_data():
    """Missing yesterday data -> no carry-over."""
    config = CalorieTargetConfig()
    result = compute_adaptive_target(
        config=config,
        today_active_cal=0,
        prev_7d_active_cals=[],
        yesterday_consumed=None,
        yesterday_target=None,
        tomorrow_has_long_run=False,
    )
    assert result == 1500


def test_preload_before_long_run():
    """Tomorrow has a long run -> +200."""
    config = CalorieTargetConfig()
    result = compute_adaptive_target(
        config=config,
        today_active_cal=0,
        prev_7d_active_cals=[],
        yesterday_consumed=None,
        yesterday_target=None,
        tomorrow_has_long_run=True,
    )
    assert result == 1700  # 1500 + 200


def test_floor_enforced():
    """Large overeating yesterday still can't push below floor."""
    config = CalorieTargetConfig()
    result = compute_adaptive_target(
        config=config,
        today_active_cal=0,
        prev_7d_active_cals=[],
        yesterday_consumed=2500,
        yesterday_target=1500,
        tomorrow_has_long_run=False,
    )
    assert result == 1200  # floor; raw would be 1500 - 500 = 1000


def test_all_factors_combined():
    """All four factors active at once."""
    config = CalorieTargetConfig()
    result = compute_adaptive_target(
        config=config,
        today_active_cal=600,
        prev_7d_active_cals=[400, 400, 400, 400, 400, 400, 400],
        yesterday_consumed=1800,
        yesterday_target=1700,
        tomorrow_has_long_run=True,
    )
    # base=1500, ex=0.5*600+0.3*400=420, excess=-0.5*100=-50, preload=200
    assert result == 2070


def test_custom_config():
    """Custom config overrides defaults."""
    config = CalorieTargetConfig(sedentary=2000, deficit=200, exercise_today_weight=0.4)
    result = compute_adaptive_target(
        config=config,
        today_active_cal=500,
        prev_7d_active_cals=[],
        yesterday_consumed=None,
        yesterday_target=None,
        tomorrow_has_long_run=False,
    )
    assert result == 2000  # (2000-200) + 0.4*500 = 1800 + 200 = 2000
```

- [ ] **Step 2: Run tests to verify they pass**

Run: `cd C:/Code/garmin-personal/apps/sync && uv run pytest tests/test_calorie_target.py -v`
Expected: All 12 tests PASS (the implementation from Task 1 already handles these cases)

- [ ] **Step 3: Commit**

```bash
git add apps/sync/tests/test_calorie_target.py
git commit -m "test(sync): add excess, preload, floor, and combined tests for calorie target"
```

---

### Task 3: Batch computation helper and config loader

**Files:**
- Modify: `apps/sync/app/services/calorie_target.py`
- Modify: `apps/sync/tests/test_calorie_target.py`

- [ ] **Step 1: Write failing test for batch computation**

Append to `apps/sync/tests/test_calorie_target.py`:

```python
from datetime import date, timedelta

from app.services.calorie_target import compute_adaptive_targets_batch


def test_batch_computes_iteratively():
    """Batch computes targets for a date range, chaining excess carry-over."""
    config = CalorieTargetConfig()
    base_date = date(2026, 3, 10)

    # active_cals: keyed by date
    active_cals = {
        base_date - timedelta(days=i): 300
        for i in range(1, 8)  # 7 days prior: all 300
    }
    active_cals[base_date] = 600  # day 1: exercise
    active_cals[base_date + timedelta(days=1)] = 0  # day 2: rest

    # consumed: day 1 overate by 200 vs expected target
    consumed = {base_date: 2200}

    # planned long runs: none
    long_run_dates: set[date] = set()

    dates = [base_date, base_date + timedelta(days=1)]
    results = compute_adaptive_targets_batch(
        config=config,
        dates=dates,
        active_cals=active_cals,
        consumed=consumed,
        long_run_dates=long_run_dates,
    )

    assert len(results) == 2
    # Day 1: base=1500, ex=0.5*600+0.3*300=390, excess=0 (no prev target), preload=0
    assert results[base_date] == 1890
    # Day 2: base=1500, ex=0.5*0+0.3*avg(300*6+600)/7=0.3*343~103, 
    #   excess=-0.5*(2200-1890)=-155, preload=0
    #   = 1500+103-155 = 1448
    day2_prev7 = [300, 300, 300, 300, 300, 300, 600]
    day2_avg = sum(day2_prev7) / 7
    day2_ex = 0.5 * 0 + 0.3 * day2_avg
    day2_excess = -0.5 * (2200 - 1890)
    expected_day2 = max(1200, round(1500 + day2_ex + day2_excess))
    assert results[base_date + timedelta(days=1)] == expected_day2
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd C:/Code/garmin-personal/apps/sync && uv run pytest tests/test_calorie_target.py::test_batch_computes_iteratively -v`
Expected: FAIL — `ImportError: cannot import name 'compute_adaptive_targets_batch'`

- [ ] **Step 3: Implement compute_adaptive_targets_batch and load_calorie_config**

Add to `apps/sync/app/services/calorie_target.py`:

```python
from datetime import date, timedelta

from sqlalchemy.orm import Session

from app.models import DailySummary, NutritionDaily
from app.models.tp_planned_workout import TPPlannedWorkout
from app.models.user_goal import UserGoal


def load_calorie_config(db: Session) -> CalorieTargetConfig:
    """Load calorie target config from user_goals, falling back to defaults."""
    goals = (
        db.query(UserGoal)
        .filter(UserGoal.category == "calorie_target")
        .all()
    )
    overrides = {g.metric_key: g.target_value for g in goals}
    defaults = CalorieTargetConfig()
    return CalorieTargetConfig(
        sedentary=int(overrides.get("sedentary_calories", defaults.sedentary)),
        deficit=int(overrides.get("calorie_deficit", defaults.deficit)),
        exercise_today_weight=overrides.get("exercise_today_weight", defaults.exercise_today_weight),
        exercise_avg_weight=overrides.get("exercise_avg_weight", defaults.exercise_avg_weight),
        excess_carryover=overrides.get("excess_carryover", defaults.excess_carryover),
        preload_bonus=int(overrides.get("preload_bonus", defaults.preload_bonus)),
        preload_threshold_sec=int(overrides.get("preload_threshold_sec", defaults.preload_threshold_sec)),
        floor=int(overrides.get("calorie_floor", defaults.floor)),
    )


def compute_adaptive_targets_batch(
    config: CalorieTargetConfig,
    dates: list[date],
    active_cals: dict[date, int],
    consumed: dict[date, int],
    long_run_dates: set[date],
) -> dict[date, int]:
    """Compute adaptive targets for a list of dates, chaining excess carry-over."""
    results: dict[date, int] = {}
    prev_target: int | None = None

    for d in sorted(dates):
        today_active = active_cals.get(d, 0)
        prev_7d = [
            active_cals.get(d - timedelta(days=i), 0)
            for i in range(1, 8)
        ]

        yesterday = d - timedelta(days=1)
        yesterday_consumed = consumed.get(yesterday)
        yesterday_target = prev_target  # from previous iteration

        tomorrow = d + timedelta(days=1)
        tomorrow_long = tomorrow in long_run_dates

        target = compute_adaptive_target(
            config=config,
            today_active_cal=today_active,
            prev_7d_active_cals=prev_7d,
            yesterday_consumed=yesterday_consumed,
            yesterday_target=yesterday_target,
            tomorrow_has_long_run=tomorrow_long,
        )
        results[d] = target
        prev_target = target

    return results


def fetch_and_compute_targets(
    db: Session,
    from_date: date,
    to_date: date,
) -> dict[date, int]:
    """Fetch all needed data from DB and compute adaptive targets for a date range."""
    config = load_calorie_config(db)

    # Batch-fetch active calories: [from_date - 7 .. to_date]
    cal_start = from_date - timedelta(days=7)
    daily_rows = (
        db.query(DailySummary.date, DailySummary.calories_active)
        .filter(DailySummary.date >= cal_start, DailySummary.date <= to_date)
        .all()
    )
    active_cals = {r.date: r.calories_active or 0 for r in daily_rows}

    # Batch-fetch consumed: [from_date - 1 .. to_date]
    nutr_rows = (
        db.query(NutritionDaily.date, NutritionDaily.calories)
        .filter(NutritionDaily.date >= from_date - timedelta(days=1), NutritionDaily.date <= to_date)
        .all()
    )
    consumed = {r.date: r.calories for r in nutr_rows if r.calories is not None}

    # Batch-fetch planned long runs: [from_date .. to_date + 1]
    planned_rows = (
        db.query(TPPlannedWorkout.date)
        .filter(
            TPPlannedWorkout.date >= from_date,
            TPPlannedWorkout.date <= to_date + timedelta(days=1),
            TPPlannedWorkout.duration_sec_planned > config.preload_threshold_sec,
        )
        .all()
    )
    long_run_dates = {r.date for r in planned_rows}

    # Build date list
    days = []
    d = from_date
    while d <= to_date:
        days.append(d)
        d += timedelta(days=1)

    return compute_adaptive_targets_batch(config, days, active_cals, consumed, long_run_dates)
```

Move the existing imports (`from dataclasses import dataclass`) to the top and add the new ones. The full import block at the top of the file should be:

```python
from dataclasses import dataclass
from datetime import date, timedelta

from sqlalchemy.orm import Session

from app.models import DailySummary, NutritionDaily
from app.models.tp_planned_workout import TPPlannedWorkout
from app.models.user_goal import UserGoal
```

- [ ] **Step 4: Run all calorie target tests**

Run: `cd C:/Code/garmin-personal/apps/sync && uv run pytest tests/test_calorie_target.py -v`
Expected: All 13 tests PASS

- [ ] **Step 5: Commit**

```bash
git add apps/sync/app/services/calorie_target.py apps/sync/tests/test_calorie_target.py
git commit -m "feat(sync): add batch computation and DB fetch for adaptive calorie targets"
```

---

### Task 4: Add adaptive target to nutrition API response

**Files:**
- Modify: `apps/sync/app/schemas/nutrition.py`
- Modify: `apps/sync/app/routers/nutrition.py`

- [ ] **Step 1: Add field to schema**

In `apps/sync/app/schemas/nutrition.py`, add after the `alcohol_drinks` field:

```python
    calories_target_adaptive: int | None = None
```

- [ ] **Step 2: Modify nutrition router to compute and attach targets**

Replace the full contents of `apps/sync/app/routers/nutrition.py` with:

```python
from datetime import date, timedelta

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import NutritionDaily
from app.schemas.nutrition import NutritionResponse
from app.services.calorie_target import fetch_and_compute_targets

router = APIRouter(prefix="/api/nutrition", tags=["nutrition"])


@router.get("", response_model=list[NutritionResponse])
def list_nutrition(
    from_date: date = Query(default_factory=lambda: date.today() - timedelta(days=30)),
    to_date: date = Query(default_factory=lambda: date.today()),
    db: Session = Depends(get_db),
):
    rows = (
        db.query(NutritionDaily)
        .filter(NutritionDaily.date >= from_date, NutritionDaily.date <= to_date)
        .order_by(NutritionDaily.date.desc())
        .all()
    )

    targets = fetch_and_compute_targets(db, from_date, to_date)

    results = []
    for row in rows:
        resp = NutritionResponse.model_validate(row)
        resp.calories_target_adaptive = targets.get(row.date)
        results.append(resp)
    return results
```

- [ ] **Step 3: Run existing tests to check nothing breaks**

Run: `cd C:/Code/garmin-personal/apps/sync && uv run pytest tests/ -v --tb=short`
Expected: All existing tests PASS

- [ ] **Step 4: Commit**

```bash
git add apps/sync/app/schemas/nutrition.py apps/sync/app/routers/nutrition.py
git commit -m "feat(sync): attach adaptive calorie target to nutrition API response"
```

---

### Task 5: Use adaptive target in plan strip

**Files:**
- Modify: `apps/sync/app/routers/plan.py:107-110`
- Modify: `apps/sync/tests/test_plan_router.py`

- [ ] **Step 1: Update plan strip to use adaptive target**

In `apps/sync/app/routers/plan.py`, add import at the top with the other imports:

```python
from app.services.calorie_target import fetch_and_compute_targets
```

Replace lines 107-110 (the calorie target block in `_build_strip`):

```python
    # Calories — prefer MFP daily goal, fall back to user_goals
    cal_val = nutrition.calories if nutrition else None
    cal_goal = nutrition.calories_goal if nutrition and nutrition.calories_goal else None
    cal_target = cal_goal or _goal_val(goals, "calories")
```

With:

```python
    # Calories — use adaptive target, fall back to MFP goal, then user_goals
    cal_val = nutrition.calories if nutrition else None
    adaptive_targets = fetch_and_compute_targets(db, target_date, target_date)
    cal_target_adaptive = adaptive_targets.get(target_date)
    cal_goal = nutrition.calories_goal if nutrition and nutrition.calories_goal else None
    cal_target = cal_target_adaptive or cal_goal or _goal_val(goals, "calories")
```

- [ ] **Step 2: Update test expectations**

In `apps/sync/tests/test_plan_router.py`, the test `test_plan_daily_calories_show_consumed_and_target` currently expects `target="2,200"` (from UserGoal). With the adaptive target, the value will be `1,500` (base with no exercise data and no prior day). Update the test:

In `test_plan_daily_calories_show_consumed_and_target`, replace:

```python
    assert cal["target"] == "2,200"
    assert cal["pct"] == 65  # 1420/2200 ~ 64.5 -> 65
```

With:

```python
    assert cal["target"] == "1,500"
    assert cal["pct"] == 95  # 1420/1500 ~ 94.7 -> 95
```

- [ ] **Step 3: Run plan router tests**

Run: `cd C:/Code/garmin-personal/apps/sync && uv run pytest tests/test_plan_router.py -v`
Expected: All 3 tests PASS

- [ ] **Step 4: Run full test suite**

Run: `cd C:/Code/garmin-personal/apps/sync && uv run pytest tests/ -v --tb=short`
Expected: All tests PASS

- [ ] **Step 5: Commit**

```bash
git add apps/sync/app/routers/plan.py apps/sync/tests/test_plan_router.py
git commit -m "feat(sync): use adaptive calorie target in plan strip"
```

---

### Task 6: Frontend — update types and calories chart

**Files:**
- Modify: `apps/web/src/lib/types.ts:113-125`
- Modify: `apps/web/src/components/nutricion/calories-chart.tsx`

- [ ] **Step 1: Add field to NutritionDay type**

In `apps/web/src/lib/types.ts`, in the `NutritionDay` interface, add after `alcohol_drinks`:

```typescript
  calories_target_adaptive: number | null;
```

- [ ] **Step 2: Update CaloriesChart to use per-day adaptive target**

In `apps/web/src/components/nutricion/calories-chart.tsx`, replace lines 65-102 (the sorted const through the goal line block) with:

```typescript
    const sorted = [...data].sort((a, b) => a.date.localeCompare(b.date));

    // Daily calorie bars — green if ≤ adaptive target, red if > adaptive target
    const barSeries = chart.addSeries(HistogramSeriesDef, {
      title: "Calories",
    });
    barSeries.setData(
      sorted
        .filter((d) => d.calories != null)
        .map((d) => {
          const target = d.calories_target_adaptive ?? d.calories_goal;
          return {
            time: d.date,
            value: d.calories!,
            color:
              target != null && d.calories! > target
                ? "#ef4444"
                : "#00d68f",
          };
        }),
    );

    // Adaptive target line (per-day, varies)
    const targetData = sorted
      .filter((d) => d.calories_target_adaptive != null)
      .map((d) => ({ time: d.date, value: d.calories_target_adaptive! }));
    if (targetData.length > 0) {
      const targetSeries = chart.addSeries(LineSeriesDef, {
        color: "#f97316",
        lineWidth: 1,
        title: "Target",
        crosshairMarkerVisible: false,
      });
      targetSeries.setData(targetData);
    }
```

- [ ] **Step 3: Update chart heading**

In the same file, replace the subtitle span:

```typescript
        bars · goal (orange) · 7d avg (blue)
```

With:

```typescript
        bars · target (orange) · 7d avg (blue)
```

- [ ] **Step 4: Build frontend to verify no type errors**

Run: `cd C:/Code/garmin-personal/apps/web && pnpm build 2>&1 | tail -20`
Expected: Build succeeds with no errors

- [ ] **Step 5: Commit**

```bash
git add apps/web/src/lib/types.ts apps/web/src/components/nutricion/calories-chart.tsx
git commit -m "feat(web): display per-day adaptive calorie target in chart"
```

---

### Task 7: Integration test — nutrition endpoint with adaptive targets

**Files:**
- Create: `apps/sync/tests/test_nutrition_router.py`

- [ ] **Step 1: Write integration test**

In `apps/sync/tests/test_nutrition_router.py`:

```python
from datetime import date, timedelta

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app
from app.models import DailySummary, NutritionDaily
from app.models.tp_planned_workout import TPPlannedWorkout

engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestSession = sessionmaker(bind=engine)


def setup_module():
    Base.metadata.create_all(engine)


def teardown_module():
    Base.metadata.drop_all(engine)


def _db():
    session = TestSession()
    try:
        yield session
    finally:
        session.rollback()
        session.close()


def _client():
    app.dependency_overrides[get_db] = _db
    c = TestClient(app)
    yield c
    app.dependency_overrides.clear()


def test_nutrition_returns_adaptive_target():
    session = TestSession()
    target = date(2026, 4, 1)

    # Seed 7 days of daily summaries with varying exercise
    for i in range(8):
        d = target - timedelta(days=7 - i)
        active = 600 if i % 2 == 0 else 100
        session.add(DailySummary(date=d, calories_active=active))

    # Seed nutrition for today
    session.add(NutritionDaily(date=target, calories=1800))
    session.commit()

    app.dependency_overrides[get_db] = lambda: (yield session) if False else None

    # Use a proper override
    def override():
        yield session

    app.dependency_overrides[get_db] = override

    client = TestClient(app)
    resp = client.get(f"/api/nutrition?from_date={target}&to_date={target}")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    row = data[0]
    assert "calories_target_adaptive" in row
    assert row["calories_target_adaptive"] is not None
    assert isinstance(row["calories_target_adaptive"], int)
    # Should be > base (1500) because there's exercise data
    assert row["calories_target_adaptive"] > 1500

    app.dependency_overrides.clear()
    session.rollback()
    session.close()


def test_nutrition_adaptive_target_with_long_run_tomorrow():
    session = TestSession()
    target = date(2026, 4, 2)
    tomorrow = target + timedelta(days=1)

    session.add(DailySummary(date=target, calories_active=0))
    session.add(NutritionDaily(date=target, calories=1500))
    # Planned long run tomorrow (3 hours)
    session.add(TPPlannedWorkout(
        tp_workout_id="test-123",
        date=tomorrow,
        title="Long run",
        duration_sec_planned=10800,
    ))
    session.commit()

    def override():
        yield session

    app.dependency_overrides[get_db] = override
    client = TestClient(app)
    resp = client.get(f"/api/nutrition?from_date={target}&to_date={target}")
    data = resp.json()
    row = data[0]
    # Should include preload bonus (+200)
    assert row["calories_target_adaptive"] == 1700  # base 1500 + preload 200

    app.dependency_overrides.clear()
    session.rollback()
    session.close()
```

- [ ] **Step 2: Run integration tests**

Run: `cd C:/Code/garmin-personal/apps/sync && uv run pytest tests/test_nutrition_router.py -v`
Expected: 2 tests PASS

- [ ] **Step 3: Run full test suite**

Run: `cd C:/Code/garmin-personal/apps/sync && uv run pytest tests/ -v --tb=short`
Expected: All tests PASS

- [ ] **Step 4: Commit**

```bash
git add apps/sync/tests/test_nutrition_router.py
git commit -m "test(sync): add integration tests for nutrition endpoint with adaptive targets"
```

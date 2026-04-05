# Adaptive Daily Calorie Targets

## Problem

The current calorie goal comes from MyFitnessPal as a flat value (1,500 on rest days) that spikes wildly on exercise days (up to 3,952). This creates a range of 1,500-3,952 that's hard to follow in practice. The target should distribute exercise calories more smoothly across the week and account for yesterday's over/undereating and tomorrow's long runs.

## Formula

```
target = max(FLOOR, base + exercise_adj + excess_adj + preload_adj)
```

### Factor 1: Base

```
base = SEDENTARY - DEFICIT    (1800 - 300 = 1500)
```

SEDENTARY is the user's BMR + daily activity. DEFICIT is the configurable weight-loss cut below sedentary.

### Factor 2: Smoothed exercise add-back

```
exercise_adj = 0.5 * today_active_cal + 0.3 * avg_7d_active_cal
```

- `today_active_cal`: `DailySummary.calories_active` for today (0 if no data yet)
- `avg_7d_active_cal`: mean of `DailySummary.calories_active` over the previous 7 days (not including today)

This adds back ~80% of exercise calories total, but smoothed: big workout days are dampened and rest days get a carry-over from the rolling average. Validated against real data: produces avg target of 2,134 vs current MFP avg of 2,087.

### Factor 3: Yesterday's excess/deficit carry-over

```
excess_adj = -0.5 * (yesterday_consumed - yesterday_target)
```

- Overate 200 yesterday -> today -100
- Underate 200 yesterday -> today +100
- Only applies when yesterday has both `nutrition_daily.calories` and a computed target
- Skipped (0) when data is missing

Self-correcting: overeating automatically tightens the next day, undereating loosens it.

### Factor 4: Tomorrow pre-load

```
preload_adj = 200   if tomorrow has a planned run > 2h
              0     otherwise
```

Checked via `TPPlannedWorkout` for tomorrow's date where `duration_sec_planned > 7200`. Allows slightly more intake the night before a long run for glycogen loading.

### Floor

```
FLOOR = 1200
```

Target never drops below this regardless of adjustments.

## Configurable Constants

Stored in the `user_goals` table with `category = 'calorie_target'`:

| metric_key | Default | Description |
|---|---|---|
| `sedentary_calories` | 1800 | BMR + daily activity baseline |
| `calorie_deficit` | 300 | Below-sedentary cut for weight loss |
| `exercise_today_weight` | 0.5 | Fraction of today's exercise added back |
| `exercise_avg_weight` | 0.3 | Fraction of 7d avg exercise added back |
| `excess_carryover` | 0.5 | How much of yesterday's over/under carries |
| `preload_bonus` | 200 | Extra kcal before long runs |
| `preload_threshold_sec` | 7200 | Min planned duration to trigger preload |
| `calorie_floor` | 1200 | Absolute minimum target |

## Implementation

### Backend

**New function** in `app/services/calorie_target.py`:

```python
def compute_adaptive_target(db: Session, target_date: date) -> int | None
```

Queries:
1. `user_goals` for configurable constants (with defaults)
2. `DailySummary.calories_active` for `target_date` (today's exercise)
3. `DailySummary.calories_active` for the 7 days before `target_date` (rolling avg)
4. `NutritionDaily.calories` for `target_date - 1` (yesterday consumed)
5. Recursively or iteratively compute yesterday's target for the excess adjustment
6. `TPPlannedWorkout` for `target_date + 1` where `duration_sec_planned > threshold`

Returns the computed integer target, or `None` if insufficient data (no daily summaries at all).

**New field on `NutritionResponse`** schema:

```python
calories_target_adaptive: int | None = None
```

**Modified nutrition endpoint** (`app/routers/nutrition.py`): For each date in the response, compute and attach `calories_target_adaptive`. To avoid N+1 queries, batch-fetch the needed data for the full date range.

**Modified plan strip** (`app/routers/plan.py`): Use `calories_target_adaptive` instead of the MFP goal for the Calories strip metric.

### Frontend

**`NutritionDay` type** (`lib/types.ts`): Add `calories_target_adaptive: number | null`.

**`CaloriesChart`** (`components/nutricion/calories-chart.tsx`): Replace the flat goal line with the per-day adaptive target. The goal line becomes a stepped/connected line that varies by day. Bar color comparison uses the adaptive target instead of the static MFP goal.

**Plan strip**: No frontend changes needed if the backend already returns the adaptive value.

### Data flow

```
User requests /api/nutrition?from_date=...&to_date=...
  -> For each date in range:
       1. Load DailySummary.calories_active for [date-7 .. date]
       2. Load NutritionDaily.calories for date-1
       3. Load TPPlannedWorkout for date+1
       4. Compute target with formula
       5. Attach as calories_target_adaptive
  -> Return enriched NutritionResponse list
```

### Performance

The nutrition endpoint typically covers 30-90 days. The calculation needs:
- One query for all DailySummary rows in [from_date - 7 .. to_date] (for exercise data + rolling avg)
- One query for all NutritionDaily rows in [from_date - 1 .. to_date] (for yesterday's consumed)
- One query for all TPPlannedWorkout rows in [from_date .. to_date + 1] (for preload)

Three queries total regardless of date range size — no N+1 concern.

### Yesterday's target (recursive dependency)

Factor 3 needs yesterday's target to compute today's excess adjustment. This creates a chain: to know today's target, you need yesterday's, which needs the day before, etc.

Resolution: Compute targets iteratively from `from_date - 1` forward. Each day's target feeds into the next day's excess calculation. The first day in the window uses `excess_adj = 0` (no carry-over).

## Validation

Simulated against 15 days of real data (Mar 1-15, 2026):

| Metric | Formula | Current MFP |
|---|---|---|
| Avg daily target | 2,134 | 2,087 |
| Min target | 1,741 | 1,500 |
| Max target | 2,706 | 3,952 |
| Std deviation | 289 | ~750 |

Weekly totals are within 3% of the naive `base + full exercise` approach, confirming the formula preserves total energy while smoothing distribution.

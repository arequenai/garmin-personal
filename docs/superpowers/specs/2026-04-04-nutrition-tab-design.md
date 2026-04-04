# Nutrition Tab Design Spec

**Date**: 2026-04-04
**Status**: Approved

## Overview

A new `/nutricion` page in the web app for tracking daily nutrition, macro composition, alcohol consumption, and body composition trends. Follows the same client-component + hooks pattern as the existing aerobico tab. Layout: Aligned Charts + Summary Sidebar.

## Data Sources

| Metric | Source | Storage |
|--------|--------|---------|
| Calories, protein, carbs, fat, fiber, sodium | MFP via `MFPClient` | `nutrition_daily` table |
| Alcohol drink count | MFP meal entries (keyword match) | New `alcohol_drinks` column on `nutrition_daily` |
| Calories goal, protein goal | MFP via `MFPClient` | `nutrition_daily` table |
| Weight, body fat % | Fitbit via `FitbitClient` | `body_composition` table |

## Page Layout

Two-column layout: time-series charts on the left sharing a daily date axis, period summary KPIs on the right.

```
┌──────────────────────────────────────────────────────────────────┐
│  ← Plan         [1W] [1M] [3M] [6M] [1Y]      [from] [to]     │
├──────────────────────────────────────────┬───────────────────────┤
│  Calories vs Goal                        │  CALORIES             │
│  (daily bars + goal line + 7d MA)        │  avg/day, deficit,    │
│                                          │  % days on target     │
├──────────────────────────────────────────┤                       │
│  Macro Split                             ├───────────────────────┤
│  (daily 100% stacked bars, P/C/F)       │  AVG MACROS           │
│                                          │  P/C/F grams + %      │
├──────────────────────────────────────────┤                       │
│  Alcohol                                 ├───────────────────────┤
│  (daily dot strip: orange=drank,         │  ALCOHOL              │
│   gray=none, week boundary markers)      │  N/3 counter +        │
│                                          │  weekly squares        │
├──────────────────────────────────────────┤                       │
│  Weight & Body Fat                       ├───────────────────────┤
│  (dual-axis line chart)                  │  BODY COMP            │
│                                          │  weight + BF% deltas  │
└──────────────────────────────────────────┴───────────────────────┘
```

- **Default time range**: 1M (one month)
- **Presets**: 1W, 1M, 3M, 6M, 1Y + custom date pickers
- **Left column**: 3/4 width. All charts share the same daily date axis for visual correlation.
- **Right column**: 1/4 width. Period summary KPIs, independent of date axis.
- **Responsive**: On mobile, summary cards collapse into a horizontal scrollable strip above the charts. Charts stack full-width below.

## Chart Specifications

### 1. Calories vs Goal (left column)

- **Type**: Histogram (bars) + line overlays, `lightweight-charts`
- **Bars**: Daily total calories. Color: green when ≤ goal, orange/red when > goal
- **Goal line**: Line series at `calories_goal` value (dashed or distinct color)
- **Trend line**: 7-day moving average of calories (thin, subtle)
- **Axes**: Y = calories, X = dates
- **Tooltip**: Date, calories, goal, delta (surplus/deficit)

### 2. Macro Split (left column)

- **Type**: Daily 100% stacked bar chart
- **Segments**: Protein / Carbs / Fat as percentage of total macro calories
- **Colors**: Protein = blue (#4da6ff), Carbs = green (#00d68f), Fat = orange (#f97316)
- **Y-axis**: 0–100%
- **X-axis**: Dates (aligned with calories chart above)
- **Hover**: Shows grams + percentages for that day
- **Implementation**: Custom SVG component (no Recharts dependency; project only uses `lightweight-charts`)

### 3. Alcohol Strip (left column)

- **Type**: Daily dot strip
- **Dots**: Orange circle on days with alcohol entries, gray circle on days without
- **Week boundaries**: Vertical line separators between ISO weeks
- **Compact**: Shortest chart (~40px height), just a visual marker row
- **Aligned**: Same date axis as calories and macros above

### 4. Weight & Body Fat (left column)

- **Type**: Dual-axis line chart, `lightweight-charts`
- **Left axis**: Weight in kg (line series, blue)
- **Right axis**: Body fat % (line series, orange)
- **Data source**: `body_composition` table (Fitbit sync)
- **Note**: Garmin's `sync_body_composition` also writes to this table but Fitbit sync in `sync_orchestrator.py` runs separately and is the preferred source

## Summary Sidebar Specifications

### Calories Summary

- Average daily calories (large number)
- Average deficit/surplus vs goal (colored: green for deficit, red for surplus)
- % days on target (progress bar)

### Avg Macros Summary

- Protein: grams + percentage (blue)
- Carbs: grams + percentage (green)
- Fat: grams + percentage (orange)
- All averaged over selected period

### Alcohol Summary

- Current week counter: large "N / 3" with color coding (green 0-1, yellow 2, red 3+)
- Weekly compliance squares: one colored square per week in the range
  - Green: under limit (< 3 drinks)
  - Yellow: at limit (2 drinks)
  - Red: over limit (≥ 3 drinks)
  - Each square shows the drink count inside it

### Body Comp Summary

- Current weight (latest in range) + delta over period (arrow + kg change)
- Current body fat % (latest in range) + delta over period (arrow + % change)
- Green = decreased, red = increased

## Backend Changes

### 1. New column on `nutrition_daily`

```python
alcohol_drinks: Mapped[int | None] = mapped_column(Integer, nullable=True)
```

Alembic migration to add the column.

### 2. Extend `MFPClient.get_day()` to include entries

The existing `get_day()` already calls `self._client.get_date()` which returns a `Day` object with `meals` containing `entries`. Extend the method to also extract individual food entry names from the same call (no new API request needed). Return them alongside the existing totals dict, e.g., add an `"entries"` key with a list of `{"name": str, "meal": str}`.

### 3. Alcohol detection in `sync_nutrition`

After fetching daily totals and entries, count alcohol drinks:

```python
ALCOHOL_KEYWORDS = [...]  # Determined by one-time LLM analysis of historical data

def _count_alcohol_drinks(entries: list[dict]) -> int:
    count = 0
    for entry in entries:
        name = entry["name"].lower()
        if any(kw in name for kw in ALCOHOL_KEYWORDS):
            count += 1
    return count
```

The keyword list is hardcoded after a one-time discovery step (see below).

### 4. New API endpoint: Body Composition

```python
# routers/body_composition.py
GET /api/body-composition?from_date=&to_date=
```

Returns list of `{date, weight_kg, body_fat_pct}` from the `body_composition` table.

### 5. Update `NutritionResponse` schema

Add `alcohol_drinks: int | None` to the Pydantic response model.

## Frontend Changes

### 1. New route

`apps/web/src/app/(dashboard)/nutricion/page.tsx` -- server component wrapper (same pattern as aerobico).

### 2. New components

```
components/nutricion/
  nutricion-page.tsx          # Main client component with date range state
  calories-chart.tsx          # Histogram + goal line + 7d MA
  macro-stacked-chart.tsx     # Daily 100% stacked bar chart (custom SVG)
  alcohol-strip.tsx           # Daily dot strip with week boundaries
  weight-bf-chart.tsx         # Dual-axis line chart
  summary-sidebar.tsx         # Right column with all KPI cards
```

### 3. New hooks

```
lib/hooks/
  use-nutrition-data.ts       # Fetches /api/nutrition?from_date=&to_date=
  use-body-composition.ts     # Fetches /api/body-composition?from_date=&to_date=
```

### 4. New types in `lib/types.ts`

```typescript
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

### 5. Sidebar update

Add "Nutricion" entry to `components/layout/sidebar.tsx` nav items (Lucide icon: `UtensilsCrossed`).

## Alcohol Keyword Discovery (One-Time Task)

Before implementing the sync:

1. Pull last 3 months of MFP meal entries via `MFPClient` for each day
2. Extract all unique food entry names
3. Pass through LLM to classify which are alcoholic beverages
4. Present list to user for review and correction
5. Hardcode final keyword list as `ALCOHOL_KEYWORDS` constant in sync service

## Out of Scope

- Manual food logging (MFP is the source of truth)
- Micronutrient tracking beyond fiber/sodium
- Meal-level breakdown view (only daily totals + alcohol count)
- Editing calorie/macro goals from the UI

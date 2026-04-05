# Workout Detail Drawer — Design Spec

## Overview

Add a click-to-expand detail drawer to the Aerobico tab's Training Calendar. Clicking a workout block (planned or completed) slides open a drawer below the calendar showing full workout detail: coach notes, key metrics, HR/pace zone charts, and best paces. For workouts that have both a planned and completed version, a planned-vs-actual comparison strip is shown.

## Interaction Model

- **Trigger:** Click any workout block in the Training Calendar grid.
- **Drawer position:** Slides up below the calendar card, pushing HR Zones and Weekly Volume charts down. CSS max-height transition (~300ms ease-out).
- **Selection highlight:** The clicked workout block gets a brighter border and subtle glow in its sport color.
- **Close:** Click the same workout again, click the X button, or click a different workout (swaps content in-place, no close/reopen flicker).
- **Data source:** All data served from the local DB (no runtime TP API calls). Drawer fetches `GET /api/aerobico/workout/{tp_workout_id}` on click.

## Completed Workout Drawer

### Header Bar
- Sport-color left accent line (green=run, blue=bike, yellow=hike, etc.)
- Workout title + type badge + date
- Close X button on the right

### Body — Two-Column Layout

**Left column (flex:1) — Coach Notes:**
- "Coach Notes" label in sport color
- Full description text, preserving line breaks
- If no description: "No notes" in muted text, column shrinks

**Right column (~200px) — Key Metrics:**
- Distance (km)
- Duration (h:mm)
- Avg Pace (min/km, computed from distance/duration)
- TSS (blue accent)
- IF (Intensity Factor)
- Avg HR / Max HR (red accent)
- Elevation gain (if available)
- Calories

### Charts Row (below both columns, 3 equal sections)

1. **HR Zones** — 5 vertical bars (Z1-Z5) with time labels. Colors: green→blue→yellow→red→crimson. Data from `workout_details_json.timeInHeartRateZones`.
2. **Pace/Speed Zones** — 5 vertical bars (Recovery, Endurance, Steady State, Tempo, Interval) in purple. Data from `workout_details_json.timeInSpeedZones`.
3. **Best Paces by Distance** — Compact list showing 400m, 1km, 5km, 10km paces in min:sec/km. Data from `workout_details_json.meanMaxSpeedsByDistance`. Speed (m/s) converted to pace (min/km).

## Planned Workout Drawer

### Header Bar
- Same layout as completed but with dashed border style and a "PLANNED" badge in muted text.

### Body — Two-Column Layout

**Left column — Coach Notes:**
- Same as completed: full description text

**Right column — Planned Targets:**
- Planned Duration
- Planned Distance
- Planned TSS
- Styled with muted/italic to distinguish from actuals

### Structure Visualization (replaces Charts Row)
- Rendered only when `structure_json` is populated (38 of 155 planned workouts have it).
- Horizontal block diagram using the `polyline` data from `structure_json`:
  - X-axis = relative time (0 to 1)
  - Y-axis = intensity (0 to 1)
  - Blocks colored by `intensityClass`: warmUp (green), active (orange/red depending on intensity), coolDown (blue)
- Labels from structure steps: e.g., "Warm up 15:00", "4x 1500m Hard", "Cool Down 5:00"
- Step details parsed from `structure_json.structure[]`:
  - `type`: "step" or "repetition"
  - `length.unit`: "second", "meter", "repetition"
  - `length.value`: numeric
  - `steps[].name`: "Warm up", "Hard", "Easy", "Cool Down"
  - `steps[].intensityClass`: "warmUp", "active", "coolDown"
  - `steps[].targets[].minValue/maxValue`: RPE range

## Planned vs Actual Comparison

When a completed workout matches a planned workout on the same date (title match logic, case-insensitive — reuses existing `TrainingCalendar` matching), a comparison strip appears between the header and body:

| Metric | Planned | Actual | Delta |
|--------|---------|--------|-------|
| Duration | 1h 20m | 1h 24m | +4min |
| Distance | 13.0 km | 13.2 km | +0.2 km |
| TSS | 90 | 95 | +5 |

Delta color coding:
- Green: actual within ~10% of planned
- Yellow: 10-25% deviation
- Red: >25% deviation

Matching is done server-side in the detail endpoint.

## Backend Changes

### Database Migration

Add column to `tp_completed_workouts`:
```
workout_details_json  JSON  NULLABLE
```

This stores the full response from `TrainingPeaksClient.get_workout_details()`, which includes: `timeInHeartRateZones`, `timeInPowerZones`, `timeInSpeedZones`, `meanMaxHeartRates`, `meanMaxPowers`, `meanMaxSpeeds`, `meanMaxSpeedsByDistance`, `meanMaxCadences`.

### Sync Changes

In `TPSyncService.sync_completed_workouts_range()`, store the full details response:
```python
details = self.tp.get_workout_details(workout_id)
if details:
    values.update(self._extract_zones(details))
    values["workout_details_json"] = details  # NEW
```

### Backfill

Extend the existing zones-backfill pattern (`POST /api/tp/sync/zones-backfill`) to also populate `workout_details_json` for workouts that have zone data but are missing the full details JSON. The backfill fetches `get_workout_details()` for each workout and stores the response.

### New Endpoint

`GET /api/aerobico/workout/{tp_workout_id}?type=completed|planned` — Returns workout detail with optional matched counterpart.

Query param `type` defaults to `completed`. When `type=completed`, looks up in `tp_completed_workouts` and matches a planned workout. When `type=planned`, looks up in `tp_planned_workouts` and matches a completed workout.

Response for a completed workout:
```json
{
  "workout": {
    "tp_workout_id": "3662017630",
    "date": "2026-04-03",
    "title": "Trail - CaCo + 2x20' TEMPO",
    "workout_type": "Run",
    "description": "CaCo 15min easy...",
    "duration_sec": 5044,
    "distance_m": 13244.65,
    "tss": 95.37,
    "intensity_factor": 0.78,
    "avg_hr": 156,
    "max_hr": 174,
    "avg_power": 268.0,
    "calories": 1046,
    "elevation_gain_m": null,
    "workout_details_json": { ... }
  },
  "planned": {
    "tp_workout_id": "...",
    "date": "2026-04-03",
    "title": "Trail - CaCo + 2x20' TEMPO",
    "duration_sec_planned": 4800,
    "distance_m_planned": 13000,
    "tss_planned": 90,
    "description": "...",
    "structure_json": { ... }
  }
}
```

Response for a planned workout: same shape but `workout` contains the planned workout fields and `planned` is null. If a completed workout exists for the same date with matching title, it's included in a `completed` field instead.

Matching logic: same date, case-insensitive title match (existing logic from frontend moved server-side).

### Schema Updates

Add `tp_workout_id` to `CalendarCompletedWorkout` and `CalendarPlannedWorkout` Pydantic schemas so the calendar can reference workouts by ID for the detail fetch.

New Pydantic models:
- `WorkoutDetailResponse` — full completed workout fields + `workout_details_json`
- `WorkoutWithPlannedResponse` — wraps `workout` + optional `planned`

## Frontend Changes

### Type Updates (`lib/types.ts`)

Add `tp_workout_id: string` to `CalendarCompletedWorkout` and `CalendarPlannedWorkout`.

New types:
```typescript
interface WorkoutDetailResponse {
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

interface PlannedWorkoutDetail {
  tp_workout_id: string;
  date: string;
  title: string | null;
  description: string | null;
  duration_sec_planned: number | null;
  distance_m_planned: number | null;
  tss_planned: number | null;
  structure_json: WorkoutStructure | null;
}

interface WorkoutWithPlanned {
  workout: WorkoutDetailResponse;
  planned: PlannedWorkoutDetail | null;
}
```

### Hook (`lib/hooks/use-workout-detail.ts`)

New `useWorkoutDetail(id: string | null)` hook:
- Fetches `GET /api/aerobico/workout/{id}` when id changes
- Caches results by id so re-clicking a previously viewed workout is instant
- Returns `{ data, loading, error }`

### Calendar Changes (`components/aerobico/training-calendar.tsx`)

- Add `selectedWorkoutId` state and `onSelectWorkout` callback
- Pass `tp_workout_id` to `WorkoutBlock`
- `WorkoutBlock` becomes clickable: `cursor-pointer`, onClick sets `selectedWorkoutId`
- Selected block: brighter border + subtle box-shadow glow in sport color
- Existing hover tooltip remains (shows on hover, detail drawer shows on click)

### New Components

**`WorkoutDetailDrawer`** — main drawer container:
- Animated max-height transition
- Skeleton loader while fetching
- Delegates to sub-components based on workout type (completed vs planned)

**`DrawerHeaderBar`** — title row with sport color, type, date, close button

**`DrawerCompletedBody`** — two-column layout: notes left, metrics right

**`DrawerPlannedBody`** — two-column layout: notes left, planned targets right

**`DrawerComparisonStrip`** — planned vs actual delta row (shown when both exist)

**`DrawerHRZones`** — 5-bar HR zone chart from details JSON

**`DrawerPaceZones`** — 5-bar speed zone chart from details JSON

**`DrawerBestPaces`** — best pace by distance list from details JSON

**`DrawerStructureViz`** — planned workout structure block diagram from structure_json polyline + steps

### Integration in `aerobico-page.tsx`

The `TrainingCalendar` lifts the selected workout ID up to `AerobicoPageClient`, which renders `WorkoutDetailDrawer` between the calendar and the HR zones chart.

## Out of Scope

- Lap splits (not available from TP details API without separate file parsing)
- Power curve chart (mean-max power data exists but a chart for it is a separate feature)
- Editing or annotating workouts
- Workout comparison across different dates

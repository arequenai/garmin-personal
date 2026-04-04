# Aerobico Tab — Design Spec

## Overview

A dedicated detail page for aerobic training, inspired by TrainingPeaks. Accessible as a top-level sidebar tab (`/aerobico`) and as a drill-down from the Aerobico pillar on the Plan page. Single scrollable page with a global date range selector and four visualization sections.

## Page Layout

```
┌──────────────────────────────────────────────┐
│  ← Plan                    [3M] [6M] [1Y]   │
│                          from [____] to [____]│
├──────────────────────────────────────────────┤
│                                              │
│            PMC Chart (full width, 350px)      │
│        CTL (blue) / ATL (orange) / TSB (green)│
│                                              │
├──────────────────────┬───────────────────────┤
│                      │                       │
│  Training Calendar   │   HR Zone Distrib.    │
│  (month grid)        │   (horizontal bar)    │
│                      │                       │
├──────────────────────┴───────────────────────┤
│                                              │
│     Weekly Volume (km bars + elev. line)      │
│                                              │
└──────────────────────────────────────────────┘
```

Max width: `max-w-6xl`. Dark theme matching existing `whoop-*` tokens.

## Backend Endpoints

New router: `apps/sync/app/routers/aerobico.py`, prefix `/api/aerobico`.

All endpoints accept `from_date` and `to_date` query parameters (date strings, ISO format). No new database tables — queries existing models only.

### `GET /api/aerobico/pmc`

Returns PMC time series from `TPFitnessData`.

Default range: 12 months back → today.

```json
[
  {"date": "2025-04-05", "ctl": 82.3, "atl": 65.1, "tsb": 17.2, "tss_day": 45.0}
]
```

Ordered by date ascending.

### `GET /api/aerobico/calendar`

Returns planned and completed workouts from `TPPlannedWorkout` and `TPCompletedWorkout`.

Default range: 30 days back → 30 days forward.

```json
{
  "planned": [
    {
      "date": "2026-04-10",
      "title": "Easy Run",
      "workout_type": "run",
      "duration_sec_planned": 3600,
      "tss_planned": 50,
      "distance_m_planned": 10000
    }
  ],
  "completed": [
    {
      "date": "2026-04-03",
      "title": "Intervals",
      "workout_type": "run",
      "tss": 85,
      "distance_m": 12000,
      "duration_sec": 4200
    }
  ]
}
```

### `GET /api/aerobico/volume`

Aggregates Garmin running activities (types: `running`, `trail_running`, `treadmill_running`, `track_running`) by ISO week, summing `distance_m` (converted to km) and `elevation_gain`.

Default range: 12 weeks back → today.

```json
[
  {"week_start": "2026-01-13", "km": 42.5, "elevation_m": 380}
]
```

Ordered by `week_start` ascending.

### `GET /api/aerobico/hr-zones`

Sums HR zone seconds from `TPCompletedWorkout` columns (`hr_zone1_sec` through `hr_zone5_sec`) for all workouts in the date range.

Default range: 4 weeks back → today.

```json
{
  "zone1_sec": 12000,
  "zone2_sec": 28000,
  "zone3_sec": 9500,
  "zone4_sec": 4200,
  "zone5_sec": 1800
}
```

## Frontend Architecture

### File Structure

```
apps/web/src/
  app/(dashboard)/aerobico/page.tsx       # Server component, renders client wrapper
  components/aerobico/
    aerobico-page.tsx                      # "use client" — global date state, layout
    pmc-chart.tsx                          # Lightweight Charts — CTL/ATL/TSB
    training-calendar.tsx                  # Custom month grid — planned/completed
    hr-zone-chart.tsx                      # CSS horizontal stacked bar
    weekly-volume-chart.tsx                # Lightweight Charts — km bars + elev. line
  lib/
    hooks/
      use-aerobic-pmc.ts
      use-aerobic-volume.ts
      use-aerobic-hr-zones.ts
      use-aerobic-calendar.ts
```

### Page Component

`aerobico/page.tsx` is a thin async server component:

```tsx
export const dynamic = "force-dynamic";
export default function AerobicoPage() {
  return <AerobicoPageClient />;
}
```

### Client Wrapper (`aerobico-page.tsx`)

Owns a single global date range state (default: 12 months back → today). Renders:
1. Back link ("← Plan") and date range selector bar with quick presets (3M, 6M, 1Y) and from/to inputs
2. PMC chart (full width)
3. Two-column row: training calendar + HR zone chart
4. Weekly volume chart (full width)

The calendar is independent of the global date range — it has its own month navigation.

### Data Hooks

Each hook lives in `lib/hooks/` and follows the pattern:

```ts
function useAerobicPMC(from: string, to: string): {
  data: PMCDataPoint[] | null;
  loading: boolean;
  error: string | null;
}
```

- Calls `fetchApi` with the date params
- Re-fetches when `from` or `to` change
- Returns `{ data, loading, error }`

The HR zones hook takes the global range but requests only the last 4 weeks within it.

### Chart Components

**`pmc-chart.tsx`** — Lightweight Charts (TradingView library).
- Three line series: CTL (`#4da6ff` blue), ATL (`#f97316` orange), TSB (`#00d68f` green)
- TSB rendered as baseline area series (green fill above zero, red fill below)
- Crosshair tooltip: date, CTL, ATL, TSB, daily TSS
- Pan and zoom enabled
- Height: ~350px, full width
- Dark theme: background `#1a1a1a`, grid `#2a2a2a`, text `#888888`

**`training-calendar.tsx`** — Custom-built with divs, no charting library.
- Month grid with day cells (7 columns, Sun–Sat)
- Month navigation arrows at top
- Completed workouts: solid colored dot (green=run, blue=bike, teal=swim, gray=other)
- Planned workouts (future): dashed ring, same color scheme
- Days with both: solid dot + small planned indicator
- Click day → popover with workout details (title, type, TSS, distance, duration)
- Today cell highlighted
- Independent month navigation, not tied to global date range

**`hr-zone-chart.tsx`** — Pure CSS, no charting library.
- Single horizontal stacked bar: 5 proportional `<div>`s in a flex row
- Zone colors: Z1 `#6b7280` (gray), Z2 `#4da6ff` (blue), Z3 `#00d68f` (green), Z4 `#f97316` (orange), Z5 `#ef4444` (red)
- Legend row below showing each zone's percentage and formatted time (e.g., "Z2 — 48% — 7h 46m")

**`weekly-volume-chart.tsx`** — Lightweight Charts.
- Bar series: weekly km (left Y-axis, `#4da6ff` blue)
- Line series: weekly elevation gain (right Y-axis, `#f97316` orange)
- X-axis: week start dates
- Crosshair tooltip: km + elevation for the week

### Date Range Selector

Rendered at the top of the page. Contains:
- Quick preset buttons: 3M, 6M, 1Y (set `from_date` relative to today)
- Two date inputs (from / to) for manual selection
- Changes trigger re-fetch for PMC, volume, and HR zones. Calendar is unaffected.

## Navigation

### Sidebar

Sidebar is restored with two nav items:
- Plan (`/`) — `Target` icon from Lucide
- Aerobico (`/aerobico`) — `Activity` icon from Lucide

`"use client"` component with `usePathname()` for active state. Desktop sidebar (fixed 72px left) + mobile bottom nav. Same visual style as the original.

### Pillar Link

The Aerobico pillar row on the Plan page (`pillar-row.tsx`) wraps its header in a `<Link href="/aerobico">`. A small chevron-right icon at the far end of the collapsed header hints it's clickable.

### Back Link

The aerobico page shows a subtle "← Plan" link at top-left, linking to `/`.

## Dependencies

**New:** `lightweight-charts` (~40KB) — TradingView's charting library for PMC and volume charts.

**Re-added:** `lucide-react` — for sidebar icons and the back arrow.

## Error Handling

Each chart section is isolated. If one API call fails, others still render. Failed charts show a muted "Could not load data" message with a retry button. Loading state shows a skeleton/spinner per chart.

## Theme

All components use existing `whoop-*` CSS tokens from `globals.css`. No new theme tokens needed. Chart backgrounds match `whoop-card` (`#1a1a1a`), grid lines match `whoop-border` (`#2a2a2a`), text matches `whoop-text-secondary` (`#888888`).

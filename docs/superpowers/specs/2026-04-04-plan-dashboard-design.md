# Plan Estrategico Dashboard — Design Spec

## Overview

Two new views for the garmin-personal dashboard, aligned with the 5-pillar strategic health plan (2026-2036). These views will eventually replace the existing Overview and Daily pages.

- **Daily Dashboard** (`/plan`) — actionable during the day, updated via frequent sync
- **Quarterly Review** (`/plan/quarterly`) — progress tracking per quarter, comparison between quarters, path to 2030 targets

Reference document: `docs/plan-estrategico-salud-2026-2036.md`

---

## 1. Daily Dashboard (`/plan`)

### Layout: Hybrid (top strip + expandable pillar rows)

#### Top Strip — 6 Metric Slots

Horizontal row of 6 cards showing the most actionable numbers. Ordered left-to-right from "what do I do now?" to "how am I today?".

| Slot | Metric | Source | Details |
|------|--------|--------|---------|
| 1 | Calories consumed / target | MFP (frequent sync) | Dual number (e.g., "1,420 / 2,200 kcal") + progress bar |
| 2 | Protein / target | MFP (frequent sync) | Dual number (e.g., "82 / 125 g") + progress bar |
| 3 | Stress last hour | Garmin (frequent sync) | Average stress value for the last 60 min. Secondary line: day avg |
| 4 | HRV | Garmin (daily) | Value in ms + trend arrow (up/down/flat) based on 7-day moving average. Secondary line: 7d avg |
| 5 | TSB | Calculated (daily) | Form value. Secondary line: contextual label ("building load", "fresh", "overreaching") |
| 6 | Sleep | Garmin (daily) | Total hours. Secondary line: deep sleep % |

Slots 1-3 update throughout the day (require frequent sync). Slots 4-6 are set in the morning.

#### Pillar Rows — 5 Expandable Sections

Each pillar is a row with two states:

**Collapsed (default on page load — all 5 start collapsed):**
- Color dot + pillar name (left)
- 3 inline KPIs showing current values (right)
- Chevron (▸) to expand

**Expanded (accordion, one at a time — expanding one collapses the previous):**
- Border takes pillar color
- Chevron rotates (▾)
- 3 KPI cards with: value, target, status (✓/✗), sparkline 7d
- Driver row: 3-4 compact cells with label + value

##### P1 Motor Aerobico (color: #00d68f)

Collapsed KPIs: VO2max, CTL, VT1 pace

Expanded:
- KPI cards: VO2max (48.3, target >52), CTL (62, target >100), VT1 pace (5:35, target <5:00)
- Each with 7d sparkline
- Drivers: km/week, TSS/week, ATL, zone distribution (when available)

##### P2 Durabilidad Muscular (color: #00c4b4)

Collapsed KPIs: Pull-ups max, Deadlift 5RM, Calf raises

Expanded:
- KPI cards: Pull-ups (8, target 15), Deadlift 5RM (90kg, target 103kg), Calf raises (22, target 30)
- Drivers: sessions/week, days since last strength, strength time (hrs)

##### P3 Fueling y Metabolismo (color: #b388ff)

Collapsed KPIs: Weight, Body fat %, Glucose mean

Expanded:
- KPI cards: Weight (68.2, no fixed target), Body fat (trend), Mean glucose (94)
- Drivers: calories avg 7d, protein avg 7d, alcohol units/week (from MFP)

##### P4 Recuperacion (color: #f5c542)

Collapsed KPIs: HRV, Sleep hours, RHR

Expanded:
- KPI cards: Sleep total (7:32, target >7:30), Deep sleep % (18%, target >15%), HRV baseline (52ms, trending)
- Drivers: sleep score, bedtime avg, body battery, stress avg

##### P5 Salud Clinica (color: #ff4d4d)

Collapsed: Screening status, LDL value, next appointment

Expanded:
- KPI table: last values for LDL, HDL, BP, calcium score, FEVI, PSA
- Checklist: upcoming screenings with dates and status
- This pillar is data-sparse (annual/punctual). Expanded view is a reference card, not a daily tracker.

---

## 2. Quarterly Review (`/plan/quarterly`)

### Layout: Cockpit with quarter navigation

#### Quarter Selector

Top bar with left/right arrows to navigate between quarters. Shows:
- Quarter label (e.g., "Q2 2026")
- "CURRENT" badge on active quarter
- Date range and week number (e.g., "Apr 1 — Jun 30, 2026 · Week 1 of 13")

#### Global Progress Bar → 2030

Horizontal bar chart showing % progress toward 2030 targets for each of the 5 pillars. Calculated as the average % completion across all KPIs in the pillar. Gives an instant read on which pillars are ahead/behind.

#### Pillar Sections (all expanded by default)

Each pillar shows:

**KPI Comparison Table:**

| KPI | Q(n-1) | Q(n) current | Delta | Target 2030 |
|-----|--------|-------------|-------|-------------|

- Columns: previous quarter end value, current quarter latest value, delta with arrow, 2030 target
- Color-coded delta: green for improving toward target, red for regressing
- For the current (in-progress) quarter, Q(n) shows the latest value, not an end-of-quarter value

**12-Week Trend Chart:**
- Sparkline/area chart of the pillar's primary KPI over the 12 weeks of the quarter
- Dashed horizontal line at target value for reference
- Only for the current quarter (historical quarters show final values only)

**Quarterly Tests Checklist (where applicable):**
- P1: Drift test, 10K time trial
- P2: Battery test (pull-ups, deadlift, calf raises), deep squat, sit-and-rise
- P3: Waist circumference, CGM cycle
- P4: (no quarterly tests — all from daily tracking)
- P5: Blood pressure measurement
- Each test shows: status (✓ done / ○ pending), date completed (if done)

#### Cross-Quarter Trends

When viewing a non-current quarter, the table still shows Q(n-1) vs Q(n) for that quarter's context. The global progress bar always reflects the latest values regardless of which quarter is selected.

---

## 3. Frequent Sync

### Requirement

The daily dashboard needs near-real-time data for 3 metrics: calories, protein, stress. Current sync runs once daily at 5:00 AM. A secondary frequent sync is needed.

### Design

New scheduler job: `frequent_sync_job()` running every 15 minutes during waking hours (7:00-23:00).

Syncs only:
- **MFP nutrition** (calories, protein, macros) — updates `nutrition_daily` for today
- **Garmin stress data** — updates `daily_summaries.stress_avg` for today, and stores hourly granularity for "last hour" calculation

Does NOT re-sync: sleep, activities, body composition, performance metrics (these stay on the daily 5 AM sync).

### Stress Last Hour

New field or computation needed. Options:
- Store raw stress data points in a new `stress_readings` table (timestamp + value) and compute last-hour avg at query time
- Compute and store `stress_last_hour` in `daily_summaries`, updated each frequent sync

Recommendation: store raw stress data points. More flexible for future use (e.g., stress by time of day charts). The `process_stress_data` function in `calculations.py` already handles raw stress arrays.

### API Changes

New endpoint or modification to existing:
- `GET /api/plan/daily` — returns the full daily dashboard payload (strip metrics + pillar data)
- `GET /api/plan/quarterly?quarter=Q2-2026` — returns quarterly review payload
- The daily endpoint must be fast (<200ms) since it will be polled or loaded frequently

---

## 4. Data Model Changes

### New: `stress_readings` table

| Column | Type | Description |
|--------|------|-------------|
| id | int PK | |
| date | date | FK-like, indexed |
| timestamp | datetime | Exact measurement time |
| value | int | Stress value (1-100, -1=activity, -2=unusable) |

Populated during frequent sync. Used to compute stress_last_hour.

### New: `quarterly_tests` table

| Column | Type | Description |
|--------|------|-------------|
| id | int PK | |
| quarter | str | e.g., "Q2-2026" |
| pillar | str | e.g., "P2" |
| test_name | str | e.g., "battery_test", "deep_squat" |
| result_value | float null | Numeric result if applicable |
| result_text | str null | Text result (e.g., "pass", "fail") |
| completed_at | date null | Date completed, null if pending |

Manual entry via API or settings page.

### New: `clinical_results` table

| Column | Type | Description |
|--------|------|-------------|
| id | int PK | |
| date | date | Date of test/checkup |
| marker | str | e.g., "ldl", "hdl", "blood_pressure_sys", "calcium_score", "fevi" |
| value | float | Numeric value |
| unit | str | e.g., "mg/dL", "mmHg", "%" |
| source | str | e.g., "olympia_2026_03" |

For P5 Salud Clinica. Populated manually. One row per marker per date.

### Existing model changes

- `nutrition_daily`: no changes needed (calories, protein_g already exist)
- `daily_summaries`: no changes needed (stress_avg exists). stress_last_hour computed from stress_readings
- `user_goal`: already exists, will use for calorie and protein targets in the strip

---

## 5. Frontend Architecture

### Route Structure

```
app/(dashboard)/plan/page.tsx          → Daily Dashboard
app/(dashboard)/plan/quarterly/page.tsx → Quarterly Review
```

### Components

```
components/plan/
  daily-strip.tsx         — Top 6 metric cards (client component, polls for updates)
  pillar-row.tsx          — Single pillar collapsed/expanded (client component)
  pillar-accordion.tsx    — Container managing which pillar is expanded
  sparkline-7d.tsx        — Reusable 7-day sparkline SVG
  progress-bar.tsx        — Reusable thin progress bar (cal/protein strip)
  
  quarterly-header.tsx    — Quarter selector with arrows
  quarterly-progress.tsx  — Global 5-pillar progress bars
  quarterly-pillar.tsx    — KPI table + trend chart + tests checklist
  quarterly-tests.tsx     — Tests checklist sub-component
```

### Data Fetching

- Daily: server component fetches initial data, `daily-strip.tsx` polls `/api/plan/daily` every 60 seconds for cal/protein/stress updates (client-side fetch with `setInterval`)
- Quarterly: server component, no polling needed

---

## 6. Scope and Phasing

### Phase 1 (MVP)
- Daily dashboard with top strip (6 metrics) and 5 pillar rows (P1-P4 with real data, P5 static)
- Frequent sync for MFP + stress
- New API endpoint `/api/plan/daily`

### Phase 2
- Quarterly review page
- New tables: `quarterly_tests`, `clinical_results`
- Quarter comparison logic
- New API endpoint `/api/plan/quarterly`
- Manual entry UI for quarterly tests and clinical results

### Phase 3
- P5 Salud Clinica with real clinical data
- Cross-pillar insights (alcohol → HRV correlation)
- Retire old Overview and Daily pages

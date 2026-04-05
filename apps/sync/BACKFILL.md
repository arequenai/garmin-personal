# Production Backfill Runbook

## Prerequisites

1. Deploy the sync fixes (Garmin removed from frequent sync, token persistence added)
2. Wait 24-48 hours for Garmin rate limit (429) to reset
3. Verify Garmin auth works:
   ```bash
   curl -X POST "https://garmin-sync-production-ec24.up.railway.app/api/sync/trigger?days_back=0"
   ```

## Backfill Order

Run these sequentially. Each is a background task — check logs for completion before starting the next.

### 1. TrainingPeaks completed workouts (fastest, no rate limits)

```bash
curl -X POST "https://garmin-sync-production-ec24.up.railway.app/api/tp/sync/workouts-backfill?days_back=365"
```

Pulls completed workouts in 30-day chunks. Takes ~5 min for a year.

### 2. TrainingPeaks HR zones backfill

```bash
curl -X POST "https://garmin-sync-production-ec24.up.railway.app/api/tp/sync/zones-backfill"
```

Re-fetches workout details for all workouts missing HR zone data. Processes in batches of 100.

### 3. Garmin full backfill (after rate limit resets)

```bash
curl -X POST "https://garmin-sync-production-ec24.up.railway.app/api/sync/backfill?days=365"
```

Runs `run_sync_for_date()` for each day: daily summaries, sleep, activities, body comp, race predictions, training readiness, stress, nutrition, and glucose. Each day makes ~10 API calls to Garmin. For 365 days, expect several hours.

**If Garmin returns 429 during backfill**, it will fail for that day and continue to the next. Re-run with a smaller range to fill gaps.

### 4. Verify data

```bash
# Check Garmin daily data count
curl "https://garmin-sync-production-ec24.up.railway.app/api/daily?from_date=2025-04-05&to_date=2026-04-05" | python -m json.tool | head

# Check TP completed workouts
curl "https://garmin-sync-production-ec24.up.railway.app/api/tp/workouts/completed?from_date=2025-04-05&to_date=2026-04-05" | python -m json.tool | head

# Check nutrition
curl "https://garmin-sync-production-ec24.up.railway.app/api/nutrition?from_date=2025-04-05&to_date=2026-04-05" | python -m json.tool | head
```

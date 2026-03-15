"""Nightscout CGM client for fetching glucose entries and computing daily aggregates."""

import logging
from datetime import date, datetime, time, timedelta, timezone

import httpx

logger = logging.getLogger(__name__)


class NightscoutClient:
    def __init__(self, base_url: str, token: str):
        self.base_url = base_url.rstrip("/")
        self.token = token

    def fetch_entries(self, start_date: date, end_date: date | None = None) -> list[dict]:
        """Fetch CGM entries from Nightscout for a date range.

        Calls {base_url}/api/v1/entries.json with token in header and date filters.
        """
        start_ms = int(
            datetime.combine(start_date, time.min, tzinfo=timezone.utc).timestamp() * 1000
        )
        params = {
            "token": self.token,
            "count": 500,
            "find[date][$gte]": start_ms,
        }
        if end_date is not None:
            end_ms = int(
                datetime.combine(end_date, time.min, tzinfo=timezone.utc).timestamp() * 1000
            )
            params["find[date][$lt]"] = end_ms

        try:
            resp = httpx.get(
                f"{self.base_url}/api/v1/entries.json",
                params=params,
                timeout=30,
            )
            resp.raise_for_status()
            return resp.json()
        except Exception:
            logger.warning("Failed to fetch Nightscout entries", exc_info=True)
            return []

    def get_daily_summary(self, target_date: date) -> dict | None:
        """Fetch entries for a single day and compute daily glucose aggregates.

        Returns dict with readings_count, mean_glucose, min_glucose, max_glucose,
        and fasting_glucose (reading at hour==6, or first reading of the day).
        Returns None if no readings found.
        """
        next_day = target_date + timedelta(days=1)
        entries = self.fetch_entries(target_date, end_date=next_day)
        if not entries:
            return None

        # Extract entries with valid sgv (date filtering already done by API)
        readings = []
        for entry in entries:
            sgv = entry.get("sgv")
            if sgv is None:
                continue
            readings.append({"date": entry.get("date", 0), "sgv": sgv})

        if not readings:
            return None

        # Sort by timestamp
        readings.sort(key=lambda r: r["date"])

        sgv_values = [r["sgv"] for r in readings]

        # Fasting glucose: reading closest to hour==6, else first reading
        fasting = None
        for r in readings:
            dt = datetime.fromtimestamp(r["date"] / 1000, tz=timezone.utc)
            if dt.hour == 6:
                fasting = r["sgv"]
                break
        if fasting is None:
            fasting = readings[0]["sgv"]

        return {
            "readings_count": len(sgv_values),
            "mean_glucose": round(sum(sgv_values) / len(sgv_values)),
            "min_glucose": min(sgv_values),
            "max_glucose": max(sgv_values),
            "latest_glucose": readings[-1]["sgv"],
            "fasting_glucose": fasting,
        }

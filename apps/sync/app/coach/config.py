"""Coach config loader.

Pulls heuristic constants from a public Google Sheet CSV. Cached in-memory
with a TTL. Falls back to DEFAULTS on any failure (network, parse, type cast).
"""
from __future__ import annotations

import csv
import io
import logging
import os
import time
from typing import Any

import httpx

logger = logging.getLogger(__name__)

DEFAULTS: dict[str, Any] = {
    "base_kcal": 2400,
    "body_weight_kg": 75,
    "target_sleep_hours": 7.5,
    "protein_g_per_kg": 1.8,
    "sleep_latency_min": 20,
    "dinner_carb_cap_g": 100,
    "dinner_protein_cap_g": 60,
}

TYPES: dict[str, type] = {
    "base_kcal": int,
    "body_weight_kg": int,
    "target_sleep_hours": float,
    "protein_g_per_kg": float,
    "sleep_latency_min": int,
    "dinner_carb_cap_g": int,
    "dinner_protein_cap_g": int,
}

TTL_SECONDS = 3600

_cache: dict[str, Any] = {"data": None, "fetched_at": 0.0, "url": None}


def _cast(key: str, raw: str) -> Any:
    caster = TYPES.get(key)
    if caster is None:
        return raw
    return caster(raw.strip())


def _parse_csv(text: str) -> dict[str, Any]:
    out: dict[str, Any] = dict(DEFAULTS)
    reader = csv.DictReader(io.StringIO(text))
    for row in reader:
        key = (row.get("key") or "").strip()
        raw_value = row.get("value")
        if not key or raw_value is None or key not in TYPES:
            continue
        try:
            out[key] = _cast(key, raw_value)
        except (ValueError, TypeError):
            logger.warning("coach.config: failed to cast %s=%r, using default", key, raw_value)
            out[key] = DEFAULTS[key]
    return out


def _reset_cache() -> None:
    _cache["data"] = None
    _cache["fetched_at"] = 0.0
    _cache["url"] = None


def load(url: str | None = None, *, now: float | None = None) -> tuple[dict[str, Any], list[str]]:
    """Load config from CSV URL with cache + defaults fallback.

    Returns (config_dict, flags). flags is `["config_fetch_failed"]` if the CSV
    was unreachable or malformed; empty otherwise. Missing keys silently fall
    back to DEFAULTS.
    """
    csv_url = url if url is not None else os.environ.get("COACH_CONFIG_SHEET_CSV_URL", "")
    ts = now if now is not None else time.time()

    if not csv_url:
        return dict(DEFAULTS), ["config_fetch_failed"]

    cached = _cache["data"]
    if (
        cached is not None
        and _cache["url"] == csv_url
        and ts - _cache["fetched_at"] < TTL_SECONDS
    ):
        return dict(cached), []

    try:
        resp = httpx.get(csv_url, timeout=5.0, follow_redirects=True)
        if resp.status_code != 200:
            logger.warning("coach.config: CSV fetch returned %d", resp.status_code)
            return dict(DEFAULTS), ["config_fetch_failed"]
        data = _parse_csv(resp.text)
    except Exception as exc:
        logger.warning("coach.config: CSV fetch failed: %s", exc)
        return dict(DEFAULTS), ["config_fetch_failed"]

    _cache["data"] = data
    _cache["fetched_at"] = ts
    _cache["url"] = csv_url
    return dict(data), []

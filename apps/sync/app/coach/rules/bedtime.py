"""Bedtime rule. Pure function."""
from __future__ import annotations

from datetime import datetime, time, timedelta


def compute(wake_time: time, cfg: dict) -> time:
    sleep_hours = float(cfg["target_sleep_hours"])
    latency_min = int(cfg["sleep_latency_min"])
    base = datetime(2000, 1, 1, wake_time.hour, wake_time.minute)
    bed = base - timedelta(hours=sleep_hours) - timedelta(minutes=latency_min)
    return bed.time()

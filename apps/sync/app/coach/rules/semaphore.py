"""Semaphore rule. Pure function.

V1 uses a crude -5ms HRV proxy; V2 will switch to rolling stddev.
"""
from __future__ import annotations

GREEN = "green"
AMBER = "amber"
RED = "red"


def compute(
    hrv_today: float | None,
    hrv_baseline_7d: float | None,
    sleep_h: float | None,
    tsb: float | None,
) -> str:
    score = 0

    if hrv_today is not None and hrv_baseline_7d is not None:
        if hrv_today < hrv_baseline_7d - 5:
            score += 1

    if sleep_h is not None and sleep_h < 6.5:
        score += 1

    if tsb is not None and tsb < -20:
        score += 1

    if score == 0:
        return GREEN
    if score == 1:
        return AMBER
    return RED

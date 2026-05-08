"""Calorie target rule. Pure function."""
from __future__ import annotations

from typing import Any

from app.coach import classifier


def compute(today_workout: Any, tomorrow_workout: Any, cfg: dict) -> int:
    base = int(cfg["base_kcal"])
    target = base

    if classifier.has_strength(tomorrow_workout):
        target += 100
    if classifier.has_z1_long(tomorrow_workout, 90):
        target += 200
    if classifier.has_quality(tomorrow_workout):
        target += 300
    if classifier.has_long_or_quality(today_workout):
        target += 200

    return min(target, base + 400)

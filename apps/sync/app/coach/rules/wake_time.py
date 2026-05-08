"""Wake-time rule.

Pure function. Constants are part of the rule definition itself, no cfg needed.
"""
from __future__ import annotations

from datetime import date, datetime, time, timedelta
from typing import Any

from app.coach import classifier

WEEKEND_WAKE = time(8, 30)
REST_WAKE = time(7, 15)
STRENGTH_WAKE = time(6, 15)
END_ANCHOR = time(8, 0)
PREP_BUFFER_MIN = 20


def _is_weekend(d: date) -> bool:
    return d.weekday() >= 5  # 5 = Saturday, 6 = Sunday


def _duration_min(workout: Any) -> int:
    if not workout:
        return 0
    if isinstance(workout, dict):
        for key in ("duration_min", "duration_minutes"):
            v = workout.get(key)
            if v is not None:
                return int(v)
        sec = workout.get("duration_sec") or workout.get("duration_seconds")
        if sec is not None:
            return int(sec) // 60
        sessions = workout.get("sessions") or []
        if sessions:
            return sum(_duration_min(s) for s in sessions)
    return 0


def _subtract(t: time, minutes: int) -> time:
    base = datetime(2000, 1, 1, t.hour, t.minute)
    return (base - timedelta(minutes=minutes)).time()


def compute(date_tomorrow: date, tomorrow_workout: Any) -> time:
    if _is_weekend(date_tomorrow):
        return WEEKEND_WAKE

    category = classifier.classify_workout(tomorrow_workout)

    if category == classifier.CATEGORY_REST:
        return REST_WAKE

    if category == classifier.CATEGORY_STRENGTH_ONLY:
        return STRENGTH_WAKE

    if category in (classifier.CATEGORY_RUN, classifier.CATEGORY_CROSS_OUTDOOR):
        duration = _duration_min(tomorrow_workout)
        return _subtract(END_ANCHOR, duration + PREP_BUFFER_MIN)

    if category == classifier.CATEGORY_MIXED:
        primary = classifier.first_am_outdoor_session(tomorrow_workout)
        if primary:
            return compute(date_tomorrow, primary)
        return STRENGTH_WAKE

    return STRENGTH_WAKE

"""Workout classifier — pure functions, no IO.

Maps a planned-workout payload to one of:
  rest, strength_only, run, cross_outdoor, mixed
"""
from __future__ import annotations

from typing import Any

CATEGORY_REST = "rest"
CATEGORY_STRENGTH_ONLY = "strength_only"
CATEGORY_RUN = "run"
CATEGORY_CROSS_OUTDOOR = "cross_outdoor"
CATEGORY_MIXED = "mixed"

_STRENGTH_TYPES = {"strength", "gym", "weights", "weight training", "fuerza"}
_RUN_TYPES = {"run", "running", "trail", "trail running", "track"}
_BIKE_OUTDOOR_TYPES = {"bike", "cycling", "cycle", "ride", "mtb", "bici", "trail bike"}


def _normalize(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip().lower()


def _session_kind(session: dict | None) -> str:
    if not session:
        return ""
    t = _normalize(session.get("type") or session.get("workout_type"))
    if t in _STRENGTH_TYPES:
        return "strength"
    if t in _RUN_TYPES:
        return "run"
    if t in _BIKE_OUTDOOR_TYPES:
        return "bike_outdoor"
    if not t:
        return ""
    return "unknown"


def _sessions(workout_obj: Any) -> list[dict]:
    if not workout_obj:
        return []
    if isinstance(workout_obj, dict):
        sessions = workout_obj.get("sessions")
        if isinstance(sessions, list) and sessions:
            return [s for s in sessions if s]
        return [workout_obj]
    if isinstance(workout_obj, list):
        return [s for s in workout_obj if s]
    return []


def classify_workout(workout_obj: Any) -> str:
    sessions = _sessions(workout_obj)
    if not sessions:
        return CATEGORY_REST

    kinds = {_session_kind(s) for s in sessions}
    kinds.discard("")

    if not kinds:
        return CATEGORY_REST

    if kinds == {"strength"}:
        return CATEGORY_STRENGTH_ONLY

    if "unknown" in kinds and len(kinds) == 1:
        return CATEGORY_RUN

    if len(kinds) >= 2 and not (kinds <= {"unknown", "strength"}):
        return CATEGORY_MIXED

    if "run" in kinds:
        return CATEGORY_RUN
    if "bike_outdoor" in kinds:
        return CATEGORY_CROSS_OUTDOOR
    if "strength" in kinds:
        return CATEGORY_STRENGTH_ONLY

    return CATEGORY_RUN


def has_strength(workout_obj: Any) -> bool:
    return any(_session_kind(s) == "strength" for s in _sessions(workout_obj))


def _duration_min(session: dict) -> float:
    for key in ("duration_min", "duration_minutes"):
        v = session.get(key)
        if v is not None:
            return float(v)
    sec = session.get("duration_sec") or session.get("duration_seconds")
    if sec is not None:
        return float(sec) / 60.0
    return 0.0


def _is_z1(session: dict) -> bool:
    if _session_kind(session) != "run":
        return False
    descr = _normalize(session.get("description")) + " " + _normalize(session.get("title"))
    zone = _normalize(session.get("zone"))
    if zone in {"z1", "zone1", "zone 1"}:
        return True
    return "z1" in descr or "zone 1" in descr or "easy" in descr or "rodaje" in descr


def has_z1_long(workout_obj: Any, min_minutes: int = 90) -> bool:
    for s in _sessions(workout_obj):
        if _is_z1(s) and _duration_min(s) >= min_minutes:
            return True
    return False


_QUALITY_KEYWORDS = ("interval", "tempo", "threshold", "vo2", "series", "intervalo", "umbral")


def has_quality(workout_obj: Any) -> bool:
    for s in _sessions(workout_obj):
        if _session_kind(s) != "run":
            # quality only applies to run for V1
            continue
        descr = _normalize(s.get("description")) + " " + _normalize(s.get("title"))
        if any(kw in descr for kw in _QUALITY_KEYWORDS):
            return True
        try:
            intensity = float(s.get("planned_if") or s.get("intensity_factor") or 0.0)
        except (TypeError, ValueError):
            intensity = 0.0
        if intensity >= 0.85:
            return True
    return False


def has_long_or_quality(workout_obj: Any) -> bool:
    return has_quality(workout_obj) or has_z1_long(workout_obj, 90)


def first_am_outdoor_session(workout_obj: Any) -> dict | None:
    for s in _sessions(workout_obj):
        if _session_kind(s) in ("run", "bike_outdoor"):
            return s
    return None

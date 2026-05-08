"""Compose the deterministic ntfy message body."""
from __future__ import annotations

from datetime import time
from typing import Any

from app.coach import classifier

SEMAPHORE_EMOJI = {
    "green": "🟢",
    "amber": "🟡",
    "red": "🔴",
}

FLAG_LABELS = {
    "mfp_no_sync": "⚠ MFP sin sync",
    "hrv_missing": "⚠ HRV sin dato",
    "tp_summary_failed": "⚠ TP sin datos",
    "config_fetch_failed": "⚠ config en defaults",
}


def _hhmm(t: time | None) -> str:
    if t is None:
        return "--:--"
    return t.strftime("%H:%M")


def _duration_min(workout: Any) -> int:
    if not workout or not isinstance(workout, dict):
        return 0
    for key in ("duration_min", "duration_minutes"):
        v = workout.get(key)
        if v is not None:
            return int(v)
    sec = workout.get("duration_sec") or workout.get("duration_seconds")
    if sec is not None:
        return int(sec) // 60
    sessions = workout.get("sessions") or []
    return sum(_duration_min(s) for s in sessions)


def workout_summary(workout: Any) -> str:
    if not workout:
        return "Rest"
    category = classifier.classify_workout(workout)
    duration = _duration_min(workout)

    if category == classifier.CATEGORY_REST:
        return "Rest"
    if category == classifier.CATEGORY_STRENGTH_ONLY:
        return f"Fuerza {duration}'" if duration else "Fuerza"
    if classifier.has_quality(workout):
        return f"Quality {duration}'" if duration else "Quality"
    if category == classifier.CATEGORY_RUN:
        if classifier.has_z1_long(workout, 90):
            return f"Z1 {duration}'"
        return f"Z2 {duration}'" if duration else "Run"
    if category == classifier.CATEGORY_CROSS_OUTDOOR:
        return f"Bici {duration}'" if duration else "Bici"
    if category == classifier.CATEGORY_MIXED:
        return f"Mixto {duration}'" if duration else "Mixto"
    return "Run"


def _flag_line(flags: list[str]) -> str:
    parts = [FLAG_LABELS[f] for f in flags if f in FLAG_LABELS]
    return " · ".join(parts)


def compose(
    *,
    semaphore: str,
    hrv: float | int | None,
    hrv_baseline: float | int | None,
    sleep_h: float | None,
    sleep_eff_pct: int | None,
    tsb: float | int | None,
    tomorrow_workout: Any,
    wake_time: time,
    bedtime: time,
    dinner: dict,
    categories: dict,
    flags: list[str],
    llm_line: str | None,
    has_tomorrow_plan: bool = True,
) -> str:
    emoji = SEMAPHORE_EMOJI.get(semaphore, "⚪")
    lines = [f"{emoji} Briefing 20:30"]

    fl = _flag_line(flags)
    if fl:
        lines.append(fl)

    if hrv is not None and hrv_baseline is not None:
        delta = round(float(hrv) - float(hrv_baseline))
        hrv_str = f"HRV {round(float(hrv))} ({delta:+d} vs 7d)"
    elif hrv is not None:
        hrv_str = f"HRV {round(float(hrv))}"
    else:
        hrv_str = "HRV —"

    if sleep_h is not None:
        eff = sleep_eff_pct if sleep_eff_pct is not None else 0
        sleep_str = f"Sueño {sleep_h:.1f}h ({eff}%)"
    else:
        sleep_str = "Sueño —"

    tsb_str = f"TSB {int(round(float(tsb))):+d}" if tsb is not None else "TSB —"

    lines.append(f"{hrv_str} · {sleep_str} · {tsb_str}")

    if has_tomorrow_plan:
        ws = workout_summary(tomorrow_workout)
    else:
        ws = "sin plan TP"
    lines.append(f"Mañana: {ws} · wake {_hhmm(wake_time)}")
    lines.append("")

    lines.append(
        f"Cena ~{dinner['kcal']} kcal | "
        f"{dinner['c']}g C · {dinner['p']}g P · {dinner['g']}g G"
    )
    lines.append(f"  {categories['carb']} + {categories['prot']} + verdura")
    lines.append("")

    lines.append(f"Bed {_hhmm(bedtime)}")

    if llm_line:
        lines.append(llm_line.strip())

    return "\n".join(lines)

"""Input builder for the briefing job.

Reads HRV, sleep, TSB, planned workouts, and nutrition directly from
Postgres. Each source is best-effort: failures are collected as flags
and never raise out of this module.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import date, timedelta
from typing import Any

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.nutrition_daily import NutritionDaily
from app.models.sleep_session import SleepSession
from app.models.tp_fitness_data import TPFitnessData
from app.models.tp_planned_workout import TPPlannedWorkout

logger = logging.getLogger(__name__)


@dataclass
class BriefingInputs:
    today: date
    tomorrow: date
    today_workout: dict | None = None
    tomorrow_workout: dict | None = None
    has_tomorrow_plan: bool = True
    hrv_today: float | None = None
    hrv_baseline_7d: float | None = None
    sleep_h: float | None = None
    sleep_eff_pct: int | None = None
    tsb: float | None = None
    consumed: dict = field(default_factory=lambda: {"prot_g": 0, "carb_g": 0, "fat_g": 0})
    flags: list[str] = field(default_factory=list)


def _planned_to_dict(p: TPPlannedWorkout | None) -> dict | None:
    if p is None:
        return None
    duration_sec = int(p.duration_sec_planned or 0)
    return {
        "type": p.workout_type,
        "title": p.title,
        "description": p.description or "",
        "duration_sec": duration_sec,
        "duration_min": duration_sec // 60,
        "planned_if": None,
    }


def _read_workouts(
    db: Session, today: date, tomorrow: date
) -> tuple[dict | None, dict | None, list[str]]:
    flags: list[str] = []
    try:
        today_row = (
            db.query(TPPlannedWorkout)
            .filter(TPPlannedWorkout.date == today)
            .order_by(TPPlannedWorkout.id)
            .first()
        )
        tomorrow_row = (
            db.query(TPPlannedWorkout)
            .filter(TPPlannedWorkout.date == tomorrow)
            .order_by(TPPlannedWorkout.id)
            .first()
        )
        return _planned_to_dict(today_row), _planned_to_dict(tomorrow_row), flags
    except Exception:
        logger.exception("coach.inputs: planned workouts query failed")
        return None, None, ["tp_summary_failed"]


def _read_sleep_and_hrv(
    db: Session, today: date
) -> tuple[float | None, float | None, float | None, int | None, list[str]]:
    flags: list[str] = []
    hrv_today: float | None = None
    hrv_baseline: float | None = None
    sleep_h: float | None = None
    sleep_eff: int | None = None

    try:
        latest = (
            db.query(SleepSession)
            .filter(SleepSession.date <= today)
            .order_by(SleepSession.date.desc())
            .first()
        )
        if latest is not None:
            hrv_today = float(latest.avg_hrv) if latest.avg_hrv is not None else None
            if latest.total_sleep_min is not None:
                sleep_h = round(latest.total_sleep_min / 60.0, 2)
                in_bed = (
                    latest.total_sleep_min
                    + (latest.awake_min or 0)
                )
                if in_bed > 0:
                    sleep_eff = int(round(latest.total_sleep_min * 100 / in_bed))

        baseline_start = today - timedelta(days=7)
        baseline = (
            db.query(func.avg(SleepSession.avg_hrv))
            .filter(
                SleepSession.date > baseline_start,
                SleepSession.date <= today,
                SleepSession.avg_hrv.isnot(None),
            )
            .scalar()
        )
        if baseline is not None:
            hrv_baseline = float(baseline)
    except Exception:
        logger.exception("coach.inputs: sleep/HRV query failed")
        flags.append("hrv_missing")

    if hrv_today is None and "hrv_missing" not in flags:
        flags.append("hrv_missing")

    return hrv_today, hrv_baseline, sleep_h, sleep_eff, flags


def _read_tsb(db: Session, today: date) -> tuple[float | None, list[str]]:
    try:
        row = (
            db.query(TPFitnessData)
            .filter(TPFitnessData.date <= today)
            .order_by(TPFitnessData.date.desc())
            .first()
        )
        if row is None or row.tsb is None:
            return None, []
        return float(row.tsb), []
    except Exception:
        logger.exception("coach.inputs: TSB query failed")
        return None, ["tp_summary_failed"]


def _read_consumed(db: Session, today: date) -> tuple[dict, list[str]]:
    flags: list[str] = []
    consumed = {"prot_g": 0, "carb_g": 0, "fat_g": 0, "kcal": 0}
    try:
        row = db.query(NutritionDaily).filter(NutritionDaily.date == today).first()
        if row is None or (row.calories is None and not row.entries):
            flags.append("mfp_no_sync")
            return consumed, flags
        consumed["prot_g"] = int(row.protein_g or 0)
        consumed["carb_g"] = int(row.carbs_g or 0)
        consumed["fat_g"] = int(row.fat_g or 0)
        consumed["kcal"] = int(row.calories or 0)
    except Exception:
        logger.exception("coach.inputs: nutrition query failed")
        flags.append("mfp_no_sync")
    return consumed, flags


def build(db: Session, today: date) -> BriefingInputs:
    tomorrow = today + timedelta(days=1)
    inputs = BriefingInputs(today=today, tomorrow=tomorrow)

    today_w, tomorrow_w, w_flags = _read_workouts(db, today, tomorrow)
    inputs.today_workout = today_w
    inputs.tomorrow_workout = tomorrow_w
    inputs.has_tomorrow_plan = tomorrow_w is not None
    inputs.flags.extend(w_flags)

    hrv, baseline, sleep_h, sleep_eff, sleep_flags = _read_sleep_and_hrv(db, today)
    inputs.hrv_today = hrv
    inputs.hrv_baseline_7d = baseline
    inputs.sleep_h = sleep_h
    inputs.sleep_eff_pct = sleep_eff
    inputs.flags.extend(sleep_flags)

    tsb, tsb_flags = _read_tsb(db, today)
    inputs.tsb = tsb
    inputs.flags.extend(tsb_flags)

    consumed, n_flags = _read_consumed(db, today)
    inputs.consumed = {
        "prot_g": consumed["prot_g"],
        "carb_g": consumed["carb_g"],
        "fat_g": consumed["fat_g"],
    }
    inputs.flags.extend(n_flags)

    seen: set[str] = set()
    deduped: list[str] = []
    for f in inputs.flags:
        if f not in seen:
            seen.add(f)
            deduped.append(f)
    inputs.flags = deduped

    return inputs


def serialize_inputs(inp: BriefingInputs, cfg: dict) -> dict:
    """JSON-serializable snapshot for inputs_json column."""
    return {
        "today": inp.today.isoformat(),
        "tomorrow": inp.tomorrow.isoformat(),
        "today_workout": inp.today_workout,
        "tomorrow_workout": inp.tomorrow_workout,
        "has_tomorrow_plan": inp.has_tomorrow_plan,
        "hrv_today": inp.hrv_today,
        "hrv_baseline_7d": inp.hrv_baseline_7d,
        "sleep_h": inp.sleep_h,
        "sleep_eff_pct": inp.sleep_eff_pct,
        "tsb": inp.tsb,
        "consumed": inp.consumed,
        "flags": list(inp.flags),
        "cfg": dict(cfg),
    }


def _intensity_from_summary(workout: dict | None) -> dict[str, Any]:
    if not workout:
        return {}
    return workout

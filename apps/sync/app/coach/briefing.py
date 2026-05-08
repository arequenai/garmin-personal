"""Pre-dinner briefing orchestrator."""
from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import date, datetime, time

from sqlalchemy.orm import Session

from app.coach import config as coach_config
from app.coach import formatter, inputs, llm, ntfy, persistence
from app.coach.rules import (
    bedtime,
    calorie_target,
    category_picker,
    dinner_macros,
    macro_split,
    semaphore,
    wake_time,
)

logger = logging.getLogger(__name__)

KIND_PRE_DINNER = "pre_dinner"


@dataclass
class BriefingResult:
    sent: bool
    skipped: bool
    briefing_id: str | None
    semaphore: str
    flags: list[str]
    body: str
    llm_used: bool
    ntfy_status_code: int | None


def _serialize_recommendation(
    *,
    wake: time,
    bed: time,
    kcal_target: int,
    daily_macros: dict,
    dinner: dict,
    categories: dict,
    body: str,
) -> dict:
    return {
        "wake_time": wake.strftime("%H:%M"),
        "bedtime": bed.strftime("%H:%M"),
        "calorie_target": kcal_target,
        "daily_macros": daily_macros,
        "dinner": dinner,
        "categories": categories,
        "body": body,
    }


def _llm_context(
    *,
    sem: str,
    inp: inputs.BriefingInputs,
    dinner: dict,
    bed: time,
) -> dict:
    delta_str = "—"
    if inp.hrv_today is not None and inp.hrv_baseline_7d is not None:
        delta_str = f"{round(inp.hrv_today - inp.hrv_baseline_7d):+d}"
    today_summary = formatter.workout_summary(inp.today_workout) if inp.today_workout else "Rest"
    tomorrow_summary = (
        formatter.workout_summary(inp.tomorrow_workout)
        if inp.has_tomorrow_plan
        else "sin plan"
    )
    return {
        "semaphore": sem,
        "hrv": round(inp.hrv_today) if inp.hrv_today is not None else "—",
        "delta": delta_str,
        "sleep_h": f"{inp.sleep_h:.1f}" if inp.sleep_h is not None else "—",
        "sleep_eff": inp.sleep_eff_pct if inp.sleep_eff_pct is not None else "—",
        "tsb": int(round(inp.tsb)) if inp.tsb is not None else "—",
        "today_workout_summary": today_summary,
        "tomorrow_workout_summary": tomorrow_summary,
        "kcal": dinner["kcal"],
        "c": dinner["c"],
        "p": dinner["p"],
        "g": dinner["g"],
        "bed": bed.strftime("%H:%M"),
    }


def run_pre_dinner(
    db: Session,
    *,
    target_date: date | None = None,
    force: bool = False,
) -> BriefingResult:
    today = target_date if target_date is not None else datetime.now().date()

    cfg, cfg_flags = coach_config.load()

    existing = persistence.get_briefing(db, today, KIND_PRE_DINNER)
    if existing is not None and not force:
        logger.info(
            "coach.pre_dinner: skip (already sent) date=%s id=%s",
            today,
            existing.id,
        )
        return BriefingResult(
            sent=False,
            skipped=True,
            briefing_id=str(existing.id),
            semaphore=existing.semaphore,
            flags=list(existing.flags or []),
            body="",
            llm_used=False,
            ntfy_status_code=existing.ntfy_status_code,
        )

    inp = inputs.build(db, today)
    flags = list(cfg_flags) + list(inp.flags)

    wake = wake_time.compute(inp.tomorrow, inp.tomorrow_workout)
    bed = bedtime.compute(wake, cfg)
    kcal_target = calorie_target.compute(inp.today_workout, inp.tomorrow_workout, cfg)
    daily_macros = macro_split.compute(kcal_target, inp.tomorrow_workout, cfg)
    dinner = dinner_macros.compute(daily_macros, inp.consumed, cfg)
    categories = category_picker.compute(dinner, inp.tomorrow_workout)
    sem = semaphore.compute(inp.hrv_today, inp.hrv_baseline_7d, inp.sleep_h, inp.tsb)

    body = formatter.compose(
        semaphore=sem,
        hrv=inp.hrv_today,
        hrv_baseline=inp.hrv_baseline_7d,
        sleep_h=inp.sleep_h,
        sleep_eff_pct=inp.sleep_eff_pct,
        tsb=inp.tsb,
        tomorrow_workout=inp.tomorrow_workout,
        wake_time=wake,
        bedtime=bed,
        dinner=dinner,
        categories=categories,
        flags=flags,
        llm_line=None,
        has_tomorrow_plan=inp.has_tomorrow_plan,
    )

    llm_line = llm.compose_closing_line(
        _llm_context(sem=sem, inp=inp, dinner=dinner, bed=bed)
    )
    if llm_line is None:
        if "llm_timeout" not in flags:
            flags.append("llm_timeout")
    else:
        body = formatter.compose(
            semaphore=sem,
            hrv=inp.hrv_today,
            hrv_baseline=inp.hrv_baseline_7d,
            sleep_h=inp.sleep_h,
            sleep_eff_pct=inp.sleep_eff_pct,
            tsb=inp.tsb,
            tomorrow_workout=inp.tomorrow_workout,
            wake_time=wake,
            bedtime=bed,
            dinner=dinner,
            categories=categories,
            flags=flags,
            llm_line=llm_line,
            has_tomorrow_plan=inp.has_tomorrow_plan,
        )

    status_code = ntfy.push(body=body, semaphore=sem)

    recommendation = _serialize_recommendation(
        wake=wake,
        bed=bed,
        kcal_target=kcal_target,
        daily_macros=daily_macros,
        dinner=dinner,
        categories=categories,
        body=body,
    )

    if existing is not None and force:
        db.delete(existing)
        db.commit()

    row = persistence.save_briefing(
        db,
        target_date=today,
        kind=KIND_PRE_DINNER,
        inputs_json=inputs.serialize_inputs(inp, cfg),
        recommendation_json=recommendation,
        semaphore=sem,
        llm_used=llm_line is not None,
        llm_text=llm_line,
        flags=flags,
        ntfy_status_code=status_code,
    )

    logger.info(
        "coach.pre_dinner sent=%s semaphore=%s flags=%s llm_used=%s",
        status_code is not None,
        sem,
        flags,
        llm_line is not None,
    )

    return BriefingResult(
        sent=status_code is not None,
        skipped=False,
        briefing_id=str(row.id),
        semaphore=sem,
        flags=flags,
        body=body,
        llm_used=llm_line is not None,
        ntfy_status_code=status_code,
    )

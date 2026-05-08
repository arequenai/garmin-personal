"""Integration tests for the full pre-dinner briefing flow.

Mocks: ntfy push, LLM call, config loader. Builds DB rows for the inputs
the orchestrator reads.
"""
from __future__ import annotations

from datetime import date, timedelta

import pytest

from app.coach import briefing as coach_briefing
from app.coach import config as coach_config
from app.coach import llm, ntfy, persistence
from app.models.nutrition_daily import NutritionDaily
from app.models.sleep_session import SleepSession
from app.models.tp_fitness_data import TPFitnessData
from app.models.tp_planned_workout import TPPlannedWorkout

TODAY = date(2026, 5, 8)  # Friday
TOMORROW = TODAY + timedelta(days=1)  # Saturday


def _seed_baseline_hrv(db, end_date, value: float, days: int = 7):
    """Seed `days` of sleep rows ending at end_date with the given HRV."""
    for i in range(days):
        d = end_date - timedelta(days=i)
        db.add(
            SleepSession(
                date=d,
                avg_hrv=value,
                total_sleep_min=420,
                awake_min=20,
            )
        )
    db.commit()


@pytest.fixture(autouse=True)
def _stub_external(monkeypatch):
    monkeypatch.setattr(ntfy, "push", lambda **kwargs: 200)
    monkeypatch.setattr(llm, "compose_closing_line", lambda *a, **k: None)
    monkeypatch.setattr(
        coach_config, "load",
        lambda url=None, now=None: (dict(coach_config.DEFAULTS), []),
    )
    yield


def test_green_happy_path(db_session, monkeypatch):
    db = db_session
    _seed_baseline_hrv(db, TODAY, 60.0)
    # overwrite today's HRV/sleep
    today_sleep = db.query(SleepSession).filter_by(date=TODAY).first()
    today_sleep.avg_hrv = 62.0
    today_sleep.total_sleep_min = 440  # 7h20
    today_sleep.awake_min = 30
    db.commit()

    db.add(TPFitnessData(date=TODAY, tsb=-8.0))
    # tomorrow Z1 60' (Saturday so weekend wake 8:30 path)
    db.add(
        TPPlannedWorkout(
            tp_workout_id="t1",
            date=TOMORROW,
            workout_type="run",
            description="Z1 easy",
            duration_sec_planned=60 * 60,
        )
    )
    db.add(NutritionDaily(date=TODAY, calories=1800, protein_g=100, carbs_g=200, fat_g=60))
    db.commit()

    res = coach_briefing.run_pre_dinner(db, target_date=TODAY)

    assert res.sent is True
    assert res.semaphore == "green"
    assert "config_fetch_failed" not in res.flags

    row = persistence.get_briefing(db, TODAY, "pre_dinner")
    assert row is not None
    assert row.semaphore == "green"
    assert "🟢" in res.body
    assert "Bed " in res.body


def test_amber_with_llm_line(db_session, monkeypatch):
    db = db_session
    _seed_baseline_hrv(db, TODAY, 60.0)
    today_sleep = db.query(SleepSession).filter_by(date=TODAY).first()
    today_sleep.avg_hrv = 51.0
    today_sleep.total_sleep_min = 370  # 6h10
    today_sleep.awake_min = 30
    db.commit()
    db.add(TPFitnessData(date=TODAY, tsb=-22.0))
    db.add(
        TPPlannedWorkout(
            tp_workout_id="today",
            date=TODAY,
            workout_type="run",
            description="Z2",
            duration_sec_planned=60 * 60,
        )
    )
    db.add(
        TPPlannedWorkout(
            tp_workout_id="tom",
            date=TOMORROW,
            workout_type="run",
            description="Z2",
            duration_sec_planned=75 * 60,
        )
    )
    db.add(NutritionDaily(date=TODAY, calories=1800, protein_g=100, carbs_g=200, fat_g=60))
    db.commit()

    monkeypatch.setattr(
        llm, "compose_closing_line",
        lambda *a, **k: "Sube horas de sueño esta noche.",
    )

    res = coach_briefing.run_pre_dinner(db, target_date=TODAY)

    assert res.semaphore == "red"  # 3 of 3 hits
    assert res.llm_used is True
    assert "Sube horas de sueño" in res.body


def test_red_with_missing_data_and_default_config(db_session, monkeypatch):
    db = db_session
    # No baseline, no nutrition, no fitness, no workouts
    db.add(
        SleepSession(
            date=TODAY,
            avg_hrv=48.0,
            total_sleep_min=330,  # 5h30
            awake_min=30,
        )
    )
    db.add(TPFitnessData(date=TODAY, tsb=-28.0))
    db.commit()

    monkeypatch.setattr(
        coach_config,
        "load",
        lambda url=None, now=None: (dict(coach_config.DEFAULTS), ["config_fetch_failed"]),
    )

    res = coach_briefing.run_pre_dinner(db, target_date=TODAY)

    assert res.semaphore == "red"
    assert "config_fetch_failed" in res.flags
    assert "mfp_no_sync" in res.flags

    row = persistence.get_briefing(db, TODAY, "pre_dinner")
    assert row is not None
    assert "config_fetch_failed" in (row.flags or [])
    # cfg snapshot stored
    assert row.inputs_json["cfg"]["base_kcal"] == coach_config.DEFAULTS["base_kcal"]

from __future__ import annotations

from datetime import date

import pytest

from app.coach import briefing as coach_briefing
from app.coach import config as coach_config
from app.coach import llm, ntfy
from app.models.sleep_session import SleepSession
from app.models.tp_fitness_data import TPFitnessData

TODAY = date(2026, 5, 8)


@pytest.fixture(autouse=True)
def _stub_external(monkeypatch):
    monkeypatch.setattr(ntfy, "push", lambda **kwargs: 200)
    monkeypatch.setattr(llm, "compose_closing_line", lambda *a, **k: None)
    monkeypatch.setattr(
        coach_config, "load",
        lambda url=None, now=None: (dict(coach_config.DEFAULTS), []),
    )


def _seed_minimum(db):
    db.add(SleepSession(date=TODAY, avg_hrv=60.0, total_sleep_min=420, awake_min=20))
    db.add(TPFitnessData(date=TODAY, tsb=-5.0))
    db.commit()


def test_double_run_skips_second(db_session):
    _seed_minimum(db_session)
    first = coach_briefing.run_pre_dinner(db_session, target_date=TODAY)
    assert first.skipped is False
    assert first.sent is True

    second = coach_briefing.run_pre_dinner(db_session, target_date=TODAY)
    assert second.skipped is True
    assert second.sent is False
    assert second.briefing_id == first.briefing_id


def test_force_replaces_row(db_session):
    _seed_minimum(db_session)
    first = coach_briefing.run_pre_dinner(db_session, target_date=TODAY)

    forced = coach_briefing.run_pre_dinner(db_session, target_date=TODAY, force=True)
    assert forced.skipped is False
    assert forced.sent is True
    # Forced run produces a new briefing row id
    assert forced.briefing_id != first.briefing_id

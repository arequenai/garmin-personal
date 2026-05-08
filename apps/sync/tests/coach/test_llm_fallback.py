from __future__ import annotations

from datetime import date

import pytest

from app.coach import briefing as coach_briefing
from app.coach import config as coach_config
from app.coach import llm, ntfy, persistence
from app.models.sleep_session import SleepSession
from app.models.tp_fitness_data import TPFitnessData

TODAY = date(2026, 5, 8)


@pytest.fixture(autouse=True)
def _stub_no_network(monkeypatch):
    monkeypatch.setattr(ntfy, "push", lambda **kwargs: 200)
    monkeypatch.setattr(
        coach_config, "load",
        lambda url=None, now=None: (dict(coach_config.DEFAULTS), []),
    )


def _seed(db):
    db.add(SleepSession(date=TODAY, avg_hrv=60.0, total_sleep_min=420, awake_min=20))
    db.add(TPFitnessData(date=TODAY, tsb=-5.0))
    db.commit()


def test_llm_timeout_keeps_briefing_sending(db_session, monkeypatch):
    def boom(*a, **k):
        return None  # the wrapper itself returns None on TimeoutError

    monkeypatch.setattr(llm, "compose_closing_line", boom)
    _seed(db_session)

    res = coach_briefing.run_pre_dinner(db_session, target_date=TODAY)
    assert res.sent is True
    assert res.llm_used is False
    assert "llm_timeout" in res.flags

    row = persistence.get_briefing(db_session, TODAY, "pre_dinner")
    assert row is not None
    assert row.llm_used is False
    assert row.llm_text is None
    assert "llm_timeout" in (row.flags or [])


def test_llm_disabled_via_env(db_session, monkeypatch):
    monkeypatch.setenv("COACH_LLM_ENABLED", "false")
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    # Don't override compose_closing_line — let the real wrapper short-circuit on env.
    _seed(db_session)

    res = coach_briefing.run_pre_dinner(db_session, target_date=TODAY)
    assert res.sent is True
    assert res.llm_used is False

"""Shared fixtures for coach tests (SQLite in-memory)."""
from __future__ import annotations

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import app.models  # noqa: F401  - register all tables on Base.metadata
from app.database import Base


@pytest.fixture()
def db_session():
    engine = create_engine("sqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, future=True, expire_on_commit=False)
    db = factory()
    try:
        yield db
    finally:
        db.close()
        engine.dispose()


@pytest.fixture(autouse=True)
def _clear_config_cache():
    from app.coach import config as coach_config

    coach_config._reset_cache()
    yield
    coach_config._reset_cache()


@pytest.fixture(autouse=True)
def _disable_real_llm(monkeypatch):
    """Default: LLM disabled. Tests that want LLM behavior re-enable explicitly."""
    monkeypatch.setenv("COACH_LLM_ENABLED", "false")
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    yield

from datetime import date
from unittest.mock import MagicMock

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base
from app.models import NutritionDaily
from app.services.sync_service import SyncService


@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine)
    session = session_factory()
    yield session
    session.close()


def _make_mfp_mock(entries: list[dict], calories: int = 2000) -> MagicMock:
    mock = MagicMock()
    mock.get_day.return_value = {
        "calories": calories,
        "protein_g": 100.0,
        "carbs_g": 200.0,
        "fat_g": 60.0,
        "fiber_g": 25.0,
        "sodium_mg": 1500.0,
        "calories_goal": 2100,
        "protein_goal_g": 120.0,
        "entries": entries,
    }
    return mock


def test_alcohol_detection_counts_drinks(db_session):
    entries = [
        {"name": "Chicken Breast", "meal": "Lunch"},
        {"name": "Corona Beer", "meal": "Dinner"},
        {"name": "Red Wine - 1 Glass", "meal": "Dinner"},
        {"name": "Brown Rice", "meal": "Dinner"},
    ]
    mock_mfp = _make_mfp_mock(entries)
    mock_garmin = MagicMock()

    service = SyncService(db=db_session, garmin=mock_garmin, mfp=mock_mfp)
    service.sync_nutrition(date(2026, 3, 6))

    record = db_session.query(NutritionDaily).filter_by(date=date(2026, 3, 6)).first()
    assert record is not None
    assert record.alcohol_drinks == 2


def test_alcohol_detection_zero_when_no_drinks(db_session):
    entries = [
        {"name": "Chicken Breast", "meal": "Lunch"},
        {"name": "Brown Rice", "meal": "Dinner"},
    ]
    mock_mfp = _make_mfp_mock(entries)
    mock_garmin = MagicMock()

    service = SyncService(db=db_session, garmin=mock_garmin, mfp=mock_mfp)
    service.sync_nutrition(date(2026, 3, 6))

    record = db_session.query(NutritionDaily).filter_by(date=date(2026, 3, 6)).first()
    assert record is not None
    assert record.alcohol_drinks == 0


def test_alcohol_detection_no_entries_key(db_session):
    """When MFP returns no entries (old format), alcohol_drinks should be None."""
    mock_mfp = MagicMock()
    mock_mfp.get_day.return_value = {
        "calories": 2000,
        "protein_g": 100.0,
        "carbs_g": 200.0,
        "fat_g": 60.0,
        "fiber_g": 25.0,
        "sodium_mg": 1500.0,
    }
    mock_garmin = MagicMock()

    service = SyncService(db=db_session, garmin=mock_garmin, mfp=mock_mfp)
    service.sync_nutrition(date(2026, 3, 6))

    record = db_session.query(NutritionDaily).filter_by(date=date(2026, 3, 6)).first()
    assert record is not None
    assert record.alcohol_drinks is None

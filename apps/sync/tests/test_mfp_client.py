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


def test_sync_nutrition(db_session):
    mock_garmin = MagicMock()
    mock_garmin.get_activities.return_value = []
    mock_garmin.get_daily_summary.return_value = {}
    mock_garmin.get_heart_rates.return_value = {}
    mock_garmin.get_stress_data.return_value = {}
    mock_garmin.get_body_battery.return_value = []
    mock_garmin.get_spo2_data.return_value = {}
    mock_garmin.get_respiration_data.return_value = {}
    mock_garmin.get_hydration_data.return_value = {}
    mock_garmin.get_sleep_data.return_value = {}

    mock_mfp = MagicMock()
    mock_mfp.get_day.return_value = {
        "calories": 2200,
        "protein_g": 150.0,
        "carbs_g": 250.0,
        "fat_g": 70.0,
        "fiber_g": 30.0,
        "sodium_mg": 2000.0,
    }

    service = SyncService(db=db_session, garmin=mock_garmin, mfp=mock_mfp)
    service.sync_nutrition(date(2026, 3, 6))

    record = db_session.query(NutritionDaily).filter_by(date=date(2026, 3, 6)).first()
    assert record is not None
    assert record.calories == 2200
    assert record.protein_g == 150.0


def test_sync_nutrition_includes_entries(db_session):
    """get_day() should return entries list alongside totals."""
    mock_garmin = MagicMock()
    mock_garmin.get_activities.return_value = []
    mock_garmin.get_daily_summary.return_value = {}
    mock_garmin.get_heart_rates.return_value = {}
    mock_garmin.get_stress_data.return_value = {}
    mock_garmin.get_body_battery.return_value = []
    mock_garmin.get_spo2_data.return_value = {}
    mock_garmin.get_respiration_data.return_value = {}
    mock_garmin.get_hydration_data.return_value = {}
    mock_garmin.get_sleep_data.return_value = {}

    mock_mfp = MagicMock()
    mock_mfp.get_day.return_value = {
        "calories": 2200,
        "protein_g": 150.0,
        "carbs_g": 250.0,
        "fat_g": 70.0,
        "fiber_g": 30.0,
        "sodium_mg": 2000.0,
        "entries": [
            {"name": "Chicken Breast", "meal": "Lunch"},
            {"name": "Corona Beer", "meal": "Dinner"},
        ],
    }

    service = SyncService(db=db_session, garmin=mock_garmin, mfp=mock_mfp)
    service.sync_nutrition(date(2026, 3, 6))

    record = db_session.query(NutritionDaily).filter_by(date=date(2026, 3, 6)).first()
    assert record is not None
    assert record.calories == 2200


def test_sync_nutrition_no_mfp_client(db_session):
    mock_garmin = MagicMock()
    service = SyncService(db=db_session, garmin=mock_garmin, mfp=None)
    # Should not crash, just skip
    service.sync_nutrition(date(2026, 3, 6))
    records = db_session.query(NutritionDaily).all()
    assert len(records) == 0

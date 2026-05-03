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


def test_normalize_meal_handles_spanish_and_english():
    from app.services.sync_service import _normalize_meal

    assert _normalize_meal("Breakfast") == "breakfast"
    assert _normalize_meal("Desayuno") == "breakfast"
    assert _normalize_meal("Lunch") == "lunch"
    assert _normalize_meal("Comida") == "lunch"
    assert _normalize_meal("Cena") == "dinner"
    assert _normalize_meal("Snacks") == "snacks"
    assert _normalize_meal("Merienda") == "snacks"
    assert _normalize_meal("Tentempié") == "snacks"
    assert _normalize_meal("Pre-workout") == "other"
    assert _normalize_meal("") == "other"


def test_sync_nutrition_persists_normalized_entries(db_session):
    mock_garmin = MagicMock()
    mock_mfp = MagicMock()
    mock_mfp.get_day.return_value = {
        "calories": 2000,
        "protein_g": 140.0,
        "carbs_g": 220.0,
        "fat_g": 65.0,
        "entries": [
            {"meal": "Breakfast", "name": "Oats", "calories": 300,
             "protein_g": 10, "carbs_g": 50, "fat_g": 5, "position": 0},
            {"meal": "Cena", "name": "Salmón", "calories": 500,
             "protein_g": 40, "carbs_g": 5, "fat_g": 30, "position": 1},
            {"meal": "Pre-workout", "name": "Banana", "calories": 100,
             "protein_g": 1, "carbs_g": 25, "fat_g": 0, "position": 2},
        ],
    }

    service = SyncService(db=db_session, garmin=mock_garmin, mfp=mock_mfp)
    service.sync_nutrition(date(2026, 5, 3))

    record = db_session.query(NutritionDaily).filter_by(date=date(2026, 5, 3)).first()
    assert record is not None
    meals = [e["meal"] for e in record.entries]
    assert meals == ["breakfast", "dinner", "other"]
    assert record.entries[0]["calories"] == 300
    assert record.entries[1]["name"] == "Salmón"

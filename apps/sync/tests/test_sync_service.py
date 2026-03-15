from datetime import date
from unittest.mock import MagicMock

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base
from app.models import DailySummary
from app.services.sync_service import SyncService


@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine)
    session = session_factory()
    yield session
    session.close()


def make_mock_garmin(overrides=None):
    mock = MagicMock()
    # Default return values
    mock.get_daily_summary.return_value = {
        "totalSteps": 10000,
        "totalKilocalories": 2500,
        "activeKilocalories": 800,
        "totalDistanceMeters": 8000.0,
        "floorsAscended": 10,
    }
    mock.get_heart_rates.return_value = {
        "restingHeartRate": 52,
        "maxHeartRate": 160,
        "minHeartRate": 45,
    }
    mock.get_stress_data.return_value = {
        "overallStressLevel": 30,
        "maxStressLevel": 75,
    }
    mock.get_body_battery.return_value = [
        {"charged": 80, "drained": 40},
    ]
    mock.get_spo2_data.return_value = {"averageSpo2": 97.0}
    mock.get_respiration_data.return_value = {"avgWakingRespirationValue": 16.0}
    mock.get_hydration_data.return_value = {"valueInML": 2000}
    mock.get_intensity_minutes.return_value = {
        "moderateIntensityMinutes": 30,
        "vigorousIntensityMinutes": 15,
    }
    mock.get_hrv_data.return_value = {
        "hrvSummary": {"lastNightAvg": 45, "weeklyAvg": 42},
    }
    mock.get_sleep_data.return_value = {
        "dailySleepDTO": {
            "sleepStartTimestampLocal": 1709686800000,
            "sleepEndTimestampLocal": 1709715600000,
            "sleepTimeSeconds": 25200,
            "deepSleepSeconds": 5400,
            "lightSleepSeconds": 10800,
            "remSleepSeconds": 7200,
            "awakeSleepSeconds": 1800,
            "averageHeartRate": 55,
            "averageSpO2Value": 96.5,
            "sleepScores": {"overall": 82},
        },
    }
    mock.get_activities.return_value = [
        {
            "activityId": 12345678,
            "startTimeLocal": "2026-03-06 07:00:00",
            "activityType": {"typeKey": "running"},
            "activityName": "Morning Run",
            "duration": 3600.0,
            "distance": 10000.0,
            "calories": 600,
            "averageHR": 145,
            "maxHR": 175,
            "avgPower": None,
            "maxPower": None,
            "aerobicTrainingEffect": 3.5,
            "anaerobicTrainingEffect": 1.2,
            "vO2MaxValue": 52.0,
            "elevationGain": 120.0,
        },
    ]
    if overrides:
        for method, value in overrides.items():
            getattr(mock, method).return_value = value
    return mock


def test_sync_daily_summary(db_session):
    garmin = make_mock_garmin()
    service = SyncService(db=db_session, garmin=garmin)
    result = service.sync_daily_summary(date(2026, 3, 6))
    assert result is not None
    assert result.steps == 10000
    assert result.calories_total == 2500
    assert result.resting_hr == 52
    assert result.stress_avg == 30


def test_sync_daily_summary_upsert(db_session):
    garmin = make_mock_garmin()
    service = SyncService(db=db_session, garmin=garmin)
    service.sync_daily_summary(date(2026, 3, 6))
    # Sync again with different data
    garmin.get_daily_summary.return_value["totalSteps"] = 15000
    service.sync_daily_summary(date(2026, 3, 6))
    # Should still be one record, updated
    records = db_session.query(DailySummary).all()
    assert len(records) == 1
    assert records[0].steps == 15000


def test_sync_sleep(db_session):
    garmin = make_mock_garmin()
    service = SyncService(db=db_session, garmin=garmin)
    result = service.sync_sleep(date(2026, 3, 6))
    assert result is not None
    assert result.total_sleep_min == 420  # 25200 / 60
    assert result.deep_min == 90  # 5400 / 60
    assert result.sleep_score == 82


def test_sync_sleep_no_data(db_session):
    garmin = make_mock_garmin({"get_sleep_data": {}})
    service = SyncService(db=db_session, garmin=garmin)
    result = service.sync_sleep(date(2026, 3, 6))
    assert result is None


def test_sync_activities(db_session):
    garmin = make_mock_garmin()
    service = SyncService(db=db_session, garmin=garmin)
    results = service.sync_activities(date(2026, 3, 6))
    assert len(results) == 1
    assert results[0].name == "Morning Run"
    assert results[0].type == "running"
    assert results[0].garmin_id == "12345678"


def test_sync_activities_filters_by_date(db_session):
    garmin = make_mock_garmin()
    service = SyncService(db=db_session, garmin=garmin)
    # Sync for a different date — should get no results because activity is on 2026-03-06
    results = service.sync_activities(date(2026, 3, 7))
    assert len(results) == 0

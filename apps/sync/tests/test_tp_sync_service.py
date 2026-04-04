from datetime import date
from unittest.mock import MagicMock

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base
from app.models.tp_completed_workout import TPCompletedWorkout
from app.models.tp_fitness_data import TPFitnessData
from app.models.tp_planned_workout import TPPlannedWorkout
from app.services.tp_sync_service import TPSyncService


@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine)
    session = session_factory()
    yield session
    session.close()


def make_mock_tp_client():
    mock = MagicMock()
    mock.get_fitness.return_value = [
        {
            "date": "2026-04-04",
            "ctl": 55.2,
            "atl": 72.1,
            "tsb": -16.9,
            "tpiTssActual": 85.0,
        },
    ]
    mock.get_workouts.return_value = [
        {
            "workoutId": 111,
            "workoutDay": "2026-04-04",
            "title": "Easy Run",
            "workoutTypeValueId": 3,
            "description": "Recovery jog",
            "totalTimePlanned": 2400,
            "tssPlanned": 40.0,
            "distancePlanned": 8000.0,
            "structure": {"warmup": [], "intervals": [], "cooldown": []},
            "completed": True,
            "totalTime": 2500,
            "distance": 8200.0,
            "tpiTssActual": 42.0,
            "heartRateAverage": 140,
            "heartRateMaximum": 165,
            "powerAverage": None,
            "powerMaximum": None,
            "normalizedPower": None,
            "caloriesUsed": 450,
            "ifActual": 0.85,
        },
        {
            "workoutId": 222,
            "workoutDay": "2026-04-06",
            "title": "Tempo Run",
            "workoutTypeValueId": 3,
            "description": "Tempo intervals",
            "totalTimePlanned": 3600,
            "tssPlanned": 80.0,
            "distancePlanned": 12000.0,
            "structure": None,
            "completed": False,
        },
    ]
    mock.get_workout_analysis.return_value = {
        "heartRateZones": [
            {"zoneName": "Z1", "timeInZone": 300},
            {"zoneName": "Z2", "timeInZone": 900},
            {"zoneName": "Z3", "timeInZone": 600},
            {"zoneName": "Z4", "timeInZone": 400},
            {"zoneName": "Z5", "timeInZone": 100},
        ],
        "powerZones": [],
        "laps": [{"lapIndex": 1, "distance": 8200}],
    }
    return mock


def test_sync_fitness(db_session):
    tp = make_mock_tp_client()
    service = TPSyncService(db=db_session, tp_client=tp)
    service.sync_fitness(date(2026, 4, 4))

    records = db_session.query(TPFitnessData).all()
    assert len(records) == 1
    assert records[0].ctl == 55.2
    assert records[0].atl == 72.1
    assert records[0].tsb == -16.9


def test_sync_fitness_upsert(db_session):
    tp = make_mock_tp_client()
    service = TPSyncService(db=db_session, tp_client=tp)
    service.sync_fitness(date(2026, 4, 4))

    tp.get_fitness.return_value[0]["ctl"] = 60.0
    service.sync_fitness(date(2026, 4, 4))

    records = db_session.query(TPFitnessData).all()
    assert len(records) == 1
    assert records[0].ctl == 60.0


def test_sync_planned_workouts(db_session):
    tp = make_mock_tp_client()
    service = TPSyncService(db=db_session, tp_client=tp)
    service.sync_planned_workouts(date(2026, 4, 4))

    planned = db_session.query(TPPlannedWorkout).all()
    assert len(planned) == 2


def test_sync_completed_workouts(db_session):
    tp = make_mock_tp_client()
    service = TPSyncService(db=db_session, tp_client=tp)
    service.sync_completed_workouts(date(2026, 4, 4))

    completed = db_session.query(TPCompletedWorkout).all()
    assert len(completed) == 1
    assert completed[0].tp_workout_id == "111"
    assert completed[0].avg_hr == 140
    assert completed[0].hr_zone1_sec == 300
    assert completed[0].hr_zone3_sec == 600


def test_sync_completed_workout_analysis_failure(db_session):
    tp = make_mock_tp_client()
    tp.get_workout_analysis.return_value = None
    service = TPSyncService(db=db_session, tp_client=tp)
    service.sync_completed_workouts(date(2026, 4, 4))

    completed = db_session.query(TPCompletedWorkout).all()
    assert len(completed) == 1
    assert completed[0].hr_zone1_sec is None


def test_sync_all(db_session):
    tp = make_mock_tp_client()
    service = TPSyncService(db=db_session, tp_client=tp)
    service.sync_all(date(2026, 4, 4))

    assert db_session.query(TPFitnessData).count() == 1
    assert db_session.query(TPPlannedWorkout).count() == 2
    assert db_session.query(TPCompletedWorkout).count() == 1

from datetime import date

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app
from app.models.activity import Activity
from app.models.tp_completed_workout import TPCompletedWorkout
from app.models.tp_fitness_data import TPFitnessData
from app.models.tp_planned_workout import TPPlannedWorkout

engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestSession = sessionmaker(bind=engine)


@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.create_all(engine)
    yield
    Base.metadata.drop_all(engine)


@pytest.fixture
def db():
    session = TestSession()
    yield session
    session.close()


@pytest.fixture
def client(db):
    def override():
        yield db

    app.dependency_overrides[get_db] = override
    yield TestClient(app)
    app.dependency_overrides.clear()


def test_pmc_returns_fitness_data(client, db):
    db.add(TPFitnessData(date=date(2026, 3, 1), ctl=80.0, atl=65.0, tsb=15.0, tss_day=50.0))
    db.add(TPFitnessData(date=date(2026, 3, 2), ctl=81.0, atl=66.0, tsb=15.0, tss_day=60.0))
    db.commit()
    resp = client.get("/api/aerobico/pmc?from_date=2026-03-01&to_date=2026-03-02")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 2
    assert data[0]["date"] == "2026-03-01"
    assert data[0]["ctl"] == 80.0
    assert data[1]["date"] == "2026-03-02"


def test_pmc_default_range(client, db):
    db.add(TPFitnessData(date=date.today(), ctl=80.0, atl=65.0, tsb=15.0, tss_day=50.0))
    db.commit()
    resp = client.get("/api/aerobico/pmc")
    assert resp.status_code == 200
    assert len(resp.json()) == 1


def test_pmc_empty(client, db):
    resp = client.get("/api/aerobico/pmc?from_date=2026-01-01&to_date=2026-01-31")
    assert resp.status_code == 200
    assert resp.json() == []


def test_calendar_returns_planned_and_completed(client, db):
    db.add(TPPlannedWorkout(
        tp_workout_id="plan-1", date=date(2026, 4, 10),
        title="Easy Run", workout_type="run",
        duration_sec_planned=3600, tss_planned=50, distance_m_planned=10000,
    ))
    db.add(TPCompletedWorkout(
        tp_workout_id="done-1", date=date(2026, 4, 3),
        title="Intervals", workout_type="run",
        tss=85, distance_m=12000, duration_sec=4200,
    ))
    db.commit()
    resp = client.get("/api/aerobico/calendar?from_date=2026-04-01&to_date=2026-04-15")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["planned"]) == 1
    assert data["planned"][0]["title"] == "Easy Run"
    assert len(data["completed"]) == 1
    assert data["completed"][0]["title"] == "Intervals"


def test_calendar_returns_tp_workout_id(client, db):
    db.add(TPPlannedWorkout(
        tp_workout_id="plan-99", date=date(2026, 4, 10),
        title="Easy Run", workout_type="run",
        duration_sec_planned=3600, tss_planned=50, distance_m_planned=10000,
    ))
    db.add(TPCompletedWorkout(
        tp_workout_id="done-99", date=date(2026, 4, 3),
        title="Intervals", workout_type="run",
        tss=85, distance_m=12000, duration_sec=4200,
    ))
    db.commit()
    resp = client.get("/api/aerobico/calendar?from_date=2026-04-01&to_date=2026-04-15")
    assert resp.status_code == 200
    data = resp.json()
    assert data["planned"][0]["tp_workout_id"] == "plan-99"
    assert data["completed"][0]["tp_workout_id"] == "done-99"


def test_calendar_empty(client, db):
    resp = client.get("/api/aerobico/calendar?from_date=2026-01-01&to_date=2026-01-31")
    assert resp.status_code == 200
    data = resp.json()
    assert data["planned"] == []
    assert data["completed"] == []


def test_volume_aggregates_by_week(client, db):
    db.add(Activity(
        garmin_id="r1", date=date(2026, 3, 30),
        type="running", distance_m=10000, elevation_gain=100,
    ))
    db.add(Activity(
        garmin_id="r2", date=date(2026, 4, 1),
        type="trail_running", distance_m=15000, elevation_gain=250,
    ))
    db.add(Activity(
        garmin_id="s1", date=date(2026, 4, 1),
        type="strength_training", distance_m=0, elevation_gain=0,
    ))
    db.commit()
    resp = client.get("/api/aerobico/volume?from_date=2026-03-30&to_date=2026-04-05")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]["km"] == 25.0
    assert data[0]["elevation_m"] == 350.0


def test_volume_empty(client, db):
    resp = client.get("/api/aerobico/volume?from_date=2026-01-01&to_date=2026-01-31")
    assert resp.status_code == 200
    assert resp.json() == []


def test_hr_zones_sums_across_workouts(client, db):
    db.add(TPCompletedWorkout(
        tp_workout_id="w1", date=date(2026, 4, 1), workout_type="run",
        hr_zone1_sec=600, hr_zone2_sec=1800, hr_zone3_sec=900, hr_zone4_sec=300, hr_zone5_sec=60,
    ))
    db.add(TPCompletedWorkout(
        tp_workout_id="w2", date=date(2026, 4, 3), workout_type="run",
        hr_zone1_sec=400, hr_zone2_sec=1200, hr_zone3_sec=600, hr_zone4_sec=200, hr_zone5_sec=40,
    ))
    db.commit()
    resp = client.get("/api/aerobico/hr-zones?from_date=2026-04-01&to_date=2026-04-05")
    assert resp.status_code == 200
    data = resp.json()
    assert data["zone1_sec"] == 1000
    assert data["zone2_sec"] == 3000
    assert data["zone3_sec"] == 1500
    assert data["zone4_sec"] == 500
    assert data["zone5_sec"] == 100


def test_hr_zones_empty(client, db):
    resp = client.get("/api/aerobico/hr-zones?from_date=2026-01-01&to_date=2026-01-31")
    assert resp.status_code == 200
    data = resp.json()
    assert data["zone1_sec"] == 0


def test_hr_zones_handles_null_values(client, db):
    db.add(TPCompletedWorkout(
        tp_workout_id="w3", date=date(2026, 4, 1), workout_type="run",
        hr_zone1_sec=600, hr_zone2_sec=None, hr_zone3_sec=900, hr_zone4_sec=None, hr_zone5_sec=None,
    ))
    db.commit()
    resp = client.get("/api/aerobico/hr-zones?from_date=2026-04-01&to_date=2026-04-05")
    assert resp.status_code == 200
    data = resp.json()
    assert data["zone1_sec"] == 600
    assert data["zone2_sec"] == 0
    assert data["zone3_sec"] == 900

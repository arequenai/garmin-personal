from datetime import date, datetime

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app
from app.models import (
    DailySummary,
    NutritionDaily,
    PerformanceMetric,
    SleepSession,
)
from app.models.stress_reading import StressReading
from app.models.user_goal import UserGoal

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


def seed_data(db, target=date(2026, 4, 4)):
    db.add(DailySummary(date=target, resting_hr=48, stress_avg=28, body_battery_high=72))
    db.add(SleepSession(
        date=target, total_sleep_min=452, deep_min=81, avg_hrv=52.0, sleep_score=85,
    ))
    db.add(NutritionDaily(date=target, calories=1420, protein_g=82.0, carbs_g=180.0, fat_g=55.0))
    db.add(PerformanceMetric(
        date=target, tss=65.0, atl=78.0, ctl=62.0, tsb=-16.0,
        vo2max=48.3, recovery_score=68.0,
    ))
    db.add(UserGoal(
        metric_key="calories", target_value=2200, target_unit="kcal", category="nutrition",
    ))
    db.add(UserGoal(metric_key="protein", target_value=125, target_unit="g", category="nutrition"))
    db.add(StressReading(date=target, timestamp=datetime(2026, 4, 4, 13, 30), value=30))
    db.add(StressReading(date=target, timestamp=datetime(2026, 4, 4, 13, 45), value=40))
    db.add(StressReading(date=target, timestamp=datetime(2026, 4, 4, 13, 55), value=38))
    db.commit()


def test_plan_daily_returns_strip_and_pillars(client, db):
    seed_data(db)
    resp = client.get("/api/plan/daily")
    assert resp.status_code == 200
    data = resp.json()
    assert "strip" in data
    assert "pillars" in data
    assert len(data["strip"]) == 6
    assert len(data["pillars"]) == 5
    # Check strip labels
    labels = [s["label"] for s in data["strip"]]
    assert "Calories" in labels
    assert "Protein" in labels
    assert "Stress 1h" in labels
    assert "HRV" in labels
    assert "TSB" in labels
    assert "Sleep" in labels


def test_plan_daily_calories_show_consumed_and_target(client, db):
    seed_data(db)
    resp = client.get("/api/plan/daily")
    data = resp.json()
    cal = next(s for s in data["strip"] if s["label"] == "Calories")
    assert cal["value"] == "1,420"
    # Adaptive target: base 1500 + carry-over from yesterday (under-ate by 80 → +40)
    assert cal["target"] == "1,540"
    assert cal["pct"] == 92  # 1420/1540 ~ 92.2 -> 92


def test_plan_daily_empty_db(client, db):
    resp = client.get("/api/plan/daily")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["strip"]) == 6
    assert len(data["pillars"]) == 5

from datetime import date, timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app
from app.models import DailySummary, NutritionDaily
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


def test_nutrition_returns_adaptive_target(client, db):
    target = date(2026, 4, 1)

    # Seed 7 days of daily summaries with varying exercise
    for i in range(8):
        d = target - timedelta(days=7 - i)
        active = 600 if i % 2 == 0 else 100
        db.add(DailySummary(date=d, calories_active=active))

    # Seed nutrition for today
    db.add(NutritionDaily(date=target, calories=1800))
    db.commit()

    resp = client.get(f"/api/nutrition?from_date={target}&to_date={target}")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    row = data[0]
    assert "calories_target_adaptive" in row
    assert row["calories_target_adaptive"] is not None
    assert isinstance(row["calories_target_adaptive"], int)
    # Should be > base (1500) because there's exercise data
    assert row["calories_target_adaptive"] > 1500


def test_nutrition_adaptive_target_with_long_run_tomorrow(client, db):
    target = date(2026, 4, 2)
    tomorrow = target + timedelta(days=1)

    db.add(DailySummary(date=target, calories_active=0))
    db.add(NutritionDaily(date=target, calories=1500))
    # Planned long run tomorrow (3 hours)
    db.add(TPPlannedWorkout(
        tp_workout_id="test-123",
        date=tomorrow,
        title="Long run",
        duration_sec_planned=10800,
    ))
    db.commit()

    resp = client.get(f"/api/nutrition?from_date={target}&to_date={target}")
    data = resp.json()
    row = data[0]
    # Should include preload bonus (+200)
    assert row["calories_target_adaptive"] == 1700  # base 1500 + preload 200


def test_meals_endpoint_groups_entries_by_bucket(client, db):
    db.add(NutritionDaily(
        date=date(2026, 5, 3),
        calories=1800,
        protein_g=120,
        carbs_g=200,
        fat_g=60,
        entries=[
            {"meal": "breakfast", "name": "Oats", "calories": 300,
             "protein_g": 10, "carbs_g": 50, "fat_g": 5, "position": 0},
            {"meal": "lunch", "name": "Chicken", "calories": 400,
             "protein_g": 50, "carbs_g": 0, "fat_g": 10, "position": 1},
            {"meal": "other", "name": "Coffee", "calories": 5,
             "protein_g": 0, "carbs_g": 0, "fat_g": 0, "position": 2},
        ],
    ))
    db.commit()

    resp = client.get("/api/nutrition/2026-05-03/meals")
    assert resp.status_code == 200
    body = resp.json()
    assert body["date"] == "2026-05-03"
    assert len(body["meals"]["breakfast"]) == 1
    assert body["meals"]["breakfast"][0]["name"] == "Oats"
    assert len(body["meals"]["lunch"]) == 1
    assert len(body["meals"]["other"]) == 1
    assert body["meals"]["dinner"] == []
    assert body["meals"]["snacks"] == []
    assert body["totals"]["calories"] == 1800


def test_meals_endpoint_returns_404_when_missing(client):
    resp = client.get("/api/nutrition/2099-01-01/meals")
    assert resp.status_code == 404

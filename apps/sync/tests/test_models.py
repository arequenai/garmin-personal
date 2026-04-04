import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base
from app.models import (
    Activity,
    DailySummary,
    NutritionDaily,
    PerformanceMetric,
    SleepSession,
    StrengthSession,
    User,
)


@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine)
    session = session_factory()
    yield session
    session.close()


def test_all_models_importable():
    assert User.__tablename__ == "users"
    assert DailySummary.__tablename__ == "daily_summaries"
    assert SleepSession.__tablename__ == "sleep_sessions"
    assert Activity.__tablename__ == "activities"
    assert StrengthSession.__tablename__ == "strength_sessions"
    assert NutritionDaily.__tablename__ == "nutrition_daily"
    assert PerformanceMetric.__tablename__ == "performance_metrics"


def test_user_has_required_columns():
    columns = {c.name for c in User.__table__.columns}
    assert "garmin_email" in columns
    assert "hr_max" in columns
    assert "hr_threshold" in columns


def test_activity_has_tss_column():
    columns = {c.name for c in Activity.__table__.columns}
    assert "tss" in columns
    assert "garmin_id" in columns


def test_strength_session_has_fk():
    columns = {c.name for c in StrengthSession.__table__.columns}
    assert "activity_id" in columns


def test_stress_reading_creation(db_session):
    from datetime import date, datetime

    from app.models.stress_reading import StressReading

    reading = StressReading(
        date=date(2026, 4, 4),
        timestamp=datetime(2026, 4, 4, 10, 30, 0),
        value=42,
    )
    db_session.add(reading)
    db_session.commit()

    result = db_session.query(StressReading).first()
    assert result.value == 42
    assert result.date == date(2026, 4, 4)
    assert result.timestamp == datetime(2026, 4, 4, 10, 30, 0)

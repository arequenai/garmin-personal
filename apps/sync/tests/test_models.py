from app.models import (
    Activity,
    DailySummary,
    NutritionDaily,
    PerformanceMetric,
    SleepSession,
    StrengthSession,
    User,
)


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

from datetime import date, timedelta

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base
from app.models import Activity, PerformanceMetric, SleepSession
from app.services.performance_updater import PerformanceUpdater


@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine)
    session = session_factory()
    yield session
    session.close()


def add_activity(db, target_date, garmin_id, tss):
    act = Activity(
        garmin_id=garmin_id,
        date=target_date,
        type="running",
        name="Test Run",
        tss=tss,
    )
    db.add(act)
    db.commit()


def test_update_creates_performance_metric(db_session):
    target = date(2026, 3, 6)
    add_activity(db_session, target, "1", 80.0)
    updater = PerformanceUpdater(db=db_session)
    updater.update(target)
    pm = db_session.query(PerformanceMetric).filter_by(date=target).first()
    assert pm is not None
    assert pm.tss == 80.0
    assert pm.atl > 0
    assert pm.ctl > 0


def test_update_aggregates_multiple_activities(db_session):
    target = date(2026, 3, 6)
    add_activity(db_session, target, "1", 50.0)
    add_activity(db_session, target, "2", 30.0)
    updater = PerformanceUpdater(db=db_session)
    updater.update(target)
    pm = db_session.query(PerformanceMetric).filter_by(date=target).first()
    assert pm.tss == 80.0


def test_update_with_no_activities(db_session):
    target = date(2026, 3, 6)
    updater = PerformanceUpdater(db=db_session)
    updater.update(target)
    pm = db_session.query(PerformanceMetric).filter_by(date=target).first()
    # Should still create a record with 0 TSS
    assert pm is not None
    assert pm.tss == 0.0


def test_update_calculates_training_loads(db_session):
    # Add activities over multiple days
    base_date = date(2026, 2, 1)
    for i in range(30):
        d = base_date + timedelta(days=i)
        add_activity(db_session, d, str(i), 50.0)

    target = base_date + timedelta(days=29)
    updater = PerformanceUpdater(db=db_session)
    updater.update(target)
    pm = db_session.query(PerformanceMetric).filter_by(date=target).first()

    assert pm.training_load_7d == pytest.approx(350.0, rel=0.01)  # 7 * 50
    assert pm.training_load_28d == pytest.approx(1400.0, rel=0.01)  # 28 * 50
    assert pm.atl > 40  # Should converge toward 50
    assert pm.ctl > 20  # 42-day EWMA slower to converge


def test_update_upserts(db_session):
    target = date(2026, 3, 6)
    add_activity(db_session, target, "1", 50.0)
    updater = PerformanceUpdater(db=db_session)
    updater.update(target)
    # Update again
    updater.update(target)
    records = db_session.query(PerformanceMetric).filter_by(date=target).all()
    assert len(records) == 1


def test_update_includes_recovery_score(db_session):
    target = date(2026, 3, 6)
    # Add sleep data
    sleep = SleepSession(date=target, sleep_score=85, avg_hrv=60.0)
    db_session.add(sleep)
    db_session.commit()
    add_activity(db_session, target, "1", 50.0)
    updater = PerformanceUpdater(db=db_session)
    updater.update(target)
    pm = db_session.query(PerformanceMetric).filter_by(date=target).first()
    assert pm.recovery_score is not None
    assert 0 <= pm.recovery_score <= 100

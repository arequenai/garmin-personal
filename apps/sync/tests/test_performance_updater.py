from datetime import date

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base
from app.models import Activity, PerformanceMetric, SleepSession
from app.models.tp_fitness_data import TPFitnessData
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
    updater = PerformanceUpdater(db=db_session)
    updater.update(target)
    pm = db_session.query(PerformanceMetric).filter_by(date=target).first()
    assert pm is not None
    assert pm.category_scores is not None


def test_update_reads_ctl_tsb_from_tp(db_session):
    target = date(2026, 3, 6)
    db_session.add(TPFitnessData(date=target, ctl=55.0, tsb=-10.0, atl=65.0, tss_day=80.0))
    db_session.commit()
    updater = PerformanceUpdater(db=db_session)
    updater.update(target)
    pm = db_session.query(PerformanceMetric).filter_by(date=target).first()
    # PerformanceUpdater uses TP's CTL/TSB for category scores, not its own
    assert pm.category_scores is not None
    assert "recovery" in pm.category_scores


def test_update_with_no_tp_data(db_session):
    target = date(2026, 3, 6)
    updater = PerformanceUpdater(db=db_session)
    updater.update(target)
    pm = db_session.query(PerformanceMetric).filter_by(date=target).first()
    assert pm is not None
    # Should still create a record even without TP data
    assert pm.category_scores is not None


def test_update_computes_category_scores(db_session):
    target = date(2026, 3, 6)
    # Add running activity for running score
    add_activity(db_session, target, "1", 50.0)
    db_session.add(TPFitnessData(date=target, ctl=50.0, tsb=5.0, atl=45.0, tss_day=50.0))
    db_session.add(SleepSession(date=target, sleep_score=80, avg_hrv=55.0))
    db_session.commit()
    updater = PerformanceUpdater(db=db_session)
    updater.update(target)
    pm = db_session.query(PerformanceMetric).filter_by(date=target).first()
    scores = pm.category_scores
    assert "running" in scores
    assert "strength" in scores
    assert "recovery" in scores
    assert "sleep" in scores
    assert "body" in scores


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

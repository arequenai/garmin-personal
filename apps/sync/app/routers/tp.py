import logging
from contextlib import contextmanager
from datetime import date, timedelta

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.models.tp_completed_workout import TPCompletedWorkout
from app.models.tp_fitness_data import TPFitnessData
from app.models.tp_planned_workout import TPPlannedWorkout
from app.schemas.tp import (
    TPCompletedWorkoutResponse,
    TPFitnessResponse,
    TPPlannedWorkoutResponse,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/tp", tags=["trainingpeaks"])


@contextmanager
def _tp_session():
    """Create a TP sync session with authenticated client. Used by background tasks."""
    from app.database import SessionLocal
    from app.services.tp_sync_service import TPSyncService
    from app.services.trainingpeaks_client import TrainingPeaksClient

    db = SessionLocal()
    try:
        tp_client = TrainingPeaksClient(auth_cookie=settings.tp_auth_cookie)
        tp_client.login()
        yield TPSyncService(db=db, tp_client=tp_client)
    finally:
        db.close()


@router.get("/fitness", response_model=list[TPFitnessResponse])
def list_fitness(
    from_date: date = Query(default_factory=lambda: date.today() - timedelta(days=90)),
    to_date: date = Query(default_factory=lambda: date.today()),
    db: Session = Depends(get_db),
):
    return (
        db.query(TPFitnessData)
        .filter(TPFitnessData.date >= from_date, TPFitnessData.date <= to_date)
        .order_by(TPFitnessData.date.desc())
        .all()
    )


@router.get("/workouts/planned", response_model=list[TPPlannedWorkoutResponse])
def list_planned_workouts(
    from_date: date = Query(default_factory=lambda: date.today()),
    to_date: date = Query(default_factory=lambda: date.today() + timedelta(days=30)),
    db: Session = Depends(get_db),
):
    return (
        db.query(TPPlannedWorkout)
        .filter(TPPlannedWorkout.date >= from_date, TPPlannedWorkout.date <= to_date)
        .order_by(TPPlannedWorkout.date)
        .all()
    )


@router.get("/workouts/completed", response_model=list[TPCompletedWorkoutResponse])
def list_completed_workouts(
    from_date: date = Query(default_factory=lambda: date.today() - timedelta(days=30)),
    to_date: date = Query(default_factory=lambda: date.today()),
    db: Session = Depends(get_db),
):
    return (
        db.query(TPCompletedWorkout)
        .filter(TPCompletedWorkout.date >= from_date, TPCompletedWorkout.date <= to_date)
        .order_by(TPCompletedWorkout.date.desc())
        .all()
    )


@router.get("/workouts/{tp_workout_id}", response_model=TPCompletedWorkoutResponse)
def get_completed_workout(tp_workout_id: str, db: Session = Depends(get_db)):
    record = (
        db.query(TPCompletedWorkout)
        .filter(TPCompletedWorkout.tp_workout_id == tp_workout_id)
        .first()
    )
    if not record:
        raise HTTPException(status_code=404, detail="Workout not found")
    return record


def _run_tp_sync(days_back: int) -> None:
    """Run TP sync for a date range."""
    with _tp_session() as tp_sync:
        today = date.today()
        for i in range(days_back, -1, -1):
            target = today - timedelta(days=i)
            try:
                tp_sync.sync_all(target)
                logger.info("TP sync completed for %s", target)
            except Exception:
                logger.error("TP sync failed for %s", target, exc_info=True)


@router.post("/sync/trigger")
def trigger_tp_sync(
    background_tasks: BackgroundTasks,
    days_back: int = 7,
):
    if not settings.tp_enabled or not settings.tp_auth_cookie:
        raise HTTPException(status_code=400, detail="TrainingPeaks not configured")
    background_tasks.add_task(_run_tp_sync, days_back)
    return {"status": "tp_sync_started", "days_back": days_back}


def _run_tp_fitness_backfill(days_back: int) -> None:
    """Backfill TP fitness (PMC) data in a single API call."""
    with _tp_session() as tp_sync:
        end = date.today()
        start = end - timedelta(days=days_back)
        try:
            tp_sync.sync_fitness_range(start, end)
            logger.info("TP fitness backfill completed: %s to %s", start, end)
        except Exception:
            logger.error("TP fitness backfill failed", exc_info=True)


@router.post("/sync/fitness-backfill")
def trigger_tp_fitness_backfill(
    background_tasks: BackgroundTasks,
    days_back: int = 365,
):
    """Backfill TP fitness/PMC data for the last N days in a single API call."""
    if not settings.tp_enabled or not settings.tp_auth_cookie:
        raise HTTPException(status_code=400, detail="TrainingPeaks not configured")
    background_tasks.add_task(_run_tp_fitness_backfill, days_back)
    start = date.today() - timedelta(days=days_back)
    return {
        "status": "tp_fitness_backfill_started",
        "from_date": start.isoformat(),
        "to_date": date.today().isoformat(),
    }


def _run_tp_workouts_backfill(days_back: int) -> None:
    """Backfill TP completed workouts in 30-day chunks."""
    with _tp_session() as tp_sync:
        end = date.today()
        start = end - timedelta(days=days_back)
        chunk_start = start
        while chunk_start < end:
            chunk_end = min(chunk_start + timedelta(days=30), end)
            try:
                tp_sync.sync_completed_workouts_range(chunk_start, chunk_end)
                logger.info("TP workouts backfill chunk: %s to %s", chunk_start, chunk_end)
            except Exception:
                logger.warning(
                    "TP workouts backfill chunk failed: %s to %s",
                    chunk_start, chunk_end, exc_info=True,
                )
            chunk_start = chunk_end + timedelta(days=1)
        logger.info("TP workouts backfill completed: %s to %s", start, end)


def _run_tp_zones_backfill() -> None:
    """Re-fetch workout details (HR/power zones) for workouts missing zone data.

    Processes in batches of 100 to avoid unbounded memory usage and commits
    after each batch so progress is not lost on failure.
    """
    BATCH_SIZE = 100
    with _tp_session() as tp_sync:
        total_filled = 0
        while True:
            batch = (
                tp_sync.db.query(TPCompletedWorkout)
                .filter(
                    or_(
                        TPCompletedWorkout.hr_zone1_sec == None,  # noqa: E711
                        TPCompletedWorkout.workout_details_json == None,  # noqa: E711
                    )
                )
                .limit(BATCH_SIZE)
                .all()
            )
            if not batch:
                break
            logger.info("Zones backfill batch: %d workouts", len(batch))
            filled = 0
            for w in batch:
                details = tp_sync.tp.get_workout_details(w.tp_workout_id)
                if not details:
                    continue
                w.workout_details_json = details
                zones = tp_sync._extract_zones(details)
                if any(v > 0 for v in zones.values()):
                    for k, v in zones.items():
                        setattr(w, k, v)
                    filled += 1
            tp_sync.db.commit()
            total_filled += filled
            logger.info("Zones backfill batch done: %d updated", filled)
            if len(batch) < BATCH_SIZE:
                break
        logger.info("Zones backfill completed: %d total workouts updated", total_filled)


@router.post("/sync/zones-backfill")
def trigger_tp_zones_backfill(background_tasks: BackgroundTasks):
    """Re-fetch HR/power zone data for all workouts missing it."""
    if not settings.tp_enabled or not settings.tp_auth_cookie:
        raise HTTPException(status_code=400, detail="TrainingPeaks not configured")
    background_tasks.add_task(_run_tp_zones_backfill)
    return {"status": "tp_zones_backfill_started"}


@router.post("/sync/workouts-backfill")
def trigger_tp_workouts_backfill(
    background_tasks: BackgroundTasks,
    days_back: int = 365,
):
    """Backfill TP completed workouts for the last N days in a single API call."""
    if not settings.tp_enabled or not settings.tp_auth_cookie:
        raise HTTPException(status_code=400, detail="TrainingPeaks not configured")
    background_tasks.add_task(_run_tp_workouts_backfill, days_back)
    start = date.today() - timedelta(days=days_back)
    return {
        "status": "tp_workouts_backfill_started",
        "from_date": start.isoformat(),
        "to_date": date.today().isoformat(),
    }

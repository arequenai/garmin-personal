import logging
from datetime import date, timedelta

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
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
    from app.database import SessionLocal
    from app.services.tp_sync_service import TPSyncService
    from app.services.trainingpeaks_client import TrainingPeaksClient

    db = SessionLocal()
    try:
        tp_client = TrainingPeaksClient(auth_cookie=settings.tp_auth_cookie)
        tp_client.login()
        tp_sync = TPSyncService(db=db, tp_client=tp_client)
        today = date.today()
        for i in range(days_back, -1, -1):
            target = today - timedelta(days=i)
            try:
                tp_sync.sync_all(target)
                logger.info("TP sync completed for %s", target)
            except Exception:
                logger.error("TP sync failed for %s", target, exc_info=True)
    finally:
        db.close()


@router.post("/sync/trigger")
def trigger_tp_sync(
    background_tasks: BackgroundTasks,
    days_back: int = 7,
):
    if not settings.tp_enabled or not settings.tp_auth_cookie:
        raise HTTPException(status_code=400, detail="TrainingPeaks not configured")
    background_tasks.add_task(_run_tp_sync, days_back)
    return {"status": "tp_sync_started", "days_back": days_back}

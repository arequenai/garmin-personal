"""Live TrainingPeaks API proxy endpoints.

These endpoints call the TP API directly (via cookie auth) and return
the response without persisting to the database.
"""

import logging
from datetime import date, timedelta

from fastapi import APIRouter, HTTPException, Query

from app.config import settings
from app.services.trainingpeaks_client import TrainingPeaksClient

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/tp", tags=["trainingpeaks-live"])


def _get_tp_client() -> TrainingPeaksClient:
    if not settings.tp_enabled or not settings.tp_auth_cookie:
        raise HTTPException(status_code=400, detail="TrainingPeaks not configured")
    client = TrainingPeaksClient(auth_cookie=settings.tp_auth_cookie)
    client.login()
    return client


@router.get("/training-load")
def get_training_load(
    from_date: date = Query(default_factory=lambda: date.today() - timedelta(days=90)),
    to_date: date = Query(default_factory=date.today),
):
    """Return daily CTL, ATL, TSB from TrainingPeaks PMC."""
    client = _get_tp_client()
    raw = client.get_fitness(from_date.isoformat(), to_date.isoformat())
    daily = []
    for entry in raw:
        daily.append(
            {
                "date": entry.get("workoutDay", "").split("T")[0],
                "tss": entry.get("tssActual", 0),
                "ctl": round(entry.get("ctl", 0), 1),
                "atl": round(entry.get("atl", 0), 1),
                "tsb": round(entry.get("tsb", 0), 1),
            }
        )
    return daily


@router.get("/workouts")
def list_workouts(
    from_date: date = Query(default_factory=lambda: date.today() - timedelta(days=30)),
    to_date: date = Query(default_factory=date.today),
):
    """List workouts with TSS, IF, duration, type, and name."""
    client = _get_tp_client()
    raw = client.get_workouts(from_date.isoformat(), to_date.isoformat())
    workouts = []
    for w in raw:
        workouts.append(
            {
                "id": w.get("workoutId"),
                "date": (w.get("workoutDay") or "").split("T")[0],
                "title": w.get("title"),
                "workout_type": w.get("workoutTypeValueId"),
                "completed": w.get("completed", False),
                "tss_planned": w.get("tssPlanned"),
                "tss_actual": w.get("tssActual"),
                "if_planned": w.get("ifPlanned"),
                "if_actual": w.get("if"),
                "duration_planned": w.get("totalTimePlanned"),
                "duration_actual": w.get("totalTime"),
                "distance_planned": w.get("distancePlanned"),
                "distance_actual": w.get("distance"),
            }
        )
    return workouts


@router.get("/workout/{workout_id}")
def get_workout(workout_id: str):
    """Get full details for a single workout."""
    client = _get_tp_client()
    details = client.get_workout_details(workout_id)
    if details is None:
        raise HTTPException(status_code=404, detail="Workout not found")
    return details

from datetime import date, timedelta

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.constants import RUNNING_TYPES
from app.database import get_db
from app.models.activity import Activity
from app.models.tp_completed_workout import TPCompletedWorkout
from app.models.tp_fitness_data import TPFitnessData
from app.models.tp_planned_workout import TPPlannedWorkout
from app.schemas.aerobico import (
    CalendarCompletedWorkout,
    CalendarPlannedWorkout,
    CalendarResponse,
    HRZonesResponse,
    PMCDataPoint,
    WeeklyVolume,
)

router = APIRouter(prefix="/api/aerobico", tags=["aerobico"])


@router.get("/pmc", response_model=list[PMCDataPoint])
def get_pmc(
    from_date: date = Query(default_factory=lambda: date.today() - timedelta(days=365)),
    to_date: date = Query(default_factory=lambda: date.today()),
    db: Session = Depends(get_db),
):
    return (
        db.query(TPFitnessData)
        .filter(TPFitnessData.date >= from_date, TPFitnessData.date <= to_date)
        .order_by(TPFitnessData.date)
        .all()
    )


@router.get("/calendar", response_model=CalendarResponse)
def get_calendar(
    from_date: date = Query(default_factory=lambda: date.today() - timedelta(days=30)),
    to_date: date = Query(default_factory=lambda: date.today() + timedelta(days=30)),
    db: Session = Depends(get_db),
):
    planned = (
        db.query(TPPlannedWorkout)
        .filter(TPPlannedWorkout.date >= from_date, TPPlannedWorkout.date <= to_date)
        .order_by(TPPlannedWorkout.date)
        .all()
    )
    completed = (
        db.query(TPCompletedWorkout)
        .filter(TPCompletedWorkout.date >= from_date, TPCompletedWorkout.date <= to_date)
        .order_by(TPCompletedWorkout.date)
        .all()
    )
    return CalendarResponse(planned=planned, completed=completed)


@router.get("/volume", response_model=list[WeeklyVolume])
def get_volume(
    from_date: date = Query(default_factory=lambda: date.today() - timedelta(weeks=12)),
    to_date: date = Query(default_factory=lambda: date.today()),
    db: Session = Depends(get_db),
):
    activities = (
        db.query(Activity)
        .filter(
            Activity.date >= from_date,
            Activity.date <= to_date,
            Activity.type.in_(RUNNING_TYPES),
        )
        .all()
    )

    weeks: dict[date, dict] = {}
    for a in activities:
        week_start = a.date - timedelta(days=a.date.weekday())
        if week_start not in weeks:
            weeks[week_start] = {"km": 0.0, "elevation_m": 0.0}
        weeks[week_start]["km"] += round((a.distance_m or 0) / 1000, 2)
        weeks[week_start]["elevation_m"] += float(a.elevation_gain or 0)

    result = [
        WeeklyVolume(
            week_start=ws,
            km=round(vals["km"], 1),
            elevation_m=round(vals["elevation_m"], 0),
        )
        for ws, vals in sorted(weeks.items())
    ]
    return result


@router.get("/hr-zones", response_model=HRZonesResponse)
def get_hr_zones(
    from_date: date = Query(default_factory=lambda: date.today() - timedelta(weeks=4)),
    to_date: date = Query(default_factory=lambda: date.today()),
    db: Session = Depends(get_db),
):
    workouts = (
        db.query(TPCompletedWorkout)
        .filter(TPCompletedWorkout.date >= from_date, TPCompletedWorkout.date <= to_date)
        .all()
    )

    totals = {f"zone{i}_sec": 0 for i in range(1, 6)}
    for w in workouts:
        for i in range(1, 6):
            totals[f"zone{i}_sec"] += getattr(w, f"hr_zone{i}_sec", None) or 0

    return HRZonesResponse(**totals)

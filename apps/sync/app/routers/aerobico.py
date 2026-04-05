from datetime import date, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.constants import RUNNING_TYPES
from app.database import get_db
from app.models.activity import Activity
from app.models.tp_completed_workout import TPCompletedWorkout
from app.models.tp_fitness_data import TPFitnessData
from app.models.tp_planned_workout import TPPlannedWorkout
from app.schemas.aerobico import (
    CalendarResponse,
    CompletedWorkoutDetail,
    PlannedWorkoutDetail,
    PMCDataPoint,
    WeeklyHRZones,
    WeeklyVolume,
    WorkoutWithPlannedResponse,
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
    # Garmin activities (have elevation data)
    garmin = (
        db.query(Activity)
        .filter(
            Activity.date >= from_date,
            Activity.date <= to_date,
            Activity.type.in_(RUNNING_TYPES),
        )
        .all()
    )

    # TP completed workouts with running type (broader date coverage)
    tp_running_keywords = ("run",)
    tp = (
        db.query(TPCompletedWorkout)
        .filter(
            TPCompletedWorkout.date >= from_date,
            TPCompletedWorkout.date <= to_date,
        )
        .all()
    )

    weeks: dict[date, dict] = {}

    # Track Garmin dates to avoid double-counting
    garmin_dates_with_distance: set[tuple[date, float]] = set()
    for a in garmin:
        week_start = a.date - timedelta(days=a.date.weekday())
        if week_start not in weeks:
            weeks[week_start] = {"km": 0.0, "elevation_m": 0.0}
        km = round((a.distance_m or 0) / 1000, 2)
        weeks[week_start]["km"] += km
        weeks[week_start]["elevation_m"] += float(a.elevation_gain or 0)
        if km > 0:
            garmin_dates_with_distance.add((a.date, round(km, 1)))

    # Fill in from TP for dates/distances not already covered by Garmin
    for w in tp:
        wtype = (w.workout_type or "").lower()
        if not any(kw in wtype for kw in tp_running_keywords):
            continue
        km = round((w.distance_m or 0) / 1000, 1)
        if km <= 0:
            continue
        if (w.date, km) in garmin_dates_with_distance:
            continue
        week_start = w.date - timedelta(days=w.date.weekday())
        if week_start not in weeks:
            weeks[week_start] = {"km": 0.0, "elevation_m": 0.0}
        weeks[week_start]["km"] += km
        weeks[week_start]["elevation_m"] += float(w.elevation_gain_m or 0)

    # Fill all weeks in range so the chart always spans the selected window
    first_week = from_date - timedelta(days=from_date.weekday())
    last_week = to_date - timedelta(days=to_date.weekday())
    ws = first_week
    while ws <= last_week:
        if ws not in weeks:
            weeks[ws] = {"km": 0.0, "elevation_m": 0.0}
        ws += timedelta(weeks=1)

    result = [
        WeeklyVolume(
            week_start=ws,
            km=round(vals["km"], 1),
            elevation_m=round(vals["elevation_m"], 0),
        )
        for ws, vals in sorted(weeks.items())
    ]
    return result


@router.get("/hr-zones", response_model=list[WeeklyHRZones])
def get_hr_zones(
    from_date: date = Query(default_factory=lambda: date.today() - timedelta(weeks=4)),
    to_date: date = Query(default_factory=lambda: date.today()),
    db: Session = Depends(get_db),
):
    workouts = (
        db.query(TPCompletedWorkout)
        .filter(
            TPCompletedWorkout.date >= from_date,
            TPCompletedWorkout.date <= to_date,
        )
        .all()
    )

    # Build all weeks in range
    first_week = from_date - timedelta(days=from_date.weekday())
    last_week = to_date - timedelta(days=to_date.weekday())
    weeks: dict[date, dict[str, int]] = {}
    ws = first_week
    while ws <= last_week:
        weeks[ws] = {f"zone{i}_sec": 0 for i in range(1, 6)}
        ws += timedelta(weeks=1)

    # Accumulate zone data, excluding strength workouts
    for w in workouts:
        if (w.workout_type or "").lower() in ("strength",):
            continue
        week_start = w.date - timedelta(days=w.date.weekday())
        if week_start not in weeks:
            weeks[week_start] = {f"zone{i}_sec": 0 for i in range(1, 6)}
        for i in range(1, 6):
            weeks[week_start][f"zone{i}_sec"] += getattr(w, f"hr_zone{i}_sec", None) or 0

    return [
        WeeklyHRZones(week_start=ws, **vals)
        for ws, vals in sorted(weeks.items())
    ]


@router.get("/workout/{tp_workout_id}", response_model=WorkoutWithPlannedResponse)
def get_workout_detail(
    tp_workout_id: str,
    type: str = Query(default="completed"),
    db: Session = Depends(get_db),
):
    if type == "planned":
        workout = (
            db.query(TPPlannedWorkout)
            .filter(TPPlannedWorkout.tp_workout_id == tp_workout_id)
            .first()
        )
        if not workout:
            raise HTTPException(status_code=404, detail="Workout not found")

        completed = None
        if workout.title:
            completed = (
                db.query(TPCompletedWorkout)
                .filter(
                    TPCompletedWorkout.date == workout.date,
                    TPCompletedWorkout.title.ilike(workout.title),
                )
                .first()
            )

        return WorkoutWithPlannedResponse(
            workout=PlannedWorkoutDetail.model_validate(workout),
            completed=CompletedWorkoutDetail.model_validate(completed) if completed else None,
        )

    # Default: completed
    workout = (
        db.query(TPCompletedWorkout)
        .filter(TPCompletedWorkout.tp_workout_id == tp_workout_id)
        .first()
    )
    if not workout:
        raise HTTPException(status_code=404, detail="Workout not found")

    planned = None
    if workout.title:
        planned = (
            db.query(TPPlannedWorkout)
            .filter(
                TPPlannedWorkout.date == workout.date,
                TPPlannedWorkout.title.ilike(workout.title),
            )
            .first()
        )

    return WorkoutWithPlannedResponse(
        workout=CompletedWorkoutDetail.model_validate(workout),
        planned=PlannedWorkoutDetail.model_validate(planned) if planned else None,
    )

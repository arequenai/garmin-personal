from datetime import date

from pydantic import BaseModel


class PMCDataPoint(BaseModel):
    date: date
    ctl: float | None
    atl: float | None
    tsb: float | None
    tss_day: float | None

    model_config = {"from_attributes": True}


class CalendarPlannedWorkout(BaseModel):
    date: date
    title: str | None
    workout_type: str | None
    description: str | None
    duration_sec_planned: int | None
    tss_planned: float | None
    distance_m_planned: float | None

    model_config = {"from_attributes": True}


class CalendarCompletedWorkout(BaseModel):
    date: date
    title: str | None
    workout_type: str | None
    description: str | None
    tss: float | None
    distance_m: float | None
    duration_sec: int | None

    model_config = {"from_attributes": True}


class CalendarResponse(BaseModel):
    planned: list[CalendarPlannedWorkout]
    completed: list[CalendarCompletedWorkout]


class WeeklyVolume(BaseModel):
    week_start: date
    km: float
    elevation_m: float


class WeeklyHRZones(BaseModel):
    week_start: date
    zone1_sec: int
    zone2_sec: int
    zone3_sec: int
    zone4_sec: int
    zone5_sec: int

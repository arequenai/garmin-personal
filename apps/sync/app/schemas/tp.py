from datetime import date

from pydantic import BaseModel


class TPFitnessResponse(BaseModel):
    id: int
    date: date
    ctl: float | None
    atl: float | None
    tsb: float | None
    tss_day: float | None
    training_load_7d: float | None
    training_load_28d: float | None
    intensity_factor: float | None
    ramp_rate: float | None

    model_config = {"from_attributes": True}


class TPPlannedWorkoutResponse(BaseModel):
    id: int
    tp_workout_id: str
    date: date
    title: str | None
    workout_type: str | None
    description: str | None
    duration_sec_planned: int | None
    tss_planned: float | None
    distance_m_planned: float | None
    structure_json: dict | None
    completed: bool | None

    model_config = {"from_attributes": True}


class TPCompletedWorkoutResponse(BaseModel):
    id: int
    tp_workout_id: str
    date: date
    title: str | None
    workout_type: str | None
    duration_sec: int | None
    distance_m: float | None
    tss: float | None
    intensity_factor: float | None
    avg_hr: int | None
    max_hr: int | None
    avg_power: float | None
    max_power: float | None
    normalized_power: float | None
    calories: int | None
    elevation_gain_m: float | None
    hr_zone1_sec: int | None
    hr_zone2_sec: int | None
    hr_zone3_sec: int | None
    hr_zone4_sec: int | None
    hr_zone5_sec: int | None
    power_zone1_sec: int | None
    power_zone2_sec: int | None
    power_zone3_sec: int | None
    power_zone4_sec: int | None
    power_zone5_sec: int | None
    power_zone6_sec: int | None
    power_zone7_sec: int | None

    model_config = {"from_attributes": True}

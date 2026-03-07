from datetime import date

from pydantic import BaseModel


class DailySummaryResponse(BaseModel):
    id: int
    date: date
    steps: int | None
    calories_total: int | None
    calories_active: int | None
    distance_m: float | None
    floors: int | None
    avg_hr: int | None
    resting_hr: int | None
    max_hr: int | None
    min_hr: int | None
    stress_avg: int | None
    stress_max: int | None
    body_battery_high: int | None
    body_battery_low: int | None
    spo2_avg: float | None
    respiration_avg: float | None
    hydration_ml: int | None

    model_config = {"from_attributes": True}

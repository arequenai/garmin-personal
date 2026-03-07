from datetime import date

from pydantic import BaseModel


class ActivityResponse(BaseModel):
    id: int
    garmin_id: str
    date: date
    type: str | None
    name: str | None
    duration_sec: int | None
    distance_m: float | None
    calories: int | None
    avg_hr: int | None
    max_hr: int | None
    avg_power: float | None
    max_power: float | None
    training_effect_aerobic: float | None
    training_effect_anaerobic: float | None
    vo2max_estimate: float | None
    elevation_gain: float | None
    tss: float | None

    model_config = {"from_attributes": True}

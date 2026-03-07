from datetime import date, datetime

from pydantic import BaseModel


class SleepResponse(BaseModel):
    id: int
    date: date
    sleep_start: datetime | None
    sleep_end: datetime | None
    total_sleep_min: int | None
    deep_min: int | None
    light_min: int | None
    rem_min: int | None
    awake_min: int | None
    avg_hr_sleep: int | None
    avg_hrv: float | None
    avg_spo2_sleep: float | None
    sleep_score: int | None

    model_config = {"from_attributes": True}

from datetime import date

from pydantic import BaseModel


class PerformanceResponse(BaseModel):
    id: int
    date: date
    tss: float | None
    atl: float | None
    ctl: float | None
    tsb: float | None
    training_load_7d: float | None
    training_load_28d: float | None
    recovery_score: float | None

    model_config = {"from_attributes": True}

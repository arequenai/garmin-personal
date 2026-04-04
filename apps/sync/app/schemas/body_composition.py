from datetime import date

from pydantic import BaseModel


class BodyCompositionResponse(BaseModel):
    date: date
    weight_kg: float | None
    body_fat_pct: float | None

    model_config = {"from_attributes": True}

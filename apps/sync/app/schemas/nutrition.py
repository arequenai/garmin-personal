from datetime import date

from pydantic import BaseModel


class NutritionResponse(BaseModel):
    id: int
    date: date
    calories: int | None
    protein_g: float | None
    carbs_g: float | None
    fat_g: float | None
    fiber_g: float | None
    sodium_mg: float | None

    model_config = {"from_attributes": True}

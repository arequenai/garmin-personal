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
    calories_goal: int | None = None
    protein_goal_g: float | None = None
    alcohol_drinks: int | None = None
    calories_target_adaptive: int | None = None

    model_config = {"from_attributes": True}


class NutritionEntryResponse(BaseModel):
    meal: str
    name: str
    calories: float | None = None
    protein_g: float | None = None
    carbs_g: float | None = None
    fat_g: float | None = None
    position: int


class NutritionMealsTotals(BaseModel):
    calories: float | None = None
    protein_g: float | None = None
    carbs_g: float | None = None
    fat_g: float | None = None


class NutritionMealsResponse(BaseModel):
    date: date
    meals: dict[str, list[NutritionEntryResponse]]
    totals: NutritionMealsTotals

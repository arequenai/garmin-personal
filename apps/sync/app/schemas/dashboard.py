from datetime import date

from pydantic import BaseModel

from app.schemas.activity import ActivityResponse
from app.schemas.daily import DailySummaryResponse
from app.schemas.nutrition import NutritionResponse
from app.schemas.performance import PerformanceResponse
from app.schemas.sleep import SleepResponse


class DashboardResponse(BaseModel):
    date: date
    daily_summary: DailySummaryResponse | None
    sleep: SleepResponse | None
    latest_activity: ActivityResponse | None
    nutrition: NutritionResponse | None
    performance: PerformanceResponse | None

    model_config = {"from_attributes": True}

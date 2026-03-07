from datetime import date

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Activity, DailySummary, NutritionDaily, PerformanceMetric, SleepSession
from app.schemas.dashboard import DashboardResponse

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


@router.get("/today", response_model=DashboardResponse)
def get_today(db: Session = Depends(get_db)):
    today = date.today()
    return DashboardResponse(
        date=today,
        daily_summary=db.query(DailySummary).filter_by(date=today).first(),
        sleep=db.query(SleepSession).filter_by(date=today).first(),
        latest_activity=db.query(Activity)
        .filter_by(date=today)
        .order_by(Activity.id.desc())
        .first(),
        nutrition=db.query(NutritionDaily).filter_by(date=today).first(),
        performance=db.query(PerformanceMetric).filter_by(date=today).first(),
    )

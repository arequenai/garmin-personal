from datetime import date

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Activity, DailySummary, NutritionDaily, PerformanceMetric, SleepSession
from app.schemas.dashboard import DashboardResponse

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


def _get_latest_date(db: Session) -> date:
    """Return today if data exists, otherwise the most recent date with data."""
    today = date.today()
    if db.query(DailySummary).filter_by(date=today).first():
        return today
    latest = db.query(DailySummary).order_by(DailySummary.date.desc()).first()
    return latest.date if latest else today


@router.get("/today", response_model=DashboardResponse)
def get_today(db: Session = Depends(get_db)):
    target = _get_latest_date(db)
    return DashboardResponse(
        date=target,
        daily_summary=db.query(DailySummary).filter_by(date=target).first(),
        sleep=db.query(SleepSession).filter_by(date=target).first(),
        latest_activity=db.query(Activity)
        .filter_by(date=target)
        .order_by(Activity.id.desc())
        .first(),
        nutrition=db.query(NutritionDaily).filter_by(date=target).first(),
        performance=db.query(PerformanceMetric).filter_by(date=target).first(),
    )

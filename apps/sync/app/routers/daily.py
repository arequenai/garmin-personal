from datetime import date, timedelta

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import DailySummary
from app.schemas.daily import DailySummaryResponse

router = APIRouter(prefix="/api/daily", tags=["daily"])


@router.get("", response_model=list[DailySummaryResponse])
def list_daily(
    from_date: date = Query(default_factory=lambda: date.today() - timedelta(days=30)),
    to_date: date = Query(default_factory=lambda: date.today()),
    db: Session = Depends(get_db),
):
    return (
        db.query(DailySummary)
        .filter(DailySummary.date >= from_date, DailySummary.date <= to_date)
        .order_by(DailySummary.date.desc())
        .all()
    )

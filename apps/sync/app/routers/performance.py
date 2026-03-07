from datetime import date, timedelta

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import PerformanceMetric
from app.schemas.performance import PerformanceResponse

router = APIRouter(prefix="/api/performance", tags=["performance"])


@router.get("", response_model=list[PerformanceResponse])
def list_performance(
    from_date: date = Query(default_factory=lambda: date.today() - timedelta(days=30)),
    to_date: date = Query(default_factory=lambda: date.today()),
    db: Session = Depends(get_db),
):
    return (
        db.query(PerformanceMetric)
        .filter(PerformanceMetric.date >= from_date, PerformanceMetric.date <= to_date)
        .order_by(PerformanceMetric.date.desc())
        .all()
    )

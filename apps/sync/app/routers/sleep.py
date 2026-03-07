from datetime import date, timedelta

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import SleepSession
from app.schemas.sleep import SleepResponse

router = APIRouter(prefix="/api/sleep", tags=["sleep"])


@router.get("", response_model=list[SleepResponse])
def list_sleep(
    from_date: date = Query(default_factory=lambda: date.today() - timedelta(days=30)),
    to_date: date = Query(default_factory=lambda: date.today()),
    db: Session = Depends(get_db),
):
    return (
        db.query(SleepSession)
        .filter(SleepSession.date >= from_date, SleepSession.date <= to_date)
        .order_by(SleepSession.date.desc())
        .all()
    )

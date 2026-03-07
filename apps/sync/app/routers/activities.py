from datetime import date, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Activity
from app.schemas.activity import ActivityResponse

router = APIRouter(prefix="/api/activities", tags=["activities"])


@router.get("", response_model=list[ActivityResponse])
def list_activities(
    from_date: date = Query(default_factory=lambda: date.today() - timedelta(days=30)),
    to_date: date = Query(default_factory=lambda: date.today()),
    db: Session = Depends(get_db),
):
    return (
        db.query(Activity)
        .filter(Activity.date >= from_date, Activity.date <= to_date)
        .order_by(Activity.date.desc())
        .all()
    )


@router.get("/{activity_id}", response_model=ActivityResponse)
def get_activity(activity_id: int, db: Session = Depends(get_db)):
    activity = db.query(Activity).filter_by(id=activity_id).first()
    if not activity:
        raise HTTPException(status_code=404, detail="Activity not found")
    return activity

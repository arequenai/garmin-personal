from datetime import date, timedelta

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import NutritionDaily
from app.schemas.nutrition import NutritionResponse

router = APIRouter(prefix="/api/nutrition", tags=["nutrition"])


@router.get("", response_model=list[NutritionResponse])
def list_nutrition(
    from_date: date = Query(default_factory=lambda: date.today() - timedelta(days=30)),
    to_date: date = Query(default_factory=lambda: date.today()),
    db: Session = Depends(get_db),
):
    return (
        db.query(NutritionDaily)
        .filter(NutritionDaily.date >= from_date, NutritionDaily.date <= to_date)
        .order_by(NutritionDaily.date.desc())
        .all()
    )

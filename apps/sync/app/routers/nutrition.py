from datetime import date, timedelta

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import NutritionDaily
from app.schemas.nutrition import NutritionResponse
from app.services.calorie_target import fetch_and_compute_targets

router = APIRouter(prefix="/api/nutrition", tags=["nutrition"])


@router.get("", response_model=list[NutritionResponse])
def list_nutrition(
    from_date: date = Query(default_factory=lambda: date.today() - timedelta(days=30)),
    to_date: date = Query(default_factory=lambda: date.today()),
    db: Session = Depends(get_db),
):
    rows = (
        db.query(NutritionDaily)
        .filter(NutritionDaily.date >= from_date, NutritionDaily.date <= to_date)
        .order_by(NutritionDaily.date.desc())
        .all()
    )

    targets = fetch_and_compute_targets(db, from_date, to_date)

    results = []
    for row in rows:
        resp = NutritionResponse.model_validate(row)
        resp.calories_target_adaptive = targets.get(row.date)
        results.append(resp)
    return results

from datetime import date, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import NutritionDaily
from app.schemas.nutrition import (
    NutritionEntryResponse,
    NutritionMealsResponse,
    NutritionMealsTotals,
    NutritionResponse,
)
from app.services.calorie_target import fetch_and_compute_targets

router = APIRouter(prefix="/api/nutrition", tags=["nutrition"])

_BUCKET_NAMES = ("breakfast", "lunch", "dinner", "snacks", "other")


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


@router.get("/{target_date}/meals", response_model=NutritionMealsResponse)
def get_meals_for_date(target_date: date, db: Session = Depends(get_db)):
    row = (
        db.query(NutritionDaily)
        .filter(NutritionDaily.date == target_date)
        .first()
    )
    if not row:
        raise HTTPException(status_code=404, detail=f"No nutrition data for {target_date}")

    buckets: dict[str, list[NutritionEntryResponse]] = {b: [] for b in _BUCKET_NAMES}
    for e in (row.entries or []):
        bucket = e.get("meal", "other")
        if bucket not in buckets:
            bucket = "other"
        buckets[bucket].append(NutritionEntryResponse(**e))

    return NutritionMealsResponse(
        date=row.date,
        meals=buckets,
        totals=NutritionMealsTotals(
            calories=row.calories,
            protein_g=row.protein_g,
            carbs_g=row.carbs_g,
            fat_g=row.fat_g,
        ),
    )

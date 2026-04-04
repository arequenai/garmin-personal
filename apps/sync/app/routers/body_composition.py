from datetime import date, timedelta

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.body_composition import BodyComposition
from app.schemas.body_composition import BodyCompositionResponse

router = APIRouter(prefix="/api/body-composition", tags=["body-composition"])


@router.get("", response_model=list[BodyCompositionResponse])
def list_body_composition(
    from_date: date = Query(default_factory=lambda: date.today() - timedelta(days=30)),
    to_date: date = Query(default_factory=lambda: date.today()),
    db: Session = Depends(get_db),
):
    return (
        db.query(BodyComposition)
        .filter(BodyComposition.date >= from_date, BodyComposition.date <= to_date)
        .order_by(BodyComposition.date.asc())
        .all()
    )

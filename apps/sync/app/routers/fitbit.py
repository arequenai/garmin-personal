import logging
from datetime import date, timedelta

from fastapi import APIRouter, BackgroundTasks
from fastapi.responses import RedirectResponse

from app.config import settings
from app.database import SessionLocal
from app.models import User
from app.models.body_composition import BodyComposition
from app.services.fitbit_client import FitbitClient

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/fitbit", tags=["fitbit"])


@router.get("/authorize")
def authorize():
    """Redirect to Fitbit OAuth2 authorization page."""
    url = FitbitClient.get_authorize_url(
        client_id=settings.fitbit_client_id,
        redirect_uri=settings.fitbit_redirect_uri,
    )
    return RedirectResponse(url)


@router.get("/callback")
def callback(code: str):
    """Handle OAuth2 callback, store tokens in DB."""
    data = FitbitClient.exchange_code(
        client_id=settings.fitbit_client_id,
        client_secret=settings.fitbit_client_secret,
        code=code,
        redirect_uri=settings.fitbit_redirect_uri,
    )

    db = SessionLocal()
    try:
        user = db.query(User).first()
        if not user:
            user = User()
            db.add(user)
        user.fitbit_access_token = data["access_token"]
        user.fitbit_refresh_token = data["refresh_token"]
        db.commit()
    finally:
        db.close()

    return {"status": "ok", "message": "Fitbit connected"}


def _get_fitbit_client(db) -> tuple[FitbitClient, object]:
    """Build a FitbitClient from DB/env tokens. Returns (client, user)."""
    user = db.query(User).first()
    access = (
        user.fitbit_access_token if user and user.fitbit_access_token else None
    ) or settings.fitbit_access_token
    refresh = (
        user.fitbit_refresh_token if user and user.fitbit_refresh_token else None
    ) or settings.fitbit_refresh_token
    if not access or not settings.fitbit_client_id:
        raise ValueError("Fitbit not configured")
    fb = FitbitClient(
        client_id=settings.fitbit_client_id,
        client_secret=settings.fitbit_client_secret,
        access_token=access,
        refresh_token=refresh,
    )
    return fb, user


def _run_fitbit_backfill(days: int) -> None:
    """Backfill Fitbit body composition in 30-day chunks."""
    db = SessionLocal()
    try:
        fb, user = _get_fitbit_client(db)
        today = date.today()
        start = today - timedelta(days=days)
        total_upserted = 0

        # Process in 30-day chunks (Fitbit API max is 31 days per range request)
        chunk_start = start
        while chunk_start <= today:
            chunk_end = min(chunk_start + timedelta(days=30), today)
            try:
                weights = fb.get_weight_range(chunk_start, chunk_end)
                fats = fb.get_body_fat_range(chunk_start, chunk_end)

                # Index fat entries by date for easy lookup
                fat_by_date: dict[str, float] = {}
                for f in fats:
                    fat_by_date[f["date"]] = f.get("fat")

                for w in weights:
                    d = date.fromisoformat(w["date"])
                    weight_kg = w.get("weight")
                    bmi = w.get("bmi")
                    body_fat_pct = fat_by_date.get(w["date"])

                    existing = db.query(BodyComposition).filter_by(date=d).first()
                    if existing:
                        if weight_kg is not None:
                            existing.weight_kg = weight_kg
                        if body_fat_pct is not None:
                            existing.body_fat_pct = body_fat_pct
                        if bmi is not None:
                            existing.bmi = bmi
                    else:
                        db.add(BodyComposition(
                            date=d,
                            weight_kg=weight_kg,
                            body_fat_pct=body_fat_pct,
                            bmi=bmi,
                        ))
                    total_upserted += 1

                # Handle fat-only dates (no weight entry for that date)
                weight_dates = {w["date"] for w in weights}
                for f in fats:
                    if f["date"] not in weight_dates and f.get("fat") is not None:
                        d = date.fromisoformat(f["date"])
                        existing = db.query(BodyComposition).filter_by(date=d).first()
                        if existing:
                            existing.body_fat_pct = f["fat"]
                        else:
                            db.add(BodyComposition(date=d, body_fat_pct=f["fat"]))
                        total_upserted += 1

                db.commit()
                logger.info(
                    "Fitbit backfill chunk: %s to %s (%d weight, %d fat entries)",
                    chunk_start, chunk_end, len(weights), len(fats),
                )
            except Exception:
                logger.exception(
                    "Fitbit backfill chunk failed: %s to %s", chunk_start, chunk_end,
                )

            chunk_start = chunk_end + timedelta(days=1)

        # Persist refreshed tokens
        if fb.tokens_were_refreshed and user:
            user.fitbit_access_token = fb.access_token
            user.fitbit_refresh_token = fb.refresh_token
            db.commit()

        logger.info("Fitbit backfill completed: %d entries upserted", total_upserted)
    finally:
        db.close()


@router.post("/backfill")
def trigger_fitbit_backfill(
    background_tasks: BackgroundTasks,
    days: int = 365,
):
    """Backfill Fitbit body composition (weight + body fat) for the last N days."""
    start = date.today() - timedelta(days=days)
    background_tasks.add_task(_run_fitbit_backfill, days)
    return {
        "status": "fitbit_backfill_started",
        "from_date": start.isoformat(),
        "to_date": date.today().isoformat(),
        "total_days": days + 1,
    }

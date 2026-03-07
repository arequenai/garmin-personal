from datetime import date, timedelta

from fastapi import APIRouter, BackgroundTasks

from app.config import settings
from app.database import SessionLocal
from app.services.garmin_client import GarminClient
from app.services.performance_updater import PerformanceUpdater
from app.services.sync_service import SyncService

router = APIRouter(prefix="/api/sync", tags=["sync"])


def run_sync(target_date: date):
    db = SessionLocal()
    try:
        garmin = GarminClient(email=settings.garmin_email, password=settings.garmin_password)
        garmin.login()
        sync = SyncService(db=db, garmin=garmin)
        sync.sync_all(target_date)
        updater = PerformanceUpdater(db=db)
        updater.update(target_date)
    finally:
        db.close()


@router.post("/trigger")
def trigger_sync(
    background_tasks: BackgroundTasks,
    days_back: int = 1,
):
    target = date.today() - timedelta(days=days_back)
    background_tasks.add_task(run_sync, target)
    return {"status": "sync_started", "target_date": target.isoformat()}

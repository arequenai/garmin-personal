import logging
from datetime import date, timedelta

from apscheduler.schedulers.background import BackgroundScheduler

from app.config import settings
from app.database import SessionLocal
from app.services.garmin_client import GarminClient
from app.services.performance_updater import PerformanceUpdater
from app.services.sync_service import SyncService

logger = logging.getLogger(__name__)


def daily_sync_job():
    logger.info("Starting daily sync job")
    db = SessionLocal()
    try:
        target = date.today() - timedelta(days=1)
        garmin = GarminClient(email=settings.garmin_email, password=settings.garmin_password)
        garmin.login()
        sync = SyncService(db=db, garmin=garmin)
        sync.sync_all(target)
        updater = PerformanceUpdater(db=db)
        updater.update(target)
        logger.info(f"Daily sync completed for {target}")
    except Exception:
        logger.exception("Daily sync failed")
    finally:
        db.close()


scheduler = BackgroundScheduler()
scheduler.add_job(daily_sync_job, "cron", hour=5, minute=0, id="daily_sync")

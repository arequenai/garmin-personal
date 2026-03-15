"""Shared sync orchestration used by both the API trigger and the scheduler."""

import logging
from datetime import date

from app.config import settings
from app.database import SessionLocal
from app.services.garmin_client import GarminClient
from app.services.performance_updater import PerformanceUpdater
from app.services.sync_service import SyncService

logger = logging.getLogger(__name__)


def run_sync_for_date(target_date: date) -> None:
    """Run full sync pipeline for a target date."""
    db = SessionLocal()
    try:
        garmin = GarminClient(email=settings.garmin_email, password=settings.garmin_password)
        garmin.login()

        mfp = None
        if settings.mfp_cookies:
            from app.services.mfp_client import MFPClient

            mfp = MFPClient(cookies_json=settings.mfp_cookies)
            mfp.login()

        sync = SyncService(db=db, garmin=garmin, mfp=mfp)
        sync.sync_all(target_date)
        updater = PerformanceUpdater(db=db, garmin=garmin)
        updater.update(target_date)
    finally:
        db.close()

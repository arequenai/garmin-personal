"""Shared sync orchestration used by both the API trigger and the scheduler."""

import logging
from datetime import date

from app.config import settings
from app.database import SessionLocal
from app.models import User
from app.services.garmin_client import GarminClient
from app.services.performance_updater import PerformanceUpdater
from app.services.sheets_exporter import GoogleSheetsExporter
from app.services.sync_service import SyncService

logger = logging.getLogger(__name__)

# Cached Garmin client — avoids a fresh login() on every sync invocation.
_garmin_client: GarminClient | None = None


def _get_garmin_client(force_new: bool = False) -> GarminClient:
    """Return a cached GarminClient, creating one only on first call or after auth failure."""
    global _garmin_client
    if _garmin_client is None or force_new:
        _garmin_client = GarminClient(
            email=settings.garmin_email, password=settings.garmin_password
        )
        _garmin_client.login()
        logger.info("Garmin client logged in (new session)")
    return _garmin_client


def run_sync_for_date(target_date: date) -> None:
    """Run full sync pipeline for a target date."""
    db = SessionLocal()
    try:
        garmin = _get_garmin_client()

        # Read MFP cookies from DB user record, fall back to env var
        user = db.query(User).first()
        mfp_cookies = (
            user.mfp_cookies if user and user.mfp_cookies else None
        ) or settings.mfp_cookies

        mfp = None
        if mfp_cookies:
            from app.services.mfp_client import MFPClient

            mfp = MFPClient(cookies_json=mfp_cookies)
            mfp.login()

        nightscout = None
        if settings.nightscout_url and settings.nightscout_token:
            from app.services.nightscout_client import NightscoutClient

            nightscout = NightscoutClient(
                base_url=settings.nightscout_url, token=settings.nightscout_token
            )

        # Each sync source is isolated so one failure doesn't block the others.
        sync = SyncService(db=db, garmin=garmin, mfp=mfp, nightscout=nightscout)
        try:
            try:
                sync.sync_all(target_date)
            except Exception:
                logger.warning("Sync failed, retrying with fresh Garmin session")
                garmin = _get_garmin_client(force_new=True)
                sync.garmin = garmin
                sync.sync_all(target_date)
            updater = PerformanceUpdater(db=db, garmin=garmin)
            updater.update(target_date)
        except Exception:
            logger.exception("Garmin sync failed")

        if settings.google_service_account_json and settings.google_spreadsheet_id:
            try:
                exporter = GoogleSheetsExporter(
                    db=db,
                    spreadsheet_id=settings.google_spreadsheet_id,
                    credentials_json=settings.google_service_account_json,
                )
                exporter.export(target_date)
            except Exception:
                logger.exception("Google Sheets export failed")

        if settings.tp_enabled and settings.tp_auth_cookie:
            try:
                from app.services.tp_sync_service import TPSyncService
                from app.services.trainingpeaks_client import TrainingPeaksClient

                tp_client = TrainingPeaksClient(auth_cookie=settings.tp_auth_cookie)
                tp_client.login()
                tp_sync = TPSyncService(db=db, tp_client=tp_client)
                tp_sync.sync_all(target_date)
            except Exception:
                logger.exception("TrainingPeaks sync failed")
    finally:
        db.close()


def run_frequent_sync() -> None:
    """Lightweight sync for intraday data: nutrition (MFP) + stress readings."""
    db = SessionLocal()
    try:
        garmin = _get_garmin_client()

        user = db.query(User).first()
        mfp_cookies = (
            user.mfp_cookies if user and user.mfp_cookies else None
        ) or settings.mfp_cookies

        mfp = None
        if mfp_cookies:
            from app.services.mfp_client import MFPClient

            mfp = MFPClient(cookies_json=mfp_cookies)
            mfp.login()

        sync = SyncService(db=db, garmin=garmin, mfp=mfp)
        today = date.today()
        try:
            sync.sync_nutrition(today)
            sync.sync_stress_readings(today)
        except Exception:
            logger.warning("Frequent sync failed, retrying with fresh Garmin session")
            garmin = _get_garmin_client(force_new=True)
            sync.garmin = garmin
            sync.sync_nutrition(today)
            sync.sync_stress_readings(today)
        logger.info(f"Frequent sync completed for {today}")
    except Exception:
        logger.exception("Frequent sync failed after retry")
    finally:
        db.close()

"""Shared sync orchestration used by both the API trigger and the scheduler."""

import logging
import time
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
_garmin_login_failed_at: float = 0  # timestamp of last login failure
_GARMIN_COOLDOWN_SEC = 900  # 15 min cooldown after a login failure


def _get_garmin_client(force_new: bool = False) -> GarminClient:
    """Return a cached GarminClient, creating one only on first call or after auth failure."""
    global _garmin_client, _garmin_login_failed_at

    if _garmin_login_failed_at and time.time() - _garmin_login_failed_at < _GARMIN_COOLDOWN_SEC:
        raise ConnectionError("Garmin login on cooldown after recent failure")

    if _garmin_client is None or force_new:
        try:
            _garmin_client = GarminClient(
                email=settings.garmin_email, password=settings.garmin_password
            )
            _garmin_client.login()
            _garmin_login_failed_at = 0
            logger.info("Garmin client logged in (new session)")
        except Exception:
            _garmin_login_failed_at = time.time()
            _garmin_client = None
            raise
    return _garmin_client


def run_sync_for_date(target_date: date) -> None:
    """Run full sync pipeline for a target date.

    Each data source is isolated so one failure doesn't block the others.
    """
    db = SessionLocal()
    try:
        # Read MFP cookies from DB user record, fall back to env var
        user = db.query(User).first()
        mfp_cookies = (
            user.mfp_cookies if user and user.mfp_cookies else None
        ) or settings.mfp_cookies

        mfp = None
        if mfp_cookies:
            try:
                from app.services.mfp_client import MFPClient

                mfp = MFPClient(cookies_json=mfp_cookies)
                mfp.login()
            except Exception:
                logger.exception("MFP login failed")

        nightscout = None
        if settings.nightscout_url and settings.nightscout_token:
            try:
                from app.services.nightscout_client import NightscoutClient

                nightscout = NightscoutClient(
                    base_url=settings.nightscout_url, token=settings.nightscout_token
                )
            except Exception:
                logger.exception("Nightscout client init failed")

        # --- MFP nutrition (independent of Garmin) ---
        if mfp:
            try:
                sync = SyncService(db=db, garmin=None, mfp=mfp)
                sync.sync_nutrition(target_date)
                logger.info("MFP nutrition sync completed for %s", target_date)
            except Exception:
                logger.exception("MFP nutrition sync failed")

        # --- Nightscout glucose (independent of Garmin) ---
        if nightscout:
            try:
                sync = SyncService(db=db, garmin=None, nightscout=nightscout)
                sync.sync_glucose(target_date)
                logger.info("Nightscout glucose sync completed for %s", target_date)
            except Exception:
                logger.exception("Nightscout glucose sync failed")

        # --- Garmin sync ---
        try:
            garmin = _get_garmin_client()
            sync = SyncService(db=db, garmin=garmin, mfp=mfp, nightscout=nightscout)
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

        # --- Google Sheets export (reads from DB, independent of Garmin) ---
        if settings.google_service_account_json and settings.google_spreadsheet_id:
            try:
                exporter = GoogleSheetsExporter(
                    db=db,
                    spreadsheet_id=settings.google_spreadsheet_id,
                    credentials_json=settings.google_service_account_json,
                )
                exporter.export(target_date)
                logger.info("Google Sheets export completed for %s", target_date)
            except Exception:
                logger.exception("Google Sheets export failed")

        # --- TrainingPeaks sync (independent of Garmin) ---
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
        today = date.today()

        user = db.query(User).first()
        mfp_cookies = (
            user.mfp_cookies if user and user.mfp_cookies else None
        ) or settings.mfp_cookies

        # --- MFP nutrition (independent of Garmin) ---
        if mfp_cookies:
            try:
                from app.services.mfp_client import MFPClient

                mfp = MFPClient(cookies_json=mfp_cookies)
                mfp.login()
                sync = SyncService(db=db, garmin=None, mfp=mfp)
                sync.sync_nutrition(today)
                logger.info("Frequent sync: nutrition completed for %s", today)
            except Exception:
                logger.exception("Frequent sync: nutrition failed")

        # --- Garmin stress readings ---
        try:
            garmin = _get_garmin_client()
            sync = SyncService(db=db, garmin=garmin)
            try:
                sync.sync_stress_readings(today)
            except Exception:
                logger.warning("Stress sync failed, retrying with fresh Garmin session")
                garmin = _get_garmin_client(force_new=True)
                sync.garmin = garmin
                sync.sync_stress_readings(today)
            logger.info("Frequent sync: stress readings completed for %s", today)
        except Exception:
            logger.exception("Frequent sync: Garmin stress readings failed")
    finally:
        db.close()

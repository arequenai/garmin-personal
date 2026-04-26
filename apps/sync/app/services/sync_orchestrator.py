"""Shared sync orchestration used by both the API trigger and the scheduler."""

import json
import logging
import os
import time
from datetime import date
from pathlib import Path

from garminconnect.exceptions import (
    GarminConnectAuthenticationError,
    GarminConnectTooManyRequestsError,
)

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
_garmin_token_store: str | None = None
_garmin_login_failed_at: float = 0  # timestamp of last login failure
_garmin_consecutive_failures: int = 0  # for exponential backoff
_garmin_last_was_429: bool = False  # tracks if last failure was a rate limit
_GARMIN_BASE_COOLDOWN_SEC = 3600  # 1 hour base cooldown for 429
_GARMIN_MAX_COOLDOWN_SEC = 86400  # cap at 24 hours for 429
_GARMIN_AUTH_COOLDOWN_SEC = 900  # 15 min for non-429 auth errors
_GARMIN_MAX_429_RETRIES = 3  # after this many 429s, stop retrying SSO entirely

_TOKEN_FILE = Path(__file__).resolve().parent.parent.parent / ".garmin_tokens"


def _load_token_store() -> str | None:
    """Load tokens from env var or disk file."""
    if settings.garmin_token_store:
        return settings.garmin_token_store
    if _TOKEN_FILE.exists():
        try:
            data = _TOKEN_FILE.read_text().strip()
            if data:
                return data
        except Exception:
            logger.warning("Failed to read token file %s", _TOKEN_FILE)
    return None


def _save_token_store(tokens: str) -> None:
    """Persist tokens to disk for surviving restarts."""
    try:
        _TOKEN_FILE.write_text(tokens)
        logger.info("Garmin tokens persisted to %s", _TOKEN_FILE)
    except Exception:
        logger.warning("Failed to write token file %s", _TOKEN_FILE)


def set_garmin_tokens(tokens: str) -> None:
    """Accept externally-provided tokens (e.g. from API upload)."""
    global _garmin_client, _garmin_token_store, _garmin_login_failed_at
    global _garmin_consecutive_failures, _garmin_last_was_429
    _garmin_token_store = tokens
    _garmin_client = None
    _garmin_login_failed_at = 0
    _garmin_consecutive_failures = 0
    _garmin_last_was_429 = False
    _save_token_store(tokens)


# Keep for backward compat with the API endpoint, but now a no-op
def set_garmin_cookies(cookie_str: str) -> None:
    """Deprecated: cookie-based auth no longer works with Garmin's new API."""
    logger.warning("set_garmin_cookies called but cookie auth is no longer supported")


def _get_garmin_client(force_new: bool = False) -> GarminClient:
    """Return a cached GarminClient, creating one only on first call or after auth failure.

    Auth strategy:
    1. Always pass persisted DI tokens to the library when available.
       The library will refresh them via diauth.garmin.com (not rate-limited)
       and only fall back to SSO login if the refresh token is also expired.
    2. Single login() call — the library handles token→refresh→credentials
       fallback internally.  We do NOT wrap it in our own fallback to avoid
       doubling SSO login attempts (each attempt can fire ~16 requests across
       4 strategies × multiple TLS impersonations).

    Uses exponential backoff on failures to avoid hammering Garmin's rate limit.
    """
    global _garmin_client, _garmin_token_store, _garmin_login_failed_at
    global _garmin_consecutive_failures, _garmin_last_was_429

    # Cooldown check: exponential for 429, short fixed for other errors
    if _garmin_login_failed_at:
        if _garmin_last_was_429:
            # 429: exponential backoff 1h, 2h, 4h, ... capped at 24h
            cooldown = min(
                _GARMIN_BASE_COOLDOWN_SEC * (2 ** (_garmin_consecutive_failures - 1)),
                _GARMIN_MAX_COOLDOWN_SEC,
            )
        else:
            # Non-429 errors: fixed 15-min cooldown (no compounding)
            cooldown = _GARMIN_AUTH_COOLDOWN_SEC
        remaining = cooldown - (time.time() - _garmin_login_failed_at)
        if remaining > 0:
            hours = remaining / 3600
            raise ConnectionError(
                f"Garmin login on cooldown ({hours:.1f}h remaining, "
                f"attempt {_garmin_consecutive_failures})"
            )
        # Cooldown expired — but if we've hit too many 429s, stop retrying
        # SSO entirely to avoid perpetuating the rate limit. Each SSO attempt
        # fires ~16 requests, refreshing Cloudflare's rate-limit timer.
        if _garmin_last_was_429 and _garmin_consecutive_failures >= _GARMIN_MAX_429_RETRIES:
            raise ConnectionError(
                f"Garmin SSO blocked after {_garmin_consecutive_failures} consecutive "
                f"429s. Upload fresh tokens via POST /api/sync/garmin-tokens "
                f"or reset via POST /api/sync/reset-cooldown"
            )
        # Non-429 errors or fewer retries — reset counter and retry.
        logger.info(
            "Garmin cooldown expired after attempt %d, resetting counter",
            _garmin_consecutive_failures,
        )
        _garmin_login_failed_at = 0
        _garmin_consecutive_failures = 0
        _garmin_last_was_429 = False

    # Load persisted tokens on first call
    if _garmin_token_store is None:
        _garmin_token_store = _load_token_store()

    if _garmin_client is None or force_new:
        try:
            client = GarminClient(
                email=settings.garmin_email, password=settings.garmin_password
            )
            # Single login call — always pass tokenstore when available.
            # The library internally: loads DI tokens → refreshes if expiring
            # → falls back to SSO credentials only if refresh fails.
            # This avoids the old double-login pattern that fired ~32 SSO
            # requests when rate-limited.
            client.login(tokenstore=_garmin_token_store)
            logger.info("Garmin client authenticated")

            # Cache and persist the tokens for next time
            _garmin_token_store = client.dump_tokens()
            if _garmin_token_store:
                _save_token_store(_garmin_token_store)
            _garmin_client = client
            _garmin_login_failed_at = 0
            _garmin_consecutive_failures = 0
        except GarminConnectTooManyRequestsError:
            _garmin_consecutive_failures += 1
            _garmin_login_failed_at = time.time()
            _garmin_last_was_429 = True
            _garmin_client = None
            next_cooldown = min(
                _GARMIN_BASE_COOLDOWN_SEC * (2 ** (_garmin_consecutive_failures - 1)),
                _GARMIN_MAX_COOLDOWN_SEC,
            )
            logger.error(
                "Garmin 429 rate-limited (attempt %d, cooldown %s)",
                _garmin_consecutive_failures,
                f"{next_cooldown / 3600:.1f}h",
            )
            raise
        except Exception:
            _garmin_consecutive_failures += 1
            _garmin_login_failed_at = time.time()
            _garmin_last_was_429 = False
            _garmin_client = None
            logger.error(
                "Garmin login failed (attempt %d, next retry in %sm)",
                _garmin_consecutive_failures,
                f"{_GARMIN_AUTH_COOLDOWN_SEC // 60}",
            )
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

        # --- Fitbit body composition (independent of Garmin) ---
        fitbit_access = (
            user.fitbit_access_token if user and user.fitbit_access_token else None
        ) or settings.fitbit_access_token
        fitbit_refresh = (
            user.fitbit_refresh_token if user and user.fitbit_refresh_token else None
        ) or settings.fitbit_refresh_token
        if fitbit_access and settings.fitbit_client_id:
            try:
                from app.models.body_composition import BodyComposition
                from app.services.fitbit_client import FitbitClient

                fb = FitbitClient(
                    client_id=settings.fitbit_client_id,
                    client_secret=settings.fitbit_client_secret,
                    access_token=fitbit_access,
                    refresh_token=fitbit_refresh,
                )
                weights = fb.get_weight(target_date)
                fats = fb.get_body_fat(target_date)

                if weights or fats:
                    weight_kg = None
                    if weights:
                        weight_kg = weights[-1].get("weight")
                    body_fat_pct = None
                    if fats:
                        body_fat_pct = fats[-1].get("fat")
                    bmi = None
                    if weights:
                        bmi = weights[-1].get("bmi")

                    existing = (
                        db.query(BodyComposition)
                        .filter_by(date=target_date)
                        .first()
                    )
                    if existing:
                        if weight_kg is not None:
                            existing.weight_kg = weight_kg
                        if body_fat_pct is not None:
                            existing.body_fat_pct = body_fat_pct
                        if bmi is not None:
                            existing.bmi = bmi
                    else:
                        bc = BodyComposition(
                            date=target_date,
                            weight_kg=weight_kg,
                            body_fat_pct=body_fat_pct,
                            bmi=bmi,
                        )
                        db.add(bc)
                    db.commit()
                    logger.info(
                        "Fitbit body composition synced for %s (weight=%s, fat=%s)",
                        target_date, weight_kg, body_fat_pct,
                    )

                # Persist refreshed tokens back to DB
                if fb.tokens_were_refreshed and user:
                    user.fitbit_access_token = fb.access_token
                    user.fitbit_refresh_token = fb.refresh_token
                    db.commit()
            except Exception:
                logger.exception("Fitbit body composition sync failed")

        # --- Garmin sync ---
        garmin = None
        try:
            garmin = _get_garmin_client()
            sync = SyncService(db=db, garmin=garmin, mfp=mfp, nightscout=nightscout)
            try:
                sync.sync_all(target_date)
            except GarminConnectTooManyRequestsError:
                # Never retry on rate limits — it only makes things worse
                logger.error("Garmin 429 during sync, not retrying")
            except GarminConnectAuthenticationError:
                # Auth failed mid-sync (token expired between calls) —
                # retry once with a fresh client.  The library's _run_request
                # already retries 401s internally, so this is a last resort.
                logger.warning("Garmin auth error during sync, retrying with fresh client")
                garmin = _get_garmin_client(force_new=True)
                sync.garmin = garmin
                sync.sync_all(target_date)
        except Exception:
            logger.exception("Garmin sync failed")

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

        # --- Performance updater (uses TP data + optionally Garmin) ---
        try:
            updater = PerformanceUpdater(db=db, garmin=garmin)
            updater.update(target_date)
        except Exception:
            logger.exception("Performance updater failed")

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

    finally:
        db.close()


def run_frequent_sync() -> None:
    """Lightweight sync for intraday data: nutrition (MFP) only.

    Garmin data (including stress readings) is synced once daily via
    run_sync_for_date() at 5 AM to avoid 429 rate-limiting from repeated
    Garmin auth calls every 15 minutes.
    """
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
    finally:
        db.close()

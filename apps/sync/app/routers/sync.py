import logging
import traceback
from datetime import date, datetime, timedelta

from fastapi import APIRouter, BackgroundTasks
from pydantic import BaseModel

from app.services.sync_orchestrator import (
    _get_garmin_client,
    run_sync_for_date,
    set_garmin_cookies,
    set_garmin_tokens,
)
import app.services.sync_orchestrator as _orch

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/sync", tags=["sync"])

# In-memory tracker for background sync status
_sync_state: dict = {"status": "idle", "started_at": None, "finished_at": None, "error": None}


def _tracked_sync(target: date) -> None:
    """Wrapper that updates _sync_state around the actual sync."""
    _sync_state.update(status="running", started_at=datetime.now().isoformat(), error=None)
    try:
        run_sync_for_date(target)
        _sync_state.update(status="ok", finished_at=datetime.now().isoformat())
    except Exception as exc:
        _sync_state.update(status="error", finished_at=datetime.now().isoformat(), error=str(exc))
        raise


@router.get("/status")
def sync_status():
    """Return the current state of the most recent background sync."""
    return _sync_state


class GarminTokensPayload(BaseModel):
    tokens: str


@router.post("/garmin-tokens")
def upload_garmin_tokens(payload: GarminTokensPayload):
    """Accept DI tokens JSON to bypass email/password login."""
    set_garmin_tokens(payload.tokens)
    return {"status": "tokens_saved"}


class CookiePayload(BaseModel):
    cookies: str


@router.post("/garmin-cookies")
def upload_garmin_cookies(payload: CookiePayload):
    """Deprecated: cookie-based auth no longer works with Garmin's new API."""
    set_garmin_cookies(payload.cookies)
    return {"status": "cookies_saved", "warning": "cookie auth is deprecated"}


@router.get("/test-garmin")
def test_garmin_connection():
    """Test whether the Garmin client can authenticate and fetch data."""
    yesterday = date.today() - timedelta(days=1)
    try:
        client = _get_garmin_client(force_new=True)
        stats = client.get_daily_summary(yesterday.isoformat())
        return {
            "status": "ok",
            "date_tested": yesterday.isoformat(),
            "has_data": bool(stats),
            "sample_keys": list(stats.keys())[:10] if isinstance(stats, dict) else str(type(stats)),
        }
    except Exception as exc:
        return {
            "status": "error",
            "error": str(exc),
            "consecutive_failures": _orch._garmin_consecutive_failures,
            "traceback": traceback.format_exc(),
        }


@router.post("/reset-cooldown")
def reset_garmin_cooldown():
    """Reset the Garmin login cooldown to allow an immediate retry."""
    _orch._garmin_login_failed_at = 0
    _orch._garmin_consecutive_failures = 0
    _orch._garmin_last_was_429 = False
    _orch._garmin_client = None
    return {"status": "cooldown_reset"}


@router.post("/trigger")
def trigger_sync(
    background_tasks: BackgroundTasks,
    days_back: int = 1,
):
    target = date.today() - timedelta(days=days_back)
    background_tasks.add_task(_tracked_sync, target)
    return {"status": "sync_started", "target_date": target.isoformat()}


def _run_backfill(days: int) -> None:
    """Sync each day from `days` ago to today, sequentially."""
    today = date.today()
    for i in range(days, -1, -1):
        target = today - timedelta(days=i)
        try:
            run_sync_for_date(target)
            logger.info("Backfill synced %s (%d days ago)", target, i)
        except Exception:
            logger.error("Backfill failed for %s", target, exc_info=True)


@router.post("/backfill")
def trigger_backfill(
    background_tasks: BackgroundTasks,
    days: int = 365,
):
    """One-off bulk sync. Pulls history from `days` ago to today."""
    start = date.today() - timedelta(days=days)
    background_tasks.add_task(_run_backfill, days)
    return {
        "status": "backfill_started",
        "from_date": start.isoformat(),
        "to_date": date.today().isoformat(),
        "total_days": days + 1,
    }

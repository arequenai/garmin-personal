import logging
from datetime import date, timedelta

from fastapi import APIRouter, BackgroundTasks

from app.services.sync_orchestrator import run_sync_for_date

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/sync", tags=["sync"])


@router.post("/trigger")
def trigger_sync(
    background_tasks: BackgroundTasks,
    days_back: int = 1,
):
    target = date.today() - timedelta(days=days_back)
    background_tasks.add_task(run_sync_for_date, target)
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

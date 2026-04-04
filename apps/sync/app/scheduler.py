import logging
from datetime import date

from apscheduler.schedulers.background import BackgroundScheduler

from app.services.sync_orchestrator import run_frequent_sync, run_sync_for_date

logger = logging.getLogger(__name__)


def daily_sync_job():
    logger.info("Starting daily sync job")
    try:
        target = date.today()
        run_sync_for_date(target)
        logger.info(f"Daily sync completed for {target}")
    except Exception:
        logger.exception("Daily sync failed")


def frequent_sync_job():
    logger.info("Starting frequent sync job")
    try:
        run_frequent_sync()
    except Exception:
        logger.exception("Frequent sync failed")


scheduler = BackgroundScheduler()
scheduler.add_job(daily_sync_job, "cron", hour=5, minute=0, id="daily_sync")
# Temporarily disabled — Garmin SSO is rate-limiting (429). Re-enable once cooldown passes.
# scheduler.add_job(
#     frequent_sync_job,
#     "cron",
#     minute="*/15",
#     hour="7-23",
#     id="frequent_sync",
# )

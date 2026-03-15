"""One-off script: backfill 1 year of history."""

import logging
import sys
from datetime import date, timedelta

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

from app.services.sync_orchestrator import run_sync_for_date

DAYS = 365
today = date.today()

for i in range(DAYS, -1, -1):
    target = today - timedelta(days=i)
    try:
        run_sync_for_date(target)
        logger.info("OK  %s  (%d/%d)", target, DAYS - i + 1, DAYS + 1)
    except Exception:
        logger.error("FAIL %s", target, exc_info=True)

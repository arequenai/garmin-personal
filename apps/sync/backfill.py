"""One-off script: backfill 1 year of history.
Logs in once and reuses the session across all days."""

import logging
import time
from datetime import date, timedelta

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

from app.config import settings
from app.database import SessionLocal
from app.models import User
from app.services.garmin_client import GarminClient
from app.services.performance_updater import PerformanceUpdater
from app.services.sync_service import SyncService

DAYS = 365
RESUME_FROM = date(2025, 6, 30)  # day after last successful sync
today = date.today()

# Single login for the whole run
garmin = GarminClient(email=settings.garmin_email, password=settings.garmin_password)
garmin.login()
logger.info("Garmin logged in")

db = SessionLocal()

# MFP setup (once)
user = db.query(User).first()
mfp_cookies = (user.mfp_cookies if user and user.mfp_cookies else None) or settings.mfp_cookies
mfp = None
if mfp_cookies:
    from app.services.mfp_client import MFPClient
    mfp = MFPClient(cookies_json=mfp_cookies)
    mfp.login()

# Nightscout setup (once)
nightscout = None
if settings.nightscout_url and settings.nightscout_token:
    from app.services.nightscout_client import NightscoutClient
    nightscout = NightscoutClient(base_url=settings.nightscout_url, token=settings.nightscout_token)

sync = SyncService(db=db, garmin=garmin, mfp=mfp, nightscout=nightscout)
updater = PerformanceUpdater(db=db, garmin=garmin)

target = RESUME_FROM
total = (today - RESUME_FROM).days + 1
i = 0
while target <= today:
    i += 1
    try:
        sync.sync_all(target)
        updater.update(target)
        logger.info("OK  %s  (%d/%d)", target, i, total)
    except Exception:
        logger.error("FAIL %s", target, exc_info=True)
    target += timedelta(days=1)
    time.sleep(1)  # gentle rate limiting

db.close()
logger.info("Backfill complete")

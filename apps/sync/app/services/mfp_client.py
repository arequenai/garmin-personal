import logging
from datetime import date

logger = logging.getLogger(__name__)


class MFPClient:
    """MyFitnessPal client. Currently a stub -- implement with actual MFP library or scraping."""

    def __init__(self, username: str, password: str):
        self.username = username
        self.password = password
        self._authenticated = False

    def login(self):
        """Authenticate with MyFitnessPal."""
        # TODO: Implement actual MFP authentication
        # Options: myfitnesspal library, or httpx scraping
        if self.username and self.password:
            self._authenticated = True
            logger.info("MFP client initialized (stub mode)")
        else:
            logger.warning("MFP credentials not configured")

    def get_day(self, target_date: date) -> dict | None:
        """Get nutrition data for a specific day.

        Returns: {calories, protein_g, carbs_g, fat_g, fiber_g, sodium_mg} or None
        """
        if not self._authenticated:
            return None
        # TODO: Implement actual MFP data retrieval
        logger.info(f"MFP get_day called for {target_date} (stub -- no data)")
        return None

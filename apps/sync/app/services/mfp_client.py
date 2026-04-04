import json
import logging
from datetime import date
from http.cookiejar import CookieJar

logger = logging.getLogger(__name__)


class MFPClient:
    """MyFitnessPal client using cookie-based authentication."""

    def __init__(self, cookies_json: str):
        self.cookies_json = cookies_json
        self._client = None
        self._authenticated = False

    def login(self):
        """Initialize MFP client with stored cookies."""
        if not self.cookies_json:
            logger.warning("MFP cookies not configured")
            return

        try:
            import myfitnesspal

            cookies = json.loads(self.cookies_json)
            jar = CookieJar()

            # Build cookie jar from the JSON cookie dict
            import time
            from http.cookiejar import Cookie

            for name, value in cookies.items():
                cookie = Cookie(
                    version=0,
                    name=name,
                    value=value,
                    port=None,
                    port_specified=False,
                    domain=".myfitnesspal.com",
                    domain_specified=True,
                    domain_initial_dot=True,
                    path="/",
                    path_specified=True,
                    secure=True,
                    expires=int(time.time()) + 86400 * 30,
                    discard=False,
                    comment=None,
                    comment_url=None,
                    rest={},
                )
                jar.set_cookie(cookie)

            self._client = myfitnesspal.Client(cookiejar=jar)
            self._authenticated = True
            logger.info("MFP client authenticated via cookies")
        except Exception as e:
            logger.warning(f"MFP authentication failed: {e}")
            self._authenticated = False

    def get_day(self, target_date: date) -> dict | None:
        """Get nutrition data for a specific day."""
        if not self._authenticated or not self._client:
            return None

        try:
            day = self._client.get_date(target_date.year, target_date.month, target_date.day)
            if not day or not day.totals:
                return None

            totals = day.totals
            goals = day.goals or {}
            return {
                "calories": totals.get("calories"),
                "protein_g": totals.get("protein"),
                "carbs_g": totals.get("carbohydrates"),
                "fat_g": totals.get("fat"),
                "fiber_g": totals.get("fiber"),
                "sodium_mg": totals.get("sodium"),
                "calories_goal": goals.get("calories"),
                "protein_goal_g": goals.get("protein"),
            }
        except Exception as e:
            logger.warning(f"MFP get_day failed for {target_date}: {e}")
            return None

    def get_weight(self) -> float | None:
        """Get most recent weight from MFP measurements API."""
        if not self._authenticated or not self._client:
            return None

        try:
            import requests

            auth = self._client._auth_data
            token = auth.get("access_token", "")
            user_id = self._client._user_metadata.get("id", "")

            headers = {
                "Authorization": f"Bearer {token}",
                "Accept": "application/json",
                "mfp-client-id": "mfp-main-js",
                "mfp-user-id": str(user_id),
            }
            resp = requests.get(
                "https://api.myfitnesspal.com/v2/measurements"
                "?type=Weight&most_recent=true",
                headers=headers,
                timeout=15,
            )
            if resp.status_code != 200:
                return None

            items = resp.json().get("items", [])
            if not items:
                return None

            return items[0].get("value")
        except Exception as e:
            logger.warning(f"MFP get_weight failed: {e}")
            return None

import logging
import time

import httpx

logger = logging.getLogger(__name__)

BASE_URL = "https://tpapi.trainingpeaks.com"


class TrainingPeaksClient:
    def __init__(self, auth_cookie: str):
        self.auth_cookie = auth_cookie
        self._token: str | None = None
        self._athlete_id: str | None = None
        self._token_expires_at: float = 0

    def login(self) -> None:
        """Exchange auth cookie for an OAuth token via GET /users/v3/token."""
        resp = httpx.get(
            f"{BASE_URL}/users/v3/token",
            headers={"Cookie": self.auth_cookie},
            timeout=15,
        )
        resp.raise_for_status()
        data = resp.json()
        token = data["token"]
        self._token = token["access_token"]
        self._token_expires_at = time.time() + token.get("expires_in", 3600) - 60

        # Fetch athlete ID from user endpoint
        resp = httpx.get(
            f"{BASE_URL}/users/v3/user",
            headers={"Cookie": self.auth_cookie},
            timeout=15,
        )
        resp.raise_for_status()
        self._athlete_id = str(resp.json()["user"]["userId"])
        logger.info("TP login OK — athlete %s", self._athlete_id)

    def _ensure_token(self) -> None:
        if self._token is None or time.time() >= self._token_expires_at:
            self.login()

    def _headers(self) -> dict[str, str]:
        self._ensure_token()
        return {"Authorization": f"Bearer {self._token}"}

    def get_athlete_id(self) -> str:
        if self._athlete_id is None:
            self.login()
        return self._athlete_id

    def get_fitness(self, start_date: str, end_date: str) -> list[dict]:
        """Get daily CTL/ATL/TSB fitness data via the reporting/performancedata endpoint."""
        self._ensure_token()
        url = (
            f"{BASE_URL}/fitness/v1/athletes/{self._athlete_id}"
            f"/reporting/performancedata/{start_date}/{end_date}"
        )
        body = {
            "atlConstant": 7,
            "atlStart": 0,
            "ctlConstant": 42,
            "ctlStart": 0,
            "workoutTypes": [],
        }
        resp = httpx.post(url, headers=self._headers(), json=body, timeout=15)
        resp.raise_for_status()
        return resp.json()

    def get_workouts(self, start_date: str, end_date: str) -> list[dict]:
        """Get workouts (both planned and completed) in a date range."""
        url = f"{BASE_URL}/fitness/v1/athletes/{self._athlete_id}/workouts"
        resp = httpx.get(url, headers=self._headers(), params={
            "startDate": start_date,
            "endDate": end_date,
        })
        resp.raise_for_status()
        return resp.json()

    def get_workout_analysis(self, workout_id: str) -> dict | None:
        """Get detailed analysis (zones, laps) for a workout. Returns None on failure."""
        try:
            url = (
                f"{BASE_URL}/fitness/v1/athletes/{self._athlete_id}"
                f"/workouts/{workout_id}"
            )
            resp = httpx.get(url, headers=self._headers())
            resp.raise_for_status()
            return resp.json()
        except Exception:
            logger.debug("Failed to fetch workout analysis for %s", workout_id, exc_info=True)
            return None

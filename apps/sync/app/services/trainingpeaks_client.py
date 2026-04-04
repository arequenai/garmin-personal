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
        """Exchange auth cookie for an OAuth token."""
        resp = httpx.post(
            f"{BASE_URL}/users/v3/token",
            headers={"Cookie": self.auth_cookie},
        )
        resp.raise_for_status()
        data = resp.json()
        self._token = data["access_token"]
        self._athlete_id = str(data["userId"])
        self._token_expires_at = time.time() + data.get("expires_in", 3600) - 60

    def _ensure_token(self) -> None:
        """Re-login if token is expired."""
        if time.time() >= self._token_expires_at:
            self.login()

    def _headers(self) -> dict[str, str]:
        self._ensure_token()
        return {"Authorization": f"Bearer {self._token}"}

    def get_athlete_id(self) -> str:
        """Return cached athlete ID from login response."""
        if self._athlete_id is None:
            raise RuntimeError("Must call login() first")
        return self._athlete_id

    def get_fitness(self, start_date: str, end_date: str) -> list[dict]:
        """Get daily CTL/ATL/TSB fitness data."""
        url = f"{BASE_URL}/fitness/v3/athletes/{self._athlete_id}/fitness"
        resp = httpx.get(url, headers=self._headers(), params={
            "startDate": start_date,
            "endDate": end_date,
        })
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

import time

from garminconnect import Garmin


class GarminClient:
    def __init__(self, email: str, password: str):
        self.email = email
        self.password = password
        self._client: Garmin | None = None

    def login(self, tokenstore: str | None = None):
        self._client = Garmin(self.email, self.password)
        self._client.login(tokenstore=tokenstore)

    def login_with_browser_token(self, browser_token: dict) -> None:
        """Login using OAuth2 token extracted from browser Local Storage.

        Sets a dummy OAuth1 token to satisfy garth's assertion, and the real
        OAuth2 token from the browser. Works as long as the access_token
        hasn't expired (~5 min from browser copy).
        """
        from garth.sso import OAuth1Token, OAuth2Token

        self._client = Garmin(self.email, self.password)
        # Initialize garth without going through SSO
        self._client.garth.oauth1_token = OAuth1Token(
            oauth_token="browser_session",
            oauth_token_secret="browser_session",
        )
        expires_ms = int(browser_token.get("expires", 0))
        refresh_expires_ms = int(browser_token.get("refresh_token_expires", 0))
        self._client.garth.oauth2_token = OAuth2Token(
            scope=browser_token.get("scope", ""),
            jti=browser_token.get("jti", ""),
            token_type=browser_token.get("token_type", "Bearer"),
            access_token=browser_token["access_token"],
            refresh_token=browser_token.get("refresh_token", ""),
            expires_in=int(browser_token.get("expires_in", 300)),
            expires_at=expires_ms // 1000 if expires_ms else int(time.time()) + 300,
            refresh_token_expires_in=int(
                browser_token.get("refresh_token_expires_in", 7200)
            ),
            refresh_token_expires_at=(
                refresh_expires_ms // 1000
                if refresh_expires_ms
                else int(time.time()) + 7200
            ),
        )

    def dump_tokens(self) -> str | None:
        """Serialize garth session tokens to a base64 string.

        Returns None if the client has not yet successfully logged in.
        """
        if self._client and self._client.garth:
            return self._client.garth.dumps()
        return None

    def get_daily_summary(self, date_str: str) -> dict:
        """Get daily stats (steps, calories, distance, etc.)."""
        return self._client.get_stats(date_str)

    def get_activities(self, start: int = 0, limit: int = 20) -> list[dict]:
        """Get list of activities."""
        return self._client.get_activities(start, limit)

    def get_activity_details(self, activity_id: str) -> dict:
        """Get detailed activity data."""
        return self._client.get_activity(activity_id)

    def get_sleep_data(self, date_str: str) -> dict:
        """Get sleep data including stages."""
        return self._client.get_sleep_data(date_str)

    def get_heart_rates(self, date_str: str) -> dict:
        """Get heart rate data (resting, max, min, values array)."""
        return self._client.get_heart_rates(date_str)

    def get_hrv_data(self, date_str: str) -> dict:
        """Get HRV data."""
        return self._client.get_hrv_data(date_str)

    def get_stress_data(self, date_str: str) -> dict:
        """Get all-day stress data including body battery values."""
        return self._client.get_all_day_stress(date_str)

    def get_body_battery(self, start_date: str, end_date: str) -> list[dict]:
        """Get body battery data for a date range."""
        return self._client.get_body_battery(start_date, end_date)

    def get_hydration_data(self, date_str: str) -> dict:
        """Get daily hydration data."""
        return self._client.get_hydration_data(date_str)

    def get_respiration_data(self, date_str: str) -> dict:
        """Get respiration data."""
        return self._client.get_respiration_data(date_str)

    def get_spo2_data(self, date_str: str) -> dict:
        """Get SpO2 data."""
        return self._client.get_spo2_data(date_str)

    def get_stats_and_body(self, date_str: str) -> dict:
        """Get comprehensive daily stats including body composition."""
        return self._client.get_stats_and_body(date_str)

    def get_body_composition(self, date_str: str) -> dict:
        """Get body composition data (weight, body fat, muscle mass, etc.)."""
        return self._client.get_body_composition(date_str, date_str)

    def get_race_predictions(self, date_str: str) -> list[dict]:
        """Get race predictions for a specific date."""
        return self._client.get_race_predictions(date_str, date_str, "daily")

    def get_training_readiness(self, date_str: str) -> dict:
        """Get training readiness score and factors."""
        return self._client.get_training_readiness(date_str)

    def get_max_metrics(self, date_str: str) -> dict:
        """Get VO2max and other max metrics."""
        return self._client.get_max_metrics(date_str)

    def get_endurance_score(self, date_str: str) -> dict:
        """Get endurance score."""
        return self._client.get_endurance_score(date_str, date_str)

    def get_hill_score(self, date_str: str) -> dict:
        """Get hill score."""
        return self._client.get_hill_score(date_str, date_str)

    def get_fitness_age(self, date_str: str) -> dict:
        """Get fitness age estimate."""
        return self._client.get_fitnessage_data(date_str)

    def get_intensity_minutes(self, date_str: str) -> dict:
        """Get intensity minutes (moderate + vigorous)."""
        return self._client.get_intensity_minutes_data(date_str)

    def get_exercise_sets(self, activity_id: str) -> dict:
        """Get per-set exercise data for strength activities."""
        return self._client.get_activity_exercise_sets(activity_id)

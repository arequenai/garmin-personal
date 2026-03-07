from garminconnect import Garmin


class GarminClient:
    def __init__(self, email: str, password: str):
        self.email = email
        self.password = password
        self._client: Garmin | None = None

    def login(self):
        self._client = Garmin(self.email, self.password)
        self._client.login()

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

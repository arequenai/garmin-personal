from unittest.mock import patch, MagicMock
from datetime import date

from app.services.sync_orchestrator import run_frequent_sync


def test_run_frequent_sync_calls_nutrition_and_stress():
    """Frequent sync only syncs nutrition and stress readings for today."""
    mock_db = MagicMock()
    mock_sync = MagicMock()

    with (
        patch("app.services.sync_orchestrator.SessionLocal", return_value=mock_db),
        patch("app.services.sync_orchestrator.GarminClient") as mock_garmin_cls,
        patch("app.services.sync_orchestrator.SyncService", return_value=mock_sync),
        patch("app.services.sync_orchestrator.settings") as mock_settings,
    ):
        mock_settings.garmin_email = "test@test.com"
        mock_settings.garmin_password = "pass"
        mock_settings.mfp_cookies = '{"key": "val"}'
        mock_settings.nightscout_url = ""
        mock_settings.nightscout_token = ""

        run_frequent_sync()

        mock_sync.sync_nutrition.assert_called_once_with(date.today())
        mock_sync.sync_stress_readings.assert_called_once_with(date.today())
        # Should NOT call full sync methods
        mock_sync.sync_all.assert_not_called()
        mock_sync.sync_sleep.assert_not_called()
        mock_sync.sync_activities.assert_not_called()

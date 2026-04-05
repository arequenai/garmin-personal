from datetime import date
from unittest.mock import MagicMock, patch

from app.services.sync_orchestrator import run_frequent_sync


def test_run_frequent_sync_calls_nutrition_only():
    """Frequent sync only syncs nutrition (MFP) for today — no Garmin calls."""
    mock_db = MagicMock()
    mock_sync = MagicMock()

    with (
        patch("app.services.sync_orchestrator.SessionLocal", return_value=mock_db),
        patch("app.services.sync_orchestrator._get_garmin_client") as mock_get_garmin,
        patch("app.services.sync_orchestrator.SyncService", return_value=mock_sync),
        patch("app.services.sync_orchestrator.settings") as mock_settings,
    ):
        mock_settings.mfp_cookies = '{"key": "val"}'

        run_frequent_sync()

        mock_sync.sync_nutrition.assert_called_once_with(date.today())
        # Garmin must NOT be called (avoids 429 rate-limiting)
        mock_get_garmin.assert_not_called()
        mock_sync.sync_stress_readings.assert_not_called()
        # Should NOT call full sync methods
        mock_sync.sync_all.assert_not_called()
        mock_sync.sync_sleep.assert_not_called()
        mock_sync.sync_activities.assert_not_called()

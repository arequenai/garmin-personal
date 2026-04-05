"""Tests for run_frequent_sync() — verifies Garmin is NOT called."""
from datetime import date
from unittest.mock import MagicMock, patch

from app.services.sync_orchestrator import run_frequent_sync


def test_frequent_sync_does_not_call_get_garmin_client():
    """run_frequent_sync() must not call _get_garmin_client (avoids 429 rate-limiting)."""
    mock_db = MagicMock()
    mock_sync = MagicMock()

    with (
        patch("app.services.sync_orchestrator.SessionLocal", return_value=mock_db),
        patch(
            "app.services.sync_orchestrator._get_garmin_client"
        ) as mock_get_garmin,
        patch("app.services.sync_orchestrator.SyncService", return_value=mock_sync),
        patch("app.services.sync_orchestrator.settings") as mock_settings,
    ):
        mock_settings.mfp_cookies = '{"key": "val"}'

        run_frequent_sync()

        mock_get_garmin.assert_not_called()

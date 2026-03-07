from unittest.mock import MagicMock, patch

from app.services.garmin_client import GarminClient


def test_garmin_client_initializes():
    client = GarminClient(email="test@test.com", password="test123")
    assert client.email == "test@test.com"


@patch("app.services.garmin_client.Garmin")
def test_login_calls_garmin_connect(mock_garmin_cls):
    mock_instance = MagicMock()
    mock_garmin_cls.return_value = mock_instance
    client = GarminClient(email="test@test.com", password="test123")
    client.login()
    mock_garmin_cls.assert_called_once_with("test@test.com", "test123")
    mock_instance.login.assert_called_once()


@patch("app.services.garmin_client.Garmin")
def test_get_daily_summary(mock_garmin_cls):
    mock_instance = MagicMock()
    mock_instance.get_stats.return_value = {"totalSteps": 10000}
    mock_garmin_cls.return_value = mock_instance
    client = GarminClient(email="t@t.com", password="p")
    client.login()
    result = client.get_daily_summary("2026-03-06")
    assert result["totalSteps"] == 10000

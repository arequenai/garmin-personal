from unittest.mock import MagicMock, patch

import pytest

from app.services.trainingpeaks_client import TrainingPeaksClient


@pytest.fixture
def mock_httpx():
    with patch("app.services.trainingpeaks_client.httpx") as mock:
        yield mock


def _token_response():
    """Mock GET /users/v3/token response."""
    resp = MagicMock()
    resp.status_code = 200
    resp.json.return_value = {
        "success": True,
        "token": {
            "access_token": "test_token_123",
            "token_type": "bearer",
            "expires_in": 3600,
        },
    }
    resp.raise_for_status = MagicMock()
    return resp


def _user_response():
    """Mock GET /users/v3/user response."""
    resp = MagicMock()
    resp.status_code = 200
    resp.json.return_value = {"user": {"userId": 12345}}
    resp.raise_for_status = MagicMock()
    return resp


def _setup_login(mock_httpx):
    """Configure mock_httpx.get to return token then user responses."""
    mock_httpx.get.side_effect = [_token_response(), _user_response()]


def test_login_exchanges_cookie_for_token(mock_httpx):
    _setup_login(mock_httpx)

    client = TrainingPeaksClient(auth_cookie="Production_tpAuth=abc123")
    client.login()

    assert client._token == "test_token_123"
    assert client._athlete_id == "12345"
    assert mock_httpx.get.call_count == 2


def test_get_athlete_id_returns_cached_id(mock_httpx):
    _setup_login(mock_httpx)

    client = TrainingPeaksClient(auth_cookie="Production_tpAuth=abc")
    client.login()
    assert client.get_athlete_id() == "12345"


def test_get_fitness_calls_correct_endpoint(mock_httpx):
    _setup_login(mock_httpx)

    client = TrainingPeaksClient(auth_cookie="Production_tpAuth=abc")
    client.login()

    fitness_resp = MagicMock()
    fitness_resp.status_code = 200
    fitness_resp.json.return_value = [{"workoutDay": "2026-04-01T00:00:00", "ctl": 55.0}]
    fitness_resp.raise_for_status = MagicMock()
    mock_httpx.post.return_value = fitness_resp

    result = client.get_fitness("2026-04-01", "2026-04-04")

    assert len(result) == 1
    assert result[0]["ctl"] == 55.0
    call_url = mock_httpx.post.call_args[0][0]
    assert "/reporting/performancedata/" in call_url


def test_get_workout_analysis_returns_none_on_failure(mock_httpx):
    _setup_login(mock_httpx)

    client = TrainingPeaksClient(auth_cookie="Production_tpAuth=abc")
    client.login()

    mock_httpx.get.side_effect = Exception("API error")
    result = client.get_workout_analysis("999")

    assert result is None


def test_login_raises_on_bad_cookie(mock_httpx):
    resp = MagicMock()
    resp.status_code = 401
    resp.raise_for_status.side_effect = Exception("401 Unauthorized")
    mock_httpx.get.return_value = resp

    client = TrainingPeaksClient(auth_cookie="bad_cookie")
    with pytest.raises(Exception, match="401"):
        client.login()

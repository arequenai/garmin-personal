import base64
import logging
from datetime import date

import httpx

logger = logging.getLogger(__name__)

API_BASE = "https://api.fitbit.com"
TOKEN_URL = "https://api.fitbit.com/oauth2/token"
AUTHORIZE_URL = "https://www.fitbit.com/oauth2/authorize"


class FitbitClient:
    def __init__(
        self,
        client_id: str,
        client_secret: str,
        access_token: str,
        refresh_token: str,
        redirect_uri: str = "",
    ):
        self.client_id = client_id
        self.client_secret = client_secret
        self.access_token = access_token
        self.refresh_token = refresh_token
        self.redirect_uri = redirect_uri
        self._tokens_refreshed = False

    @property
    def tokens_were_refreshed(self) -> bool:
        return self._tokens_refreshed

    def _basic_auth(self) -> str:
        creds = base64.b64encode(
            f"{self.client_id}:{self.client_secret}".encode()
        ).decode()
        return f"Basic {creds}"

    def _headers(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self.access_token}"}

    def refresh(self) -> dict:
        """Refresh the access token. Returns new token dict."""
        resp = httpx.post(
            TOKEN_URL,
            headers={"Authorization": self._basic_auth()},
            data={
                "grant_type": "refresh_token",
                "refresh_token": self.refresh_token,
            },
            timeout=15,
        )
        resp.raise_for_status()
        data = resp.json()
        self.access_token = data["access_token"]
        self.refresh_token = data["refresh_token"]
        self._tokens_refreshed = True
        logger.info("Fitbit tokens refreshed")
        return data

    def _get(self, path: str) -> dict:
        """Make an authenticated GET request, refreshing token on 401."""
        resp = httpx.get(f"{API_BASE}{path}", headers=self._headers(), timeout=15)
        if resp.status_code == 401:
            self.refresh()
            resp = httpx.get(f"{API_BASE}{path}", headers=self._headers(), timeout=15)
        resp.raise_for_status()
        return resp.json()

    def get_weight(self, target_date: date) -> list[dict]:
        """Get weight logs for a date. Returns list of weight entries."""
        date_str = target_date.isoformat()
        data = self._get(f"/1/user/-/body/log/weight/date/{date_str}.json")
        return data.get("weight", [])

    def get_weight_range(self, start: date, end: date) -> list[dict]:
        """Get weight logs for a date range (max 31 days)."""
        data = self._get(
            f"/1/user/-/body/log/weight/date/{start.isoformat()}/{end.isoformat()}.json"
        )
        return data.get("weight", [])

    def get_body_fat(self, target_date: date) -> list[dict]:
        """Get body fat logs for a date. Returns list of fat entries."""
        date_str = target_date.isoformat()
        data = self._get(f"/1/user/-/body/log/fat/date/{date_str}.json")
        return data.get("fat", [])

    def get_body_fat_range(self, start: date, end: date) -> list[dict]:
        """Get body fat logs for a date range (max 31 days)."""
        data = self._get(
            f"/1/user/-/body/log/fat/date/{start.isoformat()}/{end.isoformat()}.json"
        )
        return data.get("fat", [])

    @staticmethod
    def get_authorize_url(client_id: str, redirect_uri: str) -> str:
        """Build the OAuth2 authorization URL."""
        return (
            f"{AUTHORIZE_URL}"
            f"?response_type=code"
            f"&client_id={client_id}"
            f"&redirect_uri={redirect_uri}"
            f"&scope=weight"
        )

    @staticmethod
    def exchange_code(
        client_id: str, client_secret: str, code: str, redirect_uri: str
    ) -> dict:
        """Exchange authorization code for access + refresh tokens."""
        creds = base64.b64encode(
            f"{client_id}:{client_secret}".encode()
        ).decode()
        resp = httpx.post(
            TOKEN_URL,
            headers={"Authorization": f"Basic {creds}"},
            data={
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": redirect_uri,
            },
            timeout=15,
        )
        resp.raise_for_status()
        return resp.json()

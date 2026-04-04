from fastapi import APIRouter
from fastapi.responses import RedirectResponse

from app.config import settings
from app.database import SessionLocal
from app.models import User
from app.services.fitbit_client import FitbitClient

router = APIRouter(prefix="/api/fitbit", tags=["fitbit"])


@router.get("/authorize")
def authorize():
    """Redirect to Fitbit OAuth2 authorization page."""
    url = FitbitClient.get_authorize_url(
        client_id=settings.fitbit_client_id,
        redirect_uri=settings.fitbit_redirect_uri,
    )
    return RedirectResponse(url)


@router.get("/callback")
def callback(code: str):
    """Handle OAuth2 callback, store tokens in DB."""
    data = FitbitClient.exchange_code(
        client_id=settings.fitbit_client_id,
        client_secret=settings.fitbit_client_secret,
        code=code,
        redirect_uri=settings.fitbit_redirect_uri,
    )

    db = SessionLocal()
    try:
        user = db.query(User).first()
        if not user:
            user = User()
            db.add(user)
        user.fitbit_access_token = data["access_token"]
        user.fitbit_refresh_token = data["refresh_token"]
        db.commit()
    finally:
        db.close()

    return {"status": "ok", "message": "Fitbit connected"}

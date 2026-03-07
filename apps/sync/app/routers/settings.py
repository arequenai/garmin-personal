from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User
from app.schemas.settings import SettingsResponse, SettingsUpdate

router = APIRouter(prefix="/api/settings", tags=["settings"])


def get_user(db: Session) -> User:
    user = db.query(User).first()
    if not user:
        user = User()
        db.add(user)
        db.commit()
        db.refresh(user)
    return user


@router.get("", response_model=SettingsResponse)
def get_settings(db: Session = Depends(get_db)):
    return get_user(db)


@router.put("", response_model=SettingsResponse)
def update_settings(data: SettingsUpdate, db: Session = Depends(get_db)):
    user = get_user(db)
    for field, value in data.model_dump(exclude_none=True).items():
        setattr(user, field, value)
    db.commit()
    db.refresh(user)
    return user

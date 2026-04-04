from sqlalchemy import DateTime, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    garmin_email: Mapped[str] = mapped_column(String(255), default="")
    garmin_password: Mapped[str] = mapped_column(String(512), default="")
    mfp_cookies: Mapped[str] = mapped_column(Text, default="")
    hr_max: Mapped[int] = mapped_column(Integer, default=190)
    hr_rest: Mapped[int] = mapped_column(Integer, default=50)
    hr_threshold: Mapped[int] = mapped_column(Integer, default=165)
    fitbit_access_token: Mapped[str] = mapped_column(Text, default="")
    fitbit_refresh_token: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[DateTime] = mapped_column(DateTime, server_default=func.now())

from sqlalchemy import Date, DateTime, Float, Integer
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class SleepSession(Base):
    __tablename__ = "sleep_sessions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    date: Mapped[Date] = mapped_column(Date, unique=True, nullable=False)
    sleep_start: Mapped[DateTime | None] = mapped_column(DateTime, nullable=True)
    sleep_end: Mapped[DateTime | None] = mapped_column(DateTime, nullable=True)
    total_sleep_min: Mapped[int | None] = mapped_column(Integer, nullable=True)
    deep_min: Mapped[int | None] = mapped_column(Integer, nullable=True)
    light_min: Mapped[int | None] = mapped_column(Integer, nullable=True)
    rem_min: Mapped[int | None] = mapped_column(Integer, nullable=True)
    awake_min: Mapped[int | None] = mapped_column(Integer, nullable=True)
    avg_hr_sleep: Mapped[int | None] = mapped_column(Integer, nullable=True)
    avg_hrv: Mapped[float | None] = mapped_column(Float, nullable=True)
    avg_spo2_sleep: Mapped[float | None] = mapped_column(Float, nullable=True)
    sleep_score: Mapped[int | None] = mapped_column(Integer, nullable=True)

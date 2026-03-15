from sqlalchemy import Date, Float, Integer
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class DailySummary(Base):
    __tablename__ = "daily_summaries"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    date: Mapped[Date] = mapped_column(Date, unique=True, nullable=False)
    steps: Mapped[int | None] = mapped_column(Integer, nullable=True)
    calories_total: Mapped[int | None] = mapped_column(Integer, nullable=True)
    calories_active: Mapped[int | None] = mapped_column(Integer, nullable=True)
    distance_m: Mapped[float | None] = mapped_column(Float, nullable=True)
    floors: Mapped[int | None] = mapped_column(Integer, nullable=True)
    avg_hr: Mapped[int | None] = mapped_column(Integer, nullable=True)
    resting_hr: Mapped[int | None] = mapped_column(Integer, nullable=True)
    max_hr: Mapped[int | None] = mapped_column(Integer, nullable=True)
    min_hr: Mapped[int | None] = mapped_column(Integer, nullable=True)
    stress_avg: Mapped[int | None] = mapped_column(Integer, nullable=True)
    stress_max: Mapped[int | None] = mapped_column(Integer, nullable=True)
    body_battery_high: Mapped[int | None] = mapped_column(Integer, nullable=True)
    body_battery_low: Mapped[int | None] = mapped_column(Integer, nullable=True)
    spo2_avg: Mapped[float | None] = mapped_column(Float, nullable=True)
    respiration_avg: Mapped[float | None] = mapped_column(Float, nullable=True)
    hydration_ml: Mapped[int | None] = mapped_column(Integer, nullable=True)
    intensity_minutes_moderate: Mapped[int | None] = mapped_column(Integer, nullable=True)
    intensity_minutes_vigorous: Mapped[int | None] = mapped_column(Integer, nullable=True)

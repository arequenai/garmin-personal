from sqlalchemy import Date, Float, Integer, String
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class TPCompletedWorkout(Base):
    __tablename__ = "tp_completed_workouts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    tp_workout_id: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    date: Mapped[Date] = mapped_column(Date, nullable=False, index=True)
    title: Mapped[str | None] = mapped_column(String(255), nullable=True)
    workout_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    duration_sec: Mapped[int | None] = mapped_column(Integer, nullable=True)
    distance_m: Mapped[float | None] = mapped_column(Float, nullable=True)
    tss: Mapped[float | None] = mapped_column(Float, nullable=True)
    intensity_factor: Mapped[float | None] = mapped_column(Float, nullable=True)
    avg_hr: Mapped[int | None] = mapped_column(Integer, nullable=True)
    max_hr: Mapped[int | None] = mapped_column(Integer, nullable=True)
    avg_power: Mapped[float | None] = mapped_column(Float, nullable=True)
    max_power: Mapped[float | None] = mapped_column(Float, nullable=True)
    normalized_power: Mapped[float | None] = mapped_column(Float, nullable=True)
    calories: Mapped[int | None] = mapped_column(Integer, nullable=True)
    hr_zone1_sec: Mapped[int | None] = mapped_column(Integer, nullable=True)
    hr_zone2_sec: Mapped[int | None] = mapped_column(Integer, nullable=True)
    hr_zone3_sec: Mapped[int | None] = mapped_column(Integer, nullable=True)
    hr_zone4_sec: Mapped[int | None] = mapped_column(Integer, nullable=True)
    hr_zone5_sec: Mapped[int | None] = mapped_column(Integer, nullable=True)
    power_zone1_sec: Mapped[int | None] = mapped_column(Integer, nullable=True)
    power_zone2_sec: Mapped[int | None] = mapped_column(Integer, nullable=True)
    power_zone3_sec: Mapped[int | None] = mapped_column(Integer, nullable=True)
    power_zone4_sec: Mapped[int | None] = mapped_column(Integer, nullable=True)
    power_zone5_sec: Mapped[int | None] = mapped_column(Integer, nullable=True)
    power_zone6_sec: Mapped[int | None] = mapped_column(Integer, nullable=True)
    power_zone7_sec: Mapped[int | None] = mapped_column(Integer, nullable=True)
    laps_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)

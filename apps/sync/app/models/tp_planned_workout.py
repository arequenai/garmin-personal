from sqlalchemy import Boolean, Date, Float, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class TPPlannedWorkout(Base):
    __tablename__ = "tp_planned_workouts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    tp_workout_id: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    date: Mapped[Date] = mapped_column(Date, nullable=False, index=True)
    title: Mapped[str | None] = mapped_column(String(255), nullable=True)
    workout_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    duration_sec_planned: Mapped[int | None] = mapped_column(Integer, nullable=True)
    tss_planned: Mapped[float | None] = mapped_column(Float, nullable=True)
    distance_m_planned: Mapped[float | None] = mapped_column(Float, nullable=True)
    structure_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    completed: Mapped[bool | None] = mapped_column(Boolean, nullable=True, default=False)

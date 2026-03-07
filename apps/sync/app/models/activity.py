from sqlalchemy import Date, Float, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Activity(Base):
    __tablename__ = "activities"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    garmin_id: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    date: Mapped[Date] = mapped_column(Date, nullable=False, index=True)
    type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    duration_sec: Mapped[int | None] = mapped_column(Integer, nullable=True)
    distance_m: Mapped[float | None] = mapped_column(Float, nullable=True)
    calories: Mapped[int | None] = mapped_column(Integer, nullable=True)
    avg_hr: Mapped[int | None] = mapped_column(Integer, nullable=True)
    max_hr: Mapped[int | None] = mapped_column(Integer, nullable=True)
    avg_power: Mapped[float | None] = mapped_column(Float, nullable=True)
    max_power: Mapped[float | None] = mapped_column(Float, nullable=True)
    training_effect_aerobic: Mapped[float | None] = mapped_column(Float, nullable=True)
    training_effect_anaerobic: Mapped[float | None] = mapped_column(Float, nullable=True)
    vo2max_estimate: Mapped[float | None] = mapped_column(Float, nullable=True)
    elevation_gain: Mapped[float | None] = mapped_column(Float, nullable=True)
    tss: Mapped[float | None] = mapped_column(Float, nullable=True)

    strength_sets = relationship("StrengthSession", back_populates="activity")

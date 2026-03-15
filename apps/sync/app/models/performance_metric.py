from sqlalchemy import JSON, Date, Float, Integer
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class PerformanceMetric(Base):
    __tablename__ = "performance_metrics"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    date: Mapped[Date] = mapped_column(Date, unique=True, nullable=False)
    tss: Mapped[float | None] = mapped_column(Float, nullable=True)
    atl: Mapped[float | None] = mapped_column(Float, nullable=True)
    ctl: Mapped[float | None] = mapped_column(Float, nullable=True)
    tsb: Mapped[float | None] = mapped_column(Float, nullable=True)
    training_load_7d: Mapped[float | None] = mapped_column(Float, nullable=True)
    training_load_28d: Mapped[float | None] = mapped_column(Float, nullable=True)
    recovery_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    vo2max: Mapped[float | None] = mapped_column(Float, nullable=True)
    endurance_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    hill_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    fitness_age: Mapped[int | None] = mapped_column(Integer, nullable=True)
    category_scores: Mapped[dict | None] = mapped_column(JSON, nullable=True)

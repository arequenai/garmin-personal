from sqlalchemy import Date, Float, Integer
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

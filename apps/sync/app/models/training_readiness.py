from sqlalchemy import Date, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class TrainingReadiness(Base):
    __tablename__ = "training_readiness"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    date: Mapped[Date] = mapped_column(Date, unique=True, nullable=False)
    score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    level: Mapped[str | None] = mapped_column(String(50), nullable=True)
    hrv_status: Mapped[str | None] = mapped_column(String(50), nullable=True)
    sleep_status: Mapped[str | None] = mapped_column(String(50), nullable=True)
    recovery_status: Mapped[str | None] = mapped_column(String(50), nullable=True)

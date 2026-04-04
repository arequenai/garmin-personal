from sqlalchemy import Date, DateTime, Integer
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class StressReading(Base):
    __tablename__ = "stress_readings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    date: Mapped[Date] = mapped_column(Date, nullable=False, index=True)
    timestamp: Mapped[DateTime] = mapped_column(DateTime, nullable=False)
    value: Mapped[int] = mapped_column(Integer, nullable=False)

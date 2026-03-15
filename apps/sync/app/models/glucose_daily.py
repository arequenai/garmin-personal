from sqlalchemy import Date, Float, Integer
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class GlucoseDaily(Base):
    __tablename__ = "glucose_daily"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    date: Mapped[Date] = mapped_column(Date, unique=True, nullable=False)
    readings_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    mean_glucose: Mapped[int | None] = mapped_column(Integer, nullable=True)
    min_glucose: Mapped[int | None] = mapped_column(Integer, nullable=True)
    max_glucose: Mapped[int | None] = mapped_column(Integer, nullable=True)
    latest_glucose: Mapped[int | None] = mapped_column(Integer, nullable=True)
    fasting_glucose: Mapped[int | None] = mapped_column(Integer, nullable=True)

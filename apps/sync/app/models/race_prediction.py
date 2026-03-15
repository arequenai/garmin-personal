from sqlalchemy import Date, Integer
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class RacePrediction(Base):
    __tablename__ = "race_predictions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    date: Mapped[Date] = mapped_column(Date, unique=True, nullable=False)
    predicted_5k_sec: Mapped[int | None] = mapped_column(Integer, nullable=True)
    predicted_10k_sec: Mapped[int | None] = mapped_column(Integer, nullable=True)
    predicted_half_sec: Mapped[int | None] = mapped_column(Integer, nullable=True)
    predicted_marathon_sec: Mapped[int | None] = mapped_column(Integer, nullable=True)

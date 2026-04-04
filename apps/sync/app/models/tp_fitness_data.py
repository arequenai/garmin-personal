from sqlalchemy import Date, Float, Integer
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class TPFitnessData(Base):
    __tablename__ = "tp_fitness_data"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    date: Mapped[Date] = mapped_column(Date, unique=True, nullable=False)
    ctl: Mapped[float | None] = mapped_column(Float, nullable=True)
    atl: Mapped[float | None] = mapped_column(Float, nullable=True)
    tsb: Mapped[float | None] = mapped_column(Float, nullable=True)
    tss_day: Mapped[float | None] = mapped_column(Float, nullable=True)
    training_load_7d: Mapped[float | None] = mapped_column(Float, nullable=True)
    training_load_28d: Mapped[float | None] = mapped_column(Float, nullable=True)
    intensity_factor: Mapped[float | None] = mapped_column(Float, nullable=True)
    ramp_rate: Mapped[float | None] = mapped_column(Float, nullable=True)

from sqlalchemy import Date, Float, Integer
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class BodyComposition(Base):
    __tablename__ = "body_composition"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    date: Mapped[Date] = mapped_column(Date, unique=True, nullable=False)
    weight_kg: Mapped[float | None] = mapped_column(Float, nullable=True)
    body_fat_pct: Mapped[float | None] = mapped_column(Float, nullable=True)
    muscle_mass_kg: Mapped[float | None] = mapped_column(Float, nullable=True)
    bone_mass_kg: Mapped[float | None] = mapped_column(Float, nullable=True)
    body_water_pct: Mapped[float | None] = mapped_column(Float, nullable=True)
    bmi: Mapped[float | None] = mapped_column(Float, nullable=True)
    visceral_fat: Mapped[float | None] = mapped_column(Float, nullable=True)

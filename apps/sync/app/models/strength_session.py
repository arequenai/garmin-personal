from sqlalchemy import Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class StrengthSession(Base):
    __tablename__ = "strength_sessions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    activity_id: Mapped[int] = mapped_column(Integer, ForeignKey("activities.id"), nullable=False)
    exercise_name: Mapped[str] = mapped_column(String(255), nullable=False)
    sets: Mapped[int | None] = mapped_column(Integer, nullable=True)
    reps: Mapped[int | None] = mapped_column(Integer, nullable=True)
    weight_kg: Mapped[float | None] = mapped_column(Float, nullable=True)
    tonnage: Mapped[float | None] = mapped_column(Float, nullable=True)

    activity = relationship("Activity", back_populates="strength_sets")

from sqlalchemy import Float, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class ExerciseSet(Base):
    __tablename__ = "exercise_sets"
    __table_args__ = (
        UniqueConstraint("activity_id", "exercise_name", "set_number", name="uq_exercise_set"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    activity_id: Mapped[int] = mapped_column(Integer, ForeignKey("activities.id"), nullable=False)
    exercise_name: Mapped[str] = mapped_column(String(255), nullable=False)
    set_number: Mapped[int] = mapped_column(Integer, nullable=False)
    reps: Mapped[int | None] = mapped_column(Integer, nullable=True)
    weight_kg: Mapped[float | None] = mapped_column(Float, nullable=True)
    duration_sec: Mapped[int | None] = mapped_column(Integer, nullable=True)
    set_type: Mapped[str | None] = mapped_column(String(50), nullable=True)

    activity = relationship("Activity", back_populates="exercise_sets")

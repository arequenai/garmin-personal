"""add trainingpeaks tables

Revision ID: e5f6g7h8i9j0
Revises: d4e5f6g7h8i9
Create Date: 2026-04-04 12:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "e5f6g7h8i9j0"
down_revision: str | Sequence[str] | None = "d4e5f6g7h8i9"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "tp_fitness_data",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("ctl", sa.Float(), nullable=True),
        sa.Column("atl", sa.Float(), nullable=True),
        sa.Column("tsb", sa.Float(), nullable=True),
        sa.Column("tss_day", sa.Float(), nullable=True),
        sa.Column("training_load_7d", sa.Float(), nullable=True),
        sa.Column("training_load_28d", sa.Float(), nullable=True),
        sa.Column("intensity_factor", sa.Float(), nullable=True),
        sa.Column("ramp_rate", sa.Float(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("date"),
    )

    op.create_table(
        "tp_planned_workouts",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("tp_workout_id", sa.String(50), nullable=False),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("title", sa.String(255), nullable=True),
        sa.Column("workout_type", sa.String(100), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("duration_sec_planned", sa.Integer(), nullable=True),
        sa.Column("tss_planned", sa.Float(), nullable=True),
        sa.Column("distance_m_planned", sa.Float(), nullable=True),
        sa.Column("structure_json", postgresql.JSON(), nullable=True),
        sa.Column("completed", sa.Boolean(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tp_workout_id"),
    )
    op.create_index("ix_tp_planned_workouts_date", "tp_planned_workouts", ["date"])

    op.create_table(
        "tp_completed_workouts",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("tp_workout_id", sa.String(50), nullable=False),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("title", sa.String(255), nullable=True),
        sa.Column("workout_type", sa.String(100), nullable=True),
        sa.Column("duration_sec", sa.Integer(), nullable=True),
        sa.Column("distance_m", sa.Float(), nullable=True),
        sa.Column("tss", sa.Float(), nullable=True),
        sa.Column("intensity_factor", sa.Float(), nullable=True),
        sa.Column("avg_hr", sa.Integer(), nullable=True),
        sa.Column("max_hr", sa.Integer(), nullable=True),
        sa.Column("avg_power", sa.Float(), nullable=True),
        sa.Column("max_power", sa.Float(), nullable=True),
        sa.Column("normalized_power", sa.Float(), nullable=True),
        sa.Column("calories", sa.Integer(), nullable=True),
        sa.Column("hr_zone1_sec", sa.Integer(), nullable=True),
        sa.Column("hr_zone2_sec", sa.Integer(), nullable=True),
        sa.Column("hr_zone3_sec", sa.Integer(), nullable=True),
        sa.Column("hr_zone4_sec", sa.Integer(), nullable=True),
        sa.Column("hr_zone5_sec", sa.Integer(), nullable=True),
        sa.Column("power_zone1_sec", sa.Integer(), nullable=True),
        sa.Column("power_zone2_sec", sa.Integer(), nullable=True),
        sa.Column("power_zone3_sec", sa.Integer(), nullable=True),
        sa.Column("power_zone4_sec", sa.Integer(), nullable=True),
        sa.Column("power_zone5_sec", sa.Integer(), nullable=True),
        sa.Column("power_zone6_sec", sa.Integer(), nullable=True),
        sa.Column("power_zone7_sec", sa.Integer(), nullable=True),
        sa.Column("laps_json", postgresql.JSON(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tp_workout_id"),
    )
    op.create_index("ix_tp_completed_workouts_date", "tp_completed_workouts", ["date"])


def downgrade() -> None:
    op.drop_index("ix_tp_completed_workouts_date", "tp_completed_workouts")
    op.drop_table("tp_completed_workouts")
    op.drop_index("ix_tp_planned_workouts_date", "tp_planned_workouts")
    op.drop_table("tp_planned_workouts")
    op.drop_table("tp_fitness_data")

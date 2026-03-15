"""add overview tables and columns

Revision ID: a1b2c3d4e5f6
Revises: ef892169eb33
Create Date: 2026-03-14 12:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "a1b2c3d4e5f6"
down_revision: str | Sequence[str] | None = "ef892169eb33"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    # New tables
    op.create_table(
        "body_composition",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("weight_kg", sa.Float(), nullable=True),
        sa.Column("body_fat_pct", sa.Float(), nullable=True),
        sa.Column("muscle_mass_kg", sa.Float(), nullable=True),
        sa.Column("bone_mass_kg", sa.Float(), nullable=True),
        sa.Column("body_water_pct", sa.Float(), nullable=True),
        sa.Column("bmi", sa.Float(), nullable=True),
        sa.Column("visceral_fat", sa.Float(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("date"),
    )

    op.create_table(
        "race_predictions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("predicted_5k_sec", sa.Integer(), nullable=True),
        sa.Column("predicted_10k_sec", sa.Integer(), nullable=True),
        sa.Column("predicted_half_sec", sa.Integer(), nullable=True),
        sa.Column("predicted_marathon_sec", sa.Integer(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("date"),
    )

    op.create_table(
        "training_readiness",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("score", sa.Integer(), nullable=True),
        sa.Column("level", sa.String(length=50), nullable=True),
        sa.Column("hrv_status", sa.String(length=50), nullable=True),
        sa.Column("sleep_status", sa.String(length=50), nullable=True),
        sa.Column("recovery_status", sa.String(length=50), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("date"),
    )

    op.create_table(
        "exercise_sets",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("activity_id", sa.Integer(), nullable=False),
        sa.Column("exercise_name", sa.String(length=255), nullable=False),
        sa.Column("set_number", sa.Integer(), nullable=False),
        sa.Column("reps", sa.Integer(), nullable=True),
        sa.Column("weight_kg", sa.Float(), nullable=True),
        sa.Column("duration_sec", sa.Integer(), nullable=True),
        sa.Column("set_type", sa.String(length=50), nullable=True),
        sa.ForeignKeyConstraint(["activity_id"], ["activities.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("activity_id", "exercise_name", "set_number", name="uq_exercise_set"),
    )

    op.create_table(
        "user_goals",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("metric_key", sa.String(length=100), nullable=False),
        sa.Column("target_value", sa.Float(), nullable=False),
        sa.Column("target_unit", sa.String(length=50), nullable=False),
        sa.Column("category", sa.String(length=50), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("metric_key"),
    )

    # Add columns to daily_summaries
    op.add_column(
        "daily_summaries",
        sa.Column("intensity_minutes_moderate", sa.Integer(), nullable=True),
    )
    op.add_column(
        "daily_summaries",
        sa.Column("intensity_minutes_vigorous", sa.Integer(), nullable=True),
    )

    # Add columns to performance_metrics
    op.add_column("performance_metrics", sa.Column("vo2max", sa.Float(), nullable=True))
    op.add_column("performance_metrics", sa.Column("endurance_score", sa.Float(), nullable=True))
    op.add_column("performance_metrics", sa.Column("hill_score", sa.Float(), nullable=True))
    op.add_column("performance_metrics", sa.Column("fitness_age", sa.Integer(), nullable=True))
    op.add_column(
        "performance_metrics",
        sa.Column("category_scores", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    )

    # Update users table: remove mfp_username/mfp_password, add mfp_cookies
    op.add_column("users", sa.Column("mfp_cookies", sa.Text(), nullable=True, server_default=""))
    op.drop_column("users", "mfp_username")
    op.drop_column("users", "mfp_password")


def downgrade() -> None:
    """Downgrade schema."""
    # Restore users columns
    op.add_column(
        "users",
        sa.Column("mfp_password", sa.String(length=512), nullable=False, server_default=""),
    )
    op.add_column(
        "users",
        sa.Column("mfp_username", sa.String(length=255), nullable=False, server_default=""),
    )
    op.drop_column("users", "mfp_cookies")

    # Remove performance_metrics columns
    op.drop_column("performance_metrics", "category_scores")
    op.drop_column("performance_metrics", "fitness_age")
    op.drop_column("performance_metrics", "hill_score")
    op.drop_column("performance_metrics", "endurance_score")
    op.drop_column("performance_metrics", "vo2max")

    # Remove daily_summaries columns
    op.drop_column("daily_summaries", "intensity_minutes_vigorous")
    op.drop_column("daily_summaries", "intensity_minutes_moderate")

    # Drop new tables
    op.drop_table("user_goals")
    op.drop_table("exercise_sets")
    op.drop_table("training_readiness")
    op.drop_table("race_predictions")
    op.drop_table("body_composition")

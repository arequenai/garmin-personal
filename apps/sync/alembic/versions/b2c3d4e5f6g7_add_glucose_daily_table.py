"""add glucose_daily table

Revision ID: b2c3d4e5f6g7
Revises: a1b2c3d4e5f6
Create Date: 2026-03-15 12:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "b2c3d4e5f6g7"
down_revision: str | Sequence[str] | None = "a1b2c3d4e5f6"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create glucose_daily table."""
    op.create_table(
        "glucose_daily",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("readings_count", sa.Integer(), nullable=True),
        sa.Column("mean_glucose", sa.Float(), nullable=True),
        sa.Column("min_glucose", sa.Float(), nullable=True),
        sa.Column("max_glucose", sa.Float(), nullable=True),
        sa.Column("latest_glucose", sa.Float(), nullable=True),
        sa.Column("fasting_glucose", sa.Float(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("date"),
    )


def downgrade() -> None:
    """Drop glucose_daily table."""
    op.drop_table("glucose_daily")

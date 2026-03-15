"""change glucose columns from float to integer

Revision ID: d4e5f6g7h8i9
Revises: c3d4e5f6g7h8
Create Date: 2026-03-15 19:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "d4e5f6g7h8i9"
down_revision: str | Sequence[str] | None = "c3d4e5f6g7h8"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

COLUMNS = ["mean_glucose", "min_glucose", "max_glucose", "latest_glucose", "fasting_glucose"]


def upgrade() -> None:
    """Convert glucose columns from Float to Integer."""
    for col in COLUMNS:
        op.alter_column(
            "glucose_daily",
            col,
            type_=sa.Integer(),
            existing_type=sa.Float(),
            existing_nullable=True,
            postgresql_using=f"round({col})::integer",
        )


def downgrade() -> None:
    """Revert glucose columns back to Float."""
    for col in COLUMNS:
        op.alter_column(
            "glucose_daily",
            col,
            type_=sa.Float(),
            existing_type=sa.Integer(),
            existing_nullable=True,
        )

"""add latest_glucose column to glucose_daily

Revision ID: c3d4e5f6g7h8
Revises: b2c3d4e5f6g7
Create Date: 2026-03-15 18:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "c3d4e5f6g7h8"
down_revision: str | Sequence[str] | None = "b2c3d4e5f6g7"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Add latest_glucose column."""
    op.add_column("glucose_daily", sa.Column("latest_glucose", sa.Float(), nullable=True))


def downgrade() -> None:
    """Remove latest_glucose column."""
    op.drop_column("glucose_daily", "latest_glucose")

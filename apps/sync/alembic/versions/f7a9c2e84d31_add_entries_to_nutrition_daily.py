"""add entries jsonb to nutrition_daily

Revision ID: f7a9c2e84d31
Revises: ac43394b8bd6
Create Date: 2026-05-03 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'f7a9c2e84d31'
down_revision: Union[str, Sequence[str], None] = 'ac43394b8bd6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        'nutrition_daily',
        sa.Column(
            'entries',
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('nutrition_daily', 'entries')

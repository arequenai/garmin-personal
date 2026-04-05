"""add FK indexes on exercise_sets and strength_sessions

Revision ID: b3c4d5e6f7a8
Revises: 66c6c6a77a8f
Create Date: 2026-04-05 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = 'b3c4d5e6f7a8'
down_revision: Union[str, Sequence[str], None] = '66c6c6a77a8f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_index('ix_exercise_sets_activity_id', 'exercise_sets', ['activity_id'])
    op.create_index('ix_strength_sessions_activity_id', 'strength_sessions', ['activity_id'])


def downgrade() -> None:
    op.drop_index('ix_strength_sessions_activity_id', table_name='strength_sessions')
    op.drop_index('ix_exercise_sets_activity_id', table_name='exercise_sets')

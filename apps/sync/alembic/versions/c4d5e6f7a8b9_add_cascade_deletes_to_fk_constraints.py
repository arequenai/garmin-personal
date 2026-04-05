"""add cascade deletes to FK constraints

Revision ID: c4d5e6f7a8b9
Revises: b3c4d5e6f7a8
Create Date: 2026-04-05 12:01:00.000000

"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = 'c4d5e6f7a8b9'
down_revision: Union[str, Sequence[str], None] = 'b3c4d5e6f7a8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # exercise_sets FK
    op.drop_constraint('exercise_sets_activity_id_fkey', 'exercise_sets', type_='foreignkey')
    op.create_foreign_key(
        'exercise_sets_activity_id_fkey', 'exercise_sets', 'activities',
        ['activity_id'], ['id'], ondelete='CASCADE',
    )
    # strength_sessions FK
    op.drop_constraint('strength_sessions_activity_id_fkey', 'strength_sessions', type_='foreignkey')
    op.create_foreign_key(
        'strength_sessions_activity_id_fkey', 'strength_sessions', 'activities',
        ['activity_id'], ['id'], ondelete='CASCADE',
    )


def downgrade() -> None:
    op.drop_constraint('strength_sessions_activity_id_fkey', 'strength_sessions', type_='foreignkey')
    op.create_foreign_key(
        'strength_sessions_activity_id_fkey', 'strength_sessions', 'activities',
        ['activity_id'], ['id'],
    )
    op.drop_constraint('exercise_sets_activity_id_fkey', 'exercise_sets', type_='foreignkey')
    op.create_foreign_key(
        'exercise_sets_activity_id_fkey', 'exercise_sets', 'activities',
        ['activity_id'], ['id'],
    )

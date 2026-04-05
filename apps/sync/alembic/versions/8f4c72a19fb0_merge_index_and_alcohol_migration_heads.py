"""merge index and alcohol migration heads

Revision ID: 8f4c72a19fb0
Revises: 30739edcf036, c4d5e6f7a8b9
Create Date: 2026-04-05 16:44:18.406664

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '8f4c72a19fb0'
down_revision: Union[str, Sequence[str], None] = ('30739edcf036', 'c4d5e6f7a8b9')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass

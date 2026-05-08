"""create coach schema and briefings table

Revision ID: a8c1d2e3f4a5
Revises: f7a9c2e84d31
Create Date: 2026-05-08 18:00:00.000000

"""
from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "a8c1d2e3f4a5"
down_revision: str | Sequence[str] | None = "f7a9c2e84d31"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("CREATE SCHEMA IF NOT EXISTS coach")
    op.execute('CREATE EXTENSION IF NOT EXISTS "pgcrypto"')

    op.create_table(
        "briefings",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("kind", sa.Text(), nullable=False),
        sa.Column(
            "sent_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
        sa.Column("inputs_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column(
            "recommendation_json",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
        ),
        sa.Column("semaphore", sa.Text(), nullable=False),
        sa.Column(
            "llm_used",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
        sa.Column("llm_text", sa.Text(), nullable=True),
        sa.Column(
            "flags",
            postgresql.ARRAY(sa.Text()),
            nullable=False,
            server_default=sa.text("'{}'::text[]"),
        ),
        sa.Column("ntfy_status_code", sa.Integer(), nullable=True),
        sa.UniqueConstraint("date", "kind", name="uq_coach_briefings_date_kind"),
        schema="coach",
    )
    op.create_index(
        "idx_coach_briefings_date",
        "briefings",
        [sa.text("date DESC")],
        schema="coach",
    )


def downgrade() -> None:
    op.drop_index("idx_coach_briefings_date", table_name="briefings", schema="coach")
    op.drop_table("briefings", schema="coach")
    op.execute("DROP SCHEMA IF EXISTS coach")

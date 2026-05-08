import json
import os
import uuid
from datetime import date, datetime

from sqlalchemy import (
    JSON,
    Boolean,
    Date,
    DateTime,
    Integer,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import CHAR, TypeDecorator

from app.database import Base


class _UUIDType(TypeDecorator):
    """Postgres UUID with a CHAR(36) fallback for SQLite tests."""

    impl = CHAR
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql":
            return dialect.type_descriptor(UUID(as_uuid=True))
        return dialect.type_descriptor(CHAR(36))

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        if dialect.name == "postgresql":
            return value
        return str(value)

    def process_result_value(self, value, dialect):
        if value is None:
            return None
        if isinstance(value, uuid.UUID):
            return value
        return uuid.UUID(value)


class _StringArray(TypeDecorator):
    """ARRAY(Text) on Postgres, JSON-encoded list on other dialects."""

    impl = Text
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql":
            return dialect.type_descriptor(ARRAY(Text()))
        return dialect.type_descriptor(Text())

    def process_bind_param(self, value, dialect):
        if value is None:
            value = []
        if dialect.name == "postgresql":
            return list(value)
        return json.dumps(list(value))

    def process_result_value(self, value, dialect):
        if value is None:
            return []
        if isinstance(value, list):
            return value
        if not value:
            return []
        try:
            decoded = json.loads(value)
            return decoded if isinstance(decoded, list) else []
        except (TypeError, ValueError):
            return []


def _briefing_table_args() -> tuple:
    args: tuple = (UniqueConstraint("date", "kind", name="uq_coach_briefings_date_kind"),)
    if os.environ.get("COACH_TEST_NO_SCHEMA") == "1":
        return args
    return args + ({"schema": "coach"},)


class CoachBriefing(Base):
    __tablename__ = "briefings"
    __table_args__ = _briefing_table_args()

    id: Mapped[uuid.UUID] = mapped_column(_UUIDType(), primary_key=True, default=uuid.uuid4)
    date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    kind: Mapped[str] = mapped_column(Text, nullable=False)
    sent_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    inputs_json: Mapped[dict] = mapped_column(
        JSON().with_variant(JSONB(), "postgresql"), nullable=False
    )
    recommendation_json: Mapped[dict] = mapped_column(
        JSON().with_variant(JSONB(), "postgresql"), nullable=False
    )
    semaphore: Mapped[str] = mapped_column(Text, nullable=False)
    llm_used: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    llm_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    flags: Mapped[list[str]] = mapped_column(_StringArray(), nullable=False, default=list)
    ntfy_status_code: Mapped[int | None] = mapped_column(Integer, nullable=True)

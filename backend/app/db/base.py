from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, func
from sqlalchemy.types import CHAR, TypeDecorator
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class GUID(TypeDecorator):
    """
    UUID que funciona tanto no PostgreSQL (usa o tipo nativo UUID) quanto no
    SQLite (usado no modo desktop — guarda como CHAR(32) hexadecimal).

    Isso existe porque o app roda em dois "modos": servidor (Docker +
    Postgres) e desktop (SQLite embutido) — ver desktop/README.md.
    """

    impl = CHAR
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql":
            from sqlalchemy.dialects.postgresql import UUID as PG_UUID
            return dialect.type_descriptor(PG_UUID(as_uuid=True))
        return dialect.type_descriptor(CHAR(32))

    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        if dialect.name == "postgresql":
            return str(value)
        if not isinstance(value, uuid.UUID):
            value = uuid.UUID(value)
        return value.hex

    def process_result_value(self, value, dialect):
        if value is None:
            return value
        if isinstance(value, uuid.UUID):
            return value
        return uuid.UUID(value)


class UTCDateTime(TypeDecorator):
    """
    DateTime que sempre devolve data COM fuso (UTC). O PostgreSQL já faz isso;
    o SQLite (modo desktop) devolve data "ingênua" — sem isso, o navegador
    interpretaria a hora UTC como se fosse horário local e mostraria errado.
    """

    impl = DateTime(timezone=True)
    cache_ok = True

    def process_bind_param(self, value, dialect):
        if value is not None and value.tzinfo is not None:
            value = value.astimezone(timezone.utc)
        return value

    def process_result_value(self, value, dialect):
        if value is not None and value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)
        return value


class Base(DeclarativeBase):
    pass


class TimestampedUUIDBase(Base):
    """Toda tabela do SecureScan herda isto: id UUID + created_at/updated_at."""

    __abstract__ = True

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    created_at: Mapped[datetime] = mapped_column(
        UTCDateTime(), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        UTCDateTime(), server_default=func.now(), onupdate=func.now()
    )

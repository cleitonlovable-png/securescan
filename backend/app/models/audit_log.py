from __future__ import annotations

import uuid

from sqlalchemy import ForeignKey, String, JSON
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import GUID, TimestampedUUIDBase


class AuditLog(TimestampedUUIDBase):
    __tablename__ = "audit_logs"

    organization_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("organizations.id"), index=True
    )
    user_id: Mapped[uuid.UUID | None] = mapped_column(GUID(), ForeignKey("users.id"), nullable=True)

    action: Mapped[str] = mapped_column(String(100), index=True)
    resource_type: Mapped[str] = mapped_column(String(50))
    resource_id: Mapped[uuid.UUID | None] = mapped_column(GUID(), nullable=True)
    # NUNCA armazenar segredos completos aqui — ver docs/SECURITY_MODEL.md Seção 6
    log_metadata: Mapped[dict] = mapped_column(JSON, default=dict)

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Boolean, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.security import generate_verification_token
from app.db.base import GUID, TimestampedUUIDBase, UTCDateTime
from app.models.enums import VerificationMethod, VerificationStatus


class Domain(TimestampedUUIDBase):
    __tablename__ = "domains"

    project_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("projects.id"), index=True)
    hostname: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    is_subdomain_wildcard: Mapped[bool] = mapped_column(Boolean, default=False)

    verification_status: Mapped[VerificationStatus] = mapped_column(default=VerificationStatus.PENDING_VERIFICATION)
    verification_method: Mapped[VerificationMethod | None] = mapped_column(nullable=True)
    verification_token: Mapped[str] = mapped_column(String(64), default=generate_verification_token)
    verified_at: Mapped[datetime | None] = mapped_column(UTCDateTime(), nullable=True)

    project: Mapped["Project"] = relationship(back_populates="domains")

    @property
    def allows_active_scan(self) -> bool:
        """Ver docs/SECURITY_MODEL.md Seção 3 — máquina de estados."""
        return self.verification_status in (
            VerificationStatus.VERIFIED,
            VerificationStatus.PRIVATE_ENVIRONMENT,
        )

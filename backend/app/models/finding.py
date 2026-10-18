from __future__ import annotations

import uuid

from sqlalchemy import ForeignKey, String, Text, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import GUID, TimestampedUUIDBase
from app.models.enums import Confidence, FindingStatus, Severity


class Finding(TimestampedUUIDBase):
    __tablename__ = "findings"

    scan_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("scans.id"), index=True)
    plugin_name: Mapped[str] = mapped_column(String(100))

    title: Mapped[str] = mapped_column(String(300))
    description: Mapped[str] = mapped_column(Text)
    category: Mapped[str] = mapped_column(String(100), index=True)
    severity: Mapped[Severity] = mapped_column(index=True)
    confidence: Mapped[Confidence] = mapped_column(default=Confidence.HIGH)

    cwe: Mapped[str | None] = mapped_column(String(20), nullable=True)
    owasp: Mapped[str | None] = mapped_column(String(100), nullable=True)
    endpoint_or_file: Mapped[str | None] = mapped_column(String(500), nullable=True)
    evidence_sanitized: Mapped[str | None] = mapped_column(Text, nullable=True)
    impact: Mapped[str | None] = mapped_column(Text, nullable=True)
    remediation: Mapped[str | None] = mapped_column(Text, nullable=True)
    references: Mapped[list] = mapped_column(JSON, default=list)

    status: Mapped[FindingStatus] = mapped_column(default=FindingStatus.OPEN)
    status_comment: Mapped[str | None] = mapped_column(Text, nullable=True)

    first_seen_scan_id: Mapped[uuid.UUID | None] = mapped_column(
        GUID(), ForeignKey("scans.id"), nullable=True
    )

    scan: Mapped["Scan"] = relationship(back_populates="findings", foreign_keys=[scan_id])

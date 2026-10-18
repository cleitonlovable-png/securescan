from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import ForeignKey, Integer, String, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import GUID, TimestampedUUIDBase, UTCDateTime
from app.models.enums import ScanStatus, ScanType


class Scan(TimestampedUUIDBase):
    __tablename__ = "scans"

    project_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("projects.id"), index=True)
    domain_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("domains.id"), index=True)
    requested_by_user_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("users.id"))

    scan_type: Mapped[ScanType] = mapped_column()
    status: Mapped[ScanStatus] = mapped_column(default=ScanStatus.PENDING)
    progress_percent: Mapped[int] = mapped_column(Integer, default=0)
    current_step: Mapped[str | None] = mapped_column(String(200), nullable=True)

    # parâmetros opcionais do scan (ex: requirements_path, idor_sample_url) — ver ScanContext.extra_config
    extra_config: Mapped[dict] = mapped_column(JSON, default=dict)

    started_at: Mapped[datetime | None] = mapped_column(UTCDateTime(), nullable=True)
    finished_at: Mapped[datetime | None] = mapped_column(UTCDateTime(), nullable=True)
    rq_job_id: Mapped[str | None] = mapped_column(String(100), nullable=True)

    # Resultado do envio do webhook (Seção 31 — Integrações). Preenchido
    # pelo worker logo após tentar enviar, pra aparecer na interface sem
    # precisar abrir o log do container.
    webhook_status: Mapped[str | None] = mapped_column(String(20), nullable=True)  # sent | failed | None
    webhook_error: Mapped[str | None] = mapped_column(String(500), nullable=True)

    project: Mapped["Project"] = relationship(back_populates="scans")
    findings: Mapped[list["Finding"]] = relationship(
        back_populates="scan",
        cascade="all, delete-orphan",
        foreign_keys="Finding.scan_id",
    )

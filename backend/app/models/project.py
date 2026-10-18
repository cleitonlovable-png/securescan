from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import GUID, TimestampedUUIDBase, UTCDateTime
from app.models.enums import Environment


class Project(TimestampedUUIDBase):
    __tablename__ = "projects"

    organization_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("organizations.id"), index=True
    )
    name: Mapped[str] = mapped_column(String(200))
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    environment: Mapped[Environment] = mapped_column(default=Environment.PRODUCTION)
    framework: Mapped[str | None] = mapped_column(String(100), nullable=True)
    repository_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    security_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    last_scan_at: Mapped[datetime | None] = mapped_column(UTCDateTime(), nullable=True)

    organization: Mapped["Organization"] = relationship(back_populates="projects")
    domains: Mapped[list["Domain"]] = relationship(back_populates="project", cascade="all, delete-orphan")
    scans: Mapped[list["Scan"]] = relationship(back_populates="project", cascade="all, delete-orphan")

from __future__ import annotations

import uuid

from sqlalchemy import Boolean, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import GUID, TimestampedUUIDBase
from app.models.enums import OrgRole


class Organization(TimestampedUUIDBase):
    __tablename__ = "organizations"

    name: Mapped[str] = mapped_column(String(200))
    plan: Mapped[str] = mapped_column(String(50), default="free")

    # Webhook — envia o relatório automaticamente quando um scan termina
    # (Seção 31 do documento original: integrações). Ver services/webhook.py.
    webhook_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    webhook_secret: Mapped[str | None] = mapped_column(String(100), nullable=True)
    slack_webhook_url: Mapped[str | None] = mapped_column(String(500), nullable=True)

    projects: Mapped[list["Project"]] = relationship(back_populates="organization")
    members: Mapped[list["OrganizationMember"]] = relationship(back_populates="organization")


class User(TimestampedUUIDBase):
    __tablename__ = "users"

    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255))
    full_name: Mapped[str] = mapped_column(String(200))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    memberships: Mapped[list["OrganizationMember"]] = relationship(back_populates="user")


class OrganizationMember(TimestampedUUIDBase):
    __tablename__ = "organization_members"

    organization_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("organizations.id"), index=True
    )
    user_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("users.id"), index=True)
    role: Mapped[OrgRole] = mapped_column(default=OrgRole.VIEWER)

    organization: Mapped["Organization"] = relationship(back_populates="members")
    user: Mapped["User"] = relationship(back_populates="memberships")

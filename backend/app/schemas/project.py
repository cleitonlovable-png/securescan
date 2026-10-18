from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel

from app.models.enums import Environment, VerificationMethod, VerificationStatus


class DomainCreate(BaseModel):
    hostname: str
    is_private_environment: bool = False  # localhost/IP privado, ver SECURITY_MODEL.md 2.3


class DomainOut(BaseModel):
    id: uuid.UUID
    hostname: str
    verification_status: VerificationStatus
    verification_method: VerificationMethod | None
    verification_token: str
    verified_at: datetime | None

    class Config:
        from_attributes = True


class ProjectCreate(BaseModel):
    name: str
    description: str | None = None
    environment: Environment = Environment.PRODUCTION


class ProjectOut(BaseModel):
    id: uuid.UUID
    name: str
    description: str | None
    environment: Environment
    framework: str | None
    security_score: int | None
    last_scan_at: datetime | None
    created_at: datetime

    class Config:
        from_attributes = True


class ProjectDetailOut(ProjectOut):
    domains: list[DomainOut] = []

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel

from app.models.enums import Confidence, FindingStatus, ScanStatus, ScanType, Severity


class ScanCreate(BaseModel):
    domain_id: uuid.UUID
    scan_type: ScanType
    # parâmetros opcionais repassados ao ScanContext.extra_config dos plugins
    requirements_path: str | None = None
    idor_sample_url: str | None = None
    idor_session_cookie: str | None = None


class ScanOut(BaseModel):
    id: uuid.UUID
    project_id: uuid.UUID
    domain_id: uuid.UUID
    scan_type: ScanType
    status: ScanStatus
    progress_percent: int
    current_step: str | None
    started_at: datetime | None
    finished_at: datetime | None
    created_at: datetime

    class Config:
        from_attributes = True


class FindingOut(BaseModel):
    id: uuid.UUID
    scan_id: uuid.UUID
    plugin_name: str
    title: str
    description: str
    category: str
    severity: Severity
    confidence: Confidence
    cwe: str | None
    owasp: str | None
    endpoint_or_file: str | None
    evidence_sanitized: str | None
    remediation: str | None
    references: list[str]
    status: FindingStatus
    created_at: datetime

    class Config:
        from_attributes = True


class FindingStatusUpdate(BaseModel):
    status: FindingStatus
    status_comment: str | None = None


class SeveritySummary(BaseModel):
    critical: int = 0
    high: int = 0
    medium: int = 0
    low: int = 0
    info: int = 0


class ScanWithSummary(ScanOut):
    severity_summary: SeveritySummary
    webhook_status: str | None = None
    webhook_error: str | None = None

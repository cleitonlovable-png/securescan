from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel

from app.schemas.scan import SeveritySummary


class RecentScanItem(BaseModel):
    id: uuid.UUID
    project_name: str
    domain_hostname: str
    status: str
    total_findings: int
    highest_severity: str | None
    finished_at: datetime | None


class DashboardOut(BaseModel):
    security_score: int | None
    severity_summary: SeveritySummary
    total_projects: int
    recent_scans: list[RecentScanItem]

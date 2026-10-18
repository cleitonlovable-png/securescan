from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.deps import get_membership
from app.db.session import get_db
from app.models.domain import Domain
from app.models.finding import Finding
from app.models.project import Project
from app.models.scan import Scan
from app.schemas.scan import FindingOut

router = APIRouter(prefix="/organizations/{organization_id}", tags=["overview"])

SEVERITY_RANK = {"critical": 0, "high": 1, "medium": 2, "low": 3, "info": 4}


class VulnerabilityItem(FindingOut):
    project_name: str
    domain_hostname: str


class ScanHistoryItem(BaseModel):
    id: uuid.UUID
    project_name: str
    domain_hostname: str
    scan_type: str
    status: str
    total_findings: int
    created_at: str
    finished_at: str | None


@router.get("/vulnerabilities", response_model=list[VulnerabilityItem])
def list_vulnerabilities(
    organization_id: uuid.UUID,
    category: str | None = Query(default=None, description="Filtra por categoria: secrets, database, access_control, infra, web, pii_lgpd, dependencies"),
    limit: int = Query(default=200, le=500),
    db: Session = Depends(get_db),
    _membership=Depends(get_membership),
) -> list[VulnerabilityItem]:
    query = (
        db.query(Finding, Project.name, Domain.hostname)
        .join(Scan, Scan.id == Finding.scan_id)
        .join(Project, Project.id == Scan.project_id)
        .join(Domain, Domain.id == Scan.domain_id)
        .filter(Project.organization_id == organization_id)
    )

    if category:
        query = query.filter(Finding.category == category)

    rows = query.order_by(Finding.created_at.desc()).limit(limit).all()

    # ordena por severidade real (crítico primeiro), não alfabética
    rows = sorted(rows, key=lambda r: SEVERITY_RANK.get(r[0].severity.value, 99))

    return [
        VulnerabilityItem(**FindingOut.model_validate(finding).model_dump(), project_name=project_name, domain_hostname=hostname)
        for finding, project_name, hostname in rows
    ]


@router.get("/scans", response_model=list[ScanHistoryItem])
def list_all_scans(
    organization_id: uuid.UUID,
    limit: int = Query(default=100, le=300),
    db: Session = Depends(get_db),
    _membership=Depends(get_membership),
) -> list[ScanHistoryItem]:
    from sqlalchemy import func

    rows = (
        db.query(Scan, Project.name, Domain.hostname)
        .join(Project, Project.id == Scan.project_id)
        .join(Domain, Domain.id == Scan.domain_id)
        .filter(Project.organization_id == organization_id)
        .order_by(Scan.created_at.desc())
        .limit(limit)
        .all()
    )

    result = []
    for scan, project_name, hostname in rows:
        total = db.query(func.count(Finding.id)).filter_by(scan_id=scan.id).scalar() or 0
        result.append(ScanHistoryItem(
            id=scan.id,
            project_name=project_name,
            domain_hostname=hostname,
            scan_type=scan.scan_type.value,
            status=scan.status.value,
            total_findings=total,
            created_at=scan.created_at.isoformat(),
            finished_at=scan.finished_at.isoformat() if scan.finished_at else None,
        ))
    return result

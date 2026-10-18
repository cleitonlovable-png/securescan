from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.api.deps import get_membership
from app.db.session import get_db
from app.models.domain import Domain
from app.models.finding import Finding
from app.models.project import Project
from app.models.scan import Scan
from app.schemas.dashboard import DashboardOut, RecentScanItem
from app.schemas.scan import SeveritySummary
from app.services.scoring import calculate_security_score

router = APIRouter(prefix="/organizations/{organization_id}/dashboard", tags=["dashboard"])


SEVERITY_RANK = {"critical": 0, "high": 1, "medium": 2, "low": 3, "info": 4}


@router.get("", response_model=DashboardOut)
def get_dashboard(
    organization_id: uuid.UUID,
    db: Session = Depends(get_db),
    _membership=Depends(get_membership),
) -> DashboardOut:
    project_ids = [p.id for p in db.query(Project.id).filter_by(organization_id=organization_id).all()]

    severity_counts = dict(
        db.query(Finding.severity, func.count(Finding.id))
        .join(Scan, Scan.id == Finding.scan_id)
        .filter(Scan.project_id.in_(project_ids))
        .group_by(Finding.severity)
        .all()
    ) if project_ids else {}

    summary = SeveritySummary(**{sev.value: count for sev, count in severity_counts.items()})
    score = calculate_security_score(severity_counts) if severity_counts else None

    recent_scans_query = (
        db.query(Scan, Project.name, Domain.hostname)
        .join(Project, Project.id == Scan.project_id)
        .join(Domain, Domain.id == Scan.domain_id)
        .filter(Scan.project_id.in_(project_ids))
        .order_by(Scan.created_at.desc())
        .limit(5)
        .all()
        if project_ids else []
    )

    recent_scans = []
    for scan, project_name, domain_hostname in recent_scans_query:
        finding_count = db.query(func.count(Finding.id)).filter_by(scan_id=scan.id).scalar()
        all_severities = [
            s[0].value for s in db.query(Finding.severity).filter_by(scan_id=scan.id).all()
        ]
        highest_severity = (
            min(all_severities, key=lambda s: SEVERITY_RANK.get(s, 99)) if all_severities else None
        )
        recent_scans.append(RecentScanItem(
            id=scan.id,
            project_name=project_name,
            domain_hostname=domain_hostname,
            status=scan.status.value,
            total_findings=finding_count or 0,
            highest_severity=highest_severity,
            finished_at=scan.finished_at,
        ))

    return DashboardOut(
        security_score=score,
        severity_summary=summary,
        total_projects=len(project_ids),
        recent_scans=recent_scans,
    )

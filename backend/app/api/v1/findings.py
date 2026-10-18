from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_membership
from app.db.session import get_db
from app.models.finding import Finding
from app.models.scan import Scan
from app.schemas.scan import FindingOut, FindingStatusUpdate

router = APIRouter(
    prefix="/organizations/{organization_id}/projects/{project_id}/scans/{scan_id}/findings",
    tags=["findings"],
)


@router.get("", response_model=list[FindingOut])
def list_findings(
    organization_id: uuid.UUID,
    project_id: uuid.UUID,
    scan_id: uuid.UUID,
    db: Session = Depends(get_db),
    _membership=Depends(get_membership),
) -> list[Finding]:
    scan = db.query(Scan).filter_by(id=scan_id, project_id=project_id).first()
    if scan is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Scan não encontrado.")

    return (
        db.query(Finding)
        .filter_by(scan_id=scan_id)
        .order_by(Finding.severity, Finding.created_at.desc())
        .all()
    )


@router.patch("/{finding_id}", response_model=FindingOut)
def update_finding_status(
    organization_id: uuid.UUID,
    project_id: uuid.UUID,
    scan_id: uuid.UUID,
    finding_id: uuid.UUID,
    payload: FindingStatusUpdate,
    db: Session = Depends(get_db),
    _membership=Depends(get_membership),
) -> Finding:
    """Seção 26 do prompt original: Confirmado / Possível / Falso positivo / Corrigido / Aceito / Ignorado."""
    finding = db.query(Finding).filter_by(id=finding_id, scan_id=scan_id).first()
    if finding is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Achado não encontrado.")

    finding.status = payload.status
    finding.status_comment = payload.status_comment
    db.commit()
    db.refresh(finding)
    return finding

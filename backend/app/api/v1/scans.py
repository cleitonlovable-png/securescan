from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import Response
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_membership
from app.db.session import get_db
from app.models.domain import Domain
from app.models.enums import ScanStatus, Severity
from app.models.finding import Finding
from app.models.project import Project
from app.models.scan import Scan
from app.models.user import User
from app.schemas.scan import ScanCreate, ScanOut, ScanWithSummary, SeveritySummary
from app.services.pdf_report import generate_scan_pdf
from app.services.executive_report import generate_executive_pdf
from app.services.html_report import generate_scan_html
from app.services.csv_report import generate_scan_csv
from app.services.scan_service import ScanNotAllowedError, cancel_scan, create_and_enqueue_scan

router = APIRouter(prefix="/organizations/{organization_id}/projects/{project_id}/scans", tags=["scans"])


@router.post("", response_model=ScanOut, status_code=status.HTTP_201_CREATED)
def create_scan(
    organization_id: uuid.UUID,
    project_id: uuid.UUID,
    payload: ScanCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _membership=Depends(get_membership),
) -> Scan:
    domain = db.query(Domain).filter_by(id=payload.domain_id, project_id=project_id).first()
    if domain is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Domínio não encontrado neste projeto.")

    extra_config = {
        k: v for k, v in {
            "requirements_path": payload.requirements_path,
            "idor_sample_url": payload.idor_sample_url,
            "idor_session_cookie": payload.idor_session_cookie,
        }.items() if v is not None
    }

    try:
        scan = create_and_enqueue_scan(
            db=db, domain=domain, scan_type=payload.scan_type,
            requested_by_user_id=current_user.id, extra_config=extra_config,
        )
    except ScanNotAllowedError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))

    return scan


@router.get("", response_model=list[ScanOut])
def list_scans(
    organization_id: uuid.UUID,
    project_id: uuid.UUID,
    db: Session = Depends(get_db),
    _membership=Depends(get_membership),
) -> list[Scan]:
    return (
        db.query(Scan)
        .filter_by(project_id=project_id)
        .order_by(Scan.created_at.desc())
        .all()
    )


@router.get("/{scan_id}", response_model=ScanWithSummary)
def get_scan(
    organization_id: uuid.UUID,
    project_id: uuid.UUID,
    scan_id: uuid.UUID,
    db: Session = Depends(get_db),
    _membership=Depends(get_membership),
) -> ScanWithSummary:
    scan = db.query(Scan).filter_by(id=scan_id, project_id=project_id).first()
    if scan is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Scan não encontrado.")

    counts = (
        db.query(Finding.severity, func.count(Finding.id))
        .filter_by(scan_id=scan.id)
        .group_by(Finding.severity)
        .all()
    )
    summary = SeveritySummary(**{sev.value: count for sev, count in counts})

    return ScanWithSummary(
        **ScanOut.model_validate(scan).model_dump(),
        severity_summary=summary,
        webhook_status=scan.webhook_status,
        webhook_error=scan.webhook_error,
    )


@router.post("/{scan_id}/cancel", response_model=ScanOut)
def cancel_scan_route(
    organization_id: uuid.UUID,
    project_id: uuid.UUID,
    scan_id: uuid.UUID,
    db: Session = Depends(get_db),
    _membership=Depends(get_membership),
) -> Scan:
    scan = db.query(Scan).filter_by(id=scan_id, project_id=project_id).first()
    if scan is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Scan não encontrado.")

    cancel_scan(scan)
    db.commit()
    db.refresh(scan)
    return scan


@router.get("/{scan_id}/report.pdf")
def download_scan_report(
    organization_id: uuid.UUID,
    project_id: uuid.UUID,
    scan_id: uuid.UUID,
    db: Session = Depends(get_db),
    _membership=Depends(get_membership),
) -> Response:
    scan = db.query(Scan).filter_by(id=scan_id, project_id=project_id).first()
    if scan is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Scan não encontrado.")

    domain = db.get(Domain, scan.domain_id)
    findings = db.query(Finding).filter_by(scan_id=scan.id).all()

    pdf_bytes = generate_scan_pdf(target=domain.hostname if domain else "desconhecido", findings=findings)

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="relatorio_{scan_id}.pdf"'},
    )


@router.get("/{scan_id}/report/executive.pdf")
def download_executive_report(
    organization_id: uuid.UUID,
    project_id: uuid.UUID,
    scan_id: uuid.UUID,
    db: Session = Depends(get_db),
    _membership=Depends(get_membership),
) -> Response:
    scan = db.query(Scan).filter_by(id=scan_id, project_id=project_id).first()
    if scan is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Scan não encontrado.")

    domain = db.get(Domain, scan.domain_id)
    findings = db.query(Finding).filter_by(scan_id=scan.id).all()
    pdf_bytes = generate_executive_pdf(target=domain.hostname if domain else "desconhecido", findings=findings)

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="resumo_executivo_{scan_id}.pdf"'},
    )


@router.get("/{scan_id}/report.html")
def download_scan_report_html(
    organization_id: uuid.UUID,
    project_id: uuid.UUID,
    scan_id: uuid.UUID,
    db: Session = Depends(get_db),
    _membership=Depends(get_membership),
) -> Response:
    scan = db.query(Scan).filter_by(id=scan_id, project_id=project_id).first()
    if scan is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Scan não encontrado.")

    domain = db.get(Domain, scan.domain_id)
    findings = db.query(Finding).filter_by(scan_id=scan.id).all()
    html = generate_scan_html(target=domain.hostname if domain else "desconhecido", findings=findings)

    return Response(content=html, media_type="text/html")


@router.get("/{scan_id}/report.csv")
def download_scan_report_csv(
    organization_id: uuid.UUID,
    project_id: uuid.UUID,
    scan_id: uuid.UUID,
    db: Session = Depends(get_db),
    _membership=Depends(get_membership),
) -> Response:
    scan = db.query(Scan).filter_by(id=scan_id, project_id=project_id).first()
    if scan is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Scan não encontrado.")

    findings = db.query(Finding).filter_by(scan_id=scan.id).all()
    csv_text = generate_scan_csv(findings)

    return Response(
        content=csv_text,
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="relatorio_{scan_id}.csv"'},
    )


@router.get("/{scan_id}/diff")
def get_scan_diff(
    organization_id: uuid.UUID,
    project_id: uuid.UUID,
    scan_id: uuid.UUID,
    db: Session = Depends(get_db),
    _membership=Depends(get_membership),
) -> dict:
    """
    Compara os achados deste scan com o scan COMPLETED anterior mais recente
    do mesmo domínio (Seção 45 do documento original — Scan Diff).
    """
    scan = db.query(Scan).filter_by(id=scan_id, project_id=project_id).first()
    if scan is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Scan não encontrado.")

    previous_scan = (
        db.query(Scan)
        .filter(
            Scan.domain_id == scan.domain_id,
            Scan.id != scan.id,
            Scan.status == ScanStatus.COMPLETED,
            Scan.created_at < scan.created_at,
        )
        .order_by(Scan.created_at.desc())
        .first()
    )

    if previous_scan is None:
        return {"has_previous_scan": False, "new_count": 0, "resolved_count": 0, "new_findings": [], "resolved_findings": []}

    def _keys(scan_id_: uuid.UUID) -> dict[str, Finding]:
        rows = db.query(Finding).filter_by(scan_id=scan_id_).all()
        return {f"{f.plugin_name}::{f.title}": f for f in rows}

    current_keys = _keys(scan.id)
    previous_keys = _keys(previous_scan.id)

    new_keys = set(current_keys) - set(previous_keys)
    resolved_keys = set(previous_keys) - set(current_keys)

    return {
        "has_previous_scan": True,
        "previous_scan_id": str(previous_scan.id),
        "new_count": len(new_keys),
        "resolved_count": len(resolved_keys),
        "new_findings": [current_keys[k].title for k in new_keys],
        "resolved_findings": [previous_keys[k].title for k in resolved_keys],
    }

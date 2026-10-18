from __future__ import annotations

import uuid
from urllib.parse import urlparse

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_membership
from app.db.session import get_db
from app.models.domain import Domain
from app.models.enums import ScanType, VerificationStatus
from app.models.project import Project
from app.models.scan import Scan
from app.models.user import User
from app.schemas.scan import ScanOut
from app.services.authorization import is_private_host
from app.services.scan_service import ScanNotAllowedError, create_and_enqueue_scan

router = APIRouter(prefix="/organizations/{organization_id}/quick-scan", tags=["quick-scan"])

QUICK_SCAN_PROJECT_NAME = "Varreduras Rápidas"


class QuickScanRequest(BaseModel):
    url: str
    scan_type: ScanType = ScanType.FULL_SCAN
    authorize: bool = False
    requirements_path: str | None = None
    idor_sample_url: str | None = None
    idor_session_cookie: str | None = None
    zap_api_key: str | None = None
    zap_proxy: str | None = None
    repo_url: str | None = None
    repo_branch: str | None = None
    openapi_url: str | None = None
    graphql_url: str | None = None
    dockerfile_content: str | None = None
    bucket_url: str | None = None
    supabase_url: str | None = None
    supabase_anon_key: str | None = None
    rate_limit_test_url: str | None = None


def _get_or_create_quick_scan_project(db: Session, organization_id: uuid.UUID) -> Project:
    project = (
        db.query(Project)
        .filter_by(organization_id=organization_id, name=QUICK_SCAN_PROJECT_NAME)
        .first()
    )
    if project is None:
        project = Project(organization_id=organization_id, name=QUICK_SCAN_PROJECT_NAME)
        db.add(project)
        db.flush()
    return project


def _get_or_create_domain(db: Session, project: Project, hostname: str, authorize: bool) -> Domain:
    domain = db.query(Domain).filter_by(hostname=hostname, project_id=project.id).first()
    if domain is not None:
        return domain

    # Ver docs/SECURITY_MODEL.md Seção 2.3 — localhost/IP privado não precisa
    # de verificação formal. Para domínios públicos usados nesta tela rápida,
    # confiamos na confirmação explícita do usuário (mesmo padrão do
    # protótipo local: checkbox de autorização em vez de fluxo DNS/arquivo).
    if is_private_host(hostname):
        initial_status = VerificationStatus.PRIVATE_ENVIRONMENT
    elif authorize:
        initial_status = VerificationStatus.PRIVATE_ENVIRONMENT
    else:
        initial_status = VerificationStatus.PENDING_VERIFICATION

    domain = Domain(project_id=project.id, hostname=hostname, verification_status=initial_status)
    db.add(domain)
    db.flush()
    return domain


@router.post("", response_model=ScanOut, status_code=status.HTTP_201_CREATED)
def quick_scan(
    organization_id: uuid.UUID,
    payload: QuickScanRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _membership=Depends(get_membership),
) -> Scan:
    if not payload.authorize:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="É necessário confirmar que você tem autorização para escanear este alvo.",
        )

    hostname = urlparse(payload.url if "://" in payload.url else f"http://{payload.url}").hostname
    if not hostname:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="URL inválida.")

    project = _get_or_create_quick_scan_project(db, organization_id)
    domain = _get_or_create_domain(db, project, hostname, payload.authorize)
    db.commit()
    db.refresh(domain)

    extra_config = {
        k: v for k, v in {
            "requirements_path": payload.requirements_path,
            "idor_sample_url": payload.idor_sample_url,
            "idor_session_cookie": payload.idor_session_cookie,
            "zap_api_key": payload.zap_api_key,
            "zap_proxy": payload.zap_proxy,
            "repo_url": payload.repo_url,
            "repo_branch": payload.repo_branch,
            "openapi_url": payload.openapi_url,
            "graphql_url": payload.graphql_url,
            "dockerfile_content": payload.dockerfile_content,
            "bucket_url": payload.bucket_url,
            "supabase_url": payload.supabase_url,
            "supabase_anon_key": payload.supabase_anon_key,
            "rate_limit_test_url": payload.rate_limit_test_url,
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

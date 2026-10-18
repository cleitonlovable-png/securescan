from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_membership
from app.db.session import get_db
from app.models.domain import Domain
from app.models.enums import VerificationMethod, VerificationStatus
from app.models.project import Project
from app.models.user import User
from app.schemas.project import DomainCreate, DomainOut, ProjectCreate, ProjectDetailOut, ProjectOut
from app.services.authorization import attempt_verification, is_private_host

router = APIRouter(prefix="/organizations/{organization_id}/projects", tags=["projects"])


@router.post("", response_model=ProjectOut, status_code=status.HTTP_201_CREATED)
def create_project(
    organization_id: uuid.UUID,
    payload: ProjectCreate,
    db: Session = Depends(get_db),
    _membership=Depends(get_membership),
) -> Project:
    project = Project(organization_id=organization_id, **payload.model_dump())
    db.add(project)
    db.commit()
    db.refresh(project)
    return project


@router.get("", response_model=list[ProjectOut])
def list_projects(
    organization_id: uuid.UUID,
    db: Session = Depends(get_db),
    _membership=Depends(get_membership),
) -> list[Project]:
    return db.query(Project).filter_by(organization_id=organization_id).all()


@router.get("/{project_id}", response_model=ProjectDetailOut)
def get_project(
    organization_id: uuid.UUID,
    project_id: uuid.UUID,
    db: Session = Depends(get_db),
    _membership=Depends(get_membership),
) -> Project:
    project = db.query(Project).filter_by(id=project_id, organization_id=organization_id).first()
    if project is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Projeto não encontrado.")
    return project


@router.post("/{project_id}/domains", response_model=DomainOut, status_code=status.HTTP_201_CREATED)
def add_domain(
    organization_id: uuid.UUID,
    project_id: uuid.UUID,
    payload: DomainCreate,
    db: Session = Depends(get_db),
    _membership=Depends(get_membership),
) -> Domain:
    project = db.query(Project).filter_by(id=project_id, organization_id=organization_id).first()
    if project is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Projeto não encontrado.")

    existing = db.query(Domain).filter_by(hostname=payload.hostname).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Este domínio já está cadastrado.")

    initial_status = VerificationStatus.PENDING_VERIFICATION
    if payload.is_private_environment or is_private_host(payload.hostname):
        initial_status = VerificationStatus.PRIVATE_ENVIRONMENT

    domain = Domain(project_id=project_id, hostname=payload.hostname, verification_status=initial_status)
    db.add(domain)
    db.commit()
    db.refresh(domain)
    return domain


@router.post("/{project_id}/domains/{domain_id}/verify", response_model=DomainOut)
def verify_domain(
    organization_id: uuid.UUID,
    project_id: uuid.UUID,
    domain_id: uuid.UUID,
    method: VerificationMethod,
    db: Session = Depends(get_db),
    _membership=Depends(get_membership),
) -> Domain:
    """Ver docs/SECURITY_MODEL.md Seção 2 — verificação via arquivo ou DNS TXT."""
    domain = db.query(Domain).filter_by(id=domain_id, project_id=project_id).first()
    if domain is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Domínio não encontrado.")

    domain.verification_method = method
    domain.verification_status = attempt_verification(domain, method)
    if domain.verification_status == VerificationStatus.VERIFIED:
        from datetime import datetime, timezone
        domain.verified_at = datetime.now(timezone.utc)

    db.commit()
    db.refresh(domain)
    return domain

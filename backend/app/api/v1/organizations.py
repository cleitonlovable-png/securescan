from __future__ import annotations

import secrets
import uuid

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_membership, require_role
from app.db.session import get_db
from app.models.enums import OrgRole
from app.models.user import Organization, OrganizationMember, User

router = APIRouter(prefix="/organizations", tags=["organizations"])


class OrganizationOut(BaseModel):
    id: uuid.UUID
    name: str
    plan: str

    class Config:
        from_attributes = True


class WebhookSettingsOut(BaseModel):
    webhook_url: str | None
    webhook_secret: str | None
    slack_webhook_url: str | None


class WebhookSettingsUpdate(BaseModel):
    webhook_url: str | None = None
    webhook_secret: str | None = None
    slack_webhook_url: str | None = None


@router.get("", response_model=list[OrganizationOut])
def list_my_organizations(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[Organization]:
    return (
        db.query(Organization)
        .join(OrganizationMember, OrganizationMember.organization_id == Organization.id)
        .filter(OrganizationMember.user_id == current_user.id)
        .all()
    )


class OrganizationCreate(BaseModel):
    name: str


@router.post("", response_model=OrganizationOut, status_code=201)
def create_organization(
    payload: OrganizationCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Organization:
    """Multi-tenancy — Seção 35 do documento original. Qualquer usuário logado
    pode criar uma organização nova e vira OWNER dela automaticamente."""
    org = Organization(name=payload.name)
    db.add(org)
    db.flush()
    db.add(OrganizationMember(organization_id=org.id, user_id=current_user.id, role=OrgRole.OWNER))
    db.commit()
    db.refresh(org)
    return org


class MemberOut(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    email: str
    full_name: str
    role: OrgRole

    class Config:
        from_attributes = True


class MemberInvite(BaseModel):
    email: str
    role: OrgRole = OrgRole.VIEWER


@router.get("/{organization_id}/members", response_model=list[MemberOut])
def list_members(
    organization_id: uuid.UUID,
    db: Session = Depends(get_db),
    _membership=Depends(get_membership),
) -> list[MemberOut]:
    rows = (
        db.query(OrganizationMember, User)
        .join(User, User.id == OrganizationMember.user_id)
        .filter(OrganizationMember.organization_id == organization_id)
        .all()
    )
    return [
        MemberOut(id=m.id, user_id=u.id, email=u.email, full_name=u.full_name, role=m.role)
        for m, u in rows
    ]


@router.post("/{organization_id}/members", response_model=MemberOut, status_code=201)
def invite_member(
    organization_id: uuid.UUID,
    payload: MemberInvite,
    db: Session = Depends(get_db),
    membership=Depends(require_role(OrgRole.OWNER, OrgRole.ADMIN)),
) -> MemberOut:
    """
    Convite simplificado — Seção 35/37. Sem envio de e-mail ainda: a pessoa
    convidada precisa já ter uma conta no SecureScan (criada em /register).
    """
    invited_user = db.query(User).filter_by(email=payload.email).first()
    if invited_user is None:
        raise HTTPException(
            status_code=404,
            detail="Não existe usuário cadastrado com este e-mail. Peça para a pessoa criar uma "
                   "conta em /register primeiro.",
        )

    existing = db.query(OrganizationMember).filter_by(
        organization_id=organization_id, user_id=invited_user.id
    ).first()
    if existing:
        raise HTTPException(status_code=409, detail="Este usuário já faz parte da organização.")

    new_membership = OrganizationMember(
        organization_id=organization_id, user_id=invited_user.id, role=payload.role,
    )
    db.add(new_membership)
    db.commit()
    db.refresh(new_membership)

    return MemberOut(
        id=new_membership.id, user_id=invited_user.id,
        email=invited_user.email, full_name=invited_user.full_name, role=new_membership.role,
    )


@router.delete("/{organization_id}/members/{membership_id}", status_code=204)
def remove_member(
    organization_id: uuid.UUID,
    membership_id: uuid.UUID,
    db: Session = Depends(get_db),
    membership=Depends(require_role(OrgRole.OWNER, OrgRole.ADMIN)),
) -> None:
    target = db.query(OrganizationMember).filter_by(id=membership_id, organization_id=organization_id).first()
    if target is None:
        raise HTTPException(status_code=404, detail="Membro não encontrado.")
    if target.role == OrgRole.OWNER:
        raise HTTPException(status_code=400, detail="Não é possível remover o dono da organização.")
    db.delete(target)
    db.commit()


@router.get("/{organization_id}/webhook", response_model=WebhookSettingsOut)
def get_webhook_settings(
    organization_id: uuid.UUID,
    db: Session = Depends(get_db),
    _membership=Depends(get_membership),
) -> Organization:
    return db.get(Organization, organization_id)


@router.put("/{organization_id}/webhook", response_model=WebhookSettingsOut)
def update_webhook_settings(
    organization_id: uuid.UUID,
    payload: WebhookSettingsUpdate,
    db: Session = Depends(get_db),
    _membership=Depends(get_membership),
) -> Organization:
    """Ver docs/SECURITY_MODEL.md Seção 7 — só OWNER/ADMIN deveriam poder
    mudar isso em um cenário multi-usuário; no modo local, qualquer membro
    (só existe o OWNER mesmo) pode configurar."""
    org = db.get(Organization, organization_id)
    org.webhook_url = payload.webhook_url
    org.webhook_secret = payload.webhook_secret
    org.slack_webhook_url = payload.slack_webhook_url
    db.commit()
    db.refresh(org)
    return org


@router.post("/{organization_id}/webhook/generate-secret", response_model=WebhookSettingsOut)
def generate_webhook_secret(
    organization_id: uuid.UUID,
    db: Session = Depends(get_db),
    _membership=Depends(get_membership),
) -> Organization:
    org = db.get(Organization, organization_id)
    org.webhook_secret = secrets.token_urlsafe(32)
    db.commit()
    db.refresh(org)
    return org

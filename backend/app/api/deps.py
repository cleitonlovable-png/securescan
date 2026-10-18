from __future__ import annotations

import uuid

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.security import decode_token
from app.db.session import get_db
from app.models.enums import OrgRole
from app.models.user import Organization, OrganizationMember, User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    credentials_error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Credenciais inválidas ou expiradas.",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = decode_token(token)
        if payload.get("type") != "access":
            raise credentials_error
        user_id = uuid.UUID(payload["sub"])
    except (jwt.InvalidTokenError, KeyError, ValueError):
        raise credentials_error

    user = db.get(User, user_id)
    if user is None or not user.is_active:
        raise credentials_error
    return user


def get_membership(
    organization_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> OrganizationMember:
    membership = (
        db.query(OrganizationMember)
        .filter_by(organization_id=organization_id, user_id=current_user.id)
        .first()
    )
    if membership is None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Sem acesso a esta organização.")
    return membership


def require_role(*allowed_roles: OrgRole):
    """
    Uso: Depends(require_role(OrgRole.OWNER, OrgRole.ADMIN))
    Aplica RBAC de verdade na camada de API — nunca só escondido na interface
    (ver docs/SECURITY_MODEL.md Seção 7).
    """

    def dependency(membership: OrganizationMember = Depends(get_membership)) -> OrganizationMember:
        if membership.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Esta ação requer um dos papéis: {[r.value for r in allowed_roles]}.",
            )
        return membership

    return dependency

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.limiter import limiter
from app.core.security import create_access_token, create_refresh_token, hash_password, verify_password
from app.db.session import get_db
from app.models.enums import OrgRole
from app.models.user import Organization, OrganizationMember, User
from app.schemas.auth import TokenPair, UserOut, UserRegister

router = APIRouter(prefix="/auth", tags=["auth"])

DEV_USER_EMAIL = "admin@local.securescan"
DEV_ORG_NAME = "Minha Organização"


@router.post("/dev-bootstrap", response_model=TokenPair)
def dev_bootstrap(db: Session = Depends(get_db)) -> TokenPair:
    """
    Conveniência para uso local (Fase 43 — Modo Local do roadmap): cria (ou
    reaproveita) um usuário e organização padrão, sem exigir fluxo de
    cadastro manual. Pensado para quem está rodando o SecureScan sozinho na
    própria máquina via docker compose up.

    Bloqueado em produção — nunca deve existir um jeito de logar sem senha
    fora de ambiente de desenvolvimento local (ver docs/SECURITY_MODEL.md).
    """
    if settings.environment == "production":
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Não encontrado.")

    user = db.query(User).filter_by(email=DEV_USER_EMAIL).first()
    if user is None:
        user = User(
            email=DEV_USER_EMAIL,
            hashed_password=hash_password("dev-local-only"),
            full_name="Administrador",
        )
        db.add(user)
        db.flush()

        organization = Organization(name=DEV_ORG_NAME)
        db.add(organization)
        db.flush()

        db.add(OrganizationMember(organization_id=organization.id, user_id=user.id, role=OrgRole.OWNER))
        db.commit()
        db.refresh(user)

    return TokenPair(
        access_token=create_access_token(str(user.id), expires_minutes=60 * 24),  # 24h — modo local, uso pessoal
        refresh_token=create_refresh_token(str(user.id)),
    )


@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
@limiter.limit("5/minute")  # checklist de auditoria — protege contra criação em massa de contas
def register(request: Request, payload: UserRegister, db: Session = Depends(get_db)) -> User:
    existing = db.query(User).filter_by(email=payload.email).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Este e-mail já está cadastrado.")

    user = User(
        email=payload.email,
        hashed_password=hash_password(payload.password),
        full_name=payload.full_name,
    )
    db.add(user)
    db.flush()  # garante user.id sem fechar a transação

    organization = Organization(name=payload.organization_name)
    db.add(organization)
    db.flush()

    membership = OrganizationMember(
        organization_id=organization.id,
        user_id=user.id,
        role=OrgRole.OWNER,  # quem cria a organização é o dono, Seção 7 do SECURITY_MODEL.md
    )
    db.add(membership)
    db.commit()
    db.refresh(user)

    return user


@router.post("/login", response_model=TokenPair)
@limiter.limit("10/minute")  # checklist de auditoria — protege contra brute-force/credential stuffing
def login(request: Request, form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)) -> TokenPair:
    user = db.query(User).filter_by(email=form_data.username).first()

    # Mensagem genérica de propósito para os dois casos (usuário não existe OU
    # senha errada) — evita enumeração de e-mails cadastrados (Seção 3 do
    # checklist de auditoria).
    if user is None or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="E-mail ou senha inválidos.")
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Usuário desativado.")

    return TokenPair(
        access_token=create_access_token(str(user.id)),
        refresh_token=create_refresh_token(str(user.id)),
    )

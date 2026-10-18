from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from sqlalchemy import text

from app.api.v1.router import router as api_v1_router
from app.core.config import settings
from app.core.limiter import limiter
from app.db.base import Base
from app.db.session import engine
from app import models  # noqa: F401 — garante que todos os modelos sejam registrados antes do create_all
from app.models.enums import (
    Confidence, Environment, FindingStatus, OrgRole, ScanStatus, ScanType,
    Severity, VerificationMethod, VerificationStatus,
)

# Nome do tipo ENUM no Postgres -> valores esperados do Enum Python correspondente.
# O SQLAlchemy nomeia o tipo com a classe em minúsculas por padrão (ex: ScanType -> scantype).
PG_ENUM_TYPES: dict[str, list[str]] = {
    "scantype": [e.value for e in ScanType],
    "scanstatus": [e.value for e in ScanStatus],
    "severity": [e.value for e in Severity],
    "confidence": [e.value for e in Confidence],
    "findingstatus": [e.value for e in FindingStatus],
    "verificationstatus": [e.value for e in VerificationStatus],
    "verificationmethod": [e.value for e in VerificationMethod],
    "environment": [e.value for e in Environment],
    "orgrole": [e.value for e in OrgRole],
}


def sync_enum_types() -> None:
    """
    Adiciona ao Postgres qualquer valor de enum que exista no código Python
    mas ainda não exista no banco (ex: quando um ScanType novo é criado).
    `create_all` não faz isso sozinho — ele só cria o que ainda não existe,
    nunca altera um tipo já criado. Isso evita ter que apagar o banco toda
    vez que um tipo novo é adicionado ao roadmap.

    No modo desktop (SQLite), isso não existe — colunas enum lá são só
    VARCHAR comuns, aceitam qualquer valor novo automaticamente.
    """
    if engine.dialect.name != "postgresql":
        return

    with engine.connect() as conn:
        for type_name, values in PG_ENUM_TYPES.items():
            for value in values:
                try:
                    conn.execute(text(f"ALTER TYPE {type_name} ADD VALUE IF NOT EXISTS '{value}'"))
                    conn.commit()
                except Exception:
                    conn.rollback()  # tipo ainda não existe na 1ª execução — create_all cuida disso


NEW_COLUMNS: list[tuple[str, str, str]] = [
    # (tabela, coluna, definição do tipo)
    ("organizations", "webhook_url", "VARCHAR(500)"),
    ("organizations", "webhook_secret", "VARCHAR(100)"),
    ("organizations", "slack_webhook_url", "VARCHAR(500)"),
    ("scans", "webhook_status", "VARCHAR(20)"),
    ("scans", "webhook_error", "VARCHAR(500)"),
]


def sync_new_columns() -> None:
    """
    Mesma ideia do sync_enum_types, mas para colunas novas em tabelas que já
    existiam. `create_all` não altera tabelas já criadas — só cria as que
    ainda não existem.

    Postgres suporta 'ADD COLUMN IF NOT EXISTS' nativamente. SQLite não tem
    esse 'IF NOT EXISTS' para ADD COLUMN — aqui a gente tenta e ignora só o
    erro específico de "coluna já existe", sem engolir outros erros calados.
    """
    is_sqlite = engine.dialect.name == "sqlite"

    with engine.connect() as conn:
        for table, column, coltype in NEW_COLUMNS:
            stmt = (
                f"ALTER TABLE {table} ADD COLUMN {column} {coltype}"
                if is_sqlite
                else f"ALTER TABLE {table} ADD COLUMN IF NOT EXISTS {column} {coltype}"
            )
            try:
                conn.execute(text(stmt))
                conn.commit()
            except Exception as e:
                conn.rollback()
                if is_sqlite and "duplicate column name" not in str(e).lower():
                    print(f"[sync_new_columns] aviso ao adicionar {table}.{column}: {e}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Cria as tabelas automaticamente se ainda não existirem (simplificação
    # deliberada para o modo local — ver docs/ROADMAP.md Fase 43).
    Base.metadata.create_all(bind=engine)
    sync_enum_types()
    sync_new_columns()
    yield


app = FastAPI(
    title="SecureScan API",
    version="1.0.0",
    description="Plataforma de análise de segurança de aplicações web, APIs e infraestrutura.",
    lifespan=lifespan,
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_v1_router)


@app.get("/health")
def health_check() -> dict:
    return {"status": "ok", "environment": settings.environment}

"""
Execução de um scan — lógica compartilhada entre os dois modos do SecureScan:

- Modo servidor (Docker): o worker RQ (workers/tasks/scan_tasks.py) importa
  e chama run_scan() a partir da fila do Redis.
- Modo desktop: app/services/local_queue.py chama run_scan() direto numa
  thread do mesmo processo, sem Redis.

O job recebe só o scan_id — tudo o mais é buscado do banco aqui.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.models.domain import Domain
from app.models.enums import ScanStatus
from app.models.finding import Finding
from app.models.project import Project
from app.models.scan import Scan
from app.models.user import Organization
from app.services.scoring import calculate_security_score
from app.services.webhook import build_scan_payload, send_scan_webhook, send_slack_notification

from scanner_engine import ScanContext, Severity as PluginSeverity, import_all_plugins, plugins_for_scan_type

import_all_plugins()

FRIENDLY_LABELS = {
    "headers_check": "Verificando headers de segurança",
    "ssl_check": "Verificando certificado SSL/TLS",
    "tech_fingerprint": "Identificando tecnologias utilizadas",
    "port_scan": "Escaneando portas abertas",
    "exposed_files": "Verificando arquivos sensíveis expostos",
    "secrets_scan": "Buscando chaves e segredos vazados",
    "database_exposure": "Verificando exposição de banco de dados",
    "pii_exposure": "Verificando exposição de dados pessoais (LGPD)",
    "dependency_check": "Verificando dependências vulneráveis",
    "idor_check": "Testando controle de acesso (IDOR)",
    "zap_active_scan": "Conectando ao OWASP ZAP",
    "semgrep_scan": "Clonando repositório e analisando o código",
    "api_security_scan": "Verificando especificação da API",
    "docker_security_scan": "Analisando Dockerfile",
    "storage_bucket_scan": "Verificando bucket de armazenamento",
    "supabase_scan": "Verificando permissões do Supabase",
    "payment_security_scan": "Verificando segurança do checkout",
    "cors_check": "Verificando configuração de CORS",
    "session_cookie_check": "Verificando segurança dos cookies de sessão",
    "rate_limit_scan": "Testando proteção contra brute-force",
}


def _update_progress(db: Session, scan: Scan, percent: int, step: str) -> None:
    scan.progress_percent = percent
    scan.current_step = step
    db.commit()


def run_scan(scan_id: str) -> None:
    db = SessionLocal()
    try:
        scan = db.get(Scan, uuid.UUID(scan_id))
        if scan is None:
            return

        domain = db.get(Domain, scan.domain_id)
        project = db.get(Project, scan.project_id)

        scan.status = ScanStatus.RUNNING
        scan.started_at = datetime.now(timezone.utc)
        db.commit()

        plugin_classes = plugins_for_scan_type(scan.scan_type.value)
        total = len(plugin_classes) or 1

        target_url = domain.hostname
        if not target_url.startswith(("http://", "https://")):
            target_url = f"https://{target_url}"

        context = ScanContext(
            target_url=target_url,
            scope_hosts=[domain.hostname],
            requires_active_scan_allowed=domain.allows_active_scan,
            extra_config=scan.extra_config or {},
        )

        for i, plugin_cls in enumerate(plugin_classes):
            plugin = plugin_cls()
            label = FRIENDLY_LABELS.get(plugin.name, f"Executando {plugin.name}")
            base_progress = int(i / total * 100)
            next_progress = int((i + 1) / total * 100)
            _update_progress(db, scan, base_progress, label)

            def make_callback(base: int, span: int):
                def _cb(pct: int, sub_label: str) -> None:
                    # traduz o progresso interno do plugin (0-100) para a fatia
                    # que esse plugin ocupa na barra geral do scan
                    overall = base + int((pct / 100) * span)
                    _update_progress(db, scan, min(overall, next_progress), sub_label)
                return _cb

            context.progress_callback = make_callback(base_progress, next_progress - base_progress)

            try:
                findings = plugin.run(context)
            except Exception as e:
                findings = []
                db.add(Finding(
                    scan_id=scan.id,
                    plugin_name=plugin.name,
                    title=f"Falha ao executar {plugin.name}",
                    description=str(e)[:500],
                    category="engine_error",
                    severity="info",
                ))

            for f in findings:
                db.add(Finding(
                    scan_id=scan.id,
                    plugin_name=f.plugin_name or plugin.name,
                    title=f.title,
                    description=f.description,
                    category=f.category,
                    severity=f.severity.value if isinstance(f.severity, PluginSeverity) else f.severity,
                    confidence=f.confidence.value if hasattr(f.confidence, "value") else f.confidence,
                    cwe=f.cwe,
                    owasp=f.owasp,
                    endpoint_or_file=f.endpoint_or_file,
                    evidence_sanitized=f.evidence_sanitized,
                    impact=f.impact,
                    remediation=f.remediation,
                    references=f.references,
                ))
            db.commit()

        _update_progress(db, scan, 100, "Gerando relatório")

        # Linhagem dos achados: propaga first_seen_scan_id comparando com o
        # scan COMPLETED anterior do mesmo domínio (Seção 45 — Scan Diff).
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

        if previous_scan is not None:
            previous_findings = db.query(Finding).filter_by(scan_id=previous_scan.id).all()
            previous_lineage = {
                f"{f.plugin_name}::{f.title}": (f.first_seen_scan_id or previous_scan.id)
                for f in previous_findings
            }
        else:
            previous_lineage = {}

        current_findings = db.query(Finding).filter_by(scan_id=scan.id).all()
        for f in current_findings:
            key = f"{f.plugin_name}::{f.title}"
            f.first_seen_scan_id = previous_lineage.get(key, scan.id)
        db.commit()

        # recalcula o security score do projeto com base em todos os findings deste scan
        severity_counts: dict[str, int] = {}
        for (sev,) in db.query(Finding.severity).filter_by(scan_id=scan.id).all():
            key = sev.value if hasattr(sev, "value") else sev
            severity_counts[key] = severity_counts.get(key, 0) + 1

        if project is not None:
            from app.models.enums import Severity as DbSeverity
            counts_enum = {DbSeverity(k): v for k, v in severity_counts.items()}
            project.security_score = calculate_security_score(counts_enum)
            project.last_scan_at = datetime.now(timezone.utc)

        # dispara o webhook ANTES de marcar como concluído, pra "Enviando
        # relatório via webhook..." aparecer como etapa visível no polling
        # do frontend (nunca falha o scan por causa disso — só registra)
        webhook_status = None
        webhook_error = None

        if project is not None:
            organization = db.get(Organization, project.organization_id)
            if organization is not None and organization.webhook_url:
                _update_progress(db, scan, 99, "Enviando relatório via webhook...")

                findings_payload = [
                    {
                        "title": f.title,
                        "description": f.description,
                        "category": f.category,
                        "severity": f.severity.value if hasattr(f.severity, "value") else f.severity,
                        "remediation": f.remediation,
                        "endpoint_or_file": f.endpoint_or_file,
                        "plugin_name": f.plugin_name,
                    }
                    for f in db.query(Finding).filter_by(scan_id=scan.id).all()
                ]
                payload = build_scan_payload(
                    scan_id=str(scan.id),
                    project_name=project.name,
                    domain_hostname=domain.hostname if domain else "desconhecido",
                    scan_type=scan.scan_type.value,
                    status="COMPLETED",
                    severity_summary=severity_counts,
                    findings=findings_payload,
                )
                success, message = send_scan_webhook(organization.webhook_url, organization.webhook_secret, payload)
                webhook_status = "sent" if success else "failed"
                webhook_error = None if success else message
            else:
                print("[webhook] nenhuma URL configurada em Configurações — pulando.")

            if organization is not None and organization.slack_webhook_url:
                sent = send_slack_notification(
                    organization.slack_webhook_url, project.name,
                    domain.hostname if domain else "desconhecido", severity_counts,
                )
                print(f"[slack] {'enviado' if sent else 'falhou ao enviar'}")

        scan.status = ScanStatus.COMPLETED
        scan.finished_at = datetime.now(timezone.utc)
        scan.webhook_status = webhook_status
        scan.webhook_error = webhook_error
        db.commit()

    except Exception:
        db.rollback()
        scan = db.get(Scan, uuid.UUID(scan_id))
        if scan is not None:
            scan.status = ScanStatus.FAILED
            scan.finished_at = datetime.now(timezone.utc)
            db.commit()
        raise
    finally:
        db.close()

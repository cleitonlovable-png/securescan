from __future__ import annotations

import uuid

from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.domain import Domain
from app.models.enums import ScanStatus, ScanType, VerificationStatus
from app.models.scan import Scan

ACTIVE_SCAN_TYPES = {ScanType.FULL_SCAN, ScanType.API_SCAN, ScanType.CHECKOUT_SCAN, ScanType.PENTEST_SCAN}

class ScanNotAllowedError(Exception):
    """Levantado quando um scan ativo é pedido para um domínio não verificado."""


def _enqueue(scan_id: str) -> str:
    """Manda o scan para a fila configurada — Redis (servidor) ou local (desktop)."""
    if settings.queue_backend == "local":
        from app.services.local_queue import enqueue_local
        return enqueue_local(scan_id)

    import redis
    from rq import Queue

    conn = redis.from_url(settings.redis_url)
    queue = Queue("scans", connection=conn)
    job = queue.enqueue("tasks.scan_tasks.run_scan", scan_id, job_timeout="30m")
    return job.id


def _cancel(job_id: str) -> None:
    if settings.queue_backend == "local":
        from app.services.local_queue import cancel_local
        cancel_local(job_id)
        return

    import redis
    from rq import Queue

    conn = redis.from_url(settings.redis_url)
    queue = Queue("scans", connection=conn)
    job = queue.fetch_job(job_id)
    if job is not None:
        job.cancel()


def create_and_enqueue_scan(
    db: Session,
    domain: Domain,
    scan_type: ScanType,
    requested_by_user_id: uuid.UUID,
    extra_config: dict,
) -> Scan:
    """
    Ver docs/SECURITY_MODEL.md Seção 3 — nenhum scan ativo roda fora de
    VERIFIED/PRIVATE_ENVIRONMENT. QUICK_SCAN e INFRA_SCAN (somente leitura)
    são permitidos mesmo sem verificação, mas ainda respeitam rate limit
    e ficam registrados em log.
    """
    if scan_type in ACTIVE_SCAN_TYPES and not domain.allows_active_scan:
        raise ScanNotAllowedError(
            f"O domínio '{domain.hostname}' precisa estar verificado (ou marcado como "
            "ambiente privado) antes de rodar um {scan_type.value}."
        )

    scan = Scan(
        project_id=domain.project_id,
        domain_id=domain.id,
        requested_by_user_id=requested_by_user_id,
        scan_type=scan_type,
        status=ScanStatus.PENDING,
        extra_config=extra_config,
    )
    db.add(scan)
    db.commit()
    db.refresh(scan)

    # o worker (workers/tasks/scan_tasks.py::run_scan) recebe só o scan_id
    # e busca o resto no banco — mantém o job enfileirado pequeno e serializável
    job_id = _enqueue(str(scan.id))
    scan.rq_job_id = job_id
    db.commit()
    db.refresh(scan)

    return scan


def cancel_scan(scan: Scan) -> None:
    """Kill switch — Seção 42 do prompt original."""
    if scan.rq_job_id:
        _cancel(scan.rq_job_id)
    scan.status = ScanStatus.CANCELLED

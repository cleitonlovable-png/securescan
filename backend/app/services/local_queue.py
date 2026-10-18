"""
Fila local (modo desktop): roda scans numa thread em background, dentro do
mesmo processo do backend — sem precisar de Redis nem de um worker separado.

Não tem persistência entre reinicializações do app (se você fechar o
SecureScan Desktop no meio de um scan, ele não retoma sozinho ao reabrir —
o registro do Scan no banco fica com status RUNNING "preso"; isso é uma
limitação aceitável para uso pessoal, documentada aqui de propósito).
"""

from __future__ import annotations

import uuid
from concurrent.futures import ThreadPoolExecutor, Future

# um scan por vez é suficiente para uso pessoal — evita várias varreduras
# pesadas competindo por CPU/rede na mesma máquina do usuário
_executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="securescan-local-worker")
_futures: dict[str, Future] = {}


def enqueue_local(scan_id: str) -> str:
    """Roda scan_runner.run_scan(scan_id) em background. Retorna um id de
    job local, só para manter compatibilidade com o campo Scan.rq_job_id."""
    from app.services.scan_runner import run_scan  # import tardio evita ciclo

    job_id = str(uuid.uuid4())
    future = _executor.submit(run_scan, scan_id)
    _futures[job_id] = future
    return job_id


def cancel_local(job_id: str) -> bool:
    """
    Só consegue cancelar de verdade se o job ainda não começou a rodar
    (mesma limitação que o RQ tem por padrão no modo servidor). Se já
    estiver rodando, o status CANCELLED setado no banco pela rota ainda
    assim é respeitado — o scan_runner só não é interrompido no meio.
    """
    future = _futures.get(job_id)
    if future is None:
        return False
    return future.cancel()

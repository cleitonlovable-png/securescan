"""
Entrypoint do worker. Consome a fila 'scans' do Redis e executa
tasks.scan_tasks.run_scan para cada job.

Rodar com: python worker.py
(No Docker, isso é o CMD do workers/Dockerfile.)
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))

import redis
from rq import Queue, Worker

from app.core.config import settings

if __name__ == "__main__":
    conn = redis.from_url(settings.redis_url)
    queue = Queue("scans", connection=conn)
    worker = Worker([queue], connection=conn)
    worker.work()

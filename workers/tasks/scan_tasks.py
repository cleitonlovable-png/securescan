"""
Ponte para o RQ. A lógica real vive em backend/app/services/scan_runner.py
(compartilhada com o modo desktop). O nome 'tasks.scan_tasks.run_scan' é o
que o backend enfileira (ver scan_service.py), então precisa continuar
existindo aqui.
"""

from __future__ import annotations

import sys
from pathlib import Path

# permite `import app.*` reaproveitando o backend sem duplicar código
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "backend"))

from app.services.scan_runner import run_scan  # noqa: E402,F401

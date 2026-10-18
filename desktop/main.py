"""
SecureScan Desktop — entrypoint único do app.

O que este arquivo faz, na ordem:
1. Decide onde fica o banco SQLite (uma pasta no perfil do usuário).
2. Configura o backend (via variáveis de ambiente) para modo desktop:
   SQLite em vez de Postgres, fila local em vez de Redis.
3. Importa o app FastAPI (backend/app/main.py — o MESMO código do modo
   servidor, sem duplicação) e monta o frontend estático (Next.js
   exportado) na raiz "/".
4. Sobe esse app num servidor uvicorn, numa thread em segundo plano.
5. Abre uma janela nativa (PyWebView) apontando para esse servidor local.

Build: ver desktop/build.bat e desktop/README.md.
"""

from __future__ import annotations

import os
import secrets
import sys
import threading
import time
from pathlib import Path

def _resolve_base_dirs() -> tuple[Path, Path, Path]:
    """
    Retorna (backend_dir, scanner_engine_parent_dir, frontend_static_dir).

    `sys.frozen` só existe quando o PyInstaller empacotou o app — nesse
    caso os caminhos são relativos à pasta onde o .exe ficou (ver os nomes
    de destino usados em build.bat, têm que bater exatamente com isto).
    Rodando direto com `python main.py` (sem empacotar), usa a estrutura
    normal do monorepo.
    """
    if getattr(sys, "frozen", False):
        base = Path(getattr(sys, "_MEIPASS", Path(sys.executable).parent))
        return base / "backend", base, base / "desktop" / "frontend_static"

    desktop_dir = Path(__file__).resolve().parent
    project_root = desktop_dir.parent
    return project_root / "backend", project_root / "scanner-engine", desktop_dir / "frontend_static"


BACKEND_DIR, SCANNER_ENGINE_DIR, FRONTEND_STATIC_DIR = _resolve_base_dirs()

API_PORT = 8756  # porta fixa só pra uso interno (loopback), sem exposição externa


def _app_data_dir() -> Path:
    """Pasta onde o SecureScan Desktop guarda o banco e a chave de sessão."""
    if sys.platform == "win32":
        base = Path(os.environ.get("APPDATA", Path.home() / "AppData" / "Roaming"))
    elif sys.platform == "darwin":
        base = Path.home() / "Library" / "Application Support"
    else:
        base = Path.home() / ".config"

    app_dir = base / "SecureScanDesktop"
    app_dir.mkdir(parents=True, exist_ok=True)
    return app_dir


def _get_or_create_jwt_secret(app_dir: Path) -> str:
    """Gera uma chave na primeira execução e reaproveita depois — assim a
    sessão não cai a cada vez que o app abre."""
    secret_file = app_dir / "jwt_secret.txt"
    if secret_file.exists():
        return secret_file.read_text(encoding="utf-8").strip()

    secret = secrets.token_urlsafe(48)
    secret_file.write_text(secret, encoding="utf-8")
    return secret


def _configure_environment() -> Path:
    app_dir = _app_data_dir()
    db_path = app_dir / "securescan.db"

    os.environ["DATABASE_URL"] = f"sqlite:///{db_path}"
    os.environ["QUEUE_BACKEND"] = "local"
    os.environ["ENVIRONMENT"] = "desktop"  # != "production", então /auth/dev-bootstrap continua liberado
    os.environ["JWT_SECRET"] = _get_or_create_jwt_secret(app_dir)
    os.environ["CORS_ORIGINS"] = '["http://127.0.0.1", "http://localhost", "http://127.0.0.1:8756", "https://securescan.pages.dev"]'

    os.environ.setdefault("ACCESS_TOKEN_EXPIRE_MINUTES", str(60 * 24 * 7))  # sessão de 7 dias, uso pessoal

    return app_dir


def _build_app():
    """Importa o FastAPI já existente e monta o frontend estático nele."""
    sys.path.insert(0, str(BACKEND_DIR))
    sys.path.insert(0, str(SCANNER_ENGINE_DIR))

    from app.main import app  # mesmo app do modo servidor — nenhuma rota duplicada
    from fastapi.staticfiles import StaticFiles

    if FRONTEND_STATIC_DIR.exists():
        app.mount("/", StaticFiles(directory=str(FRONTEND_STATIC_DIR), html=True), name="frontend")
    else:
        print(f"[AVISO] Frontend estático não encontrado em {FRONTEND_STATIC_DIR}. "
              f"Rode build.bat primeiro (ele gera essa pasta via 'next export').")

    return app


def _run_server(app) -> None:
    import uvicorn
    uvicorn.run(
        app,
        host="127.0.0.1",
        port=API_PORT,
        log_level="warning",
        log_config=None,
    )


def main() -> None:
    app_dir = _configure_environment()

    # No modo --windowed do PyInstaller, sys.stdout e sys.stderr são None,
    # o que faz qualquer print() ou logger do uvicorn/FastAPI quebrar.
    if sys.stdout is None or sys.stderr is None:
        log_file = open(app_dir / "securescan_desktop.log", "a", encoding="utf-8", buffering=1)
        if sys.stdout is None:
            sys.stdout = log_file
        if sys.stderr is None:
            sys.stderr = log_file

    app = _build_app()

    server_thread = threading.Thread(target=_run_server, args=(app,), daemon=True)
    server_thread.start()

    # dá um tempinho pro uvicorn subir antes de abrir a janela
    time.sleep(1.5)

    import webview
    webview.create_window(
        "CSC Scan",
        f"http://127.0.0.1:{API_PORT}/",
        width=1280,
        height=800,
        min_size=(960, 600),
    )
    webview.start()



if __name__ == "__main__":
    main()


from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

import requests
from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/system", tags=["system"])

GITHUB_REPO = "cleitonlovable-png/securescan"
CLOUDFLARE_VERSION_URL = "https://securescan.pages.dev/version.json"


def _local_version_file() -> Path:
    if getattr(sys, "frozen", False):
        base = Path(getattr(sys, "_MEIPASS", Path(sys.executable).parent))
        candidate = base / "VERSION.json"
        if candidate.exists():
            return candidate
    # Fallback para raiz do monorepo
    return Path(__file__).resolve().parents[4] / "VERSION.json"


def get_local_version_info() -> dict:
    vf = _local_version_file()
    if vf.exists():
        try:
            return json.loads(vf.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {"version": "1.0.0", "release_date": "", "notes": ""}


def _parse_version(v: str) -> tuple[int, ...]:
    clean = v.strip().lstrip("vV")
    parts = []
    for p in clean.split("."):
        try:
            parts.append(int(p))
        except ValueError:
            parts.append(0)
    return tuple(parts)


@router.get("/version")
def get_version() -> dict:
    info = get_local_version_info()
    return {
        "version": info.get("version", "1.0.0"),
        "release_date": info.get("release_date", ""),
        "notes": info.get("notes", ""),
    }


@router.get("/update-check")
def check_for_updates() -> dict:
    local_info = get_local_version_info()
    current_version = local_info.get("version", "1.0.0")

    remote_version = current_version
    notes = ""
    download_url = f"https://github.com/{GITHUB_REPO}/releases/latest/download/SecureScan_Setup.exe"

    # 1. Tenta consultar GitHub Releases API
    try:
        resp = requests.get(
            f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest",
            headers={"Accept": "application/vnd.github+json"},
            timeout=6,
        )
        if resp.status_code == 200:
            data = resp.json()
            tag = data.get("tag_name", "")
            if tag:
                remote_version = tag.lstrip("vV")
            notes = data.get("body", "") or ""
            for asset in data.get("assets", []):
                if asset.get("name", "").endswith(".exe"):
                    download_url = asset.get("browser_download_url", download_url)
                    break
    except Exception:
        pass

    # 2. Tenta consultar Cloudflare Pages version.json como fallback/complemento
    try:
        cf_resp = requests.get(CLOUDFLARE_VERSION_URL, timeout=5)
        if cf_resp.status_code == 200:
            cf_data = cf_resp.json()
            cf_ver = cf_data.get("version", "")
            if cf_ver and _parse_version(cf_ver) > _parse_version(remote_version):
                remote_version = cf_ver
                notes = cf_data.get("notes", notes)
                if cf_data.get("download_url"):
                    download_url = cf_data["download_url"]
    except Exception:
        pass

    update_available = _parse_version(remote_version) > _parse_version(current_version)

    return {
        "current_version": current_version,
        "latest_version": remote_version,
        "update_available": update_available,
        "notes": notes,
        "download_url": download_url,
    }


@router.post("/update-apply")
def apply_update() -> dict:
    check = check_for_updates()
    download_url = check.get("download_url")
    if not download_url:
        raise HTTPException(status_code=400, detail="URL do instalador de atualização não encontrada.")

    try:
        resp = requests.get(download_url, stream=True, timeout=120)
        if resp.status_code != 200:
            raise HTTPException(
                status_code=502,
                detail=f"Não foi possível baixar o instalador (status {resp.status_code}).",
            )

        temp_dir = Path(tempfile.gettempdir())
        installer_path = temp_dir / "SecureScan_Update_Setup.exe"
        with open(installer_path, "wb") as f:
            for chunk in resp.iter_content(chunk_size=65536):
                if chunk:
                    f.write(chunk)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao baixar atualização: {e}")

    # Dispara um script em segundo plano que espera 1.5s, fecha o app atual,
    # roda o instalador silenciosamente (/SILENT) e reabre o SecureScan atualizado.
    if sys.platform == "win32":
        bat_path = temp_dir / "apply_securescan_update.bat"
        exe_dir = Path(sys.executable).parent if getattr(sys, "frozen", False) else None
        relaunch_cmd = (
            f'start "" "{exe_dir / "SecureScan.exe"}"'
            if exe_dir and (exe_dir / "SecureScan.exe").exists()
            else ""
        )
        bat_content = f"""@echo off
timeout /t 2 /nobreak >nul
taskkill /F /IM SecureScan.exe >nul 2>&1
"{installer_path}" /VERYSILENT /SUPPRESSMSGBOXES /NORESTART /CLOSEAPPLICATIONS
timeout /t 2 /nobreak >nul
{relaunch_cmd}
"""
        bat_path.write_text(bat_content, encoding="utf-8")
        subprocess.Popen(
            ["cmd.exe", "/c", str(bat_path)],
            creationflags=subprocess.CREATE_NO_WINDOW if hasattr(subprocess, "CREATE_NO_WINDOW") else 0,
        )

    return {"status": "updating", "message": "Instalador baixado! O aplicativo será atualizado e reiniciado em instantes."}

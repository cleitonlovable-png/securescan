"""
Análise estática de código (SAST) via Semgrep.

Clona um repositório Git em um diretório temporário e roda o Semgrep com o
conjunto de regras "auto" (detecta a linguagem e aplica regras públicas
relevantes: SQLi, XSS, comandos perigosos, criptografia insegura, etc).

Requer os binários `git` e `semgrep` disponíveis no worker.
"""

from __future__ import annotations

import json
import shutil
import subprocess
import tempfile
from pathlib import Path


def is_available() -> bool:
    return shutil.which("git") is not None and shutil.which("semgrep") is not None


def _clone_repo(repo_url: str, branch: str | None, dest: Path, timeout: int = 120) -> None:
    cmd = ["git", "clone", "--depth", "1"]
    if branch:
        cmd += ["--branch", branch]
    cmd += [repo_url, str(dest)]

    result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    if result.returncode != 0:
        raise RuntimeError(f"Falha ao clonar repositório: {result.stderr[:500]}")


def run_semgrep_scan(repo_url: str, branch: str | None = None, timeout: int = 600) -> dict:
    if not is_available():
        raise RuntimeError("git e/ou semgrep não estão instalados no worker.")

    with tempfile.TemporaryDirectory() as tmp_dir:
        repo_path = Path(tmp_dir) / "repo"
        _clone_repo(repo_url, branch, repo_path, timeout=min(timeout, 120))

        cmd = ["semgrep", "--config=auto", "--json", "--timeout", "300", str(repo_path)]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)

        try:
            data = json.loads(result.stdout)
        except json.JSONDecodeError:
            raise RuntimeError(f"Semgrep não retornou JSON válido: {result.stderr[:500]}")

        findings = []
        for item in data.get("results", []):
            severity_raw = item.get("extra", {}).get("severity", "INFO").upper()
            severity_map = {"ERROR": "high", "WARNING": "medium", "INFO": "low"}

            file_path = item.get("path", "").replace(str(repo_path) + "/", "")
            line = item.get("start", {}).get("line", "?")

            findings.append({
                "severity": severity_map.get(severity_raw, "low"),
                "issue": item.get("extra", {}).get("message", item.get("check_id", "Achado do Semgrep"))[:200],
                "description": f"Regra: {item.get('check_id', 'desconhecida')}",
                "recommendation": item.get("extra", {}).get("metadata", {}).get("references", [""])[0] or
                                   "Revisar o trecho de código indicado e aplicar a correção sugerida pela regra.",
                "file": f"{file_path}:{line}",
                "cwe": ",".join(item.get("extra", {}).get("metadata", {}).get("cwe", [])) or None,
                "owasp": ",".join(item.get("extra", {}).get("metadata", {}).get("owasp", [])) or None,
            })

        return {"findings": findings, "total_files_scanned": len(data.get("paths", {}).get("scanned", []))}

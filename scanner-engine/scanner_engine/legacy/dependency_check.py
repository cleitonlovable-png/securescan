"""
Módulo de verificação: dependências vulneráveis.

Lê um requirements.txt local (do seu projeto, no seu disco) e cruza cada
pacote/versão com a OSV.dev (Open Source Vulnerabilities), uma base pública
e gratuita mantida pela Google, sem necessidade de API key.

Diferente dos outros módulos, este NÃO acessa o alvo pela rede — ele lê um
arquivo local do seu computador. Por isso não precisa de validação de escopo
(não há risco de atingir um alvo não autorizado).
"""

from __future__ import annotations

import re
from pathlib import Path

import requests

OSV_API_URL = "https://api.osv.dev/v1/querybatch"


def parse_requirements(path: str | Path) -> list[dict]:
    """Extrai nome e versão de cada linha de um requirements.txt."""
    packages = []
    path = Path(path)

    if not path.exists():
        raise FileNotFoundError(f"Arquivo não encontrado: {path}")

    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or line.startswith("-"):
            continue

        # cobre formatos: pacote==1.2.3 / pacote>=1.2.3 / pacote~=1.2
        match = re.match(r"^([A-Za-z0-9_.\-]+)\s*(==|>=|~=|>)\s*([0-9][A-Za-z0-9_.\-]*)", line)
        if match:
            name, _, version = match.groups()
            packages.append({"name": name, "version": version})
        else:
            # sem versão fixada — ainda vale registrar o nome, mas sem poder checar CVE por versão
            name_only = re.match(r"^([A-Za-z0-9_.\-]+)", line)
            if name_only:
                packages.append({"name": name_only.group(1), "version": None})

    return packages


def query_osv(packages: list[dict], timeout: int = 20) -> dict:
    """Consulta a OSV.dev em lote para todos os pacotes com versão definida."""
    queries = [
        {"package": {"name": p["name"], "ecosystem": "PyPI"}, "version": p["version"]}
        for p in packages if p["version"]
    ]

    if not queries:
        return {"results": []}

    try:
        resp = requests.post(OSV_API_URL, json={"queries": queries}, timeout=timeout)
        resp.raise_for_status()
        return resp.json()
    except requests.RequestException as e:
        return {"error": str(e), "results": []}


def check_dependencies(requirements_path: str | Path) -> dict:
    packages = parse_requirements(requirements_path)
    packages_with_version = [p for p in packages if p["version"]]
    packages_without_version = [p for p in packages if not p["version"]]

    osv_response = query_osv(packages_with_version)

    findings = []
    severity_summary = {"critical": 0, "high": 0, "medium": 0, "low": 0}

    results = osv_response.get("results", [])
    for pkg, result in zip(packages_with_version, results):
        vulns = result.get("vulns", []) if result else []
        for vuln in vulns:
            vuln_id = vuln.get("id", "desconhecido")
            summary = vuln.get("summary", "Sem descrição disponível.")

            # OSV nem sempre traz severidade padronizada; usamos 'high' como
            # padrão conservador quando não informado, já que é uma CVE confirmada
            severity = "high"
            for sev_entry in vuln.get("severity", []):
                score_str = sev_entry.get("score", "")
                if score_str.startswith("CVSS"):
                    # heurística simples baseada no texto do vetor, quando presente
                    if "CRITICAL" in score_str.upper():
                        severity = "critical"

            findings.append({
                "severity": severity,
                "issue": f"{pkg['name']} {pkg['version']} tem vulnerabilidade conhecida: {vuln_id}",
                "description": summary[:300],
                "recommendation": f"Atualizar {pkg['name']} para uma versão mais recente sem essa vulnerabilidade.",
            })
            severity_summary[severity] += 1

    for pkg in packages_without_version:
        findings.append({
            "severity": "low",
            "issue": f"{pkg['name']} está sem versão fixada no requirements.txt.",
            "recommendation": "Fixar a versão (ex: pacote==1.2.3) para permitir checagem de vulnerabilidades "
                               "e builds reproduzíveis.",
        })
        severity_summary["low"] += 1

    return {
        "module": "dependency_check",
        "requirements_path": str(requirements_path),
        "total_packages": len(packages),
        "findings": findings,
        "severity_summary": severity_summary,
    }




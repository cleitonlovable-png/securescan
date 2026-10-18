#!/usr/bin/env python3
"""
SecureScan CLI — para rodar em pipelines de CI/CD (Seção 32 do documento original).

Uso:
    python securescan_cli.py \\
        --api-url http://localhost:8000 \\
        --email admin@empresa.com --password ****** \\
        --org-id <uuid> \\
        --url https://staging.seusite.com \\
        --scan-type FULL_SCAN \\
        --fail-on high

Exit code:
    0 — scan concluído, nenhum achado no nível de --fail-on ou acima
    1 — scan concluído, mas achou algo no nível de --fail-on ou acima (falha o build)
    2 — erro ao rodar o scan (rede, autenticação, etc)

Exemplo de uso num pipeline (GitHub Actions):

    - name: Security scan
      run: |
        python cli/securescan_cli.py \\
          --api-url ${{ secrets.SECURESCAN_URL }} \\
          --email ${{ secrets.SECURESCAN_EMAIL }} \\
          --password ${{ secrets.SECURESCAN_PASSWORD }} \\
          --org-id ${{ secrets.SECURESCAN_ORG_ID }} \\
          --url https://staging.meuapp.com \\
          --fail-on critical
"""

from __future__ import annotations

import argparse
import sys
import time

import requests

SEVERITY_RANK = {"critical": 0, "high": 1, "medium": 2, "low": 3, "info": 4}


def login(api_url: str, email: str, password: str) -> str:
    resp = requests.post(
        f"{api_url}/api/v1/auth/login",
        data={"username": email, "password": password},
        timeout=15,
    )
    resp.raise_for_status()
    return resp.json()["access_token"]


def start_scan(api_url: str, token: str, org_id: str, target_url: str, scan_type: str) -> dict:
    resp = requests.post(
        f"{api_url}/api/v1/organizations/{org_id}/quick-scan",
        headers={"Authorization": f"Bearer {token}"},
        json={"url": target_url, "scan_type": scan_type, "authorize": True},
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json()


def poll_scan(api_url: str, token: str, org_id: str, project_id: str, scan_id: str,
              timeout_seconds: int = 1800) -> dict:
    deadline = time.time() + timeout_seconds
    url = f"{api_url}/api/v1/organizations/{org_id}/projects/{project_id}/scans/{scan_id}"

    while time.time() < deadline:
        resp = requests.get(url, headers={"Authorization": f"Bearer {token}"}, timeout=15)
        resp.raise_for_status()
        data = resp.json()

        print(f"  [{data['progress_percent']}%] {data.get('current_step') or '...'}")

        if data["status"] in ("COMPLETED", "FAILED", "CANCELLED"):
            return data

        time.sleep(3)

    raise TimeoutError("Scan não terminou dentro do tempo limite.")


def get_findings(api_url: str, token: str, org_id: str, project_id: str, scan_id: str) -> list[dict]:
    resp = requests.get(
        f"{api_url}/api/v1/organizations/{org_id}/projects/{project_id}/scans/{scan_id}/findings",
        headers={"Authorization": f"Bearer {token}"},
        timeout=15,
    )
    resp.raise_for_status()
    return resp.json()


def main() -> int:
    parser = argparse.ArgumentParser(description="SecureScan CLI — rode scans a partir do CI/CD.")
    parser.add_argument("--api-url", required=True)
    parser.add_argument("--email", required=True)
    parser.add_argument("--password", required=True)
    parser.add_argument("--org-id", required=True)
    parser.add_argument("--url", required=True, help="URL do alvo a ser escaneado")
    parser.add_argument("--scan-type", default="FULL_SCAN",
                         choices=["QUICK_SCAN", "FULL_SCAN", "API_SCAN", "INFRA_SCAN"])
    parser.add_argument("--fail-on", default="critical",
                         choices=["critical", "high", "medium", "low"],
                         help="Falha o pipeline (exit 1) se achar algo neste nível ou mais grave.")
    args = parser.parse_args()

    try:
        print(f"→ Autenticando em {args.api_url}...")
        token = login(args.api_url, args.email, args.password)

        print(f"→ Iniciando {args.scan_type} em {args.url}...")
        scan = start_scan(args.api_url, token, args.org_id, args.url, args.scan_type)

        print("→ Aguardando conclusão...")
        result = poll_scan(args.api_url, token, args.org_id, scan["project_id"], scan["id"])

        if result["status"] != "COMPLETED":
            print(f"✗ Scan terminou com status {result['status']}, não foi possível avaliar achados.")
            return 2

        findings = get_findings(args.api_url, token, args.org_id, scan["project_id"], scan["id"])

    except requests.RequestException as e:
        print(f"✗ Erro de rede/API: {e}")
        return 2
    except TimeoutError as e:
        print(f"✗ {e}")
        return 2

    fail_threshold = SEVERITY_RANK[args.fail_on]
    blocking = [f for f in findings if SEVERITY_RANK.get(f["severity"], 99) <= fail_threshold]

    print()
    print(f"Total de achados: {len(findings)}")
    for sev in ["critical", "high", "medium", "low"]:
        count = sum(1 for f in findings if f["severity"] == sev)
        print(f"  {sev}: {count}")

    if blocking:
        print()
        print(f"✗ FALHOU: {len(blocking)} achado(s) no nível '{args.fail_on}' ou mais grave:")
        for f in blocking:
            print(f"  - [{f['severity'].upper()}] {f['title']}")
        return 1

    print()
    print(f"✓ OK: nenhum achado no nível '{args.fail_on}' ou mais grave.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

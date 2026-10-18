"""
Envia o relatório de um scan concluído para o webhook configurado na
organização (Seção 31 do documento original — Integrações).

Autorização em duas camadas, pra você escolher o nível de rigor na sua
central de recebimento:

1. Header `Authorization: Bearer <segredo>` — comparação simples de string.
2. Header `X-SecureScan-Signature: sha256=<hex>` — assinatura HMAC-SHA256
   do corpo (JSON) usando o mesmo segredo. Prova que o conteúdo não foi
   alterado no caminho, não só que quem mandou "sabia o segredo".

Nunca falha o scan por causa do webhook — se o envio der erro, registra e
segue em frente.
"""

from __future__ import annotations

import hashlib
import hmac
import json

import requests


def _sign_payload(body: bytes, secret: str) -> str:
    digest = hmac.new(secret.encode("utf-8"), body, hashlib.sha256).hexdigest()
    return f"sha256={digest}"


def send_scan_webhook(
    webhook_url: str,
    webhook_secret: str | None,
    payload: dict,
    timeout: int = 10,
) -> tuple[bool, str]:
    """Retorna (sucesso, mensagem) — a mensagem é guardada no scan para
    aparecer na interface, sem precisar abrir o log do worker."""
    # ensure_ascii=True escapa acentos/caracteres não-ASCII como \uXXXX em vez
    # de mandar bytes UTF-8 crus — formato mais universal, evita problemas de
    # parsing em receptores que não lidam bem com UTF-8 direto no corpo.
    body = json.dumps(payload, ensure_ascii=True).encode("ascii")

    headers = {"Content-Type": "application/json"}
    if webhook_secret:
        headers["Authorization"] = f"Bearer {webhook_secret}"
        headers["X-SecureScan-Signature"] = _sign_payload(body, webhook_secret)

    print(f"[webhook] Enviando para {webhook_url} ...")
    try:
        resp = requests.post(webhook_url, data=body, headers=headers, timeout=timeout)
        ok = 200 <= resp.status_code < 300
        if ok:
            print(f"[webhook] OK — status {resp.status_code}")
            return True, f"Enviado com sucesso (status {resp.status_code})."
        else:
            print(f"[webhook] FALHOU — status {resp.status_code}, corpo: {resp.text[:300]}")
            return False, f"O destino respondeu com erro {resp.status_code}: {resp.text[:200]}"
    except requests.RequestException as e:
        print(f"[webhook] ERRO DE CONEXÃO — não foi possível alcançar {webhook_url}: {e}")
        return False, f"Não foi possível conectar em {webhook_url}: {str(e)[:200]}"


def build_scan_payload(
    scan_id: str,
    project_name: str,
    domain_hostname: str,
    scan_type: str,
    status: str,
    severity_summary: dict[str, int],
    findings: list[dict],
) -> dict:
    return {
        "event": "scan.completed",
        "scan_id": scan_id,
        "project_name": project_name,
        "domain": domain_hostname,
        "scan_type": scan_type,
        "status": status,
        "severity_summary": severity_summary,
        "findings": findings,
    }


def send_slack_notification(
    slack_webhook_url: str,
    project_name: str,
    domain_hostname: str,
    severity_summary: dict[str, int],
    timeout: int = 10,
) -> bool:
    """
    Notificação no Slack (Seção 31 — Integrações). Só manda mensagem se
    houver achado crítico ou alto — evita virar spam de canal a cada scan
    limpo.
    """
    critical = severity_summary.get("critical", 0)
    high = severity_summary.get("high", 0)

    if critical == 0 and high == 0:
        return True  # nada relevante pra avisar, não é falha

    emoji = "🔴" if critical > 0 else "🟠"
    parts = []
    if critical:
        parts.append(f"{critical} crítica(s)")
    if high:
        parts.append(f"{high} alta(s)")

    text = (
        f"{emoji} *SecureScan* — {' e '.join(parts)} vulnerabilidade(s) encontrada(s)\n"
        f"Projeto: *{project_name}* · Alvo: `{domain_hostname}`"
    )

    try:
        resp = requests.post(slack_webhook_url, json={"text": text}, timeout=timeout)
        return resp.status_code == 200
    except requests.RequestException:
        return False

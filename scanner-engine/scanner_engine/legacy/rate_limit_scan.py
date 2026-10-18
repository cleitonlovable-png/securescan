"""
Verificação de rate limiting — Seção 2/3 do checklist de auditoria.

Manda um número pequeno e controlado de requisições seguidas contra um
endpoint (ex: login) e verifica se alguma foi bloqueada (429) ou se o
servidor aceita todas sem limite — o que indica ausência de proteção
contra brute-force/credential stuffing.

Isso é ATIVO por definição (gera tráfego repetido contra o alvo), mas
respeita um teto rígido de tentativas — nunca um brute-force de verdade.
"""

from __future__ import annotations

import time

import requests

MAX_ATTEMPTS_HARD_CAP = 30  # teto de segurança, nunca ultrapassa isso


def check_rate_limit(url: str, method: str = "POST", attempts: int = 15,
                      timeout: int = 5, delay_seconds: float = 0.2) -> dict:
    attempts = min(attempts, MAX_ATTEMPTS_HARD_CAP)

    statuses = []
    for _ in range(attempts):
        try:
            resp = requests.request(method, url, timeout=timeout,
                                     json={"probe": "securescan-rate-limit-check"})
            statuses.append(resp.status_code)
        except requests.RequestException:
            statuses.append(None)
        time.sleep(delay_seconds)

    blocked_count = sum(1 for s in statuses if s == 429)
    successful_count = sum(1 for s in statuses if s is not None and s < 400)

    findings = []
    if blocked_count == 0 and attempts >= 10:
        findings.append({
            "severity": "high",
            "issue": f"Nenhuma das {attempts} requisições seguidas foi bloqueada (nenhum status 429).",
            "recommendation": "Implementar rate limiting neste endpoint (ex: por IP e/ou por conta), "
                               "especialmente se ele lida com login, cadastro ou recuperação de senha. "
                               "Sem isso, o endpoint é vulnerável a brute-force e credential stuffing.",
        })
    elif blocked_count > 0:
        findings.append({
            "severity": "info",
            "issue": f"{blocked_count} de {attempts} requisições foram bloqueadas (status 429). "
                     "Rate limiting parece estar ativo.",
            "recommendation": "Bom sinal — ainda vale confirmar se o limite é razoável e se "
                               "existe também bloqueio por conta, não só por IP.",
        })

    return {
        "attempts": attempts,
        "blocked_count": blocked_count,
        "successful_count": successful_count,
        "findings": findings,
    }

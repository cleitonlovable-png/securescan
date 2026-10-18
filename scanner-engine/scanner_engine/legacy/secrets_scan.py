"""
Módulo de verificação: chaves e segredos vazados.

Baixa a página principal e os arquivos JavaScript linkados nela, e procura
por padrões conhecidos de chaves de API, tokens e credenciais que
desenvolvedores acidentalmente deixam no código do lado do cliente.

IMPORTANTE: qualquer segredo encontrado no frontend (HTML/JS) já está
"vazado" por definição, pois qualquer visitante do site pode vê-lo — não é
necessária nenhuma ação ofensiva para "descobrir" isso, só ler o código-fonte
público. Por isso este módulo é passivo.
"""

from __future__ import annotations

import re
from urllib.parse import urljoin

import requests


# (nome do tipo de segredo, regex, severidade)
SECRET_PATTERNS = [
    ("AWS Access Key ID", r"AKIA[0-9A-Z]{16}", "critical"),
    ("AWS Secret Key (possível)", r"aws_secret_access_key\s*=\s*['\"][A-Za-z0-9/+=]{40}['\"]", "critical"),
    ("Google API Key", r"AIza[0-9A-Za-z\-_]{35}", "high"),
    ("Stripe Live Secret Key", r"sk_live_[0-9a-zA-Z]{24,}", "critical"),
    ("Stripe Publishable Key", r"pk_live_[0-9a-zA-Z]{24,}", "low"),  # pública por design, só informativo
    ("Slack Token", r"xox[baprs]-[0-9A-Za-z-]{10,}", "high"),
    ("Chave privada (PEM)", r"-----BEGIN (RSA |EC |OPENSSH )?PRIVATE KEY-----", "critical"),
    ("JWT (token de sessão)", r"eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}", "medium"),
    ("Firebase Server Key", r"AAAA[A-Za-z0-9_-]{7}:[A-Za-z0-9_-]{140}", "high"),
    ("Genérico: 'secret'/'password' hardcoded", r"(?:secret|password|senha|api_key)['\"]?\s*[:=]\s*['\"][^'\"]{8,}['\"]", "medium"),
    ("GitHub Token", r"gh[pousr]_[A-Za-z0-9]{36,}", "critical"),
]


def _mask(value: str) -> str:
    if len(value) <= 8:
        return "*" * len(value)
    return value[:4] + "..." + value[-4:]


def _scan_text(text: str, source: str) -> list[dict]:
    findings = []
    for name, pattern, severity in SECRET_PATTERNS:
        for match in re.finditer(pattern, text):
            value = match.group(0)
            findings.append({
                "severity": severity,
                "issue": f"Possível {name} exposto no código-fonte público.",
                "recommendation": "Remover do código do cliente e mover para variável de ambiente "
                                   "no backend. Se for uma chave real, revogue-a e gere uma nova imediatamente.",
                "url": source,
                "description": f"Trecho encontrado (mascarado): {_mask(value)}",
            })
    return findings


def _extract_script_srcs(html: str, base_url: str) -> list[str]:
    srcs = re.findall(r'<script[^>]+src=["\']([^"\']+)["\']', html, re.IGNORECASE)
    # só JS do mesmo domínio, para não sair batendo em CDNs de terceiros
    same_origin = []
    for src in srcs:
        full = urljoin(base_url, src)
        if full.split("/")[2] == base_url.split("/")[2]:  # mesmo host
            same_origin.append(full)
    return same_origin[:15]  # limite de segurança para não demorar demais


def scan_for_secrets(target_url: str, timeout: int = 8) -> dict:
    findings = []

    try:
        resp = requests.get(target_url, timeout=timeout)
        html = resp.text
    except requests.RequestException:
        return {"module": "secrets_scan", "findings": [], "severity_summary": {"critical": 0, "high": 0, "medium": 0, "low": 0}}

    findings.extend(_scan_text(html, target_url))

    for js_url in _extract_script_srcs(html, target_url):
        try:
            js_resp = requests.get(js_url, timeout=timeout)
            findings.extend(_scan_text(js_resp.text, js_url))
        except requests.RequestException:
            continue

    severity_summary = {"critical": 0, "high": 0, "medium": 0, "low": 0}
    for f in findings:
        severity_summary[f["severity"]] += 1

    return {
        "module": "secrets_scan",
        "findings": findings,
        "severity_summary": severity_summary,
    }




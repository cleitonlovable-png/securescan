"""
Verificação de cookies de sessão — Seção 6 do checklist de auditoria.

Diferente do check de cookies já existente em pii_exposure.py (que só olha
formulários de senha), este verifica QUALQUER cookie que pareça de sessão
(nome contendo session/token/auth/sid/jwt), em qualquer página.
"""

from __future__ import annotations

import re

import requests

SESSION_COOKIE_NAME_PATTERN = re.compile(r"(session|token|auth|sid|jwt|csrf)", re.IGNORECASE)


def check_session_cookies(url: str, timeout: int = 10) -> list[dict]:
    findings = []

    try:
        resp = requests.get(url, timeout=timeout, allow_redirects=True)
    except requests.RequestException:
        return []

    raw_cookies = resp.raw.headers.get_all("Set-Cookie") if resp.raw and resp.raw.headers else []

    for cookie_header in raw_cookies or []:
        cookie_name = cookie_header.split("=")[0].strip()
        if not SESSION_COOKIE_NAME_PATTERN.search(cookie_name):
            continue

        cookie_lower = cookie_header.lower()
        missing = []
        if "secure" not in cookie_lower:
            missing.append("Secure")
        if "httponly" not in cookie_lower:
            missing.append("HttpOnly")
        if "samesite" not in cookie_lower:
            missing.append("SameSite")

        if missing:
            findings.append({
                "severity": "high" if "HttpOnly" in missing else "medium",
                "issue": f"Cookie de sessão '{cookie_name}' sem a(s) flag(s): {', '.join(missing)}.",
                "recommendation": "Adicionar as flags ausentes: Secure (só trafega em HTTPS), "
                                   "HttpOnly (não acessível via JavaScript, protege contra roubo "
                                   "via XSS), SameSite=Strict ou Lax (protege contra CSRF).",
            })

    return findings

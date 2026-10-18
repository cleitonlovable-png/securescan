"""
Módulo de verificação: headers de segurança HTTP.

Checa a presença e configuração correta dos principais headers de segurança
recomendados pela OWASP Secure Headers Project.
"""

from __future__ import annotations

import requests


# cada entrada: (header, severidade se ausente, descrição)
SECURITY_HEADERS = {
    "Strict-Transport-Security": ("high", "Força uso de HTTPS (HSTS). Ausência permite downgrade attacks."),
    "Content-Security-Policy": ("high", "Mitiga XSS e injeção de conteúdo. Ausência é uma falha comum e grave."),
    "X-Content-Type-Options": ("medium", "Sem 'nosniff', o navegador pode interpretar MIME types incorretamente."),
    "X-Frame-Options": ("medium", "Ausência permite clickjacking via iframe."),
    "Referrer-Policy": ("low", "Controla vazamento de informação via header Referer."),
    "Permissions-Policy": ("low", "Restringe acesso a APIs do navegador (câmera, geolocalização, etc)."),
}


def check_cookies(set_cookie_headers: list[str]) -> list[dict]:
    findings = []
    for cookie in set_cookie_headers:
        cookie_lower = cookie.lower()
        issues = []
        if "secure" not in cookie_lower:
            issues.append("faltando flag 'Secure' (cookie pode trafegar em HTTP puro)")
        if "httponly" not in cookie_lower:
            issues.append("faltando flag 'HttpOnly' (acessível via JavaScript, risco de roubo via XSS)")
        if "samesite" not in cookie_lower:
            issues.append("faltando atributo 'SameSite' (risco de CSRF)")

        if issues:
            cookie_name = cookie.split("=")[0]
            findings.append({
                "cookie": cookie_name,
                "severity": "medium",
                "issues": issues,
            })
    return findings


def check_headers(url: str, timeout: int = 10) -> dict:
    if not url.startswith("http"):
        url = f"https://{url}"

    resp = requests.get(url, timeout=timeout, allow_redirects=True)
    headers = resp.headers

    findings = []
    severity_summary = {"critical": 0, "high": 0, "medium": 0, "low": 0}

    for header, (severity, description) in SECURITY_HEADERS.items():
        if header not in headers:
            findings.append({
                "severity": severity,
                "issue": f"Header '{header}' ausente.",
                "recommendation": description,
            })
            severity_summary[severity] += 1

    # cookies inseguros
    raw_cookies = resp.raw.headers.get_all("Set-Cookie") if resp.raw and resp.raw.headers else []
    cookie_findings = check_cookies(raw_cookies or [])
    for cf in cookie_findings:
        severity_summary[cf["severity"]] += 1
    findings.extend([
        {"severity": cf["severity"], "issue": f"Cookie '{cf['cookie']}': {', '.join(cf['issues'])}",
         "recommendation": "Adicionar flags Secure, HttpOnly e SameSite."}
        for cf in cookie_findings
    ])

    # CORS mal configurado
    acao = headers.get("Access-Control-Allow-Origin")
    if acao == "*":
        findings.append({
            "severity": "high",
            "issue": "CORS configurado com 'Access-Control-Allow-Origin: *'.",
            "recommendation": "Restringir CORS a domínios confiáveis específicos, especialmente se "
                               "a API usa credenciais/cookies.",
        })
        severity_summary["high"] += 1

    return {
        "url": url,
        "status_code": resp.status_code,
        "findings": findings,
        "severity_summary": severity_summary,
        "headers_present": dict(headers),
    }




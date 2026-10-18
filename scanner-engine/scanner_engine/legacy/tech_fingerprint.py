"""
Módulo de reconhecimento: identifica tecnologias usadas pelo alvo
(servidor web, frameworks, CMS) a partir de headers HTTP e padrões no HTML.

Abordagem simples baseada em assinaturas conhecidas. Para algo mais robusto
pode-se integrar a lib `webtech` ou `Wappalyzer` via CLI.
"""

from __future__ import annotations

import re

import requests


SIGNATURES = {
    "WordPress": [r"wp-content", r"wp-includes"],
    "Django": [r"csrfmiddlewaretoken"],
    "Laravel": [r"laravel_session"],
    "Express": [r"X-Powered-By: Express"],
    "Ruby on Rails": [r"_session_id", r"X-Runtime"],
    "Nginx": [r"nginx"],
    "Apache": [r"apache"],
    "Cloudflare": [r"cloudflare"],
    "React": [r"react", r"__REACT_DEVTOOLS"],
    "Vue.js": [r"__VUE__", r"vue\.js"],
}


def fingerprint(url: str, timeout: int = 10) -> dict:
    if not url.startswith("http"):
        url = f"https://{url}"

    detected = []
    server_header = None
    powered_by = None

    try:
        resp = requests.get(url, timeout=timeout, allow_redirects=True)
        headers_blob = "\n".join(f"{k}: {v}" for k, v in resp.headers.items())
        body = resp.text[:200_000]  # limita para não processar páginas gigantes
        server_header = resp.headers.get("Server")
        powered_by = resp.headers.get("X-Powered-By")
        combined = headers_blob + "\n" + body

        for tech, patterns in SIGNATURES.items():
            if any(re.search(p, combined, re.IGNORECASE) for p in patterns):
                detected.append(tech)

    except requests.RequestException as e:
        return {"error": str(e), "url": url}

    return {
        "url": url,
        "server_header": server_header,
        "x_powered_by": powered_by,
        "detected_technologies": detected,
        "status_code": resp.status_code,
    }




"""
Verificação de CORS — Seção 4 do checklist de auditoria.

O teste mais importante não é só "existe Access-Control-Allow-Origin: *",
mas sim: o servidor REFLETE de volta qualquer Origin que a gente mandar?
Isso é mais perigoso que um wildcard simples, porque normalmente é usado
junto com credenciais (cookies), o que vaza dados de sessão pra qualquer
site malicioso que fizer uma requisição.
"""

from __future__ import annotations

import requests

FAKE_ORIGIN = "https://origem-de-teste-securescan.invalid"


def check_cors(url: str, timeout: int = 10) -> list[dict]:
    findings = []

    try:
        resp = requests.get(url, headers={"Origin": FAKE_ORIGIN}, timeout=timeout)
    except requests.RequestException:
        return []

    acao = resp.headers.get("Access-Control-Allow-Origin")
    acac = resp.headers.get("Access-Control-Allow-Credentials", "").lower()

    if acao == FAKE_ORIGIN:
        findings.append({
            "severity": "critical" if acac == "true" else "high",
            "issue": "O servidor reflete de volta qualquer Origin enviada no CORS "
                     + ("(e permite credenciais!)." if acac == "true" else "."),
            "recommendation": "Nunca refletir a Origin recebida sem validar contra uma lista "
                               "de domínios confiáveis. Combinado com "
                               "'Access-Control-Allow-Credentials: true', isso permite que "
                               "qualquer site na internet faça requisições autenticadas em nome "
                               "da vítima e leia a resposta.",
        })
    elif acao == "*" and acac == "true":
        findings.append({
            "severity": "critical",
            "issue": "CORS configurado com 'Access-Control-Allow-Origin: *' junto com "
                     "'Access-Control-Allow-Credentials: true'.",
            "recommendation": "Essa combinação é inválida pela especificação (a maioria dos "
                               "navegadores ignora), mas indica configuração descuidada. "
                               "Definir uma lista explícita de origens confiáveis.",
        })
    elif acao == "*":
        findings.append({
            "severity": "medium",
            "issue": "CORS configurado com 'Access-Control-Allow-Origin: *' (qualquer site pode ler a resposta).",
            "recommendation": "Se a API não precisa ser pública para qualquer origem, restringir "
                               "a uma lista de domínios confiáveis específicos.",
        })

    return findings

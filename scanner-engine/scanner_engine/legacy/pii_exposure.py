"""
Módulo de verificação: exposição de dados pessoais (LGPD).

Verifica três coisas relacionadas à Lei Geral de Proteção de Dados:

1. Se dados pessoais (CPF, CNPJ, cartão de crédito) aparecem em texto puro
   no HTML/JS servido pela aplicação (indicando que talvez estejam sendo
   expostos sem necessidade, cacheados incorretamente, etc).
2. Se páginas com formulários que coletam dados sensíveis (senha, CPF,
   cartão) estão sendo servidas por HTTP em vez de HTTPS.
3. Se a resposta tem headers de cache que poderiam reter dados sensíveis
   em caches intermediários (proxies, CDN) ou no navegador.

Isso não é uma auditoria de conformidade jurídica com a LGPD — é uma
checagem técnica dos sintomas mais comuns de vazamento/exposição de dados
pessoais que a lei exige proteger.
"""

from __future__ import annotations

import re

import requests


# CPF: 000.000.000-00 ou 00000000000 (11 dígitos seguidos, com validação leve)
CPF_PATTERN = r"\b\d{3}\.\d{3}\.\d{3}-\d{2}\b"
# CNPJ: 00.000.000/0000-00
CNPJ_PATTERN = r"\b\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}\b"
# Cartão de crédito: 4 grupos de 4 dígitos (com ou sem separador)
CREDIT_CARD_PATTERN = r"\b(?:\d{4}[ -]?){3}\d{4}\b"
# Email: quantidade excessiva em uma única resposta pode indicar vazamento de lista de usuários
EMAIL_PATTERN = r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"


def _looks_like_real_cpf(cpf_digits: str) -> bool:
    """Filtro simples para reduzir falso-positivo (ex: '000.000.000-00' de placeholder)."""
    return len(set(cpf_digits)) > 1  # todos os dígitos iguais quase sempre é dado de exemplo


def scan_page_for_pii(url: str, timeout: int = 8) -> dict:
    findings = []
    severity_summary = {"critical": 0, "high": 0, "medium": 0, "low": 0}

    try:
        resp = requests.get(url, timeout=timeout)
    except requests.RequestException:
        return {"module": "pii_exposure", "findings": [], "severity_summary": severity_summary}

    body = resp.text
    is_https = url.startswith("https://")

    # --- dados pessoais em texto puro na resposta ---
    cpfs = [m for m in re.findall(CPF_PATTERN, body) if _looks_like_real_cpf(m.replace(".", "").replace("-", ""))]
    if cpfs:
        findings.append({
            "severity": "critical",
            "issue": f"{len(cpfs)} possível(is) CPF(s) encontrado(s) em texto puro na resposta.",
            "recommendation": "Nunca expor CPF completo no frontend. Mascarar (ex: 123.***.**9-00) "
                               "ou remover do payload enviado ao cliente quando não for estritamente necessário.",
            "url": url,
        })
        severity_summary["critical"] += 1

    cnpjs = re.findall(CNPJ_PATTERN, body)
    if cnpjs:
        findings.append({
            "severity": "medium",
            "issue": f"{len(cnpjs)} CNPJ(s) encontrado(s) em texto puro na resposta.",
            "recommendation": "CNPJ é dado público em geral, mas avalie se a exposição em massa "
                               "(ex: lista completa de clientes) é realmente necessária no frontend.",
            "url": url,
        })
        severity_summary["medium"] += 1

    cards = re.findall(CREDIT_CARD_PATTERN, body)
    if cards:
        findings.append({
            "severity": "critical",
            "issue": f"{len(cards)} sequência(s) parecida(s) com número de cartão de crédito encontrada(s).",
            "recommendation": "Cartões de crédito NUNCA devem trafegar ou ser armazenados em texto puro. "
                               "Usar um provedor de pagamento tokenizado (Stripe, PagSeguro, etc) e nunca "
                               "manipular o número completo do cartão diretamente na sua aplicação.",
            "url": url,
        })
        severity_summary["critical"] += 1

    emails = re.findall(EMAIL_PATTERN, body)
    if len(emails) >= 10:
        findings.append({
            "severity": "high",
            "issue": f"{len(emails)} endereços de e-mail encontrados na mesma resposta.",
            "recommendation": "Uma lista grande de e-mails em uma única resposta pode indicar "
                               "vazamento de base de usuários (ex: endpoint de listagem sem paginação/autorização "
                               "adequada). Verificar se este endpoint deveria estar acessível publicamente.",
            "url": url,
        })
        severity_summary["high"] += 1

    # --- formulário sensível servido sem HTTPS ---
    has_password_field = bool(re.search(r'type=["\']password["\']', body, re.IGNORECASE))
    has_cpf_field = bool(re.search(r'name=["\'][^"\']*cpf[^"\']*["\']', body, re.IGNORECASE))

    if not is_https and (has_password_field or has_cpf_field):
        findings.append({
            "severity": "critical",
            "issue": "Formulário que coleta dados sensíveis (senha/CPF) está sendo servido via HTTP, não HTTPS.",
            "recommendation": "Servir toda página que colete dados pessoais ou senha exclusivamente via HTTPS. "
                               "Sem isso, os dados trafegam sem criptografia e podem ser interceptados na rede.",
            "url": url,
        })
        severity_summary["critical"] += 1

    # --- cache de resposta com dados sensíveis ---
    if (cpfs or cards) and "no-store" not in resp.headers.get("Cache-Control", ""):
        findings.append({
            "severity": "medium",
            "issue": "Resposta contendo dados pessoais não define 'Cache-Control: no-store'.",
            "recommendation": "Adicionar 'Cache-Control: no-store' em respostas que contêm dados pessoais "
                               "para evitar que fiquem retidos em caches de proxy, CDN ou no navegador.",
            "url": url,
        })
        severity_summary["medium"] += 1

    return {
        "module": "pii_exposure",
        "findings": findings,
        "severity_summary": severity_summary,
    }




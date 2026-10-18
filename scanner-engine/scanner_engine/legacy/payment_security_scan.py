"""
Payment Security — Seção 16 do documento original.

NÃO realiza nenhuma transação real. Apenas analisa a página de checkout
publicamente acessível procurando por padrões de implementação insegura.
"""

from __future__ import annotations

import re

import requests

CLIENT_PRICE_FIELD_PATTERN = re.compile(
    r'<input[^>]*(?:name|id)=["\'][^"\']*(price|amount|valor|total)[^"\']*["\'][^>]*type=["\']?(hidden|text|number)["\']?',
    re.IGNORECASE,
)
CARD_FIELD_PATTERN = re.compile(r'<input[^>]*(?:name|id)=["\'][^"\']*(card.?number|numero.?cart)[^"\']*["\']', re.IGNORECASE)


def check_checkout_page(url: str, timeout: int = 10) -> list[dict]:
    findings = []

    try:
        resp = requests.get(url, timeout=timeout)
        body = resp.text
    except requests.RequestException as e:
        return [{
            "severity": "low",
            "issue": "Não foi possível acessar a página de checkout informada.",
            "recommendation": f"Verifique a URL. Erro: {str(e)[:150]}",
        }]

    is_https = url.startswith("https://")

    # preço/valor controlável pelo cliente
    price_matches = CLIENT_PRICE_FIELD_PATTERN.findall(body)
    if price_matches:
        findings.append({
            "severity": "high",
            "issue": "A página de checkout tem campo de preço/valor no formulário do cliente.",
            "recommendation": "O preço final NUNCA deve ser confiado a partir do que o navegador envia. "
                               "O backend deve recalcular o valor a partir do ID do produto/carrinho, "
                               "ignorando qualquer valor de preço vindo do cliente.",
        })

    # campo de cartão sem HTTPS
    has_card_field = bool(CARD_FIELD_PATTERN.search(body))
    if has_card_field and not is_https:
        findings.append({
            "severity": "critical",
            "issue": "Formulário com campo de número de cartão servido via HTTP (sem HTTPS).",
            "recommendation": "Página de checkout DEVE ser servida exclusivamente via HTTPS. "
                               "Dados de cartão em HTTP trafegam sem criptografia.",
        })

    # chaves de pagamento expostas (Stripe, Mercado Pago) — verifica secret keys client-side
    if re.search(r"sk_live_[0-9a-zA-Z]{24,}", body):
        findings.append({
            "severity": "critical",
            "issue": "Chave secreta de pagamento (Stripe sk_live_) encontrada no HTML/JS da página.",
            "recommendation": "Chaves secretas de gateway de pagamento NUNCA podem estar no "
                               "frontend. Revogar essa chave imediatamente e mover para o backend.",
        })

    # confirmação de pagamento sem indicação de validação server-side
    # (heurística simples: presença de "payment_status" ou "paid=true" como parâmetro de URL)
    if re.search(r"[?&](paid|payment_status|status)=true", url, re.IGNORECASE):
        findings.append({
            "severity": "medium",
            "issue": "URL de retorno do checkout parece confiar em um parâmetro de status na própria URL.",
            "recommendation": "O status de pagamento deve ser confirmado no backend consultando "
                               "diretamente a API do gateway (ou validando o webhook assinado), "
                               "nunca confiando em um parâmetro que o navegador pode editar.",
        })

    return findings

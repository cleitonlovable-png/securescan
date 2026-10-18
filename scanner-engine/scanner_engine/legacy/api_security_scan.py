"""
Verificação de segurança de API a partir de:
1. Especificação OpenAPI/Swagger (JSON) — endpoints sem autenticação declarada.
2. Endpoint GraphQL — checa se a introspecção está habilitada (não deveria
   estar em produção, pois expõe todo o schema da API para quem quiser).
"""

from __future__ import annotations

import requests

SENSITIVE_FIELD_NAMES = {"password", "senha", "cpf", "ssn", "credit_card", "cartao", "token", "secret"}

INTROSPECTION_QUERY = """
query IntrospectionQuery { __schema { queryType { name } types { name } } }
"""


def check_openapi_spec(spec_url: str, timeout: int = 10) -> list[dict]:
    findings = []
    try:
        resp = requests.get(spec_url, timeout=timeout)
        resp.raise_for_status()
        spec = resp.json()
    except Exception as e:
        return [{
            "severity": "low",
            "issue": "Não foi possível buscar/ler a especificação OpenAPI.",
            "recommendation": f"Verifique se a URL está correta e acessível. Erro: {str(e)[:150]}",
        }]

    global_security = spec.get("security")
    paths = spec.get("paths", {})

    for path, methods in paths.items():
        for method, operation in methods.items():
            if method.upper() not in {"GET", "POST", "PUT", "PATCH", "DELETE"}:
                continue

            has_security = "security" in operation or (global_security and "security" not in operation)
            is_write = method.upper() in {"POST", "PUT", "PATCH", "DELETE"}

            if not has_security:
                findings.append({
                    "severity": "high" if is_write else "medium",
                    "issue": f"Endpoint {method.upper()} {path} não declara autenticação na especificação.",
                    "recommendation": "Adicionar um esquema de segurança (security) a este endpoint na "
                                       "especificação OpenAPI, ou confirmar que ele é intencionalmente público.",
                })

            # exposição excessiva de dados: campos sensíveis na resposta
            responses = operation.get("responses", {})
            for resp_code, resp_data in responses.items():
                schema_str = str(resp_data).lower()
                found_sensitive = [f for f in SENSITIVE_FIELD_NAMES if f in schema_str]
                if found_sensitive:
                    findings.append({
                        "severity": "medium",
                        "issue": f"Resposta de {method.upper()} {path} parece incluir campo(s) sensível(is): "
                                 f"{', '.join(set(found_sensitive))}.",
                        "recommendation": "Confirme se esses campos realmente precisam estar na resposta da API. "
                                           "Evite retornar senhas, tokens ou documentos pessoais completos.",
                    })

    return findings


def check_graphql_introspection(graphql_url: str, timeout: int = 10) -> list[dict]:
    try:
        resp = requests.post(graphql_url, json={"query": INTROSPECTION_QUERY}, timeout=timeout)
        data = resp.json()
    except Exception:
        return []

    if data.get("data", {}).get("__schema"):
        return [{
            "severity": "medium",
            "issue": "Introspecção do GraphQL está habilitada.",
            "recommendation": "Desabilitar introspecção em produção (a maioria dos frameworks GraphQL tem uma "
                               "opção para isso). Isso evita que qualquer pessoa descubra todo o schema da API.",
        }]
    return []

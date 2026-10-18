"""
Teste de controle de acesso — IDOR (Insecure Direct Object Reference).

IDOR é quando a aplicação usa um ID (ex: /pedido/145) para buscar um
registro, mas não verifica se o usuário logado tem permissão para ver
*aquele* registro específico. Resultado: trocando o número na URL, dá pra
ver pedidos, perfis ou dados de outras pessoas.

Como funciona este teste:
1. Você informa uma URL de exemplo que contém um ID (ex: um pedido seu)
2. Opcionalmente, informa o cookie de sessão de um usuário logado
3. O scanner tenta acessar IDs vizinhos (145 -> 143, 144, 146, 147...) e
   também IDs baixos comuns (1, 2, 3) usando a MESMA sessão
4. Se conseguir uma resposta válida (200, com conteúdo real) para um ID
   diferente do original, isso é um forte indício de IDOR

IMPORTANTE: este teste não consegue confirmar com certeza absoluta que o
dado retornado pertence a OUTRO usuário (isso exigiria duas contas de
teste). Ele confirma que a aplicação não valida propriedade do recurso,
o que já é a causa raiz do problema — mas recomенda-se conferir manualmente
o conteúdo retornado.
"""

from __future__ import annotations

import re

import requests



def _extract_id_and_build_url_template(sample_url: str) -> tuple[str, int] | None:
    """
    Encontra o último número na URL e retorna um template com {ID} no lugar,
    junto com o valor numérico original.
    """
    match = re.search(r"(\d+)(?!.*\d)", sample_url)  # último grupo de dígitos da URL
    if not match:
        return None

    original_id = int(match.group(1))
    start, end = match.span(1)
    template = sample_url[:start] + "{ID}" + sample_url[end:]
    return template, original_id


def _fetch(url: str, cookie: str | None, timeout: int = 8) -> requests.Response | None:
    headers = {"Cookie": cookie} if cookie else {}
    try:
        return requests.get(url, headers=headers, timeout=timeout, allow_redirects=False)
    except requests.RequestException:
        return None


def test_idor(sample_url: str, cookie: str | None = None, timeout: int = 8) -> dict:
    findings = []
    severity_summary = {"critical": 0, "high": 0, "medium": 0, "low": 0}

    parsed = _extract_id_and_build_url_template(sample_url)
    if parsed is None:
        return {
            "module": "idor_check",
            "findings": [{
                "severity": "low",
                "issue": "Não foi encontrado nenhum número na URL informada para testar como ID.",
                "recommendation": "Informe uma URL que contenha um ID numérico, ex: "
                                   "https://seusite.com/api/pedido/145",
            }],
            "severity_summary": {"critical": 0, "high": 0, "medium": 0, "low": 1},
        }

    template, original_id = parsed

    baseline_resp = _fetch(template.format(ID=original_id), cookie, timeout)
    if baseline_resp is None or baseline_resp.status_code != 200:
        return {
            "module": "idor_check",
            "findings": [{
                "severity": "low",
                "issue": "Não foi possível acessar a URL de exemplo original com a sessão informada.",
                "recommendation": "Confira se o cookie de sessão é válido e se a URL de exemplo "
                                   "realmente existe e pertence a você.",
            }],
            "severity_summary": {"critical": 0, "high": 0, "medium": 0, "low": 1},
        }

    baseline_len = len(baseline_resp.content)

    # baseline de "não existe", para filtrar páginas catch-all/SPA
    fake_id = 999_999_991
    not_found_resp = _fetch(template.format(ID=fake_id), cookie, timeout)
    not_found_status = not_found_resp.status_code if not_found_resp else 0
    not_found_len = len(not_found_resp.content) if not_found_resp else 0

    candidate_ids = {original_id - 2, original_id - 1, original_id + 1, original_id + 2, 1, 2, 3}
    candidate_ids.discard(original_id)

    accessible_ids = []
    for candidate_id in sorted(candidate_ids):
        if candidate_id < 1:
            continue
        resp = _fetch(template.format(ID=candidate_id), cookie, timeout)
        if resp is None:
            continue

        looks_like_real_data = (
            resp.status_code == 200
            and not (resp.status_code == not_found_status and len(resp.content) == not_found_len)
            and len(resp.content) > 0
        )
        if looks_like_real_data:
            accessible_ids.append(candidate_id)

    if accessible_ids:
        auth_context = "com a sessão informada" if cookie else "SEM NENHUMA autenticação"
        findings.append({
            "severity": "critical",
            "issue": f"Foi possível acessar {len(accessible_ids)} registro(s) diferente(s) "
                     f"({', '.join(map(str, accessible_ids))}) trocando o ID na URL, {auth_context}.",
            "recommendation": "Adicionar verificação de propriedade/permissão no backend: antes de "
                               "retornar o recurso, confirmar que ele pertence ao usuário autenticado "
                               "na sessão atual (ex: WHERE user_id = current_user.id na consulta). "
                               "Confirme manualmente se os dados retornados pertencem a outra pessoa.",
            "url": template.format(ID=accessible_ids[0]),
        })
        severity_summary["critical"] += 1
    else:
        findings.append({
            "severity": "low",
            "issue": "Nenhum indício de IDOR encontrado nos IDs testados.",
            "recommendation": "Isso não garante ausência total de IDOR — apenas que os IDs "
                               "próximos testados não retornaram dados. Considere testar outros "
                               "endpoints e tipos de recurso manualmente.",
        })
        severity_summary["low"] += 1

    return {
        "module": "idor_check",
        "tested_ids": sorted(candidate_ids),
        "findings": findings,
        "severity_summary": severity_summary,
    }




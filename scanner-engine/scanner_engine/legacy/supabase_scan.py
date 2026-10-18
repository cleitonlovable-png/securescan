"""
Módulo específico Supabase — Seção 15 do documento original.

IMPORTANTE: a anon key do Supabase NÃO é, por si só, uma vulnerabilidade —
ela é pública por design (fica embutida no frontend de qualquer app Supabase).
O que verificamos é se as PERMISSÕES por trás dela estão abertas demais
(RLS ausente/mal configurado, buckets de storage públicos sem necessidade).
"""

from __future__ import annotations

import requests


def discover_tables(project_url: str, anon_key: str, timeout: int = 10) -> list[str]:
    """PostgREST expõe um documento no estilo OpenAPI na raiz — usamos isso
    para descobrir os nomes das tabelas sem precisar que o usuário digite."""
    try:
        resp = requests.get(
            f"{project_url}/rest/v1/",
            headers={"apikey": anon_key, "Authorization": f"Bearer {anon_key}"},
            timeout=timeout,
        )
        data = resp.json()
        paths = data.get("paths", {})
        return [p.lstrip("/") for p in paths.keys() if p not in ("/", "")]
    except Exception:
        return []


def check_table_access(project_url: str, anon_key: str, table: str, timeout: int = 10) -> dict | None:
    """Testa se dá pra ler dados da tabela usando só a anon key."""
    try:
        resp = requests.get(
            f"{project_url}/rest/v1/{table}",
            headers={"apikey": anon_key, "Authorization": f"Bearer {anon_key}"},
            params={"select": "*", "limit": "5"},
            timeout=timeout,
        )
    except requests.RequestException:
        return None

    if resp.status_code == 200:
        try:
            rows = resp.json()
        except ValueError:
            return None
        if isinstance(rows, list) and len(rows) > 0:
            return {
                "severity": "high",
                "issue": f"Tabela '{table}' retorna dados usando só a anon key (sem login).",
                "recommendation": "Verificar se Row Level Security (RLS) está habilitado nesta "
                                   "tabela e se as policies realmente restringem o acesso esperado. "
                                   "Se os dados devem ser públicos, isso é intencional — confirme.",
            }
    elif resp.status_code == 401 or resp.status_code == 403:
        return None  # bom sinal, RLS bloqueando
    return None


def check_storage_buckets(project_url: str, anon_key: str, timeout: int = 10) -> list[dict]:
    findings = []
    try:
        resp = requests.get(
            f"{project_url}/storage/v1/bucket",
            headers={"apikey": anon_key, "Authorization": f"Bearer {anon_key}"},
            timeout=timeout,
        )
        buckets = resp.json()
    except Exception:
        return findings

    if not isinstance(buckets, list):
        return findings

    for bucket in buckets:
        if bucket.get("public"):
            findings.append({
                "severity": "medium",
                "issue": f"Bucket de storage '{bucket.get('name')}' está marcado como público.",
                "recommendation": "Confirme se este bucket realmente deveria ser público (ex: avatares, "
                                   "imagens de produto). Se tiver documentos sensíveis, marque como privado.",
            })

    return findings


def run_supabase_scan(project_url: str, anon_key: str, timeout: int = 10) -> dict:
    project_url = project_url.rstrip("/")
    findings = []

    tables = discover_tables(project_url, anon_key, timeout)
    for table in tables[:20]:  # limite de segurança para não demorar demais
        result = check_table_access(project_url, anon_key, table, timeout)
        if result:
            findings.append(result)

    findings.extend(check_storage_buckets(project_url, anon_key, timeout))

    return {"tables_checked": len(tables), "findings": findings}

"""
Verifica se um bucket de armazenamento (S3, Google Cloud Storage, etc) está
listando conteúdo publicamente — uma das causas mais comuns de vazamento de
dados em massa (Seção 17 do documento original — storage público, buckets).
"""

from __future__ import annotations

import requests

S3_LISTING_MARKERS = ["<ListBucketResult", "<Contents>", "<Key>"]
GCS_LISTING_MARKERS = ['"kind": "storage#objects"', '"items":']


def check_public_bucket(bucket_url: str, timeout: int = 10) -> list[dict]:
    findings = []

    try:
        resp = requests.get(bucket_url, timeout=timeout)
    except requests.RequestException as e:
        return [{
            "severity": "low",
            "issue": "Não foi possível acessar a URL do bucket informada.",
            "recommendation": f"Verifique se a URL está correta. Erro: {str(e)[:150]}",
        }]

    body = resp.text[:5000]

    is_s3_listing = resp.status_code == 200 and any(marker in body for marker in S3_LISTING_MARKERS)
    is_gcs_listing = resp.status_code == 200 and any(marker in body for marker in GCS_LISTING_MARKERS)

    if is_s3_listing or is_gcs_listing:
        findings.append({
            "severity": "critical",
            "issue": "O bucket está listando seu conteúdo publicamente.",
            "recommendation": "Restringir a política do bucket para negar 's3:ListBucket' (ou "
                               "equivalente) para o público. Qualquer pessoa pode ver todos os "
                               "arquivos armazenados enquanto isso não for corrigido.",
        })
    elif resp.status_code == 403:
        findings.append({
            "severity": "info",
            "issue": "Bucket respondeu com 403 (acesso negado) — listagem pública parece bloqueada.",
            "recommendation": "Bom sinal. Ainda vale checar manualmente as permissões de objetos "
                               "individuais, que podem estar públicas mesmo com a listagem bloqueada.",
        })

    return findings

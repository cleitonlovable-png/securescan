"""
Módulo de verificação: arquivos e caminhos sensíveis expostos.

Testa uma lista de caminhos comuns que nunca deveriam estar acessíveis
publicamente (variáveis de ambiente, configs, histórico do git, backups,
painéis de debug). Isso é uma das causas mais comuns de vazamento de dados
em aplicações reais.
"""

from __future__ import annotations

import requests


# (caminho, severidade, descrição)
SENSITIVE_PATHS = [
    ("/.env", "critical", "Arquivo .env pode conter senhas, chaves de API e strings de conexão."),
    ("/.git/config", "critical", "Repositório Git exposto — todo o histórico e código-fonte podem ser baixados."),
    ("/.git/HEAD", "critical", "Repositório Git exposto — todo o histórico e código-fonte podem ser baixados."),
    ("/.aws/credentials", "critical", "Credenciais da AWS podem estar expostas."),
    ("/config.py", "high", "Arquivo de configuração da aplicação pode conter segredos."),
    ("/settings.py", "high", "Arquivo de configuração da aplicação pode conter segredos."),
    ("/wp-config.php", "critical", "Configuração do WordPress exposta (inclui credenciais do banco)."),
    ("/docker-compose.yml", "high", "Arquivo docker-compose pode expor variáveis de ambiente e senhas."),
    ("/.htpasswd", "high", "Arquivo de senhas do Apache exposto."),
    ("/backup.sql", "critical", "Backup de banco de dados acessível publicamente."),
    ("/backup.zip", "high", "Arquivo de backup acessível publicamente."),
    ("/database.sql", "critical", "Dump de banco de dados acessível publicamente."),
    ("/.DS_Store", "low", "Arquivo de sistema do macOS pode revelar estrutura de diretórios."),
    ("/server-status", "medium", "Página de status do Apache exposta (pode revelar requisições em tempo real)."),
    ("/phpinfo.php", "high", "phpinfo() exposto — revela detalhes internos do servidor."),
    ("/.well-known/security.txt", "low", "Informativo: não é uma falha, apenas indica se a política de segurança está publicada."),
    ("/debug", "medium", "Endpoint de debug pode estar acessível."),
    ("/console", "high", "Console de debug (ex: Werkzeug/Flask debugger) pode permitir execução remota de código."),
    ("/.svn/entries", "high", "Repositório Subversion exposto."),
    ("/id_rsa", "critical", "Possível chave privada SSH exposta."),
]


def _get_baseline(base_url: str, timeout: int) -> tuple[int, int]:
    """
    Pega uma resposta de um caminho que certamente não existe, para servir
    de referência. Isso evita falso-positivo em apps que retornam 200 para
    qualquer rota (SPAs com catch-all), sem servidor de arquivos estáticos.
    """
    probe_path = "/isso-nao-deveria-existir-nunca-9f8e7d6c5b4a"
    try:
        resp = requests.get(base_url + probe_path, timeout=timeout, allow_redirects=False)
        return resp.status_code, len(resp.content)
    except requests.RequestException:
        return 0, 0


def check_exposed_files(target_url: str, timeout: int = 6) -> dict:
    base_url = target_url.rstrip("/")
    baseline_status, baseline_len = _get_baseline(base_url, timeout)

    findings = []
    severity_summary = {"critical": 0, "high": 0, "medium": 0, "low": 0}

    for path, severity, description in SENSITIVE_PATHS:
        try:
            resp = requests.get(base_url + path, timeout=timeout, allow_redirects=False)
        except requests.RequestException:
            continue

        # ignora se o comportamento é idêntico ao baseline (provável catch-all/SPA)
        if resp.status_code == baseline_status and len(resp.content) == baseline_len:
            continue

        if resp.status_code == 200 and len(resp.content) > 0:
            findings.append({
                "severity": severity,
                "issue": f"Caminho sensível acessível publicamente: {path}",
                "recommendation": description,
                "url": base_url + path,
            })
            severity_summary[severity] += 1

    return {
        "module": "exposed_files",
        "target": target_url,
        "paths_checked": len(SENSITIVE_PATHS),
        "findings": findings,
        "severity_summary": severity_summary,
    }




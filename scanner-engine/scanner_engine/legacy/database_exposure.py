"""
Módulo de verificação: exposição de banco de dados.

Checa se portas de bancos de dados comuns estão abertas e, quando possível,
testa se aceitam conexão SEM autenticação — uma das falhas mais graves e
mais comuns em ambientes mal configurados (containers Docker expostos,
firewalls mal configurados, etc).

Todos os testes aqui são de "a porta responde sem senha?", nunca tentam
adivinhar senha nem exploram falhas — é equivalente a bater na porta e ver
se ela está destrancada.
"""

from __future__ import annotations

import socket

import requests


DB_PORTS = {
    3306: "MySQL/MariaDB",
    5432: "PostgreSQL",
    27017: "MongoDB",
    6379: "Redis",
    9200: "Elasticsearch",
    1433: "Microsoft SQL Server",
    5984: "CouchDB",
    9042: "Cassandra",
}


def _port_open(host: str, port: int, timeout: float = 2.5) -> bool:
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except (socket.timeout, ConnectionRefusedError, OSError):
        return False


def _check_redis_no_auth(host: str, port: int, timeout: float = 3) -> bool:
    """Envia o comando PING sem autenticação. Se responder PONG, está aberto."""
    try:
        with socket.create_connection((host, port), timeout=timeout) as s:
            s.sendall(b"PING\r\n")
            response = s.recv(100)
            return b"PONG" in response
    except (socket.timeout, OSError):
        return False


def _check_mongodb_no_auth(host: str, port: int, timeout: float = 3) -> bool:
    """
    Tenta uma conexão TCP simples e verifica se o MongoDB responde ao
    handshake inicial sem exigir autenticação. Requer pymongo se disponível;
    caso contrário, apenas confirma que a porta está aberta.
    """
    try:
        import pymongo
        client = pymongo.MongoClient(host, port, serverSelectionTimeoutMS=int(timeout * 1000))
        client.admin.command("ping")  # se isso não levantar exceção, não pede autenticação
        return True
    except ImportError:
        return False  # não dá pra confirmar sem a lib, só sinaliza porta aberta depois
    except Exception:
        return False


def _check_elasticsearch_no_auth(host: str, port: int, timeout: float = 3) -> bool:
    try:
        resp = requests.get(f"http://{host}:{port}/", timeout=timeout)
        return resp.status_code == 200 and "cluster_name" in resp.text
    except requests.RequestException:
        return False


def check_database_exposure(host: str) -> dict:
    findings = []
    severity_summary = {"critical": 0, "high": 0, "medium": 0, "low": 0}

    for port, db_name in DB_PORTS.items():
        if not _port_open(host, port):
            continue

        # porta aberta já é digno de nota se for banco de dados
        no_auth_confirmed = False
        if port == 6379:
            no_auth_confirmed = _check_redis_no_auth(host, port)
        elif port == 27017:
            no_auth_confirmed = _check_mongodb_no_auth(host, port)
        elif port == 9200:
            no_auth_confirmed = _check_elasticsearch_no_auth(host, port)

        if no_auth_confirmed:
            findings.append({
                "severity": "critical",
                "issue": f"{db_name} (porta {port}) está aberto e ACEITA CONEXÕES SEM SENHA.",
                "recommendation": "Habilitar autenticação imediatamente e restringir o acesso à "
                                   "porta via firewall (permitir só IPs internos/confiáveis).",
                "url": f"{host}:{port}",
            })
            severity_summary["critical"] += 1
        else:
            findings.append({
                "severity": "medium",
                "issue": f"{db_name} (porta {port}) está aberto e acessível pela rede.",
                "recommendation": "Verificar se a exposição é intencional. Bancos de dados geralmente "
                                   "não deveriam estar acessíveis fora da rede interna/VPC.",
                "url": f"{host}:{port}",
            })
            severity_summary["medium"] += 1

    # painéis de administração de banco expostos via HTTP
    admin_panels = {
        "/phpmyadmin/": "phpMyAdmin",
        "/adminer.php": "Adminer",
        "/_utils/": "CouchDB Fauxton",
    }
    for path, panel_name in admin_panels.items():
        try:
            resp = requests.get(f"http://{host}{path}", timeout=3)
            if resp.status_code == 200:
                findings.append({
                    "severity": "high",
                    "issue": f"Painel de administração de banco de dados exposto: {panel_name} ({path})",
                    "recommendation": "Restringir acesso a este painel por IP ou removê-lo do ambiente de produção.",
                    "url": f"http://{host}{path}",
                })
                severity_summary["high"] += 1
        except requests.RequestException:
            continue

    return {
        "module": "database_exposure",
        "host": host,
        "findings": findings,
        "severity_summary": severity_summary,
    }




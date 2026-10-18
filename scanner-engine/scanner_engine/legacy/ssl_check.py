"""
Módulo de verificação: SSL/TLS.

Checa validade do certificado, dias até expirar, e tenta identificar
protocolos obsoletos (SSLv3, TLS 1.0, TLS 1.1) que ainda estejam habilitados.
"""

from __future__ import annotations

import socket
import ssl
from datetime import datetime


OBSOLETE_PROTOCOLS = {
    "SSLv3": ssl.PROTOCOL_SSLv23 if hasattr(ssl, "PROTOCOL_SSLv23") else None,
    "TLSv1": getattr(ssl, "PROTOCOL_TLSv1", None),
    "TLSv1.1": getattr(ssl, "PROTOCOL_TLSv1_1", None),
}


def get_certificate_info(host: str, port: int = 443, timeout: int = 10) -> dict:
    context = ssl.create_default_context()
    with socket.create_connection((host, port), timeout=timeout) as sock:
        with context.wrap_socket(sock, server_hostname=host) as ssock:
            cert = ssock.getpeercert()
            cipher = ssock.cipher()

    not_after = datetime.strptime(cert["notAfter"], "%b %d %H:%M:%S %Y %Z")
    days_left = (not_after - datetime.utcnow()).days

    issuer = dict(x[0] for x in cert.get("issuer", []))
    subject = dict(x[0] for x in cert.get("subject", []))

    return {
        "issuer": issuer.get("organizationName", "desconhecido"),
        "subject_cn": subject.get("commonName", "desconhecido"),
        "expires_at": cert["notAfter"],
        "days_until_expiry": days_left,
        "expired": days_left < 0,
        "expiring_soon": 0 <= days_left <= 30,
        "cipher_suite": cipher[0] if cipher else None,
        "tls_version_negotiated": cipher[1] if cipher else None,
    }


def check_obsolete_protocols(host: str, port: int = 443, timeout: int = 5) -> list[str]:
    """Tenta conectar usando protocolos antigos. Se conseguir, é uma falha."""
    weak_found = []

    for name, proto_const in OBSOLETE_PROTOCOLS.items():
        if proto_const is None:
            continue  # não suportado nesta versão do Python/OpenSSL, pula
        try:
            context = ssl.SSLContext(proto_const)
            with socket.create_connection((host, port), timeout=timeout) as sock:
                with context.wrap_socket(sock, server_hostname=host):
                    weak_found.append(name)
        except (ssl.SSLError, socket.error, OSError):
            continue  # não conseguiu conectar com esse protocolo = bom sinal

    return weak_found




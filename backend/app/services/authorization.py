from __future__ import annotations

import ipaddress
from urllib.parse import urlparse

import dns.resolver
import requests

from app.models.domain import Domain
from app.models.enums import VerificationMethod, VerificationStatus

PRIVATE_HOSTS = {"localhost", "127.0.0.1"}


def is_private_host(hostname: str) -> bool:
    """Ver docs/SECURITY_MODEL.md Seção 2.3 — exceções sem verificação."""
    if hostname in PRIVATE_HOSTS:
        return True
    try:
        ip = ipaddress.ip_address(hostname)
        return ip.is_private or ip.is_loopback
    except ValueError:
        return False


def verify_via_well_known_file(domain: Domain, timeout: int = 8) -> bool:
    url = f"https://{domain.hostname}/.well-known/securescan-verification.txt"
    try:
        resp = requests.get(url, timeout=timeout)
        return resp.status_code == 200 and domain.verification_token in resp.text
    except requests.RequestException:
        return False


def verify_via_dns_txt(domain: Domain, timeout: int = 8) -> bool:
    record_name = f"_securescan-verification.{domain.hostname}"
    expected = f"securescan-verify={domain.verification_token}"
    try:
        answers = dns.resolver.resolve(record_name, "TXT", lifetime=timeout)
        return any(expected in str(rdata) for rdata in answers)
    except Exception:
        return False


def attempt_verification(domain: Domain, method: VerificationMethod) -> VerificationStatus:
    """
    Roda a checagem escolhida e retorna o novo status. Não persiste no banco
    — quem chama (a rota) é responsável por salvar o resultado.
    """
    if is_private_host(domain.hostname):
        return VerificationStatus.PRIVATE_ENVIRONMENT

    ok = (
        verify_via_well_known_file(domain)
        if method == VerificationMethod.WELL_KNOWN_FILE
        else verify_via_dns_txt(domain)
    )
    return VerificationStatus.VERIFIED if ok else VerificationStatus.FAILED

from __future__ import annotations

from urllib.parse import urlparse

from ..base import Confidence, Finding, ScanContext, ScannerPlugin, Severity
from ..registry import register
from ..legacy.ssl_check import get_certificate_info, check_obsolete_protocols


@register
class SslPlugin(ScannerPlugin):
    name = "ssl_check"
    version = "1.0.0"
    category = "web"
    requires_active_scan = False

    def run(self, context: ScanContext) -> list[Finding]:
        if not context.target_url.startswith("https://"):
            return []  # nada a checar em alvo sem HTTPS

        host = urlparse(context.target_url).hostname
        findings = []

        try:
            cert_info = get_certificate_info(host, timeout=context.timeout_seconds)
        except Exception:
            return [Finding(
                title="Não foi possível verificar o certificado SSL/TLS",
                description="Falha ao conectar via TLS no host informado.",
                category="tls",
                severity=Severity.INFO,
                confidence=Confidence.MEDIUM,
                plugin_name=self.name,
            )]

        if cert_info["expired"]:
            findings.append(Finding(
                title="Certificado SSL expirado",
                description=f"O certificado expirou em {cert_info['expires_at']}.",
                category="tls",
                severity=Severity.CRITICAL,
                owasp="A02:2021 - Cryptographic Failures",
                remediation="Renovar o certificado imediatamente.",
                plugin_name=self.name,
            ))
        elif cert_info["expiring_soon"]:
            findings.append(Finding(
                title="Certificado SSL expira em breve",
                description=f"Expira em {cert_info['days_until_expiry']} dias.",
                category="tls",
                severity=Severity.MEDIUM,
                remediation="Renovar o certificado antes do vencimento.",
                plugin_name=self.name,
            ))

        weak_protocols = check_obsolete_protocols(host, timeout=context.timeout_seconds)
        for proto in weak_protocols:
            findings.append(Finding(
                title=f"Protocolo obsoleto {proto} habilitado",
                description=f"O servidor ainda aceita conexões via {proto}.",
                category="tls",
                severity=Severity.HIGH,
                owasp="A02:2021 - Cryptographic Failures",
                remediation="Desabilitar protocolos TLS antigos (< 1.2) no servidor web.",
                plugin_name=self.name,
            ))

        return findings

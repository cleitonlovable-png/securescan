from __future__ import annotations

from urllib.parse import urlparse

from ..base import Confidence, Finding, ScanContext, ScannerPlugin, Severity
from ..registry import register
from ..legacy.port_scan import scan_ports

RISKY_PORTS = {
    21: "FTP", 23: "Telnet", 3389: "RDP", 3306: "MySQL exposto",
    5432: "PostgreSQL exposto", 27017: "MongoDB exposto", 6379: "Redis exposto",
}


@register
class PortScanPlugin(ScannerPlugin):
    name = "port_scan"
    version = "1.0.0"
    category = "infra"
    requires_active_scan = False

    def health_check(self) -> bool:
        import shutil
        return shutil.which("nmap") is not None

    def run(self, context: ScanContext) -> list[Finding]:
        if not self.health_check():
            return [Finding(
                title="Scan de portas não executado",
                description="Nmap não está instalado no worker.",
                category="infra",
                severity=Severity.INFO,
                confidence=Confidence.HIGH,
                remediation="Instalar nmap na imagem Docker do worker.",
                plugin_name=self.name,
            )]

        host = urlparse(context.target_url).hostname or context.target_url

        try:
            ports = scan_ports(host, fast=True)
        except Exception as e:
            return [Finding(
                title="Erro ao executar scan de portas",
                description=str(e)[:200],
                category="infra",
                severity=Severity.INFO,
                plugin_name=self.name,
            )]

        findings = []
        for p in ports:
            if p.state != "open":
                continue
            if p.port in RISKY_PORTS:
                findings.append(Finding(
                    title=f"Porta arriscada aberta: {p.port} ({RISKY_PORTS[p.port]})",
                    description=f"Serviço identificado: {p.service} {p.version}".strip(),
                    category="infra",
                    severity=Severity.HIGH,
                    owasp="A05:2021 - Security Misconfiguration",
                    remediation="Restringir acesso via firewall/security group a IPs confiáveis.",
                    plugin_name=self.name,
                ))
        return findings

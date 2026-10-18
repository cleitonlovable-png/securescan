from __future__ import annotations

from ..base import Confidence, Finding, ScanContext, ScannerPlugin, Severity
from ..registry import register
from ..legacy.idor_check import test_idor


@register
class IdorPlugin(ScannerPlugin):
    name = "idor_check"
    version = "1.0.0"
    category = "access_control"
    requires_active_scan = True  # tenta acessar recursos que não são "seus" por definição

    def run(self, context: ScanContext) -> list[Finding]:
        if not context.requires_active_scan_allowed:
            return [Finding(
                title="Teste de IDOR não executado — domínio não verificado",
                description="Este plugin tenta acessar registros de outros IDs e só roda em "
                             "domínios com autorização confirmada (VERIFIED ou PRIVATE_ENVIRONMENT).",
                category="access_control",
                severity=Severity.INFO,
                plugin_name=self.name,
            )]

        sample_url = context.extra_config.get("idor_sample_url")
        if not sample_url:
            return []  # opcional — só roda se o usuário informou uma URL de exemplo

        cookie = context.extra_config.get("idor_session_cookie")
        raw = test_idor(sample_url, cookie=cookie, timeout=context.timeout_seconds)

        return [
            Finding(
                title=f["issue"],
                description=f.get("recommendation", ""),
                category="access_control",
                severity=Severity(f["severity"]),
                confidence=Confidence.MEDIUM,  # exige confirmação manual do conteúdo retornado
                cwe="CWE-639",
                owasp="A01:2021 - Broken Access Control",
                endpoint_or_file=f.get("url"),
                remediation=f.get("recommendation", ""),
                plugin_name=self.name,
            )
            for f in raw.get("findings", [])
        ]

from __future__ import annotations

from ..base import Confidence, Finding, ScanContext, ScannerPlugin, Severity
from ..registry import register
from ..legacy.secrets_scan import scan_for_secrets


@register
class SecretsPlugin(ScannerPlugin):
    name = "secrets_scan"
    version = "1.0.0"
    category = "secrets"
    requires_active_scan = False

    def run(self, context: ScanContext) -> list[Finding]:
        raw = scan_for_secrets(context.target_url, timeout=context.timeout_seconds)

        return [
            Finding(
                title=f["issue"],
                description=f.get("description", ""),
                category="secrets",
                severity=Severity(f["severity"]),
                confidence=Confidence.MEDIUM,  # regex-based, sempre confirmar manualmente
                cwe="CWE-798",
                owasp="A02:2021 - Cryptographic Failures",
                endpoint_or_file=f.get("url"),
                evidence_sanitized=f.get("description"),  # já vem mascarado do legacy
                remediation=f.get("recommendation", ""),
                plugin_name=self.name,
            )
            for f in raw.get("findings", [])
        ]

from __future__ import annotations

from ..base import Confidence, Finding, ScanContext, ScannerPlugin, Severity
from ..registry import register
from ..legacy.headers_check import check_headers


@register
class HeadersPlugin(ScannerPlugin):
    name = "headers_check"
    version = "1.0.0"
    category = "web"
    requires_active_scan = False

    def run(self, context: ScanContext) -> list[Finding]:
        raw = check_headers(context.target_url, timeout=context.timeout_seconds)

        findings = []
        for f in raw.get("findings", []):
            findings.append(Finding(
                title=f["issue"],
                description=f.get("recommendation", ""),
                category="headers",
                severity=Severity(f["severity"]),
                confidence=Confidence.HIGH,
                owasp="A05:2021 - Security Misconfiguration",
                endpoint_or_file=raw.get("url"),
                remediation=f.get("recommendation", ""),
                plugin_name=self.name,
            ))
        return findings

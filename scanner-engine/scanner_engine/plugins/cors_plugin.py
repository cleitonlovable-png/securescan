from __future__ import annotations

from ..base import Confidence, Finding, ScanContext, ScannerPlugin, Severity
from ..registry import register
from ..legacy.cors_scan import check_cors


@register
class CorsPlugin(ScannerPlugin):
    name = "cors_check"
    version = "1.0.0"
    category = "web"
    requires_active_scan = False

    def run(self, context: ScanContext) -> list[Finding]:
        raw = check_cors(context.target_url, timeout=context.timeout_seconds)

        return [
            Finding(
                title=f["issue"],
                description=f.get("recommendation", ""),
                category="web",
                severity=Severity(f["severity"]),
                confidence=Confidence.HIGH,
                owasp="A05:2021 - Security Misconfiguration",
                endpoint_or_file=context.target_url,
                remediation=f.get("recommendation", ""),
                plugin_name=self.name,
            )
            for f in raw
        ]

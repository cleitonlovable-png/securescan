from __future__ import annotations

from ..base import Confidence, Finding, ScanContext, ScannerPlugin, Severity
from ..registry import register
from ..legacy.pii_exposure import scan_page_for_pii


@register
class PiiExposurePlugin(ScannerPlugin):
    name = "pii_exposure"
    version = "1.0.0"
    category = "web"
    requires_active_scan = False

    def run(self, context: ScanContext) -> list[Finding]:
        raw = scan_page_for_pii(context.target_url, timeout=context.timeout_seconds)

        return [
            Finding(
                title=f["issue"],
                description=f.get("recommendation", ""),
                category="pii_lgpd",
                severity=Severity(f["severity"]),
                confidence=Confidence.MEDIUM,
                owasp="A02:2021 - Cryptographic Failures",
                endpoint_or_file=f.get("url"),
                remediation=f.get("recommendation", ""),
                plugin_name=self.name,
            )
            for f in raw.get("findings", [])
        ]

from __future__ import annotations

from urllib.parse import urlparse

from ..base import Confidence, Finding, ScanContext, ScannerPlugin, Severity
from ..registry import register
from ..legacy.database_exposure import check_database_exposure


@register
class DatabaseExposurePlugin(ScannerPlugin):
    name = "database_exposure"
    version = "1.0.0"
    category = "database"
    requires_active_scan = False

    def run(self, context: ScanContext) -> list[Finding]:
        host = urlparse(context.target_url).hostname or context.target_url
        raw = check_database_exposure(host)

        return [
            Finding(
                title=f["issue"],
                description=f.get("recommendation", ""),
                category="database",
                severity=Severity(f["severity"]),
                confidence=Confidence.HIGH,
                cwe="CWE-306",
                owasp="A05:2021 - Security Misconfiguration",
                endpoint_or_file=f.get("url"),
                remediation=f.get("recommendation", ""),
                plugin_name=self.name,
            )
            for f in raw.get("findings", [])
        ]

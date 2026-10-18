from __future__ import annotations

from ..base import Confidence, Finding, ScanContext, ScannerPlugin, Severity
from ..registry import register
from ..legacy.exposed_files import check_exposed_files


@register
class ExposedFilesPlugin(ScannerPlugin):
    name = "exposed_files"
    version = "1.0.0"
    category = "web"
    requires_active_scan = False

    def run(self, context: ScanContext) -> list[Finding]:
        raw = check_exposed_files(context.target_url, timeout=context.timeout_seconds)

        return [
            Finding(
                title=f["issue"],
                description=f.get("recommendation", ""),
                category="exposed_files",
                severity=Severity(f["severity"]),
                confidence=Confidence.HIGH,
                cwe="CWE-538",
                owasp="A05:2021 - Security Misconfiguration",
                endpoint_or_file=f.get("url"),
                remediation=f.get("recommendation", ""),
                plugin_name=self.name,
            )
            for f in raw.get("findings", [])
        ]

from __future__ import annotations

from ..base import Confidence, Finding, ScanContext, ScannerPlugin, Severity
from ..registry import register
from ..legacy.storage_bucket_scan import check_public_bucket


@register
class StorageBucketPlugin(ScannerPlugin):
    name = "storage_bucket_scan"
    version = "1.0.0"
    category = "infra"
    requires_active_scan = False

    def run(self, context: ScanContext) -> list[Finding]:
        bucket_url = context.extra_config.get("bucket_url")
        if not bucket_url:
            return []

        raw = check_public_bucket(bucket_url, timeout=context.timeout_seconds)

        return [
            Finding(
                title=f["issue"],
                description=f.get("recommendation", ""),
                category="infra",
                severity=Severity(f["severity"]),
                confidence=Confidence.HIGH,
                endpoint_or_file=bucket_url,
                remediation=f.get("recommendation", ""),
                plugin_name=self.name,
            )
            for f in raw
        ]

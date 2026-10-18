from __future__ import annotations

from ..base import Confidence, Finding, ScanContext, ScannerPlugin, Severity
from ..registry import register
from ..legacy.session_cookie_scan import check_session_cookies


@register
class SessionCookiePlugin(ScannerPlugin):
    name = "session_cookie_check"
    version = "1.0.0"
    category = "web"
    requires_active_scan = False

    def run(self, context: ScanContext) -> list[Finding]:
        raw = check_session_cookies(context.target_url, timeout=context.timeout_seconds)

        return [
            Finding(
                title=f["issue"],
                description=f.get("recommendation", ""),
                category="web",
                severity=Severity(f["severity"]),
                confidence=Confidence.HIGH,
                cwe="CWE-1004" if "HttpOnly" in f["issue"] else "CWE-614",
                owasp="A05:2021 - Security Misconfiguration",
                endpoint_or_file=context.target_url,
                remediation=f.get("recommendation", ""),
                plugin_name=self.name,
            )
            for f in raw
        ]

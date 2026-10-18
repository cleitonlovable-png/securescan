from __future__ import annotations

from ..base import Confidence, Finding, ScanContext, ScannerPlugin, Severity
from ..registry import register
from ..legacy.payment_security_scan import check_checkout_page


@register
class PaymentSecurityPlugin(ScannerPlugin):
    name = "payment_security_scan"
    version = "1.0.0"
    category = "payments"
    requires_active_scan = False  # só lê a página publicamente acessível, não faz nenhuma transação

    def run(self, context: ScanContext) -> list[Finding]:
        raw = check_checkout_page(context.target_url, timeout=context.timeout_seconds)

        return [
            Finding(
                title=f["issue"],
                description=f.get("recommendation", ""),
                category="payments",
                severity=Severity(f["severity"]),
                confidence=Confidence.MEDIUM,
                owasp="A04:2021 - Insecure Design",
                endpoint_or_file=context.target_url,
                remediation=f.get("recommendation", ""),
                plugin_name=self.name,
            )
            for f in raw
        ]

from __future__ import annotations

from ..base import Confidence, Finding, ScanContext, ScannerPlugin, Severity
from ..registry import register
from ..legacy.rate_limit_scan import check_rate_limit


@register
class RateLimitPlugin(ScannerPlugin):
    name = "rate_limit_scan"
    version = "1.0.0"
    category = "access_control"
    requires_active_scan = True  # manda requisições repetidas — é um teste ativo

    def run(self, context: ScanContext) -> list[Finding]:
        if not context.requires_active_scan_allowed:
            return [Finding(
                title="Teste de rate limiting não executado — domínio não verificado",
                description="Este plugin manda requisições repetidas contra um endpoint e só "
                             "roda em domínios com autorização confirmada.",
                category="access_control",
                severity=Severity.INFO,
                plugin_name=self.name,
            )]

        test_url = context.extra_config.get("rate_limit_test_url")
        if not test_url:
            return []  # opcional — só roda se o usuário informou o endpoint

        method = context.extra_config.get("rate_limit_method", "POST")
        attempts = int(context.extra_config.get("rate_limit_attempts", 15))

        raw = check_rate_limit(test_url, method=method, attempts=attempts, timeout=context.timeout_seconds)

        return [
            Finding(
                title=f["issue"],
                description=f.get("recommendation", ""),
                category="access_control",
                severity=Severity(f["severity"]),
                confidence=Confidence.HIGH,
                owasp="API4:2023 - Unrestricted Resource Consumption",
                endpoint_or_file=test_url,
                remediation=f.get("recommendation", ""),
                plugin_name=self.name,
            )
            for f in raw.get("findings", [])
        ]

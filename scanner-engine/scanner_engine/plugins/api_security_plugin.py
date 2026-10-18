from __future__ import annotations

from ..base import Confidence, Finding, ScanContext, ScannerPlugin, Severity
from ..registry import register
from ..legacy.api_security_scan import check_openapi_spec, check_graphql_introspection


@register
class ApiSecurityPlugin(ScannerPlugin):
    name = "api_security_scan"
    version = "1.0.0"
    category = "api_security"
    requires_active_scan = False  # lê a especificação pública, não ataca endpoints

    def run(self, context: ScanContext) -> list[Finding]:
        openapi_url = context.extra_config.get("openapi_url")
        graphql_url = context.extra_config.get("graphql_url")

        if not openapi_url and not graphql_url:
            return []  # opcional — só roda se algo foi informado

        raw_findings = []
        if openapi_url:
            raw_findings.extend(check_openapi_spec(openapi_url, timeout=context.timeout_seconds))
        if graphql_url:
            raw_findings.extend(check_graphql_introspection(graphql_url, timeout=context.timeout_seconds))

        return [
            Finding(
                title=f["issue"],
                description=f.get("recommendation", ""),
                category="api_security",
                severity=Severity(f["severity"]),
                confidence=Confidence.MEDIUM,
                owasp="API1:2023 - Broken Object Level Authorization" if "autenticação" in f["issue"].lower() else None,
                remediation=f.get("recommendation", ""),
                plugin_name=self.name,
            )
            for f in raw_findings
        ]

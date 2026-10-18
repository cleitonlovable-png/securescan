from __future__ import annotations

from ..base import Confidence, Finding, ScanContext, ScannerPlugin, Severity
from ..registry import register
from ..legacy.tech_fingerprint import fingerprint


@register
class TechFingerprintPlugin(ScannerPlugin):
    name = "tech_fingerprint"
    version = "1.0.0"
    category = "web"
    requires_active_scan = False

    def run(self, context: ScanContext) -> list[Finding]:
        result = fingerprint(context.target_url, timeout=context.timeout_seconds)

        if "error" in result:
            return []

        techs = result.get("detected_technologies", [])
        if not techs:
            return []

        # isto não é uma vulnerabilidade em si — é informativo, usado para
        # popular Project.framework e para decidir quais outros plugins fazem sentido
        return [Finding(
            title=f"Tecnologias identificadas: {', '.join(techs)}",
            description="Identificação passiva via headers e assinaturas no HTML.",
            category="fingerprint",
            severity=Severity.INFO,
            confidence=Confidence.MEDIUM,
            evidence_sanitized=f"Server: {result.get('server_header')}",
            plugin_name=self.name,
        )]

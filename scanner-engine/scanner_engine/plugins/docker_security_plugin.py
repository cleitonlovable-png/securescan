from __future__ import annotations

from ..base import Confidence, Finding, ScanContext, ScannerPlugin, Severity
from ..registry import register
from ..legacy.docker_security_scan import analyze_dockerfile


@register
class DockerSecurityPlugin(ScannerPlugin):
    name = "docker_security_scan"
    version = "1.0.0"
    category = "infra"
    requires_active_scan = False

    def run(self, context: ScanContext) -> list[Finding]:
        dockerfile_content = context.extra_config.get("dockerfile_content")
        if not dockerfile_content:
            return []  # opcional — só roda se o usuário colou o conteúdo

        raw = analyze_dockerfile(dockerfile_content)

        return [
            Finding(
                title=f["issue"],
                description=f.get("recommendation", ""),
                category="infra",
                severity=Severity(f["severity"]) if f["severity"] != "info" else Severity.INFO,
                confidence=Confidence.HIGH,
                remediation=f.get("recommendation", ""),
                plugin_name=self.name,
            )
            for f in raw
        ]

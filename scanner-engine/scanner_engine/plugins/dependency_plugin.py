from __future__ import annotations

from ..base import Confidence, Finding, ScanContext, ScannerPlugin, Severity
from ..registry import register
from ..legacy.dependency_check import check_dependencies


@register
class DependencyPlugin(ScannerPlugin):
    name = "dependency_check"
    version = "1.0.0"
    category = "dependencies"
    requires_active_scan = False

    def run(self, context: ScanContext) -> list[Finding]:
        requirements_path = context.extra_config.get("requirements_path")
        if not requirements_path:
            return []  # opcional — só roda se o projeto informou o caminho

        try:
            raw = check_dependencies(requirements_path)
        except FileNotFoundError as e:
            return [Finding(
                title="Arquivo de dependências não encontrado",
                description=str(e),
                category="dependencies",
                severity=Severity.INFO,
                plugin_name=self.name,
            )]

        return [
            Finding(
                title=f["issue"],
                description=f.get("description", ""),
                category="dependencies",
                severity=Severity(f["severity"]),
                confidence=Confidence.HIGH,
                owasp="A06:2021 - Vulnerable and Outdated Components",
                remediation=f.get("recommendation", ""),
                plugin_name=self.name,
            )
            for f in raw.get("findings", [])
        ]

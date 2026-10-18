from __future__ import annotations

from ..base import Confidence, Finding, ScanContext, ScannerPlugin, Severity
from ..registry import register
from ..legacy.semgrep_scan import is_available, run_semgrep_scan


@register
class SemgrepPlugin(ScannerPlugin):
    name = "semgrep_scan"
    version = "1.0.0"
    category = "code"
    requires_active_scan = False  # lê código-fonte, não ataca o servidor em produção

    def health_check(self) -> bool:
        return is_available()

    def run(self, context: ScanContext) -> list[Finding]:
        repo_url = context.extra_config.get("repo_url")
        if not repo_url:
            return []  # opcional — só roda se um repositório foi informado

        if not self.health_check():
            return [Finding(
                title="Análise de código não executada — Semgrep/git não instalados",
                description="O worker precisa ter os binários 'git' e 'semgrep' disponíveis.",
                category="code",
                severity=Severity.INFO,
                plugin_name=self.name,
            )]

        branch = context.extra_config.get("repo_branch")

        try:
            raw = run_semgrep_scan(repo_url, branch=branch, timeout=context.timeout_seconds * 60 or 600)
        except RuntimeError as e:
            return [Finding(
                title="Não foi possível concluir a análise de código",
                description=str(e)[:400],
                category="code",
                severity=Severity.INFO,
                plugin_name=self.name,
            )]

        findings = []
        for f in raw.get("findings", []):
            findings.append(Finding(
                title=f["issue"],
                description=f.get("description", ""),
                category="code",
                severity=Severity(f["severity"]),
                confidence=Confidence.MEDIUM,
                cwe=f.get("cwe"),
                owasp=f.get("owasp"),
                endpoint_or_file=f.get("file"),
                remediation=f.get("recommendation", ""),
                plugin_name=self.name,
            ))
        return findings

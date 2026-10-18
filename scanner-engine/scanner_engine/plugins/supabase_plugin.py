from __future__ import annotations

from ..base import Confidence, Finding, ScanContext, ScannerPlugin, Severity
from ..registry import register
from ..legacy.supabase_scan import run_supabase_scan


@register
class SupabasePlugin(ScannerPlugin):
    name = "supabase_scan"
    version = "1.0.0"
    category = "database"
    requires_active_scan = False  # usa só a anon key, que é pública por design

    def run(self, context: ScanContext) -> list[Finding]:
        project_url = context.extra_config.get("supabase_url")
        anon_key = context.extra_config.get("supabase_anon_key")

        if not project_url or not anon_key:
            return []

        raw = run_supabase_scan(project_url, anon_key, timeout=context.timeout_seconds)

        return [
            Finding(
                title=f["issue"],
                description=f.get("recommendation", ""),
                category="database",
                severity=Severity(f["severity"]),
                confidence=Confidence.MEDIUM,  # sempre exige confirmação manual — dado público pode ser intencional
                owasp="A01:2021 - Broken Access Control",
                remediation=f.get("recommendation", ""),
                plugin_name=self.name,
            )
            for f in raw.get("findings", [])
        ]

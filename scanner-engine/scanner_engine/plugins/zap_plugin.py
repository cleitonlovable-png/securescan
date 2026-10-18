from __future__ import annotations

from ..base import Confidence, Finding, ScanContext, ScannerPlugin, Severity
from ..registry import register
from ..legacy.zap_client import ZapClient


@register
class ZapActiveScanPlugin(ScannerPlugin):
    name = "zap_active_scan"
    version = "1.0.0"
    category = "web"
    requires_active_scan = True  # envia payloads reais de ataque

    def health_check(self) -> bool:
        from ..legacy.zap_client import ZAPv2
        return ZAPv2 is not None

    def run(self, context: ScanContext) -> list[Finding]:
        if not context.requires_active_scan_allowed:
            return [Finding(
                title="Teste de invasão (ZAP) não executado — domínio não verificado",
                description="Este plugin envia payloads reais de ataque e só roda em domínios "
                             "com autorização confirmada (VERIFIED ou PRIVATE_ENVIRONMENT).",
                category="web",
                severity=Severity.INFO,
                plugin_name=self.name,
            )]

        zap_api_key = context.extra_config.get("zap_api_key")
        if not zap_api_key:
            return [Finding(
                title="Teste de invasão (ZAP) não executado — chave de API não informada",
                description="Informe a chave da API do OWASP ZAP para habilitar este teste.",
                category="web",
                severity=Severity.INFO,
                plugin_name=self.name,
            )]

        if not self.health_check():
            return [Finding(
                title="Lib do OWASP ZAP não instalada no worker",
                description="python-owasp-zap-v2.4 não está disponível.",
                category="web",
                severity=Severity.INFO,
                plugin_name=self.name,
            )]

        import os
        default_proxy = (
            "http://127.0.0.1:8080"
            if os.environ.get("ENVIRONMENT") == "desktop" or os.environ.get("QUEUE_BACKEND") == "local"
            else "http://host.docker.internal:8080"
        )
        zap_proxy = context.extra_config.get("zap_proxy", default_proxy)

        try:
            client = ZapClient(api_key=zap_api_key, zap_proxy=zap_proxy)

            def on_progress(pct: int, label: str) -> None:
                if context.progress_callback:
                    context.progress_callback(pct, label)

            client.spider(context.target_url, progress_callback=on_progress)
            client.active_scan(context.target_url, progress_callback=on_progress)
            raw_alerts = client.get_alerts(context.target_url)
        except Exception as e:
            return [Finding(
                title="Não foi possível conectar ao OWASP ZAP",
                description=f"Verifique se o OWASP ZAP está aberto na sua máquina na porta 8080 "
                             f"({zap_proxy}) e se a chave de API está correta. Erro: {str(e)[:200]}",
                category="web",
                severity=Severity.INFO,
                plugin_name=self.name,
            )]


        findings = []
        for alert in raw_alerts:
            severity = ZapClient._map_risk(alert.get("risk", "Informational"))
            findings.append(Finding(
                title=alert.get("alert", "Achado do ZAP"),
                description=(alert.get("description") or "")[:500],
                category="web",
                severity=Severity(severity),
                confidence=Confidence.MEDIUM,
                cwe=f"CWE-{alert['cweid']}" if alert.get("cweid") else None,
                owasp="A03:2021 - Injection" if "injection" in alert.get("alert", "").lower() else None,
                endpoint_or_file=alert.get("url"),
                remediation=(alert.get("solution") or "")[:400],
                plugin_name=self.name,
            ))
        return findings

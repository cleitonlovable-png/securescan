"""Gera um relatório HTML autocontido a partir dos Findings de um scan."""

from __future__ import annotations

from datetime import datetime
from html import escape

from app.models.finding import Finding

SEVERITY_RANK = {"critical": 0, "high": 1, "medium": 2, "low": 3, "info": 4}
SEVERITY_LABEL_PT = {"critical": "Crítica", "high": "Alta", "medium": "Média", "low": "Baixa", "info": "Info"}
SEVERITY_COLOR = {"critical": "#dc2626", "high": "#ea580c", "medium": "#d97706", "low": "#65a30d", "info": "#6b7280"}

TEMPLATE = """<!DOCTYPE html>
<html lang="pt-BR"><head><meta charset="UTF-8"><title>Relatório de Segurança — {target}</title>
<style>
body {{ font-family: -apple-system, sans-serif; background:#f8fafc; color:#1e293b; padding:32px; max-width:900px; margin:0 auto; }}
h1 {{ font-size:22px; }} .meta {{ color:#64748b; font-size:13px; margin-bottom:24px; }}
.finding {{ border-left:4px solid #cbd5e1; background:#fff; padding:14px 18px; margin-bottom:10px; border-radius:0 8px 8px 0; }}
.badge {{ font-size:11px; font-weight:700; text-transform:uppercase; padding:2px 10px; border-radius:999px; color:#fff; float:right; }}
.rec {{ background:#eef2ff; padding:8px 12px; border-radius:6px; margin-top:8px; font-size:13px; }}
</style></head><body>
<h1>Relatório de Segurança</h1>
<div class="meta">Alvo: {target} · Gerado em: {generated_at}</div>
{findings_html}
</body></html>"""


def generate_scan_html(target: str, findings: list[Finding]) -> str:
    sorted_findings = sorted(
        findings,
        key=lambda f: SEVERITY_RANK.get(f.severity.value if hasattr(f.severity, "value") else f.severity, 99),
    )

    blocks = []
    for f in sorted_findings:
        sev = f.severity.value if hasattr(f.severity, "value") else f.severity
        color = SEVERITY_COLOR.get(sev, "#6b7280")
        block = f'''<div class="finding" style="border-left-color:{color}">
<span class="badge" style="background:{color}">{SEVERITY_LABEL_PT.get(sev, sev)}</span>
<strong>{escape(f.title)}</strong>
<p>{escape(f.description or "")}</p>
{f'<div class="rec"><b>Recomendação:</b> {escape(f.remediation)}</div>' if f.remediation else ""}
</div>'''
        blocks.append(block)

    findings_html = "\n".join(blocks) if blocks else "<p>Nenhum achado registrado.</p>"

    return TEMPLATE.format(
        target=escape(target),
        generated_at=datetime.now().strftime("%d/%m/%Y %H:%M"),
        findings_html=findings_html,
    )

"""
Gera o relatório em PDF de um scan a partir dos Findings salvos no banco.

Formato pensado para ser fácil de colar em uma IA depois e pedir correções:
texto limpo, sem HTML, cada achado numerado com severidade e recomendação.
"""

from __future__ import annotations

from datetime import datetime
from io import BytesIO

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle

from app.models.finding import Finding

SEVERITY_RANK = {"critical": 0, "high": 1, "medium": 2, "low": 3, "info": 4}
SEVERITY_LABEL_PT = {"critical": "Crítica", "high": "Alta", "medium": "Média", "low": "Baixa", "info": "Info"}
SEVERITY_HEX = {"critical": "#dc2626", "high": "#ea580c", "medium": "#d97706", "low": "#65a30d", "info": "#6b7280"}


def _build_styles():
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name="ReportTitle", fontSize=20, leading=24, spaceAfter=4,
                               textColor=colors.HexColor("#0f172a"), fontName="Helvetica-Bold"))
    styles.add(ParagraphStyle(name="Meta", fontSize=9.5, leading=13, textColor=colors.HexColor("#64748b")))
    styles.add(ParagraphStyle(name="SectionHeading", fontSize=13, leading=16, spaceBefore=18, spaceAfter=8,
                               textColor=colors.HexColor("#0f172a"), fontName="Helvetica-Bold"))
    styles.add(ParagraphStyle(name="FindingTitle", fontSize=11, leading=14, spaceAfter=2,
                               textColor=colors.HexColor("#0f172a"), fontName="Helvetica-Bold"))
    styles.add(ParagraphStyle(name="FindingBody", fontSize=9.5, leading=13.5,
                               textColor=colors.HexColor("#334155"), spaceAfter=2))
    styles.add(ParagraphStyle(name="FindingRec", fontSize=9.5, leading=13.5,
                               textColor=colors.HexColor("#0f172a"), backColor=colors.HexColor("#eef2ff"),
                               borderPadding=6, spaceAfter=2))
    styles.add(ParagraphStyle(name="FindingMeta", fontSize=8, leading=11, textColor=colors.HexColor("#94a3b8")))
    return styles


def _severity_summary_table(counts: dict[str, int], styles) -> Table:
    keys = ["critical", "high", "medium", "low"]
    labels = [SEVERITY_LABEL_PT[k] for k in keys]
    values = [str(counts.get(k, 0)) for k in keys]

    table = Table([labels, values], colWidths=[4 * cm] * 4)
    style_commands = [
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"), ("FONTSIZE", (0, 0), (-1, 0), 9),
        ("FONTSIZE", (0, 1), (-1, 1), 16), ("FONTNAME", (0, 1), (-1, 1), "Helvetica-Bold"),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#64748b")), ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 4), ("TOPPADDING", (0, 1), (-1, 1), 2),
        ("BOTTOMPADDING", (0, 1), (-1, 1), 10), ("LINEBELOW", (0, 0), (-1, 0), 0.5, colors.HexColor("#e2e8f0")),
    ]
    for i, key in enumerate(keys):
        style_commands.append(("TEXTCOLOR", (i, 1), (i, 1), colors.HexColor(SEVERITY_HEX[key])))
    table.setStyle(TableStyle(style_commands))
    return table


def _render_finding(index: int, finding: Finding, styles) -> list:
    severity = finding.severity.value if hasattr(finding.severity, "value") else finding.severity
    elements = [Paragraph(
        f'<font color="{SEVERITY_HEX.get(severity, "#6b7280")}">●</font> '
        f'[{SEVERITY_LABEL_PT.get(severity, severity).upper()}] {index}. {finding.title}',
        styles["FindingTitle"],
    )]
    if finding.description:
        elements.append(Paragraph(finding.description, styles["FindingBody"]))
    if finding.remediation:
        elements.append(Paragraph(f"<b>Recomendação:</b> {finding.remediation}", styles["FindingRec"]))

    meta_parts = [p for p in [
        f"Módulo: {finding.plugin_name}" if finding.plugin_name else "",
        f"Local: {finding.endpoint_or_file}" if finding.endpoint_or_file else "",
    ] if p]
    if meta_parts:
        elements.append(Paragraph(" · ".join(meta_parts), styles["FindingMeta"]))

    elements.append(Spacer(1, 10))
    return elements


def generate_scan_pdf(target: str, findings: list[Finding]) -> bytes:
    buffer = BytesIO()
    styles = _build_styles()
    doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=2 * cm, bottomMargin=2 * cm,
                             leftMargin=2 * cm, rightMargin=2 * cm)

    sorted_findings = sorted(
        findings,
        key=lambda f: SEVERITY_RANK.get(f.severity.value if hasattr(f.severity, "value") else f.severity, 99),
    )

    counts: dict[str, int] = {}
    for f in findings:
        sev = f.severity.value if hasattr(f.severity, "value") else f.severity
        counts[sev] = counts.get(sev, 0) + 1

    story = [
        Paragraph("Relatório de Segurança", styles["ReportTitle"]),
        Paragraph(f"Alvo: {target}", styles["Meta"]),
        Paragraph(f"Gerado em: {datetime.now().strftime('%d/%m/%Y %H:%M')}", styles["Meta"]),
        Spacer(1, 16),
        _severity_summary_table(counts, styles),
        Spacer(1, 8),
        Paragraph("Achados detalhados e recomendações", styles["SectionHeading"]),
    ]

    if sorted_findings:
        for i, finding in enumerate(sorted_findings, start=1):
            story.extend(_render_finding(i, finding, styles))
    else:
        story.append(Paragraph("Nenhum achado registrado.", styles["FindingBody"]))

    story.append(Spacer(1, 20))
    story.append(Paragraph(
        "Relatório gerado automaticamente pelo SecureScan. Uso restrito a sistemas de "
        "sua propriedade ou com autorização documentada.",
        styles["FindingMeta"],
    ))

    doc.build(story)
    buffer.seek(0)
    return buffer.read()

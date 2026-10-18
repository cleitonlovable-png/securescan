"""
Relatório Executivo — Seção 30 do documento original.

Diferente do relatório técnico (PDF/HTML/CSV já existentes, com endpoint,
CWE, evidência), o executivo é enxuto: score, resumo, principais riscos e
prioridades. Pensado pra mandar pra alguém que não é técnico.
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
from app.services.scoring import calculate_security_score, score_label

SEVERITY_RANK = {"critical": 0, "high": 1, "medium": 2, "low": 3, "info": 4}
SEVERITY_LABEL_PT = {"critical": "Crítica", "high": "Alta", "medium": "Média", "low": "Baixa", "info": "Info"}


def _severity_counts(findings: list[Finding]) -> dict:
    counts: dict = {}
    for f in findings:
        sev = f.severity.value if hasattr(f.severity, "value") else f.severity
        counts[sev] = counts.get(sev, 0) + 1
    return counts


def generate_executive_pdf(target: str, findings: list[Finding]) -> bytes:
    buffer = BytesIO()
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name="ExecTitle", fontSize=22, fontName="Helvetica-Bold", textColor=colors.HexColor("#0f172a")))
    styles.add(ParagraphStyle(name="ExecMeta", fontSize=10, textColor=colors.HexColor("#64748b"), spaceAfter=12))
    styles.add(ParagraphStyle(name="ExecScore", fontSize=36, fontName="Helvetica-Bold", spaceAfter=4, alignment=1))
    styles.add(ParagraphStyle(name="ExecLabel", fontSize=13, textColor=colors.HexColor("#334155"), spaceAfter=16, alignment=1))
    styles.add(ParagraphStyle(name="ExecHeading", fontSize=13, fontName="Helvetica-Bold", spaceBefore=14, spaceAfter=8))
    styles.add(ParagraphStyle(name="ExecItem", fontSize=10.5, textColor=colors.HexColor("#334155"), spaceAfter=4))

    doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=2.5 * cm, bottomMargin=2.5 * cm,
                             leftMargin=2.5 * cm, rightMargin=2.5 * cm)

    counts = _severity_counts(findings)
    score = calculate_security_score(counts) if counts else 100
    label = score_label(score)
    score_hex = "#16a34a" if score >= 75 else "#d97706" if score >= 50 else "#dc2626"

    sorted_findings = sorted(
        findings,
        key=lambda f: SEVERITY_RANK.get(f.severity.value if hasattr(f.severity, "value") else f.severity, 99),
    )
    top_risks = sorted_findings[:5]

    story = [
        Paragraph("Relatório Executivo de Segurança", styles["ExecTitle"]),
        Paragraph(f"Alvo: {target} · Gerado em {datetime.now().strftime('%d/%m/%Y %H:%M')}", styles["ExecMeta"]),
        Spacer(1, 10),
        Paragraph(f'<font color="{score_hex}">{score}</font>/100', styles["ExecScore"]),
        Paragraph(label, styles["ExecLabel"]),
    ]

    counts_line = " · ".join(
        f"{counts.get(k, 0)} {SEVERITY_LABEL_PT[k].lower()}" for k in ["critical", "high", "medium", "low"]
    )
    story.append(Paragraph(f"Resumo: {counts_line}", styles["ExecItem"]))

    story.append(Paragraph("Principais riscos", styles["ExecHeading"]))
    if top_risks:
        for f in top_risks:
            sev = f.severity.value if hasattr(f.severity, "value") else f.severity
            story.append(Paragraph(f"• [{SEVERITY_LABEL_PT.get(sev, sev)}] {f.title}", styles["ExecItem"]))
    else:
        story.append(Paragraph("Nenhum risco relevante identificado.", styles["ExecItem"]))

    story.append(Paragraph("Prioridades recomendadas", styles["ExecHeading"]))
    if counts.get("critical", 0) > 0:
        story.append(Paragraph("• Corrigir os achados críticos imediatamente — risco de comprometimento total.", styles["ExecItem"]))
    if counts.get("high", 0) > 0:
        story.append(Paragraph("• Priorizar os achados altos antes do próximo deploy em produção.", styles["ExecItem"]))
    if not counts.get("critical") and not counts.get("high"):
        story.append(Paragraph("• Nenhuma ação urgente — manter o hábito de escanear periodicamente.", styles["ExecItem"]))

    doc.build(story)
    buffer.seek(0)
    return buffer.read()

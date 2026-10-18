"""Gera um relatório CSV a partir dos Findings de um scan."""

from __future__ import annotations

import csv
import io

from app.models.finding import Finding


def generate_scan_csv(findings: list[Finding]) -> str:
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(["Severidade", "Título", "Categoria", "Plugin", "Descrição", "Recomendação", "Local"])

    for f in findings:
        sev = f.severity.value if hasattr(f.severity, "value") else f.severity
        writer.writerow([
            sev, f.title, f.category, f.plugin_name,
            f.description or "", f.remediation or "", f.endpoint_or_file or "",
        ])

    return buffer.getvalue()

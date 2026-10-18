from __future__ import annotations

from app.models.enums import Severity

# Seção 25 do prompt original: não é só contar vulnerabilidades, é ponderar
# por severidade, com decaimento para não punir infinitamente projetos com
# muitos achados de baixo risco.
SEVERITY_PENALTY = {
    Severity.CRITICAL: 25,
    Severity.HIGH: 12,
    Severity.MEDIUM: 5,
    Severity.LOW: 2,
    Severity.INFO: 0,
}

SEVERITY_CAP = {
    Severity.CRITICAL: 100,   # uma única crítica já pode derrubar bastante o score
    Severity.HIGH: 60,
    Severity.MEDIUM: 30,
    Severity.LOW: 15,
    Severity.INFO: 0,
}


def calculate_security_score(severity_counts: dict[Severity, int]) -> int:
    """
    Score de 0 a 100. Cada severidade tem um teto de penalidade (evita que
    50 achados 'low' derrubem o score tanto quanto 2 'critical').
    """
    total_penalty = 0.0
    for severity, count in severity_counts.items():
        penalty_per_item = SEVERITY_PENALTY.get(severity, 0)
        cap = SEVERITY_CAP.get(severity, 0)
        total_penalty += min(count * penalty_per_item, cap)

    score = max(0, 100 - int(total_penalty))
    return score


def score_label(score: int) -> str:
    """Seção 25 do prompt original — faixas de classificação."""
    if score >= 90:
        return "Excelente"
    if score >= 75:
        return "Bom"
    if score >= 50:
        return "Atenção"
    if score >= 25:
        return "Alto risco"
    return "Crítico"

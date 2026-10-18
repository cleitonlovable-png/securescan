"""
Contrato base para todo plugin de scanner do SecureScan.

Nenhum plugin sabe nada sobre FastAPI, PostgreSQL ou o worker que o chama.
Ele recebe um ScanContext e devolve uma lista de Finding — só isso.
Ver docs/SCANNER_ENGINE.md para o racional completo.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Callable


class Severity(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class Confidence(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass
class ScanContext:
    """Tudo que um plugin pode precisar para rodar, de forma padronizada."""

    target_url: str
    scope_hosts: list[str]                     # hosts autorizados (domínio + subdomínios)
    rate_limit_rps: int = 10
    timeout_seconds: int = 8
    requires_active_scan_allowed: bool = False  # domínio VERIFIED ou PRIVATE_ENVIRONMENT
    extra_config: dict = field(default_factory=dict)  # parâmetros específicos do plugin
    progress_callback: Callable[[int, str], None] | None = None  # progresso fino DENTRO de um plugin


@dataclass
class Finding:
    """Formato universal de achado — todo plugin retorna isto."""

    title: str
    description: str
    category: str
    severity: Severity
    confidence: Confidence = Confidence.HIGH
    cwe: str | None = None
    owasp: str | None = None
    endpoint_or_file: str | None = None
    evidence_sanitized: str | None = None
    impact: str = ""
    remediation: str = ""
    references: list[str] = field(default_factory=list)
    plugin_name: str = ""

    def to_dict(self) -> dict:
        return {
            "title": self.title,
            "description": self.description,
            "category": self.category,
            "severity": self.severity.value if isinstance(self.severity, Severity) else self.severity,
            "confidence": self.confidence.value if isinstance(self.confidence, Confidence) else self.confidence,
            "cwe": self.cwe,
            "owasp": self.owasp,
            "endpoint_or_file": self.endpoint_or_file,
            "evidence_sanitized": self.evidence_sanitized,
            "impact": self.impact,
            "remediation": self.remediation,
            "references": self.references,
            "plugin_name": self.plugin_name,
        }


class ScannerPlugin(ABC):
    """Todo plugin de scanner implementa esta interface."""

    name: str = "unnamed_plugin"
    version: str = "1.0.0"
    category: str = "web"  # web | api | database | secrets | infra | access_control | dependencies
    requires_active_scan: bool = False

    def health_check(self) -> bool:
        """Confirma que dependências externas (binários, libs) estão disponíveis.
        Padrão: sempre saudável. Sobrescrever quando o plugin depender de algo externo."""
        return True

    @abstractmethod
    def run(self, context: ScanContext) -> list[Finding]:
        """Executa a análise e retorna achados já normalizados."""
        raise NotImplementedError

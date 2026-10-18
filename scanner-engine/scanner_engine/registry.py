"""
Registro central de plugins. O worker consulta este registro para saber
quais plugins existem e quais rodar para cada tipo de scan.
"""

from __future__ import annotations

from .base import ScannerPlugin

_REGISTRY: dict[str, type[ScannerPlugin]] = {}


def register(plugin_cls: type[ScannerPlugin]) -> type[ScannerPlugin]:
    """Decorator: uso @register acima da classe do plugin."""
    _REGISTRY[plugin_cls.name] = plugin_cls
    return plugin_cls


def get_plugin(name: str) -> type[ScannerPlugin] | None:
    return _REGISTRY.get(name)


def all_plugins() -> dict[str, type[ScannerPlugin]]:
    return dict(_REGISTRY)


def plugins_for_scan_type(scan_type: str) -> list[type[ScannerPlugin]]:
    """
    Mapeia o tipo de scan (QUICK_SCAN, FULL_SCAN, etc) para o conjunto de
    plugins que devem rodar. Ver docs/DATABASE.md para a definição de
    scan_type e docs/SCANNER_ENGINE.md para a categoria de cada plugin.
    """
    passive_web = ["headers_check", "ssl_check", "tech_fingerprint", "cors_check", "session_cookie_check"]
    full_passive = passive_web + [
        "port_scan", "exposed_files", "secrets_scan",
        "database_exposure", "pii_exposure", "dependency_check",
    ]

    mapping = {
        "QUICK_SCAN": ["headers_check", "ssl_check", "tech_fingerprint"],
        "FULL_SCAN": full_passive,
        "INFRA_SCAN": ["port_scan", "ssl_check", "database_exposure", "docker_security_scan", "storage_bucket_scan"],
        "API_SCAN": ["idor_check", "api_security_scan", "rate_limit_scan"],
        "PENTEST_SCAN": ["zap_active_scan"],
        "CODE_SCAN": ["semgrep_scan"],
        "SUPABASE_SCAN": ["supabase_scan"],
        "CHECKOUT_SCAN": ["payment_security_scan"],
    }

    names = mapping.get(scan_type, passive_web)
    return [_REGISTRY[n] for n in names if n in _REGISTRY]


def import_all_plugins() -> None:
    """Importa o pacote plugins/ para que os decorators @register rodem."""
    from . import plugins  # noqa: F401

"""
Importa todos os módulos de plugin para que o decorator @register de cada
um rode e popule o registry central. Ver scanner-engine/registry.py.
"""

from . import (  # noqa: F401
    headers_plugin,
    ssl_plugin,
    port_scan_plugin,
    tech_fingerprint_plugin,
    exposed_files_plugin,
    secrets_plugin,
    database_exposure_plugin,
    pii_exposure_plugin,
    dependency_plugin,
    idor_plugin,
    zap_plugin,
    semgrep_plugin,
    api_security_plugin,
    docker_security_plugin,
    storage_bucket_plugin,
    supabase_plugin,
    payment_security_plugin,
    cors_plugin,
    session_cookie_plugin,
    rate_limit_plugin,
)

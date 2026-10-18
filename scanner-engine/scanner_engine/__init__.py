"""SecureScan Scanner Engine — biblioteca de plugins de scanner, independente do backend."""

from .base import ScannerPlugin, ScanContext, Finding, Severity, Confidence
from .registry import register, get_plugin, all_plugins, plugins_for_scan_type, import_all_plugins

__all__ = [
    "ScannerPlugin", "ScanContext", "Finding", "Severity", "Confidence",
    "register", "get_plugin", "all_plugins", "plugins_for_scan_type", "import_all_plugins",
]

"""
Módulo de reconhecimento: scan de portas via Nmap.

Requer o binário `nmap` instalado no sistema (não é uma lib pip que faz
scan sozinha — é um wrapper em cima do nmap real).

Instalação do nmap:
    Ubuntu/Debian: sudo apt install nmap
    macOS:         brew install nmap
    Windows:       https://nmap.org/download.html
"""

from __future__ import annotations

from dataclasses import dataclass


try:
    import nmap
except ImportError:
    nmap = None


@dataclass
class PortResult:
    port: int
    protocol: str
    state: str
    service: str
    version: str


def scan_ports(host: str, port_range: str = "1-1000", fast: bool = True) -> list[PortResult]:
    """
    Faz scan de portas TCP no host.

    fast=True usa a flag -F do nmap (top 100 portas, mais rápido).
    fast=False varre o port_range completo (mais lento, mais completo).
    """
    if nmap is None:
        raise RuntimeError(
            "python-nmap não instalado. Rode: pip install python-nmap "
            "e garanta que o binário 'nmap' está no PATH do sistema."
        )

    scanner = nmap.PortScanner()
    args = "-sV -F" if fast else f"-sV -p {port_range}"

    scanner.scan(host, arguments=args)

    results = []
    if host in scanner.all_hosts():
        for proto in scanner[host].all_protocols():
            ports = scanner[host][proto].keys()
            for port in ports:
                info = scanner[host][proto][port]
                results.append(
                    PortResult(
                        port=port,
                        protocol=proto,
                        state=info.get("state", "unknown"),
                        service=info.get("name", ""),
                        version=f"{info.get('product', '')} {info.get('version', '')}".strip(),
                    )
                )
    return results




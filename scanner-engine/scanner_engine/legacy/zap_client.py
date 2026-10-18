"""
Cliente para o OWASP ZAP — esta é a peça central do "teste de invasão".

O ZAP faz spider (mapeia o site) e depois active scan (envia payloads reais
de SQLi, XSS, path traversal, etc contra os parâmetros encontrados). É uma
ferramenta madura, usada profissionalmente, com anos de desenvolvimento —
por isso orquestramos ela em vez de reimplementar ataques do zero.

PRÉ-REQUISITOS:
1. Baixar o OWASP ZAP: https://www.zaproxy.org/download/
2. Rodar o ZAP em modo daemon com API habilitada:
   zap.sh -daemon -port 8080 -config api.key=SUA_CHAVE_AQUI
3. pip install python-owasp-zap-v2.4

Este módulo SÓ RODA em modo "active" e portanto exige que o alvo tenha
allow_active_scan: true no scope.yaml.
"""

from __future__ import annotations

import time


try:
    from zapv2 import ZAPv2
except ImportError:
    ZAPv2 = None


class ZapClient:
    def __init__(self, api_key: str, zap_proxy: str = "http://127.0.0.1:8080"):
        if ZAPv2 is None:
            raise RuntimeError(
                "Lib python-owasp-zap-v2.4 não instalada. Rode: "
                "pip install python-owasp-zap-v2.4"
            )
        self.zap = ZAPv2(
            apikey=api_key,
            proxies={"http": zap_proxy, "https": zap_proxy},
        )

    def spider(self, target: str, max_wait_seconds: int = 300, progress_callback=None) -> None:
        """Mapeia o site: descobre páginas, formulários e parâmetros."""
        scan_id = self.zap.spider.scan(target)

        waited = 0
        while waited < max_wait_seconds:
            pct = int(self.zap.spider.status(scan_id))
            if progress_callback:
                progress_callback(pct, "Mapeando páginas e formulários do site")
            if pct >= 100:
                break
            time.sleep(2)
            waited += 2

    def active_scan(self, target: str, max_wait_seconds: int = 1800, progress_callback=None) -> None:
        """
        Dispara o scan ativo: envia payloads reais de teste (SQLi, XSS,
        command injection, path traversal, etc) contra os endpoints mapeados.
        """
        scan_id = self.zap.ascan.scan(target)

        waited = 0
        while waited < max_wait_seconds:
            pct = int(self.zap.ascan.status(scan_id))
            if progress_callback:
                progress_callback(pct, "Testando vulnerabilidades (SQLi, XSS e outras)")
            if pct >= 100:
                break
            time.sleep(5)
            waited += 5

    def get_alerts(self, target: str) -> list[dict]:
        alerts = self.zap.core.alerts(baseurl=target)
        return alerts

    @staticmethod
    def _map_risk(zap_risk: str) -> str:
        mapping = {
            "High": "critical", "Medium": "high",
            "Low": "medium", "Informational": "low",
        }
        return mapping.get(zap_risk, "low")




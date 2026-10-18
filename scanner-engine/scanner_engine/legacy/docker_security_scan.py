"""
Análise estática de Dockerfile — Seção 18 do documento original.

Recebe o CONTEÚDO do Dockerfile como texto (o usuário cola, não precisamos
ter acesso ao repositório nem buildar a imagem) e verifica os problemas mais
comuns de segurança em containers.
"""

from __future__ import annotations

import re

SENSITIVE_PORTS = {22: "SSH", 23: "Telnet", 3389: "RDP", 3306: "MySQL", 5432: "PostgreSQL", 6379: "Redis"}
SECRET_KEYWORDS = re.compile(r"(password|senha|secret|api_key|token|private_key)", re.IGNORECASE)


def analyze_dockerfile(content: str) -> list[dict]:
    findings = []
    lines = [l.strip() for l in content.splitlines() if l.strip() and not l.strip().startswith("#")]

    has_user_instruction = any(l.upper().startswith("USER ") and "root" not in l.lower() for l in lines)
    has_healthcheck = any(l.upper().startswith("HEALTHCHECK") for l in lines)

    for line in lines:
        upper = line.upper()

        # FROM com tag "latest" ou sem tag (que também vira "latest")
        if upper.startswith("FROM"):
            image = line.split(None, 1)[1] if len(line.split()) > 1 else ""
            image = image.split(" AS ")[0].split(" as ")[0].strip()
            if ":latest" in image or (":" not in image and "@" not in image):
                findings.append({
                    "severity": "medium",
                    "issue": f"Imagem base usa tag 'latest' (ou nenhuma tag): {image}",
                    "recommendation": "Fixar uma versão específica da imagem (ex: node:20.11-slim) "
                                       "para builds reproduzíveis e previsíveis.",
                })

        # segredos em ENV/ARG
        if upper.startswith(("ENV ", "ARG ")) and SECRET_KEYWORDS.search(line):
            findings.append({
                "severity": "critical",
                "issue": f"Possível segredo declarado diretamente no Dockerfile: {line[:100]}",
                "recommendation": "Nunca colocar senhas/chaves em ENV ou ARG do Dockerfile — usar "
                                   "secrets do Docker/Kubernetes ou variáveis de ambiente injetadas no runtime.",
            })

        # portas sensíveis expostas
        if upper.startswith("EXPOSE"):
            for port_str in re.findall(r"\d+", line):
                port = int(port_str)
                if port in SENSITIVE_PORTS:
                    findings.append({
                        "severity": "high",
                        "issue": f"Porta sensível exposta no Dockerfile: {port} ({SENSITIVE_PORTS[port]})",
                        "recommendation": "Evitar expor portas administrativas/de banco diretamente "
                                           "do container. Usar rede interna do Docker Compose.",
                    })

        # comando ADD de URL remota (risco de supply chain)
        if upper.startswith("ADD") and ("http://" in line or "https://" in line):
            findings.append({
                "severity": "medium",
                "issue": f"ADD baixando arquivo remoto diretamente: {line[:100]}",
                "recommendation": "Preferir COPY com arquivos já verificados, ou baixar com checksum "
                                   "verificado explicitamente em um RUN.",
            })

    if not has_user_instruction:
        findings.append({
            "severity": "high",
            "issue": "Dockerfile não define um usuário não-root (instrução USER ausente).",
            "recommendation": "Adicionar 'USER appuser' (criando o usuário antes) para o container "
                               "não rodar como root — reduz o impacto de uma eventual falha de segurança.",
        })

    if not has_healthcheck:
        findings.append({
            "severity": "low",
            "issue": "Dockerfile não define HEALTHCHECK.",
            "recommendation": "Adicionar HEALTHCHECK para orquestradores conseguirem detectar "
                               "containers travados/não saudáveis automaticamente.",
        })

    return findings

# Contexto de build = raiz do monorepo (mesma razão do backend/Dockerfile)

FROM python:3.12-slim

WORKDIR /app

# nmap é necessário pelo plugin port_scan_plugin.py
# git é necessário pelo plugin semgrep_plugin.py (clona o repositório a analisar)
RUN apt-get update && apt-get install -y --no-install-recommends \
    nmap git \
    && rm -rf /var/lib/apt/lists/*

COPY workers/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY scanner-engine /scanner-engine
RUN pip install --no-cache-dir -e /scanner-engine

# o worker importa app.* do backend (models, config, session) para acessar o banco
COPY backend/ /backend/
RUN pip install --no-cache-dir -r /backend/requirements.txt

COPY workers/ .

CMD ["python", "worker.py"]

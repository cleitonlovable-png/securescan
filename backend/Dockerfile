# Este Dockerfile é construído com o CONTEXTO na raiz do monorepo
# (ver docker/docker-compose.yml: build.context = "..", build.dockerfile = "backend/Dockerfile"),
# para poder instalar o pacote scanner-engine que vive fora da pasta backend/.

FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY scanner-engine /scanner-engine
RUN pip install --no-cache-dir -e /scanner-engine

COPY backend/ .

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

# SecureScan — Arquitetura

## 1. Visão geral

SecureScan é uma plataforma de análise de segurança de aplicações web, APIs
e infraestrutura, organizada como um monorepo com quatro grandes blocos:

```
frontend/         Next.js + React + TypeScript + Tailwind — interface do usuário
backend/          FastAPI — API, autenticação, regras de negócio, persistência
workers/          Processos assíncronos (RQ) que executam os scans de verdade
scanner-engine/   Biblioteca de plugins de scanner, independente do backend
docker/           docker-compose.yml e Dockerfiles de cada serviço
docs/             Este conjunto de documentos
```

O backend NUNCA executa um scan diretamente dentro do processo da API.
Toda análise ativa roda em um **worker** separado, isolado, para que uma
varredura pesada (ou travada) nunca derrube a API nem consuma seus recursos.

## 2. Fluxo de alto nível

```
Usuário (frontend)
      │
      │  1. Cria projeto / cadastra domínio
      ▼
Backend (FastAPI) ──── grava em ──── PostgreSQL
      │
      │  2. Usuário clica em "Iniciar Varredura"
      ▼
Backend cria um registro Scan (status=PENDING) e enfileira um Job no Redis
      │
      ▼
Redis (fila) ──────────────────────► Worker (RQ)
                                          │
                                          │ 3. Worker carrega os plugins
                                          │    do scanner-engine relevantes
                                          │    para o tipo de scan pedido
                                          ▼
                                   scanner-engine/plugins/*
                                          │
                                          │ 4. Cada plugin roda, retorna
                                          │    Findings normalizados
                                          ▼
                                   Worker grava Findings no PostgreSQL
                                   e atualiza o status do Scan
                                          │
                                          ▼
Frontend consulta /scans/{id}/status (polling ou SSE) e atualiza a barra
de progresso em tempo real. Ao terminar, mostra os Findings.
```

## 3. Por que essa separação?

- **Backend isolado dos workers**: um scan mal comportado (ex: um alvo que
  nunca responde) trava o worker, não a API. O usuário continua navegando
  normalmente enquanto o scan roda em background.
- **Scanner-engine independente**: os plugins de scanner não sabem nada
  sobre FastAPI, PostgreSQL ou HTTP. Eles recebem uma configuração (alvo,
  escopo, credenciais) e devolvem uma lista de `Finding`. Isso permite
  reusar os mesmos plugins em um futuro `securescan-cli` (Fase 32) sem
  depender do backend.
- **Fila (Redis + RQ)**: permite limitar quantos scans rodam em paralelo
  (rate limiting em nível de infraestrutura), cancelar jobs, e escalar
  workers horizontalmente no futuro sem mexer no backend.

## 4. Comunicação em tempo real

Para a Fase 1, o progresso do scan é obtido via **polling simples**
(`GET /api/v1/scans/{id}` a cada ~1s), igual ao padrão já validado no
scanner local que construímos antes. Isso é suficiente para o MVP e evita
a complexidade de gerenciar conexões WebSocket/SSE nesta fase. Server-Sent
Events fica no roadmap (Seção 6 do ROADMAP.md) como melhoria de UX.

## 5. Ambientes

Tudo roda via `docker compose up` a partir de `docker/docker-compose.yml`:

| Serviço   | Porta local | Descrição                          |
|-----------|-------------|-------------------------------------|
| frontend  | 3000        | Next.js                             |
| backend   | 8000        | FastAPI                             |
| worker    | —           | Processo RQ, sem porta HTTP exposta |
| postgres  | 5432        | Banco da plataforma                 |
| redis     | 6379        | Fila de jobs                        |

## 6. Convenções de código

- Backend: Python 3.12, tipagem obrigatória (`mypy` estrito nas camadas de
  serviço), Pydantic v2 para schemas, SQLAlchemy 2.0 para ORM.
- Frontend: TypeScript estrito, componentes funcionais, Tailwind para
  estilo (sem CSS-in-JS), fetch centralizado em `lib/api.ts`.
- Nomes de tabelas em `snake_case`, nomes de modelos Pydantic/TS em
  `PascalCase`.
- Nenhum segredo (senha de banco, chave JWT, etc.) commitado — tudo via
  variáveis de ambiente (`.env`, nunca versionado).

## 7. Referências cruzadas

- Modelo de dados completo: `DATABASE.md`
- Como o scanner-engine funciona e como adicionar um plugin novo:
  `SCANNER_ENGINE.md`
- Modelo de ameaças e limites de segurança da própria plataforma:
  `SECURITY_MODEL.md`
- Ordem de implementação: `ROADMAP.md`

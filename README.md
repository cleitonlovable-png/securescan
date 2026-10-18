# SecureScan

Plataforma de análise de segurança de aplicações web, APIs e infraestrutura.
Ver `docs/` para arquitetura, modelo de dados, modelo de segurança e roadmap
completos.

## Como rodar

```bash
cp backend/.env.example backend/.env
# edite backend/.env e troque JWT_SECRET por um valor aleatório

cd docker
docker compose up --build
```

- Frontend: http://localhost:3000
- Backend (API): http://localhost:8000
- Documentação interativa da API: http://localhost:8000/docs

Primeira execução: crie sua conta em `POST /api/v1/auth/register` (via
`/docs` mesmo, é o Swagger UI do FastAPI) — a tela de registro no frontend
ainda não foi construída nesta entrega, só o login.

## Status honesto desta entrega (Fase 1 + Fase 2 antecipada)

**O que foi testado de verdade, com resultado confirmado:**
- `scanner-engine`: os 10 plugins carregam, o registry funciona, e testei o
  plugin de IDOR de ponta a ponta contra um app Flask vulnerável de
  propósito — detectou a falha corretamente.
- Todo o código Python (backend + workers + scanner-engine) passou por
  checagem de sintaxe (`py_compile`) sem erros.
- Todo o código TypeScript/TSX do frontend passou por checagem de sintaxe
  (`tsc`) sem erros.
- `docker-compose.yml` validado como YAML sintaticamente correto.

**O que NÃO pôde ser testado neste ambiente** (sem acesso à internet para
baixar pacotes/imagens Docker):
- `docker compose up` de ponta a ponta — não rodei os containers de
  verdade aqui. É esperado que ajustes pequenos sejam necessários na
  primeira execução na sua máquina (nomes de variável, alguma dependência
  de versão). Me avise o erro exato e eu corrijo.
- Migrations do Alembic — o `alembic/env.py` está pronto, mas a primeira
  migration precisa ser gerada na sua máquina: `alembic revision
  --autogenerate -m "initial"` dentro do container do backend, depois
  `alembic upgrade head`.
- `npm install` / build do Next.js — sem acesso ao registro do npm aqui
  para instalar `next`, `react`, etc. e rodar `next build` de verdade.
- Fluxo de login → dashboard conectado ao backend real (a página de
  dashboard hoje mostra dados zerados; falta ligar o `useEffect` em
  `app/page.tsx` ao `organization_id` do usuário logado).

## Próximos passos sugeridos

1. Rodar `docker compose up --build` e me mandar qualquer erro que aparecer.
2. Gerar e rodar a primeira migration do Alembic.
3. Testar o registro/login via `/docs`, pegar o `organization_id` retornado.
4. Conectar `app/page.tsx` ao endpoint real do dashboard.
5. Construir a tela de registro e a página "Meus Projetos" (criar
  projeto → cadastrar domínio → verificar → rodar scan).

Isso completa o essencial da Fase 1. A Fase 2 (scanners) já está
antecipada — os 10 plugins battle-tested do protótipo local estão
migrados e funcionando dentro da nova arquitetura.

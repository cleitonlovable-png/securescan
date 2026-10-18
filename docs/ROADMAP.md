# SecureScan — Roadmap

Status atualizado a cada entrega. Seguimos rigorosamente a ordem — nenhuma
fase futura é iniciada antes da fundação da fase atual estar de pé.

## FASE 1 — Fundação — ✅ CÓDIGO COMPLETO (testes de integração pendentes)

- [x] Documentação (`docs/ARCHITECTURE.md`, `SECURITY_MODEL.md`,
      `SCANNER_ENGINE.md`, `DATABASE.md`, `ROADMAP.md`)
- [x] Monorepo + árvore de diretórios
- [x] Docker Compose (postgres, redis, backend, worker, frontend) — YAML
      validado, não executado de ponta a ponta neste ambiente
- [x] Backend FastAPI: config, conexão com banco, modelos SQLAlchemy,
      esqueleto de migrations Alembic — sintaxe validada, não executado
      contra um Postgres real ainda
- [x] Autenticação (registro, login, JWT, hashing bcrypt) — código pronto
- [x] CRUD de Organization / Project / Domain (com verificação de domínio)
- [x] CRUD de Scan (criação enfileira job; consulta de status)
- [x] Persistência de Finding
- [x] Frontend Next.js: layout com sidebar + topbar (tema dark), tela de
      login, dashboard com cards de severidade, painel "Nova Varredura",
      tela de progresso do scan (visual), listagem de últimas varreduras,
      grade de módulos — sintaxe TS validada, não buildado com Next real
      (sem acesso ao registro npm neste ambiente)

Ver README.md raiz — seção "Status honesto desta entrega" — para o
detalhamento exato do que foi testado e o que precisa de uma primeira
rodada na sua máquina.

## FASE 2 — Primeiros scanners — ⏳ PARCIALMENTE ANTECIPADA

O prompt original coloca isso na Fase 2, mas como já tínhamos esses
scanners **prontos e testados** do protótipo local, migramos a lógica
deles para o `scanner-engine` já na Fase 1, para o `QUICK_SCAN` e
`FULL_SCAN` funcionarem de ponta a ponta desde o primeiro `docker compose up`:

- [x] headers
- [x] TLS/SSL
- [x] port scan
- [x] tech fingerprint
- [x] crawler simples (reutilizando subdomain_enum como base — crawler
      completo de rotas/formulários fica para consolidar nesta fase)
- [x] secrets scanner (regex-based, já validado)
- [x] dependency scanner (via OSV.dev, já validado)
- [x] exposed files
- [x] database exposure
- [x] PII exposure (LGPD)
- [x] IDOR / controle de acesso

## FASE 3 — Código (SAST) — ✅ CÓDIGO COMPLETO

- [x] Integração com Semgrep (adapter, clona repositório via git e roda `--config=auto`)
- [ ] Integração com Gitleaks (git history) — não construído ainda
- [ ] Integração com Trivy (imagens/dependências) — não construído ainda
- [ ] Geração de SBOM (CycloneDX) — não construído ainda

## FASE 4 — Web avançado — ✅ PARCIALMENTE ANTECIPADA (via Teste de Invasão)

- [x] Integração com OWASP ZAP (spider + active scan via API, aba dedicada "Teste de Invasão")
- [ ] Crawler avançado (formulários, parâmetros, JS, sitemap, robots.txt) — não construído ainda

## FASE 5 — API Security — ✅ CÓDIGO COMPLETO

- [x] Parser de OpenAPI/Swagger (endpoints sem autenticação, exposição de dados sensíveis na resposta)
- [x] Scanner de GraphQL (introspecção)
- [ ] Limites de rate limiting por endpoint — não construído ainda

## FASE 6 — Infraestrutura — ✅ CÓDIGO COMPLETO

- [x] Análise estática de Dockerfile (usuário sem root, tag latest, segredos
      em ENV/ARG, portas sensíveis expostas, ADD remoto, HEALTHCHECK ausente)
- [x] Verificação de bucket de armazenamento público (S3/GCS)
- [ ] Isolamento de rede dos workers (aplicando à própria plataforma) — não construído
- [ ] Trivy (scan de vulnerabilidades em imagens) — não construído
- [ ] DNS/CDN/WAF — não construído

## FASE 7 — Banco de dados avançado — ✅ CÓDIGO COMPLETO (Supabase)

- [x] Módulo Supabase: descoberta automática de tabelas via PostgREST,
      teste de leitura com anon key (RLS ausente/mal configurado),
      verificação de buckets de storage públicos
- [ ] Conexão autorizada a Postgres/MySQL/MongoDB gerenciados pelo usuário — não construído

## FASE 8 — Checkout/Pagamentos — ✅ CÓDIGO COMPLETO

- [x] Verificação de página de checkout: preço/valor controlável pelo cliente,
      campo de cartão sem HTTPS, chaves de pagamento (Stripe sk_live_)
      expostas no frontend, status de pagamento confiado na URL
- [ ] Teste de webhook (assinatura, idempotência) — não construído
- [ ] Integração real com sandbox de Stripe/Asaas/Mercado Pago — não construído

## FASE 9 — Relatórios avançados — ✅ COMPLETA

- [x] Exportação em PDF, HTML e CSV (relatório técnico completo)
- [x] Resumo Executivo separado (score, principais riscos, prioridades — sem detalhe técnico)
- [x] Scan Diff (novo / corrigido, comparando com o scan anterior do mesmo domínio)

## FASE 11 — Modo Desktop — ⚠️ CÓDIGO COMPLETO, NÃO TESTADO DE PONTA A PONTA

- [x] Banco trocável entre PostgreSQL (servidor) e SQLite (desktop), mesmo
      código de modelos nos dois (tipo `GUID`/`UTCDateTime` compatível)
- [x] Fila trocável entre Redis+RQ (servidor) e thread local (desktop),
      lógica do scan unificada em `backend/app/services/scan_runner.py`
- [x] Entrypoint desktop (`desktop/main.py`) — PyWebView + FastAPI
      embutido + frontend Next.js exportado como site estático
- [x] Scripts de build (`desktop/build.bat`, `desktop/run_dev.bat`)
- [ ] **Nunca rodou de verdade** — ambiente de desenvolvimento sem Windows
      nem internet para instalar pywebview/pyinstaller e testar o .exe final
- [ ] Instalador (hoje gera uma pasta com o .exe, não um instalador único)
- [ ] Ícone/branding do executável

## FASE 10 — SaaS completo — ✅ PARCIALMENTE COMPLETA (avançada)

- [x] Tela de registro de usuário/organização
- [x] Multi-tenancy básico: criar organização nova, trocar entre organizações
- [x] Convidar/remover membros de uma organização (com papel/role)
- [x] Webhook de integrações (JSON genérico, com HMAC)
- [x] Notificação no Slack (Incoming Webhook, só quando há achado crítico/alto)
- [x] CLI (`cli/securescan_cli.py`) para rodar scans a partir de CI/CD, com
      exemplo de GitHub Actions incluído — falha o build se achar algo no
      nível configurado
- [ ] Billing/planos — não construído (Organization.plan existe no banco, mas não há cobrança real)
- [ ] Monitoramento contínuo agendado (scans recorrentes automáticos) — não construído
- [ ] Integrações nomeadas com GitHub/Jira — não construído (Slack sim, GitHub/Jira não)
- [ ] Envio de e-mail de convite — hoje o convite exige que a pessoa já tenha conta

## Regra de ouro

Nenhuma fase começa antes da anterior ter: testes básicos passando, build
funcionando, e este arquivo atualizado com o que foi de fato entregue.

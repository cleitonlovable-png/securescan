# SecureScan — Modelo de Segurança

## 1. Princípio central

O SecureScan só pode rodar testes ATIVOS (que enviam tráfego de teste/ataque
contra um alvo) depois que a propriedade ou autorização sobre aquele domínio
for verificada. Isso é inegociável e é aplicado no **backend**, nunca
apenas na interface — mesmo uma chamada direta à API sem passar pelo
frontend deve ser bloqueada se o domínio não estiver verificado.

## 2. Mecanismo de verificação de domínio

Dois métodos, à escolha do usuário (igual ao padrão usado por Google
Search Console, Vercel, etc.):

### 2.1 Arquivo bem-conhecido

O usuário sobe em seu servidor:
```
https://SEUDOMINIO.com/.well-known/securescan-verification.txt
```
contendo um token único gerado pelo SecureScan no momento do cadastro do
domínio (`Domain.verification_token`, ver DATABASE.md). O backend faz uma
requisição HTTP a essa URL e compara o conteúdo com o token esperado.

### 2.2 Registro DNS TXT

Alternativa para quem não consegue subir arquivos (SaaS de terceiros,
subdomínios gerenciados por outra equipe):
```
TXT  _securescan-verification.SEUDOMINIO.com   securescan-verify=<token>
```
O backend consulta o DNS (via biblioteca `dnspython`) e confirma o token.

### 2.3 Exceções sem verificação

- `localhost`, `127.0.0.1`, faixas de IP privadas (`10.0.0.0/8`,
  `172.16.0.0/12`, `192.168.0.0/16`) podem ser cadastradas como
  **ambiente privado explícito** sem verificação de domínio, mas ainda
  exigem que o usuário marque a caixa de autorização explícita na
  criação do projeto.
- Isso é o que já valida nosso `scope.yaml` do scanner local — a mesma
  lógica, agora centralizada no backend como `Domain.verification_status`.

## 3. Máquina de estados de um Domain

```
PENDING_VERIFICATION → VERIFIED → (testes ativos liberados)
                     ↘ FAILED   → (usuário pode tentar de novo)

PRIVATE_ENVIRONMENT → (testes ativos liberados imediatamente, com
                        autorização explícita marcada na criação)
```

Nenhum scan do tipo `FULL_SCAN`, `API_SCAN` (com testes ativos) ou
`CHECKOUT_SCAN` pode ser criado (`POST /scans`) para um domínio fora dos
estados `VERIFIED` ou `PRIVATE_ENVIRONMENT`. O `QUICK_SCAN` (somente
leitura/observação: headers, TLS, tecnologia usada) é permitido mesmo sem
verificação, pois não envia payloads de teste — mas ainda respeita
rate limiting e é registrado em log.

## 4. Limites obrigatórios em todo scan ativo (Seção 42 do prompt original)

Aplicados na camada de **worker**, antes de qualquer plugin rodar:

| Limite               | Como é aplicado                                              |
|-----------------------|---------------------------------------------------------------|
| Domain allowlist       | Worker recusa qualquer alvo fora do host cadastrado no Project |
| URL scope              | Crawler não segue links para fora do domínio/subdomínios autorizados |
| Rate limit             | Configurável por Project (`rate_limit_rps`), aplicado por plugin |
| Request/redirect limit | Máximo de requisições e redirecionamentos por scan            |
| Timeouts               | Timeout por requisição E timeout total do scan (kill switch)  |
| Cancelamento           | `POST /scans/{id}/cancel` publica uma mensagem que o worker verifica entre cada plugin |
| Isolamento de rede     | Worker roda em container com `network_mode` restrito na Fase 6 (Infra) |
| Audit log              | Toda execução de scan gera entradas em `AuditLog` |

## 5. O que NUNCA é permitido, independente de configuração

- Alterar ou apagar dados do alvo (todos os plugins de banco de dados são
  somente leitura — `SELECT`/comandos de introspecção apenas).
- Ataques de força bruta agressivos (mais de N tentativas/segundo —
  configurável, mas com teto rígido no código, não só na config).
- Persistência no alvo (nenhum plugin cria usuário, webshell, cron job, etc.)
- Exfiltração de dados reais do alvo para fora do próprio banco do
  SecureScan (achados armazenam **evidência sanitizada**, nunca o dado
  completo — ex: um segredo encontrado é truncado, um CPF é mascarado).
- Scans do tipo `CHECKOUT_SCAN` só podem confirmar transações em
  **sandbox/test mode** dos gateways de pagamento — nunca em produção.

## 6. Segurança da própria plataforma (Seção 39 do prompt original)

- Senhas: `bcrypt` (via `passlib`), nunca texto puro, nunca reversível.
- Sessão: JWT de curta duração (access token 15 min) + refresh token
  armazenado em cookie `HttpOnly`, `Secure`, `SameSite=Strict`.
- Rate limiting na própria API (login, criação de scan) via `slowapi`.
- Segredos da própria plataforma (senha do Postgres, `JWT_SECRET`, etc)
  ficam em variáveis de ambiente, nunca commitados — `.env.example` documenta
  as chaves esperadas sem valores reais.
- Logs de auditoria nunca armazenam segredos completos — reaproveita a
  mesma lógica de mascaramento do `secrets_scan.py` que já construímos.
- Workers rodam como usuário não-root no container (Fase 6, Docker
  Security aplicado ao próprio SecureScan).

## 7. RBAC (papéis)

| Papel              | Pode ver projetos | Pode criar scan | Pode gerenciar usuários | Pode mudar billing |
|--------------------|:---:|:---:|:---:|:---:|
| OWNER              | ✅ | ✅ | ✅ | ✅ |
| ADMIN              | ✅ | ✅ | ✅ | ❌ |
| SECURITY_ANALYST   | ✅ | ✅ | ❌ | ❌ |
| DEVELOPER          | ✅ (projetos atribuídos) | ✅ (projetos atribuídos) | ❌ | ❌ |
| VIEWER             | ✅ (somente leitura) | ❌ | ❌ | ❌ |

Aplicado via dependency do FastAPI (`app/api/deps.py::require_role(...)`),
nunca apenas escondido na interface.

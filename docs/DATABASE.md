# SecureScan — Modelo de Dados

PostgreSQL, acessado via SQLAlchemy 2.0. Todas as tabelas têm `id` (UUID),
`created_at` e `updated_at`. Chaves estrangeiras sempre indexadas.

## 1. Diagrama de entidades (Fase 1 — implementadas agora)

```
Organization ─┬──< User (via OrganizationMember)
              ├──< Project ─┬──< Domain
              │              ├──< Scan ─┬──< Finding
              │              │           └──< AuditLog (por scan)
              │              └──< Repository (opcional, Fase 3)
              └──< AuditLog (geral da organização)
```

## 2. Tabelas — Fase 1

### `organizations`
| Coluna | Tipo | Observação |
|---|---|---|
| id | UUID PK | |
| name | text | |
| plan | text | `free` \| `pro` \| `enterprise` (Fase 10, default `free` por ora) |
| created_at / updated_at | timestamptz | |

### `users`
| Coluna | Tipo | Observação |
|---|---|---|
| id | UUID PK | |
| email | text unique | |
| hashed_password | text | bcrypt |
| full_name | text | |
| is_active | bool | default true |
| created_at / updated_at | timestamptz | |

### `organization_members`
Tabela de associação N:N entre `users` e `organizations`, carregando o papel.
| Coluna | Tipo | Observação |
|---|---|---|
| id | UUID PK | |
| organization_id | UUID FK → organizations | |
| user_id | UUID FK → users | |
| role | enum | `OWNER` \| `ADMIN` \| `SECURITY_ANALYST` \| `DEVELOPER` \| `VIEWER` |

### `projects`
| Coluna | Tipo | Observação |
|---|---|---|
| id | UUID PK | |
| organization_id | UUID FK | |
| name | text | |
| description | text nullable | |
| environment | enum | `production` \| `staging` \| `development` |
| framework | text nullable | preenchido pelo tech_fingerprint no 1º scan |
| repository_url | text nullable | Fase 3 |
| security_score | int nullable | 0–100, recalculado a cada scan concluído |
| last_scan_at | timestamptz nullable | |
| created_at / updated_at | timestamptz | |

### `domains`
| Coluna | Tipo | Observação |
|---|---|---|
| id | UUID PK | |
| project_id | UUID FK | |
| hostname | text | ex: `app.meuprojeto.com` |
| is_subdomain_wildcard | bool | permite `*.meuprojeto.com` |
| verification_status | enum | `PENDING_VERIFICATION` \| `VERIFIED` \| `FAILED` \| `PRIVATE_ENVIRONMENT` |
| verification_method | enum nullable | `WELL_KNOWN_FILE` \| `DNS_TXT` |
| verification_token | text | gerado na criação, usado para checar |
| verified_at | timestamptz nullable | |

### `scans`
| Coluna | Tipo | Observação |
|---|---|---|
| id | UUID PK | |
| project_id | UUID FK | |
| domain_id | UUID FK | alvo específico deste scan |
| scan_type | enum | `QUICK_SCAN` \| `FULL_SCAN` \| `API_SCAN` \| `INFRA_SCAN` \| `CHECKOUT_SCAN` (Fases futuras: `CODE_SCAN`, `CONTINUOUS_MONITORING`) |
| status | enum | `PENDING` \| `RUNNING` \| `COMPLETED` \| `FAILED` \| `CANCELLED` |
| progress_percent | int | 0–100, atualizado pelo worker |
| current_step | text nullable | label amigável, ex: "Verificando headers de segurança" |
| requested_by_user_id | UUID FK → users | |
| started_at / finished_at | timestamptz nullable | |
| rq_job_id | text nullable | id do job no Redis, usado para cancelar |
| created_at | timestamptz | |

### `findings`
| Coluna | Tipo | Observação |
|---|---|---|
| id | UUID PK | |
| scan_id | UUID FK | |
| plugin_name | text | ex: `headers_check` |
| title | text | |
| description | text | |
| category | text | ver taxonomia em SCANNER_ENGINE.md |
| severity | enum | `critical` \| `high` \| `medium` \| `low` \| `info` |
| confidence | enum | `high` \| `medium` \| `low` |
| cwe | text nullable | |
| owasp | text nullable | |
| endpoint_or_file | text nullable | |
| evidence_sanitized | text nullable | NUNCA o dado/segredo completo |
| impact | text nullable | |
| remediation | text nullable | |
| references | jsonb | lista de URLs |
| status | enum | `open` \| `confirmed` \| `possible` \| `false_positive` \| `fixed` \| `accepted_risk` \| `ignored` (Seção 26) |
| status_comment | text nullable | |
| first_seen_scan_id | UUID FK → scans nullable | usado pelo Scan Diff (Seção 45) |
| created_at / updated_at | timestamptz | |

### `audit_logs`
| Coluna | Tipo | Observação |
|---|---|---|
| id | UUID PK | |
| organization_id | UUID FK | |
| user_id | UUID FK nullable | nulo para ações automáticas do sistema |
| action | text | ex: `scan.started`, `finding.status_changed`, `project.created` |
| resource_type | text | ex: `scan`, `project`, `finding` |
| resource_id | UUID nullable | |
| metadata | jsonb | contexto adicional, NUNCA segredos completos |
| created_at | timestamptz | |

## 3. Índices importantes

- `findings(scan_id, severity)` — listagem do dashboard por severidade.
- `scans(project_id, created_at DESC)` — histórico e Scan Diff.
- `domains(hostname)` unique — evita cadastro duplicado do mesmo host.
- `audit_logs(organization_id, created_at DESC)` — trilha de auditoria paginada.

## 4. Tabelas adiadas para fases futuras (documentadas, não criadas ainda)

- `repositories` (Fase 3 — Código/SAST)
- `dependencies` + `sbom_components` (Fase 3 — SCA/SBOM)
- `integrations` (Fase 31 — GitHub, Slack, Stripe, etc)
- `reports` (Fase 9 — arquivos de relatório gerados)
- `backups` (Seção 33 — snapshots da própria plataforma)

Essas entidades já estão nomeadas no prompt original (Seção 34) e serão
adicionadas via migration Alembic quando a fase correspondente começar,
para não incluir tabelas vazias e sem uso na Fase 1.

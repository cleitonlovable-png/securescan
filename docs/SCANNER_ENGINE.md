# SecureScan — Scanner Engine (Arquitetura de Plugins)

## 1. Por que plugins, e não um monólito

O prompt original é explícito: "Não quero um monolito gigante". Cada
categoria de análise (headers, TLS, secrets, dependências, IDOR, etc) é um
**plugin independente**, sem conhecimento do backend, do banco de dados ou
de outros plugins. Isso permite:

- Adicionar um scanner novo sem tocar no backend ou no worker.
- Reusar exatamente o mesmo código no futuro `securescan-cli` (Fase 32).
- Testar cada plugin isoladamente.
- Rodar plugins em paralelo com segurança (não compartilham estado).

## 2. Contrato de um plugin

Todo plugin implementa a interface `ScannerPlugin` (`scanner-engine/base.py`):

```python
class ScannerPlugin(ABC):
    name: str            # identificador único, ex: "headers_check"
    version: str         # versão do plugin, ex: "1.0.0"
    category: str        # "web" | "api" | "database" | "secrets" | "infra" | "access_control" | "dependencies"
    requires_active_scan: bool  # True = precisa de domínio VERIFIED (ver SECURITY_MODEL.md)

    def health_check(self) -> bool:
        """Confirma que dependências externas do plugin estão disponíveis
        (ex: binário nmap instalado). Rodado antes do scan começar."""

    def run(self, context: ScanContext) -> list[Finding]:
        """Executa a análise e retorna achados já normalizados."""
```

`ScanContext` carrega tudo que um plugin pode precisar, de forma
padronizada: `target_url`, `scope` (lista de hosts autorizados),
`rate_limit_rps`, `timeout`, `extra_config` (dict livre para parâmetros
específicos do plugin, ex: `requirements_path` para o dependency scanner).

## 3. O modelo `Finding` (normalização universal)

Não importa qual plugin gerou o achado — todos retornam a mesma forma
(Seção 24 do prompt original):

```python
@dataclass
class Finding:
    title: str
    description: str
    category: str          # mesma taxonomia do plugin
    severity: str           # critical | high | medium | low | info
    confidence: str         # high | medium | low  (Seção 21: nem toda string parece segredo real)
    cwe: str | None         # ex: "CWE-798"
    owasp: str | None       # ex: "A02:2021 - Cryptographic Failures"
    endpoint_or_file: str | None
    evidence_sanitized: str | None   # NUNCA o segredo/dado completo
    impact: str
    remediation: str
    references: list[str]
    plugin_name: str
```

O worker recebe essa lista e persiste como linhas de `Finding` no
PostgreSQL (ver DATABASE.md), associadas ao `Scan` que as gerou.

## 4. Migrando nossos scanners já validados

Os módulos que já construímos e testamos no protótipo local (scanner
pessoal em Flask) viram a primeira geração de plugins, só embrulhados no
contrato `ScannerPlugin`:

| Plugin novo (scanner-engine/plugins/)  | Lógica reaproveitada          | Categoria        |
|------------------------------------------|-------------------------------|------------------|
| `headers_plugin.py`                       | `headers_check.py`             | web              |
| `ssl_plugin.py`                           | `ssl_check.py`                 | web              |
| `port_scan_plugin.py`                     | `port_scan.py`                 | infra            |
| `tech_fingerprint_plugin.py`               | `tech_fingerprint.py`          | web              |
| `exposed_files_plugin.py`                  | `exposed_files.py`             | web              |
| `secrets_plugin.py`                        | `secrets_scan.py`              | secrets          |
| `database_exposure_plugin.py`              | `database_exposure.py`         | database         |
| `pii_exposure_plugin.py`                   | `pii_exposure.py`              | web (LGPD)       |
| `idor_plugin.py`                           | `idor_check.py`                | access_control   |
| `dependency_plugin.py`                     | `dependency_check.py`          | dependencies     |

A lógica interna de cada um (regex, requests, sockets) não muda — só o
formato de entrada/saída é adaptado ao contrato novo. Isso é
intencionalmente de baixo risco: já validamos essa lógica com testes reais
(inclusive contra um app Flask com falha IDOR proposital).

## 5. Plugins futuros via ferramentas externas (Seção 41)

Fase 3+ do roadmap. Cada ferramenta madura (Semgrep, Gitleaks, Trivy, OWASP
ZAP, OSV) ganha um **adapter**, não uma reimplementação:

```python
class SemgrepPlugin(ScannerPlugin):
    name = "semgrep"
    category = "code"

    def run(self, context: ScanContext) -> list[Finding]:
        raw = subprocess.run(["semgrep", "--json", "--config=auto", context.repo_path], ...)
        return self._normalize(json.loads(raw.stdout))
```

O adapter só faz duas coisas: chamar a ferramenta e traduzir a saída dela
para `Finding`. Nunca reimplementamos a lógica de detecção da ferramenta.

## 6. Registro e carregamento de plugins

`scanner-engine/registry.py` mantém um dicionário `name -> classe do plugin`.
O worker consulta quais plugins rodar com base no `scan_type` do `Scan`
(ex: `QUICK_SCAN` roda só `headers`, `ssl`, `tech_fingerprint`;
`FULL_SCAN` roda todos os plugins compatíveis com o `category` liberado
no projeto).

## 7. Execução e falhas

Cada plugin roda dentro de um `try/except` no worker — se um plugin falhar
(timeout, exceção, dependência ausente), isso vira um `Finding` de
severidade `info` documentando a falha (ex: "Nmap não encontrado"), e o
worker **continua** para o próximo plugin. Um plugin quebrado nunca derruba
o scan inteiro — este é o mesmo padrão de `friendly_error()` que já usamos
no protótipo local.

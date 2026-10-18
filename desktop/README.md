# SecureScan Desktop

Versão do SecureScan como programa desktop — sem Docker, sem Postgres, sem
Redis. Um `.exe` só, com banco SQLite local.

## O que muda em relação ao modo servidor (Docker)

| | Modo servidor (Docker) | Modo desktop |
|---|---|---|
| Banco de dados | PostgreSQL | SQLite (um arquivo, em `%APPDATA%\SecureScanDesktop\securescan.db`) |
| Fila de scans | Redis + worker separado | Thread em background, mesmo processo |
| Frontend | Next.js rodando (`next dev`) | Site estático exportado, servido pelo próprio backend |
| Portas | 3001 (frontend) + 8000 (API) | Uma só, 8756, interna (loopback) |

O **código do backend é o mesmo** nos dois modos — nenhuma rota, plugin ou
lógica de scan foi duplicada. O que muda é só configuração (variáveis de
ambiente) e a forma como o banco/fila funcionam por baixo.

## Como gerar o .exe

Requisitos: **Python 3.12+** e **Node.js** instalados no Windows.

```
cd desktop
build.bat
```

O executável final fica em `desktop\dist\SecureScan\SecureScan.exe`.

## Testar rápido, sem gerar o .exe

```
cd desktop
run_dev.bat
```

Builda o frontend uma vez e roda o app direto com Python — mais rápido
pra testar mudanças do que esperar o PyInstaller empacotar tudo de novo.

## O que foi testado e o que não foi

Fui honesto sobre isso durante todo o projeto, e aqui não é diferente:

✅ **Testado:** sintaxe de todo o código Python e TypeScript novo/alterado.

⚠️ **NÃO testado de ponta a ponta** — este ambiente onde o código foi
escrito não tem acesso à internet nem Windows, então não consegui instalar
`pywebview`, `pyinstaller`, rodar `next build` com export estático, nem
testar o `.exe` final rodando de verdade. É esperado que apareça algum
ajuste na primeira tentativa — me manda o erro exato (igual fizemos com o
Docker) que eu corrijo.

Pontos que merecem atenção especial na primeira tentativa:
- O caminho que o PyInstaller usa pra achar `backend/`, `scanner_engine/`
  e o frontend estático dentro do `.exe` empacotado (`desktop/main.py`,
  função `_resolve_base_dirs()`) — a lógica está lá, mas nunca rodou de
  verdade dentro de um `.exe` real.
- `next export` com rotas tipo `/pentest`, `/code` etc — todas são páginas
  estáticas (sem parâmetro dinâmico tipo `[id]`), então deveria exportar
  sem problema, mas também nunca rodou de verdade aqui.

## Limitações conhecidas (by design, pra uso pessoal)

- **Um scan por vez.** A fila local roda numa thread só — se você disparar
  dois scans ao mesmo tempo, o segundo espera o primeiro terminar.
- **Fechar o app no meio de um scan deixa ele "preso" como RUNNING** no
  banco. Não tem como retomar sozinho ao reabrir — é só apagar o registro
  ou rodar de novo.
- **nmap, git e Semgrep continuam sendo programas externos.** Se não
  estiverem instalados no Windows, os plugins que dependem deles avisam
  e pulam, igual já fazem hoje.
- **O ZAP continua sendo outro programa**, do jeito que já é hoje — o
  SecureScan Desktop só conversa com ele pela API local.

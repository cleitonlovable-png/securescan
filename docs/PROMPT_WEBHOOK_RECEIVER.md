Preciso que você crie um endpoint na minha aplicação para RECEBER relatórios
de segurança enviados automaticamente por outro sistema meu (SecureScan).

## O que precisa ser criado

1. Um endpoint HTTP que aceite requisições **POST** (ex: `/webhooks/securescan`
   ou o caminho que fizer mais sentido na estrutura do projeto).
2. Uma aba/tela na interface que **liste o histórico** de relatórios recebidos
   (não é só mostrar o último — preciso guardar todos, mais recente primeiro).
3. Persistência: salvar cada relatório recebido (banco de dados, arquivo JSON,
   o que já for usado no projeto).

## Formato exato do que chega

### Headers da requisição
```
Content-Type: application/json
Authorization: Bearer <segredo_compartilhado>
X-SecureScan-Signature: sha256=<hmac_hex>
```

O segredo compartilhado (`<segredo_compartilhado>`) é configurado manualmente
nos dois lados (no SecureScan e aqui). Preciso que o endpoint:

1. Verifique se o header `Authorization` bate com o segredo configurado
   (comparação de string simples). Se não bater, retornar **401**.
2. Opcionalmente (mas recomendado), valide a assinatura HMAC também:
   recalcular `HMAC-SHA256(corpo_bruto_da_requisicao, segredo)` e comparar
   com o valor após `sha256=` no header `X-SecureScan-Signature`. Se não
   bater, retornar **401**. Use comparação de tempo constante
   (ex: `hmac.compare_digest` em Python, `crypto.timingSafeEqual` em Node)
   para evitar timing attack.

O segredo deve vir de uma variável de ambiente (ex: `SECURESCAN_WEBHOOK_SECRET`),
nunca hardcoded no código.

### Corpo da requisição (JSON)

```json
{
  "event": "scan.completed",
  "scan_id": "aa17bf55-4d03-44bf-bdc8-150af4fcb673",
  "project_name": "Varreduras Rápidas",
  "domain": "meusite.com.br",
  "scan_type": "FULL_SCAN",
  "status": "COMPLETED",
  "severity_summary": {
    "critical": 1,
    "high": 2,
    "medium": 0,
    "low": 3,
    "info": 0
  },
  "findings": [
    {
      "title": "Header 'Content-Security-Policy' ausente.",
      "description": "Mitiga XSS e injeção de conteúdo.",
      "category": "web",
      "severity": "high",
      "remediation": "Adicionar CSP restritiva ao servidor.",
      "endpoint_or_file": "https://meusite.com.br",
      "plugin_name": "headers_check"
    }
  ]
}
```

Campos:
- `scan_type` pode ser: `QUICK_SCAN`, `FULL_SCAN`, `API_SCAN`, `INFRA_SCAN`,
  `PENTEST_SCAN`, `CODE_SCAN`, `CHECKOUT_SCAN`.
- `status` normalmente vem como `COMPLETED`.
- `severity_summary` sempre tem essas 5 chaves (`critical`, `high`, `medium`,
  `low`, `info`), mesmo que o valor seja 0.
- `findings` é uma lista, pode vir vazia (`[]`) se o scan não achou nada.
- `endpoint_or_file` pode ser `null`.

## O que exibir na tela/aba

Para cada relatório recebido, mostrar:
- Nome do projeto + domínio (`project_name` + `domain`)
- Tipo de scan (`scan_type`) e quando chegou
- Resumo de severidade em cards/badges coloridos (crítico=vermelho,
  alto=laranja, médio=amarelo, baixo=verde), usando os números de
  `severity_summary`
- Lista expansível dos `findings`, cada um mostrando título, severidade,
  descrição e recomendação

## Requisitos técnicos
- Responder **200 OK** rapidamente após salvar (não processar de forma
  lenta/síncrona se puder evitar — se precisar processar algo pesado,
  aceitar o payload, responder 200, e processar em background).
- Não é necessário CORS (é uma chamada servidor-para-servidor, não vem do
  navegador).
- Tratar corpo malformado/JSON inválido retornando 400.

Antes de implementar, me diga qual stack/framework este projeto já usa,
para eu adaptar o endpoint corretamente (rota, ORM, etc).

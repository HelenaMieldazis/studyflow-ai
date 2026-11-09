# Arquitetura

## Visão geral

```
┌──────────────┐  HTTP (mesma origem)  ┌────────────────────┐   SQL (psycopg 3)   ┌──────────────┐
│  Navegador   │ ───── /api/* ───────► │   Flask API        │ ──────────────────► │ PostgreSQL 16│
│  React SPA   │                       │   (Blueprints)     │                     │ 127.0.0.1    │
└──────────────┘                       └─────────┬──────────┘                     └──────────────┘
        ▲                                        │ (Etapa 4)
        │ Vite dev server (:5173)                ▼
        │ proxy /api → :5001             ┌──────────────┐
        └────────────────────────────────│   Ollama     │  nunca acessível pelo navegador
                                         └──────────────┘
```

## Princípios

1. **O backend é a única porta de entrada.** O navegador só fala com `/api`; banco e modelo de IA não ficam expostos.
2. **Mesma origem.** Em desenvolvimento o Vite faz proxy de `/api` para o Flask. Em produção um proxy reverso (Etapa 8) servirá frontend e API sob o mesmo domínio. Isso permite cookies `HttpOnly` + `SameSite` sem CORS com credenciais entre domínios.
3. **Camadas no backend:** `routes` (HTTP, validação de entrada, serialização) → `services` (regras de negócio) → `models` (persistência). Rotas não acessam o banco diretamente; serviços não conhecem `request`.
4. **Falha fechada.** Sem `APP_ENV`, a aplicação assume `production` e exige `SECRET_KEY` forte, `DATABASE_URL` e origens CORS em HTTPS.

## Backend

| Arquivo | Responsabilidade |
|---|---|
| `run.py` | Ponto de entrada; cria a app e inicia o servidor de desenvolvimento. |
| `app/__init__.py` | `create_app()`: carrega a config, inicializa extensões, registra blueprints, erros e headers. |
| `app/config.py` | Classes `DevelopmentConfig`, `TestingConfig`, `ProductionConfig`; lê o `.env` da raiz; valida segredos. |
| `app/extensions.py` | Instâncias de `SQLAlchemy` (com convenção de nomes de constraints), `Migrate` e `CORS`. |
| `app/routes/__init__.py` | Registra todos os blueprints sob `/api`. |
| `app/routes/health.py` | `GET /api/health`. |
| `app/services/health_service.py` | Executa `SELECT 1` e informa se o banco respondeu. |
| `app/utils/errors.py` | Handlers centrais: toda falha vira JSON `{"error": {"code", "message"}}`, sem stack trace. |
| `app/utils/log_config.py` | Formato e nível de logs. |
| `app/utils/security_headers.py` | Headers de segurança em todas as respostas. |
| `migrations/` | Ambiente Alembic gerado por `flask db init`. |
| `tests/` | Pytest: health, erros, CORS, headers, validação da config de produção. |

### Contrato do `/api/health`

| Situação | Status | Corpo |
|---|---|---|
| API e banco OK | `200` | `{"status":"ok","service":"studyflow-api","checks":{"database":"ok"}}` |
| Banco indisponível | `503` | `{"status":"degraded",...,"checks":{"database":"unavailable"}}` |

## Frontend

| Pasta/arquivo | Responsabilidade |
|---|---|
| `src/main.tsx` | Monta React, `BrowserRouter`, fonte Inter e estilos globais. |
| `src/App.tsx` | Tabela de rotas. |
| `src/services/api.ts` | Instância única do Axios (`baseURL=/api`, `withCredentials`, timeout). |
| `src/services/healthService.ts` | Chama `/health`, valida o formato da resposta e converte em `ConnectionState`. |
| `src/hooks/useHealthCheck.ts` | Estado de carregamento/resultado + `retry`, com cancelamento via `AbortController`. |
| `src/types/health.ts` | Tipos do contrato da API. |
| `src/components/AppLayout/` | Estrutura da página (barra superior, link "pular para o conteúdo", `<main>`). |
| `src/components/HealthStatus/` | Cartão de status acessível (`role="status"`, `aria-live`). |
| `src/pages/` | Páginas roteáveis (`HomePage`, `NotFoundPage`). |
| `src/styles/global.css` | Tokens de design (paleta, espaçamento, raios) e foco visível. |

**Regra:** componentes nunca chamam Axios diretamente; sempre `services/` → `hooks/` → componentes.

## Decisões técnicas (ADR resumido)

| Decisão | Motivo |
|---|---|
| `psycopg` 3 em vez de `psycopg2` | Driver mantido ativamente, wheels binárias para Python 3.13, suportado pelo SQLAlchemy 2. |
| `.env` único na raiz | Evita divergência entre backend, Compose e Vite. O Vite só expõe variáveis `VITE_*`. |
| Porta 5001 para o Flask | A porta 5000 é ocupada pelo AirPlay Receiver no macOS. |
| Fonte Inter via `@fontsource` | Sem requisição a CDN de terceiros (privacidade/LGPD e funcionamento offline). |
| Testes com PostgreSQL real ou SQLite | `TEST_DATABASE_URL` aponta para um banco de testes dedicado; sem ela, SQLite em memória permite rodar os testes sem Docker. |
| PyJWT ainda não instalado | Será adicionado na Etapa 2, quando a estratégia de sessão for implementada (evita dependências sem uso). |

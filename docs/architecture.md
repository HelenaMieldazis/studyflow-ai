# Arquitetura

## Visão geral

```
┌──────────────┐  HTTP (mesma origem)  ┌────────────────────┐   SQL (psycopg 3)   ┌──────────────┐
│  Navegador   │ ───── /api/* ───────► │   Flask API        │ ──────────────────► │ PostgreSQL 16│
│  React SPA   │  cookie HttpOnly +    │   (Blueprints)     │                     │ 127.0.0.1    │
└──────────────┘  header X-CSRF-Token  └─────────┬──────────┘                     └──────────────┘
        ▲                                        │ (Etapa 4)
        │ Vite dev server (:5173)                ▼
        │ proxy /api → :5001             ┌──────────────┐
        └────────────────────────────────│   Ollama     │  nunca acessível pelo navegador
                                         └──────────────┘
```

## Princípios

1. **O backend é a única porta de entrada.** O navegador só fala com `/api`; banco e modelo de IA não ficam expostos.
2. **Mesma origem.** Em desenvolvimento o Vite faz proxy de `/api` para o Flask. Em produção um proxy reverso (Etapa 8) servirá frontend e API sob o mesmo domínio. Isso permite cookies `HttpOnly` + `SameSite=Lax`.
3. **Camadas no backend:** `routes` (HTTP) → `schemas` (validação) → `services` (regras de negócio) → `models` (persistência).
4. **O usuário vem da sessão, nunca do cliente.** Não existem rotas com id de usuário na URL; tudo é `/me`.
5. **Falha fechada.** Sem `APP_ENV`, a aplicação assume `production` e exige configuração segura.

## Autenticação (Etapa 2)

### Fluxo

```
Cadastro/Login ──► backend cria sessão ──► Set-Cookie: sf_session=<token> (HttpOnly, SameSite=Lax)
                                      └──► corpo: { user, csrf_token }
                                                       │
Frontend guarda csrf_token só em memória ◄─────────────┘
Toda requisição POST/PUT/PATCH/DELETE ──► header X-CSRF-Token: <csrf_token>
Recarregou a página? ──► GET /api/auth/me devolve user + csrf_token de novo
```

### Por que sessão no banco e não JWT puro

| Requisito | JWT puro | Sessão no banco (escolhida) |
|---|---|---|
| Logout invalida de verdade | ❌ token vale até expirar | ✅ apaga o registro |
| Troca de senha encerra outros dispositivos | ❌ | ✅ |
| Exclusão de conta encerra tudo | ❌ | ✅ (cascata) |
| Token no banco | — | só o hash SHA-256 |

O PyJWT continua previsto para os tokens de recuperação de senha (uso único, curta duração).

### Sessões

- Token: `secrets.token_urlsafe(32)` (256 bits). Banco guarda `sha256(token)`.
- Expiração por inatividade: `SESSION_IDLE_TIMEOUT_MINUTES` (padrão 120), renovada automaticamente com o uso (no máximo uma escrita a cada 5 min).
- Expiração absoluta: `SESSION_ABSOLUTE_TIMEOUT_HOURS` (padrão 168 = 7 dias) desde o login.
- Login sempre cria um token novo e revoga o anterior do mesmo navegador (contra fixação de sessão).
- Cookie em produção: `__Host-sf_session`, `Secure`, `HttpOnly`, `SameSite=Lax`, `Path=/`.

### CSRF

- **Com sessão:** token CSRF = `HMAC-SHA256(SECRET_KEY, "csrf:" + token_da_sessão)`. Vinculado à sessão, não precisa ser armazenado, comparado em tempo constante.
- **Sem sessão (cadastro/login):** verificação do header `Origin` contra a lista autorizada + exigência de `Content-Type: application/json` (força preflight CORS em requisições de outros sites) + `SameSite=Lax`.

## API

Todas as respostas são JSON. Erros seguem `{"error": {"code", "message", "fields?"}}`.

| Método | Rota | Auth | CSRF | Descrição |
|---|---|---|---|---|
| GET | `/api/health` | — | — | Saúde da API e do banco (200/503) |
| POST | `/api/auth/register` | — | Origin | Cria conta e inicia sessão (201) |
| POST | `/api/auth/login` | — | Origin | Inicia sessão |
| POST | `/api/auth/logout` | ✅ | ✅ | Encerra a sessão atual |
| GET | `/api/auth/me` | ✅ | — | Usuário atual + token CSRF |
| GET | `/api/users/me` | ✅ | — | Perfil |
| PATCH | `/api/users/me` | ✅ | ✅ | Altera nome e/ou e-mail (e-mail exige `current_password`) |
| PUT | `/api/users/me/password` | ✅ | ✅ | Troca a senha; encerra as outras sessões |
| DELETE | `/api/users/me` | ✅ | ✅ | Exclui a conta (exige `password`) |

### Códigos de erro relevantes

| Status | `code` | Quando |
|---|---|---|
| 401 | `unauthenticated` | Sem sessão, expirada ou revogada |
| 401 | `invalid_credentials` | E-mail ou senha incorretos (mesma resposta nos dois casos) |
| 403 | `csrf_failed` | Token CSRF ausente ou inválido |
| 403 | `origin_not_allowed` | Header `Origin` não autorizado |
| 403 | `invalid_password` | Senha atual incorreta em operação sensível |
| 409 | `email_unavailable` | E-mail já em uso |
| 413 | `payload_too_large` | Corpo maior que `MAX_CONTENT_LENGTH` |
| 415 | `unsupported_media_type` | Corpo não é JSON |
| 422 | `unprocessable_entity` | Validação falhou (detalhes em `fields`) |
| 429 | `too_many_requests` | Rate limit atingido (header `Retry-After`) |

### Limites de requisição

| Rota | Limite | Chave |
|---|---|---|
| Todas | 300/min | IP |
| `POST /auth/login` | 10/min e 50/h | IP |
| `POST /auth/login` | 5 a cada 15 min e 20/dia | conta (hash do e-mail) |
| `POST /auth/register` | 5/h | IP |
| Troca de senha e exclusão de conta | 10/h | sessão |

## Backend — arquivos

| Arquivo | Responsabilidade |
|---|---|
| `run.py` | Ponto de entrada. |
| `app/__init__.py` | `create_app()`: config, extensões, blueprints, hooks de segurança, CLI. |
| `app/config.py` | Configurações por ambiente; validação de segredos, cookie e CORS em produção. |
| `app/extensions.py` | `db`, `migrate`, `cors`, `limiter`; liga chaves estrangeiras no SQLite. |
| `app/cli.py` | `flask cleanup-sessions`. |
| `app/models/base.py` | `utcnow()`, `as_utc()`, `TimestampMixin`. |
| `app/models/user.py` | Tabela `users`. |
| `app/models/user_session.py` | Tabela `user_sessions`. |
| `app/schemas/fields.py` | Tipos validados: `Email`, `DisplayName`, `NewPassword`, `CurrentPassword`. |
| `app/schemas/auth.py` | Formato aceito por cada rota (`extra="forbid"`). |
| `app/schemas/serializers.py` | JSON público do usuário (lista explícita de campos). |
| `app/routes/auth.py` | `/api/auth/*`. |
| `app/routes/users.py` | `/api/users/me*`. |
| `app/routes/health.py` | `/api/health`. |
| `app/services/password_service.py` | Argon2id: hash, verificação com tempo constante, rehash. |
| `app/services/session_service.py` | Criar, validar, renovar, revogar sessões; token CSRF. |
| `app/services/auth_service.py` | Cadastro, login, perfil, troca de senha, exclusão. |
| `app/services/health_service.py` | `SELECT 1`. |
| `app/utils/auth.py` | `@login_required`, cookie de sessão, verificação CSRF. |
| `app/utils/origin_check.py` | Bloqueia escrita vinda de origens não autorizadas. |
| `app/utils/rate_limit.py` | Chaves por conta e por sessão para o limitador. |
| `app/utils/validation.py` | `parse_json_body()`: JSON obrigatório, erros 422 em português. |
| `app/utils/errors.py` | `ApiError` e tratamento central de erros. |
| `app/utils/security_headers.py` | Headers de segurança e `Cache-Control: no-store`. |
| `app/utils/log_config.py` | Logs sem dados pessoais. |

## Frontend — arquivos

| Pasta/arquivo | Responsabilidade |
|---|---|
| `src/main.tsx` | `BrowserRouter` + `AuthProvider` + `App`. |
| `src/App.tsx` | Rotas públicas (`/entrar`, `/cadastro`, `/privacidade`) e protegidas (`/`, `/configuracoes`). |
| `src/services/api.ts` | Axios único; injeta `X-CSRF-Token`; detecta sessão expirada. |
| `src/services/apiError.ts` | Converte erros da API em mensagens e erros por campo. |
| `src/services/authService.ts` | Chamadas de autenticação e conta. |
| `src/contexts/AuthContext.tsx` | Estado da sessão (carregando / autenticado / anônimo) e ações. |
| `src/contexts/authContextValue.ts` | Tipos e objeto do contexto. |
| `src/hooks/useAuth.ts` | Acesso ao contexto de autenticação. |
| `src/components/RouteGuards/` | `ProtectedRoute` e `PublicOnlyRoute` (fazem todos os redirecionamentos de login/logout). |
| `src/components/forms/` | `TextField`, `Button`, `Alert` acessíveis. |
| `src/components/AppLayout/` | Barra superior, menu lateral, "Sair". |
| `src/components/AuthLayout/` | Cartão centralizado das telas públicas. |
| `src/pages/LoginPage`, `RegisterPage` | Formulários de acesso. |
| `src/pages/SettingsPage/` | Perfil, troca de senha, exclusão de conta. |
| `src/pages/PrivacyPage/` | Aviso de uso de dados (LGPD). |
| `src/utils/redirect.ts` | Validação do destino pós-login (contra open redirect). |
| `src/utils/validators.ts` | Validação rápida no navegador (o backend sempre revalida). |

## Decisões técnicas (ADR resumido)

| Decisão | Motivo |
|---|---|
| Sessão no banco em vez de JWT puro | Logout, troca de senha e exclusão precisam invalidar sessões imediatamente. |
| Argon2id (argon2-cffi) | Recomendação OWASP; resistente a ataques com GPU. |
| Pydantic para validação | Tipos, tamanhos e formatos declarativos; `extra="forbid"` bloqueia mass assignment. |
| UUID como chave primária de `users` | Não revela quantidade de usuários nem permite adivinhar IDs. |
| CSRF por HMAC da sessão | Vinculado à sessão, sem armazenamento extra, sem cookie legível por JavaScript. |
| `psycopg` 3 | Driver mantido, wheels para Python 3.13, suportado pelo SQLAlchemy 2. |
| `.env` único na raiz | Evita divergência entre backend, Compose e Vite. |
| Porta 5001 para o Flask | A 5000 é usada pelo AirPlay no macOS. |
| Fonte Inter via `@fontsource` | Sem CDN de terceiros (privacidade e funcionamento offline). |

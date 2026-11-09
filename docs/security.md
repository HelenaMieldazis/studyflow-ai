# Segurança

Este documento registra as medidas implementadas, as pendentes e as limitações conhecidas. Ele é atualizado a cada etapa.

## Implementado na Etapa 1

### Configuração e segredos
- Segredos apenas em variáveis de ambiente; `.env` está no `.gitignore` e `.env.example` não contém credenciais.
- Ambiente padrão é `production` (falha fechada): sem `APP_ENV`, a aplicação exige configuração segura.
- Em produção a aplicação **não inicia** se:
  - `SECRET_KEY` estiver vazia, for um placeholder conhecido ou tiver menos de 32 caracteres;
  - `DATABASE_URL` não estiver definida;
  - `CORS_ORIGINS` estiver vazia, contiver `*` ou origens sem HTTPS.
- `DEBUG=False` em produção e nos testes.

### API
- **Erros centralizados** (`app/utils/errors.py`): respostas JSON padronizadas; stack traces e mensagens de exceção ficam somente no log do servidor.
- **`/api/health` não vaza detalhes**: falhas de banco retornam apenas `"unavailable"`; o log registra só o tipo da exceção (a mensagem do driver pode conter host/usuário).
- **Limite de tamanho de requisição**: `MAX_CONTENT_LENGTH` (1 MiB por padrão) → `413`.
- **CORS restritivo**: só origens listadas em `CORS_ORIGINS`, apenas em `/api/*`, headers CORS enviados somente quando há `Origin`.
- **Headers de segurança** em todas as respostas: `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`, `Referrer-Policy: no-referrer`, `Content-Security-Policy: default-src 'none'; frame-ancestors 'none'`, `Cross-Origin-Resource-Policy: same-site`, `Permissions-Policy` e `Strict-Transport-Security` fora de dev/teste.
- **Consultas parametrizadas**: todo acesso ao banco passa pelo SQLAlchemy (ORM ou `text()` sem interpolação).
- **Timeout de conexão** com o banco (`DATABASE_CONNECT_TIMEOUT`) e `pool_pre_ping`.

### Infraestrutura local
- PostgreSQL publicado **somente em `127.0.0.1`**, autenticação `scram-sha-256`, `no-new-privileges`, limites de CPU (1) e memória (512 MiB).
- Imagem oficial com versão fixada.
- Banco de testes separado do banco de desenvolvimento.

### Frontend
- Nenhum token em `localStorage`; o cliente Axios usa `withCredentials` para cookies HttpOnly (Etapa 2).
- Apenas variáveis `VITE_*` chegam ao navegador; nenhuma contém segredo.
- Respostas da API são validadas antes de usadas (`isHealthResponse`).
- React escapa conteúdo por padrão; não há uso de `dangerouslySetInnerHTML`.
- Fonte servida localmente (sem CDN de terceiros); `<meta name="referrer" content="no-referrer">`.
- Source maps desabilitados no build de produção.

### Testes de segurança automatizados
- 404/405/413/500 retornam JSON sem stack trace nem detalhes internos.
- Falha real de conexão com PostgreSQL não vaza senha nem host.
- CORS aceita a origem configurada e ignora origens desconhecidas (inclusive em preflight).
- Configuração de produção recusa `SECRET_KEY` fraca, `*` em CORS, origens HTTP e ausência de `DATABASE_URL`.

## Pendente (por etapa)

| Etapa | Medida |
|---|---|
| 2 | Hash de senhas com Argon2id; sessão em cookie `HttpOnly`/`Secure`/`SameSite`; proteção CSRF; expiração e renovação de sessão; logout com invalidação no servidor; rate limiting (Flask-Limiter) em login e cadastro; mensagens que evitam enumeração de contas; validação de entrada com schemas; testes de IDOR. |
| 3+ | Toda consulta filtrada pelo usuário autenticado (nunca por `user_id` vindo do cliente); paginação obrigatória. |
| 4 | Camada de IA isolada; separação de instruções e dados (prompt injection); limites de entrada/saída e timeout; Ollama sem exposição externa. |
| 7 | Proteção contra SSRF ao processar links (não buscar URLs no servidor sem allowlist/validação de IP). |
| 8 | Servidor WSGI (gunicorn) com usuário não-root; proxy reverso com HTTPS; CSP do frontend; Dockerfile da API; backups e teste de restauração; varredura de dependências (`pip-audit`, `npm audit`) na CI. |

## Limitações conhecidas

- O servidor de desenvolvimento do Flask (`python run.py`) **não deve ser usado em produção**.
- Ainda não há autenticação: nenhuma rota além de `/api/health` existe.
- A versão do PostgreSQL deve ser atualizada periodicamente (patches de segurança trimestrais).
- Testes passando não significam que o sistema é seguro; uma revisão de segurança dedicada será feita antes da publicação.

## Relato de vulnerabilidades

Enquanto o projeto não tiver um canal público, relate problemas de segurança diretamente à mantenedora, sem abrir issue pública.

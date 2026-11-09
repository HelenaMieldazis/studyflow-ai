# StudyFlow AI

Plataforma web de organização e acompanhamento de estudos com um tutor de Inteligência Artificial adaptativo, executado localmente via Ollama.

> **Status:** Etapa 2 — Usuários e segurança concluída (cadastro, login, sessões seguras, perfil, troca de senha, exclusão de conta).
> Organização dos estudos, tutor de IA e exercícios ainda **não** foram implementados.

## Stack

| Camada | Tecnologias |
|---|---|
| Frontend | React 19, Vite, TypeScript, React Router, Axios, CSS Modules, Vitest + Testing Library |
| Backend | Python 3.12+, Flask, Flask-SQLAlchemy, Flask-Migrate (Alembic), Flask-CORS, Flask-Limiter, Pydantic, argon2-cffi, Pytest |
| Banco | PostgreSQL 16 (via Docker Compose em desenvolvimento) |
| IA | Ollama (a partir da Etapa 4, sempre atrás do backend) |

## Pré-requisitos

- Python **3.12+** — no Windows, marque **"Add python.exe to PATH"** no instalador
- Node.js **20.19+** ou **22.12+** e npm
- Docker Desktop (para o PostgreSQL)
- Git

## Como executar (desenvolvimento)

Os comandos estão em duas versões: **Windows (cmd)** e **Linux/macOS**.

### 1. Variáveis de ambiente

| Windows (cmd) | Linux/macOS |
|---|---|
| `copy .env.example .env` | `cp .env.example .env` |
| `notepad .env` | abra o `.env` no seu editor |

Preencha no `.env`:

- **`SECRET_KEY`**: gere com `python -c "import secrets; print(secrets.token_urlsafe(48))"` (no Windows, `py` se `python` não funcionar). Também funciona com Node: `node -e "console.log(require('crypto').randomBytes(48).toString('base64url'))"`.
- **`POSTGRES_PASSWORD`**: uma senha forte só para desenvolvimento. **De preferência só letras e números.**
- **`DATABASE_URL`** e **`TEST_DATABASE_URL`**: troque `SUA_SENHA_AQUI` pela mesma senha. Se ela tiver `@`, `#`, `/`, `:`, `?` ou `%`, codifique-os (ex.: `@` vira `%40`). Veja os comentários no `.env.example`.

### 2. Banco de dados

```
docker compose up -d db
docker compose ps          (aguarde o estado "healthy")
```

O PostgreSQL fica acessível **apenas** em `127.0.0.1`. Na primeira inicialização também é criado o banco `studyflow_test`.

> **A senha só vale na primeira criação.** Se você mudar `POSTGRES_PASSWORD` depois de subir o banco, recrie-o (isso apaga os dados): `docker compose down -v` e `docker compose up -d db`.
>
> **Porta 5432 ocupada** (por exemplo, um PostgreSQL instalado no Windows)? Mude `POSTGRES_PORT=5433` e a porta nas duas URLs do `.env`.

### 3. Backend

| Windows (cmd) | Linux/macOS |
|---|---|
| `cd backend` | `cd backend` |
| `py -m venv .venv` | `python3 -m venv .venv` |
| `.venv\Scripts\activate` | `source .venv/bin/activate` |
| `pip install -r requirements-dev.txt` | `pip install -r requirements-dev.txt` |
| `flask --app run db upgrade` | `flask --app run db upgrade` |
| `python run.py` | `python run.py` |

A API sobe em http://127.0.0.1:5001. Teste: `curl http://127.0.0.1:5001/api/health`.

> Depois de ativar o ambiente virtual, o prompt mostra `(.venv)`. Todo comando `python`, `pip` e `flask` do backend deve ser executado com ele ativo.
> No PowerShell, a ativação é `.venv\Scripts\Activate.ps1`.

### 4. Frontend

Em outro terminal:

```
cd frontend
npm install
npm run dev
```

Acesse http://localhost:5173 e crie sua conta. O Vite encaminha `/api/*` para o Flask, então o navegador fala com uma única origem.

### Depois de atualizar o código (nova etapa)

Com o `(.venv)` ativo, na pasta `backend`:

```
pip install -r requirements-dev.txt
flask --app run db upgrade
```

E na pasta `frontend`: `npm install`. Reinicie o backend e o frontend.

## Testes e verificações

```
# Backend (pasta backend, com .venv ativo). Usa TEST_DATABASE_URL; sem ela, SQLite em memória.
python -m pytest

# Frontend (pasta frontend)
npm test              # Vitest
npm run typecheck     # TypeScript
npm run lint          # oxlint
npm run build         # build de produção
```

## Comandos úteis

| Comando (pasta `backend`, `.venv` ativo) | Para que serve |
|---|---|
| `flask --app run db upgrade` | Aplica as migrações pendentes |
| `flask --app run db migrate -m "mensagem"` | Gera uma migração a partir dos modelos |
| `flask --app run db check` | Confere se os modelos e as migrações estão em sincronia |
| `flask --app run cleanup-sessions` | Apaga sessões expiradas |

## Problemas comuns

| Sintoma | Causa provável e solução |
|---|---|
| `'cp' não é reconhecido` | No cmd do Windows, use `copy`. |
| `Python não foi encontrado` (Microsoft Store) | Python não instalado ou fora do PATH. Instale pelo python.org marcando "Add to PATH", ou use `py`. Ative o `.venv` antes de `python run.py`. |
| "Banco de dados indisponível" na tela inicial | Senha diferente entre `POSTGRES_PASSWORD` e `DATABASE_URL`, caractere especial sem codificar na URL, banco criado com senha antiga (`down -v`) ou backend não reiniciado após editar o `.env`. |
| `password authentication failed` | O volume do banco foi criado com outra senha. `docker compose down -v` e `docker compose up -d db`. |
| "Muitas requisições" ao entrar | O limite de tentativas foi atingido (5 por conta a cada 15 min). Aguarde ou reinicie o backend em desenvolvimento. |

## Estrutura

```
studyflow-ai/
├── backend/
│   ├── app/
│   │   ├── __init__.py        # create_app(): fábrica da aplicação
│   │   ├── config.py          # configurações por ambiente + validação
│   │   ├── extensions.py      # db, migrate, cors, limiter
│   │   ├── cli.py             # comandos flask (cleanup-sessions)
│   │   ├── models/            # User, UserSession
│   │   ├── schemas/           # validação de entrada (Pydantic) e serialização
│   │   ├── routes/            # /api/health, /api/auth/*, /api/users/me*
│   │   ├── services/          # regras de negócio (auth, sessão, senha)
│   │   └── utils/             # auth, CSRF/origem, erros, logs, headers, rate limit
│   ├── migrations/            # Alembic (Flask-Migrate)
│   ├── tests/
│   └── run.py
├── frontend/
│   └── src/{components,contexts,hooks,pages,services,types,utils,styles,test}
├── docker/postgres/init/      # script que cria o banco de testes
├── docs/                      # architecture.md, database.md, security.md
├── docker-compose.yml
└── .env.example
```

## Documentação

- [Arquitetura e API](docs/architecture.md)
- [Banco de dados](docs/database.md)
- [Segurança](docs/security.md)

## Roadmap

1. ~~Fundação~~ ✅
2. ~~Usuários e segurança~~ ✅ (recuperação de senha por e-mail fica para um passo posterior)
3. Organização dos estudos (áreas, trilhas, módulos, tarefas, dashboard)
4. Tutor IA (Ollama)
5. Exercícios
6. Adaptação
7. Biblioteca e relatórios
8. Testes finais e publicação

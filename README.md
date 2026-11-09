# StudyFlow AI

Plataforma web de organização e acompanhamento de estudos com um tutor de Inteligência Artificial adaptativo, executado localmente via Ollama.

> **Status:** Etapa 1 — Fundação concluída (estrutura, API Flask, PostgreSQL, frontend React e verificação de saúde).
> Autenticação, tutor de IA e funcionalidades de estudo ainda **não** foram implementados.

## Stack

| Camada | Tecnologias |
|---|---|
| Frontend | React 19, Vite, TypeScript, React Router, Axios, CSS Modules, Vitest + Testing Library |
| Backend | Python 3.12+, Flask, Flask-SQLAlchemy, Flask-Migrate (Alembic), Flask-CORS, Pytest |
| Banco | PostgreSQL 16 (via Docker Compose em desenvolvimento) |
| IA | Ollama (a partir da Etapa 4, sempre atrás do backend) |

## Pré-requisitos

- Python **3.12+**
- Node.js **20.19+** ou **22.12+** (exigência do Vite) e npm
- Docker + Docker Compose (para o PostgreSQL) — ou um PostgreSQL 16 instalado localmente
- Git

## Como executar (desenvolvimento)

### 1. Variáveis de ambiente

```bash
cp .env.example .env
```

Edite o `.env` e preencha:

- `SECRET_KEY` — gere com `python -c "import secrets; print(secrets.token_urlsafe(48))"`
- `POSTGRES_PASSWORD` — uma senha forte só para desenvolvimento
- substitua `SUA_SENHA_AQUI` em `DATABASE_URL` e `TEST_DATABASE_URL` pela mesma senha

### 2. Banco de dados

```bash
docker compose up -d db
docker compose ps          # aguarde o estado "healthy"
```

O PostgreSQL fica acessível **apenas** em `127.0.0.1:5432`. Na primeira inicialização também é criado o banco `studyflow_test`, usado pelos testes.

> Se você já tem um PostgreSQL rodando na porta 5432, altere `POSTGRES_PORT` e a porta nas URLs do `.env`.

### 3. Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate            # Windows: .venv\Scripts\activate
pip install -r requirements-dev.txt
flask --app run db upgrade           # aplica migrações (ainda não há tabelas na Etapa 1)
python run.py                        # API em http://127.0.0.1:5001
```

Teste rápido: `curl http://127.0.0.1:5001/api/health`

### 4. Frontend

Em outro terminal:

```bash
cd frontend
npm install
npm run dev                          # http://localhost:5173
```

O Vite encaminha `/api/*` para o Flask, então o navegador fala com uma única origem.

## Testes e verificações

```bash
# Backend (usa TEST_DATABASE_URL; sem ela, SQLite em memória)
cd backend && python -m pytest

# Frontend
cd frontend
npm test              # Vitest
npm run typecheck     # TypeScript
npm run lint          # oxlint
npm run build         # build de produção
```

## Estrutura

```
studyflow-ai/
├── backend/
│   ├── app/
│   │   ├── __init__.py        # create_app(): fábrica da aplicação
│   │   ├── config.py          # configurações por ambiente + validação
│   │   ├── extensions.py      # db, migrate, cors
│   │   ├── models/            # modelos SQLAlchemy (a partir da Etapa 2)
│   │   ├── routes/            # blueprints HTTP (/api/...)
│   │   ├── services/          # regras de negócio
│   │   └── utils/             # erros, logs, headers de segurança
│   ├── migrations/            # Alembic (Flask-Migrate)
│   ├── tests/
│   ├── requirements.txt / requirements-dev.txt
│   └── run.py
├── frontend/
│   └── src/{components,pages,services,hooks,types,styles,test}
├── docker/postgres/init/      # script que cria o banco de testes
├── docs/                      # architecture.md, database.md, security.md
├── docker-compose.yml
├── .env.example
└── README.md
```

## Documentação

- [Arquitetura](docs/architecture.md)
- [Banco de dados](docs/database.md)
- [Segurança](docs/security.md)

## Roadmap

1. ~~Fundação~~ ✅
2. Usuários e segurança (cadastro, login, sessões com cookie HttpOnly, CSRF, rate limiting)
3. Organização dos estudos (áreas, trilhas, módulos, tarefas, dashboard)
4. Tutor IA (Ollama)
5. Exercícios
6. Adaptação
7. Biblioteca e relatórios
8. Testes finais e publicação

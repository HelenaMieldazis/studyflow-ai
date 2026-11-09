# Banco de dados

## Visão geral

- PostgreSQL 16 via `docker-compose.yml` (imagem oficial `postgres:16.15-alpine`).
- Bancos: `studyflow` (desenvolvimento) e `studyflow_test` (testes automatizados).
- Conexão: SQLAlchemy 2 + `psycopg` 3 (`postgresql+psycopg://...`).
- Migrações: Flask-Migrate/Alembic em `backend/migrations/`.

## Migrações

| Revisão | Descrição |
|---|---|
| `ba9543b57066` | Cria `users` e `user_sessions` (Etapa 2) |

## Tabelas

### `users`

| Coluna | Tipo | Restrições | Observação |
|---|---|---|---|
| `id` | `uuid` | PK | Gerado pela aplicação (`uuid4`) |
| `email` | `varchar(254)` | NOT NULL, UNIQUE, CHECK `email = lower(email)` | Sempre normalizado em minúsculas |
| `display_name` | `varchar(80)` | NOT NULL, CHECK `length > 0` | Sem caracteres de controle |
| `password_hash` | `varchar(255)` | NOT NULL | Formato PHC do Argon2id |
| `password_changed_at` | `timestamptz` | NOT NULL | |
| `created_at` | `timestamptz` | NOT NULL, default `now()` | |
| `updated_at` | `timestamptz` | NOT NULL, default `now()` | Atualizado a cada alteração |

### `user_sessions`

| Coluna | Tipo | Restrições | Observação |
|---|---|---|---|
| `id` | `uuid` | PK | |
| `user_id` | `uuid` | NOT NULL, FK → `users.id` **ON DELETE CASCADE**, índice | Excluir o usuário apaga as sessões |
| `token_hash` | `varchar(64)` | NOT NULL, UNIQUE | SHA-256 do token do cookie, nunca o token |
| `created_at` | `timestamptz` | NOT NULL, default `now()` | |
| `last_seen_at` | `timestamptz` | NOT NULL | Base da expiração por inatividade |
| `expires_at` | `timestamptz` | NOT NULL, índice | Expiração absoluta; índice usado na limpeza |

**Dados que deliberadamente NÃO são guardados nas sessões:** endereço IP e user agent (minimização de dados, LGPD).

## Convenções

- **Nomes de constraints determinísticos** (`app/extensions.py`): `pk_<tabela>`, `fk_<tabela>_<coluna>_<tabela_ref>`, `uq_<tabela>_<coluna>`, `ix_<...>`, `ck_<tabela>_<nome>`.
- Tabelas no plural, `snake_case`.
- Datas sempre `timestamptz`, gravadas em UTC.
- Toda tabela com dados do usuário terá `user_id` com FK para `users.id`, `ON DELETE CASCADE` e índice. Assim, a exclusão de conta apaga tudo automaticamente.
- Chaves primárias UUID para entidades expostas na API.

## Comandos

Dentro de `backend/`, com o ambiente virtual ativo:

```
flask --app run db upgrade                             # aplica migrações pendentes
flask --app run db migrate -m "descrição da mudança"   # gera migração a partir dos modelos
flask --app run db downgrade                           # desfaz a última
flask --app run db current                             # revisão atual
flask --app run db check                               # modelos e migrações em sincronia?
flask --app run cleanup-sessions                       # apaga sessões expiradas
```

Sempre revise o arquivo gerado em `migrations/versions/` antes de aplicar e faça commit dele junto com a mudança no modelo.

## Entidades planejadas

| Etapa | Tabelas |
|---|---|
| ~~2~~ | ~~`users`~~, `user_sessions` ✅ |
| 3 | `study_areas`, `study_tracks`, `study_modules`, `study_tasks`, `study_sessions` |
| 4 | `chat_conversations`, `chat_messages` |
| 5 | `exercises`, `exercise_attempts` |
| 6 | `topic_progress`, `recommendations` |
| 7 | `materials` |

## Backup (desenvolvimento)

```
docker compose exec db pg_dump -U studyflow -d studyflow -Fc > backup.dump
docker compose exec -T db pg_restore -U studyflow -d studyflow --clean < backup.dump
```

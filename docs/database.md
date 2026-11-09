# Banco de dados

## Estado atual (Etapa 1)

- PostgreSQL 16 configurado via `docker-compose.yml` (imagem oficial `postgres:16.15-alpine`).
- Bancos: `studyflow` (desenvolvimento) e `studyflow_test` (testes automatizados).
- Conexão pelo SQLAlchemy 2 + driver `psycopg` 3 (`postgresql+psycopg://...`).
- Flask-Migrate/Alembic inicializado em `backend/migrations/`. **Ainda não há tabelas nem migrações.**

## Convenções adotadas

- **Nomes de constraints determinísticos** (`app/extensions.py`):
  `pk_<tabela>`, `fk_<tabela>_<coluna>_<tabela_ref>`, `uq_<tabela>_<coluna>`, `ix_<...>`, `ck_<tabela>_<nome>`.
  Isso deixa as migrações reproduzíveis e permite remover/alterar constraints com segurança.
- Tabelas no plural, `snake_case` (ex.: `study_tracks`).
- Toda tabela de domínio terá `id`, `created_at` e `updated_at` (timestamps com fuso horário, em UTC).
- Toda tabela com dados do usuário terá `user_id` com FK para `users.id` e `ON DELETE CASCADE`, além de índice em `user_id`.

## Comandos de migração

Executar dentro de `backend/` com o ambiente virtual ativo:

```bash
flask --app run db migrate -m "descrição da mudança"   # gera a migração a partir dos modelos
flask --app run db upgrade                             # aplica
flask --app run db downgrade                           # desfaz a última
flask --app run db current                             # mostra a revisão atual
```

Sempre revise o arquivo gerado em `migrations/versions/` antes de aplicar e faça commit dele junto com a mudança no modelo.

## Entidades planejadas

| Etapa | Tabelas |
|---|---|
| 2 | `users` |
| 3 | `study_areas`, `study_tracks`, `study_modules`, `study_tasks`, `study_sessions` |
| 4 | `chat_conversations`, `chat_messages` |
| 5 | `exercises`, `exercise_attempts` |
| 6 | `topic_progress`, `recommendations` |
| 7 | `materials` |

O modelo detalhado de cada tabela será documentado aqui quando ela for criada.

## Backup (desenvolvimento)

```bash
docker compose exec db pg_dump -U studyflow -d studyflow -Fc > backup.dump
docker compose exec -T db pg_restore -U studyflow -d studyflow --clean < backup.dump
```

A política de backup e o teste de restauração de produção serão definidos na Etapa 8.

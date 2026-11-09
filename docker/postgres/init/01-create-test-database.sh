#!/bin/sh
# Executado pela imagem oficial do PostgreSQL apenas na PRIMEIRA inicialização
# do volume. Cria um banco separado para os testes automatizados, para que os
# testes nunca toquem no banco de desenvolvimento.
set -eu

TEST_DB="${POSTGRES_TEST_DB:-studyflow_test}"

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" \
  -v test_db="$TEST_DB" -v owner="$POSTGRES_USER" <<-'EOSQL'
	SELECT format('CREATE DATABASE %I OWNER %I', :'test_db', :'owner')
	WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = :'test_db')\gexec
EOSQL

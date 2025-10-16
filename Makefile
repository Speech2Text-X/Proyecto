SHELL := /bin/bash
DB_URL ?= postgresql://$(POSTGRES_USER):$(POSTGRES_PASSWORD)@localhost:$(POSTGRES_PORT)/$(POSTGRES_DB)

export POSTGRES_DB ?= s2x
export POSTGRES_USER ?= postgres
export POSTGRES_PASSWORD ?= postgres
export POSTGRES_PORT ?= 5432
export PGADMIN_EMAIL ?= admin@local
export PGADMIN_PASSWORD ?= admin
export PGADMIN_PORT ?= 5050

.PHONY: help
help:
	@echo "Targets:"
	@echo "  db-up           - Levantar Postgres + pgAdmin"
	@echo "  db-down         - Bajar contenedores (sin borrar datos)"
	@echo "  db-destroy      - Bajar y borrar volumen de datos"
	@echo "  db-logs         - Ver logs"
	@echo "  db-psql         - Abrir psql dentro del contenedor"
	@echo "  db-init         - Ejecutar SQLs (extensiones + schema + índices)"
	@echo "  db-migrate      - Sinónimo de db-init"
	@echo "  seed            - Semilla de ejemplo"
	@echo "  py-venv         - Crear venv y deps psycopg"
	@echo "  py-test         - Probar conexión simple"

db-up:
	docker compose up -d

db-down:
	docker compose down

db-destroy:
	docker compose down -v

db-logs:
	docker compose logs -f

db-psql:
	docker exec -it s2x-postgres psql -U $(POSTGRES_USER) -d $(POSTGRES_DB)

# Ejecuta SQLs en orden
db-init db-migrate:
	docker exec -i s2x-postgres psql -U $(POSTGRES_USER) -d $(POSTGRES_DB) < db/00_extensions.sql
	docker exec -i s2x-postgres psql -U $(POSTGRES_USER) -d $(POSTGRES_DB) < db/01_schema.sql
	docker exec -i s2x-postgres psql -U $(POSTGRES_USER) -d $(POSTGRES_DB) < db/idx_text_search.sql

seed:
	docker exec -i s2x-postgres psql -U $(POSTGRES_USER) -d $(POSTGRES_DB) < scripts/seed.sql

py-venv:
	python3 -m venv .venv && . .venv/bin/activate && pip install --upgrade pip && pip install "psycopg[binary,pool]>=3.2.0"

py-test:
	python - <<'PY'
from app.db_pool import get_conn
with get_conn() as c, c.cursor() as cur:
    cur.execute('select 1')
    print('DB OK ->', cur.fetchone()[0])
PY


api-run:
	uvicorn app.main:app --reload --port 8000

api-prod:
	uvicorn app.main:app --host 0.0.0.0 --port 8000

# ============================================
# SISPAD-PEI-POA — Makefile
# ============================================
# Comandos para desarrollo local con Docker
# Uso: make <target>
# ============================================

# Cargar variables de entorno desde .env (si existe)
ifneq (,$(wildcard .env))
    include .env
    export
endif

.PHONY: setup build up down restart logs migrate makemigrations createsuperuser seed test test-backend test-frontend lint format shell dbshell backup backup-db backup-minio backup-geoserver restore-db restore-minio restore-geoserver openapi clean full-reset env

# --- Infraestructura ---
setup: build up migrate seed

build:
	docker compose --profile dev build

up:
	docker compose --profile dev up -d

down:
	docker compose --profile dev down

restart: down up

logs:
	docker compose logs -f

# --- Django ---
migrate:
	docker compose exec backend python manage.py migrate

makemigrations:
	docker compose exec backend python manage.py makemigrations

createsuperuser:
	docker compose exec backend python manage.py createsuperuser

seed:
	docker compose exec backend python manage.py shell -c "exec(open('scripts/seed.py').read())" || echo "Seed ya ejecutado o script no encontrado"

shell:
	docker compose exec backend python manage.py shell

dbshell:
	docker compose exec postgres-postgis psql -U $(DB_USER) -d $(DB_NAME)

# --- Testing ---
test:
	docker compose exec backend python -m pytest

test-backend:
	docker compose exec backend python -m pytest apps/ -v

test-frontend:
	docker compose exec frontend npm test -- --watch=false

# --- Calidad ---
lint:
	docker compose exec backend ruff check . || echo "ruff no instalado"

format:
	docker compose exec backend ruff format . || echo "ruff no instalado"

# === Backups ===

.PHONY: backup backup-db backup-minio backup-geoserver restore-db restore-minio restore-geoserver

backup:
	@echo "=== Backup completo del sistema ==="
	@mkdir -p backups
	@./infra/backup/backup_database.sh backups
	@echo "Backup de base de datos completado."
	@echo "Para backup de MinIO: ./infra/backup/backup_minio.sh"
	@echo "Para backup de GeoServer: ./infra/backup/backup_geoserver.sh"

backup-db:
	@./infra/backup/backup_database.sh backups

backup-minio:
	@./infra/backup/backup_minio.sh backups

backup-geoserver:
	@./infra/backup/backup_geoserver.sh backups

restore-db:
	@if [ -z "$(FILE)" ]; then echo "Uso: make restore-db FILE=backups/archivo.dump"; exit 1; fi
	@./infra/backup/restore_database.sh $(FILE)

restore-minio:
	@if [ -z "$(DIR)" ]; then echo "Uso: make restore-minio DIR=backups/minio/20260101_120000"; exit 1; fi
	@./infra/backup/restore_minio.sh $(DIR)

restore-geoserver:
	@if [ -z "$(DIR)" ]; then echo "Uso: make restore-geoserver DIR=backups/geoserver/20260101_120000"; exit 1; fi
	@./infra/backup/restore_geoserver.sh $(DIR)

# --- Documentación ---
openapi:
	docker compose exec backend python manage.py spectacular --file /tmp/schema.yml
	docker compose cp backend:/tmp/schema.yml ./schema.yml

# --- Utilidades ---
clean:
	docker compose down -v
	docker system prune -f

full-reset: down
	docker compose --profile dev build --no-cache
	docker compose --profile dev up -d
	make migrate
	make seed

env:
	@echo "Copiando .env.example a .env (no sobrescribe si existe)"
	cp -n .env.example .env 2>/dev/null || echo ".env ya existe"

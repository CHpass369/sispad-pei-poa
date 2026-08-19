# ============================================
# PIP-GAMS — Makefile
# ============================================
# Despliegue local: PostgreSQL nativo, sin contenedores.
# Uso: make <target>
# ============================================

# Cargar variables de entorno desde .env (si existe)
ifneq (,$(wildcard .env))
    include .env
    export
endif

PYTHON ?= .venv/bin/python
BACKEND ?= backend
FRONTEND ?= frontend/sispoa

.PHONY: setup migrate makemigrations createsuperuser seed shell dbshell \
        test test-backend test-frontend lint format \
        backup backup-db restore-db openapi build-frontend clean env help

help:
	@echo "PIP-GAMS — comandos disponibles:"
	@grep -E '^[a-z][a-z-]*:.*?## .*$$' $(MAKEFILE_LIST) \
	  | awk 'BEGIN{FS=":.*?## "}{printf "  \033[36m%-18s\033[0m %s\n", $$1, $$2}'

# --- Puesta en marcha ---

setup: env migrate seed ## Prepara el entorno: .env, migraciones y semillas

env: ## Copia .env.example a .env (no sobrescribe)
	@cp -n .env.example .env 2>/dev/null || echo ".env ya existe"

# --- Base de datos ---

migrate: ## Aplica las migraciones pendientes
	cd $(BACKEND) && ../$(PYTHON) manage.py migrate

makemigrations: ## Genera migraciones a partir de los modelos
	cd $(BACKEND) && ../$(PYTHON) manage.py makemigrations

createsuperuser: ## Crea un superusuario
	cd $(BACKEND) && ../$(PYTHON) manage.py createsuperuser

seed: ## Siembra los datos base
	cd $(BACKEND) && ../$(PYTHON) manage.py shell -c "exec(open('scripts/seed.py').read())"

shell: ## Abre la consola de Django
	cd $(BACKEND) && ../$(PYTHON) manage.py shell

dbshell: ## Abre psql contra la base configurada
	@PGPASSWORD="$(DB_PASSWORD)" psql -h "$(DB_HOST)" -p "$(DB_PORT)" -U "$(DB_USER)" -d "$(DB_NAME)"

# --- Calidad ---

test: test-backend ## Alias de test-backend

test-backend: ## Suite de pytest
	cd $(BACKEND) && ../$(PYTHON) -m pytest

test-frontend: ## Suite de Karma. Chromium por snap necesita TMPDIR fuera de /tmp
	cd $(FRONTEND) && TMPDIR="$$HOME/karma-tmp" \
	  npx ng test --watch=false --browsers=ChromeHeadlessNoSandbox

lint: ## Ruff sobre el backend
	cd $(BACKEND) && ../$(PYTHON) -m ruff check .

format: ## Formatea el backend con ruff
	cd $(BACKEND) && ../$(PYTHON) -m ruff format .

build-frontend: ## Compila el frontend para producción
	cd $(FRONTEND) && npx ng build --configuration production

openapi: ## Genera el esquema OpenAPI en ./schema.yml
	cd $(BACKEND) && ../$(PYTHON) manage.py spectacular --file ../schema.yml

# --- Respaldos ---

backup: backup-db ## Respaldo completo (hoy: solo base de datos)

backup-db: ## Vuelca la base a backups/ en formato custom
	@mkdir -p backups
	@./infra/backup/backup_database.sh backups

restore-db: ## Restaura un dump: make restore-db FILE=backups/archivo.dump
	@if [ -z "$(FILE)" ]; then \
	  echo "Uso: make restore-db FILE=backups/archivo.dump"; exit 1; fi
	@./infra/backup/restore_database.sh "$(FILE)"

# --- Limpieza ---

clean: ## Borra artefactos de compilación y cachés
	@find . -type d -name __pycache__ -not -path "./node_modules/*" -exec rm -rf {} + 2>/dev/null || true
	@rm -rf $(FRONTEND)/dist .pytest_cache
	@echo "Artefactos eliminados."

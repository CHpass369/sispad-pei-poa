#!/bin/bash
set -e

echo "=== SISPOA Backend — Entrypoint ==="

echo "→ Ejecutando migraciones..."
python manage.py migrate --noinput

echo "→ Recolectando archivos estáticos..."
python manage.py collectstatic --noinput || true

echo "→ Sembrando datos iniciales..."
python manage.py shell -c "exec(open('scripts/seed.py').read())" || true

echo "→ Iniciando Gunicorn..."
exec gunicorn config.wsgi:application -c /gunicorn.conf.py

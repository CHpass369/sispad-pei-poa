#!/bin/bash
set -e

echo "=== SISPOA Backend — Entrypoint ==="

echo "→ Ejecutando migraciones..."
python manage.py migrate --noinput

echo "→ Recolectando archivos estáticos..."
python manage.py collectstatic --noinput || true

if [[ "${SEED_DEMO_DATA:-false}" =~ ^(1|true|yes|on)$ ]]; then
  echo "→ Sembrando datos demo (SEED_DEMO_DATA=${SEED_DEMO_DATA})..."
  python manage.py shell -c "exec(open('scripts/seed.py').read())"
else
  echo "→ Seed demo omitido (SEED_DEMO_DATA no está habilitado)."
fi

echo "→ Iniciando Gunicorn..."
exec gunicorn config.wsgi:application -c /gunicorn.conf.py

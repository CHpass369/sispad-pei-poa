#!/bin/bash
# Respaldo de PostgreSQL + PostGIS (instalación local, sin contenedores).
# Uso: ./backup_database.sh [directorio_destino]
#
# Toma las credenciales de .env en la raíz del repositorio.

set -euo pipefail

RAIZ="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
DESTINO="${1:-${RAIZ}/backups}"

if [ -f "${RAIZ}/.env" ]; then
  set -a; . "${RAIZ}/.env"; set +a
fi

DB_NAME="${DB_NAME:-gams_pip}"
DB_USER="${DB_USER:-postgres}"
DB_HOST="${DB_HOST:-localhost}"
DB_PORT="${DB_PORT:-5432}"

SELLO="$(date +%Y%m%d-%H%M%S)"
ARCHIVO="${DESTINO}/${DB_NAME}-${SELLO}.dump"

mkdir -p "${DESTINO}"
export PGPASSWORD="${DB_PASSWORD:-}"

echo "[$(date '+%F %T')] Respaldando ${DB_NAME} desde ${DB_HOST}:${DB_PORT}..."

# Formato custom: comprimido y restaurable de forma selectiva con pg_restore.
pg_dump -h "${DB_HOST}" -p "${DB_PORT}" -U "${DB_USER}" -d "${DB_NAME}" \
        -Fc -f "${ARCHIVO}"

# Un respaldo que no se puede listar no es un respaldo.
if ! pg_restore -l "${ARCHIVO}" > /dev/null 2>&1; then
  echo "ERROR: el archivo generado no es un dump válido." >&2
  exit 1
fi

OBJETOS="$(pg_restore -l "${ARCHIVO}" | grep -c '^[0-9]')"
echo "[$(date '+%F %T')] Listo: ${ARCHIVO}"
echo "  tamaño:  $(du -h "${ARCHIVO}" | cut -f1)"
echo "  objetos: ${OBJETOS}"

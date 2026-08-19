#!/bin/bash
# Restauración de PostgreSQL + PostGIS (instalación local, sin contenedores).
# Uso: ./restore_database.sh <archivo.dump> [base_destino]
#
# Por defecto restaura sobre una base NUEVA llamada <DB_NAME>_restore, para no
# pisar la base en uso. Para restaurar sobre la real hay que nombrarla
# explícitamente como segundo argumento.

set -euo pipefail

ARCHIVO="${1:-}"
if [ -z "${ARCHIVO}" ] || [ ! -f "${ARCHIVO}" ]; then
  echo "Uso: $0 <archivo.dump> [base_destino]" >&2
  exit 1
fi

RAIZ="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
if [ -f "${RAIZ}/.env" ]; then
  set -a; . "${RAIZ}/.env"; set +a
fi

DB_USER="${DB_USER:-postgres}"
DB_HOST="${DB_HOST:-localhost}"
DB_PORT="${DB_PORT:-5432}"
DESTINO="${2:-${DB_NAME:-gams_pip}_restore}"

export PGPASSWORD="${DB_PASSWORD:-}"

if [ "${DESTINO}" = "${DB_NAME:-}" ]; then
  echo "ATENCIÓN: va a restaurar SOBRE la base en uso (${DESTINO})."
  read -r -p "Escriba 'confirmo' para continuar: " respuesta
  [ "${respuesta}" = "confirmo" ] || { echo "Cancelado."; exit 1; }
fi

echo "[$(date '+%F %T')] Restaurando ${ARCHIVO} en ${DESTINO}..."
createdb -h "${DB_HOST}" -p "${DB_PORT}" -U "${DB_USER}" "${DESTINO}" 2>/dev/null \
  || echo "  (la base ${DESTINO} ya existía)"

pg_restore -h "${DB_HOST}" -p "${DB_PORT}" -U "${DB_USER}" -d "${DESTINO}" \
           --no-owner --no-privileges "${ARCHIVO}"

TABLAS="$(psql -h "${DB_HOST}" -p "${DB_PORT}" -U "${DB_USER}" -d "${DESTINO}" -tAc \
  "select count(*) from pg_stat_user_tables")"
echo "[$(date '+%F %T')] Listo: ${DESTINO} con ${TABLAS} tablas."

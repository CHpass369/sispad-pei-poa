#!/bin/bash
# Restauración de PostgreSQL + PostGIS
# Uso: ./restore_database.sh <backup_file>

set -e

BACKUP_FILE="${1}"
if [ -z "${BACKUP_FILE}" ]; then
  echo "❌ Uso: $0 <archivo_backup.dump>"
  echo "   Ej: $0 ./backups/sispoa_db_20260101_120000.dump"
  exit 1
fi

if [ ! -f "${BACKUP_FILE}" ]; then
  echo "❌ Archivo no encontrado: ${BACKUP_FILE}"
  exit 1
fi

DB_CONTAINER="${DB_CONTAINER:-postgres-postgis}"
DB_NAME="${DB_NAME:-gams_sis_poa}"
DB_USER="${DB_USER:-sispoa_user}"

echo "[$(date '+%Y-%m-%d %H:%M:%S')] Iniciando restauración de ${BACKUP_FILE}..."

# Copiar backup al contenedor
echo "Copiando backup al contenedor..."
docker compose cp "${BACKUP_FILE}" "${DB_CONTAINER}:/tmp/restore.dump"

# Restaurar
echo "Restaurando base de datos ${DB_NAME}..."
docker compose exec -T "${DB_CONTAINER}" pg_restore \
  -U "${DB_USER}" \
  -d "${DB_NAME}" \
  --clean \
  --if-exists \
  --no-owner \
  --no-acl \
  -v \
  "/tmp/restore.dump" 2>&1

# Limpiar
docker compose exec -T "${DB_CONTAINER}" rm -f /tmp/restore.dump

echo "✅ Restauración completada"

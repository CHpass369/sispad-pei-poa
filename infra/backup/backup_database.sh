#!/bin/bash
# Backup de PostgreSQL + PostGIS
# Uso: ./backup_database.sh [output_dir]

set -e

BACKUP_DIR="${1:-./backups}"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
DB_CONTAINER="${DB_CONTAINER:-postgres-postgis}"
DB_NAME="${DB_NAME:-gams_sis_poa}"
DB_USER="${DB_USER:-sispoa_user}"
BACKUP_FILE="${BACKUP_DIR}/sispoa_db_${TIMESTAMP}.dump"
LOG_FILE="${BACKUP_DIR}/backup_${TIMESTAMP}.log"

mkdir -p "${BACKUP_DIR}"

echo "[$(date '+%Y-%m-%d %H:%M:%S')] Iniciando backup de ${DB_NAME}..." | tee -a "${LOG_FILE}"

# Backup con pg_dump en formato custom (comprimido, paralelizable)
docker compose exec -T "${DB_CONTAINER}" pg_dump \
  -U "${DB_USER}" \
  -d "${DB_NAME}" \
  -F c \
  -v \
  -f "/tmp/$(basename ${BACKUP_FILE})" 2>&1 | tee -a "${LOG_FILE}"

# Copiar el backup del contenedor al host
docker compose cp "${DB_CONTAINER}:/tmp/$(basename ${BACKUP_FILE})" "${BACKUP_FILE}" 2>&1 | tee -a "${LOG_FILE}"

# Limpiar archivo temporal en el contenedor
docker compose exec -T "${DB_CONTAINER}" rm -f "/tmp/$(basename ${BACKUP_FILE})"

# Validar backup
if [ -f "${BACKUP_FILE}" ]; then
  echo "Backup creado: ${BACKUP_FILE}" | tee -a "${LOG_FILE}"
  ls -lh "${BACKUP_FILE}" | tee -a "${LOG_FILE}"

  # Validar integridad con pg_restore --list
  if docker compose exec -T "${DB_CONTAINER}" pg_restore -l "/tmp/$(basename ${BACKUP_FILE})" > /dev/null 2>&1; then
    echo "✅ Backup validado correctamente" | tee -a "${LOG_FILE}"
  else
    echo "⚠️ No se pudo validar el backup (puede estar incompleto)" | tee -a "${LOG_FILE}"
    exit 1
  fi
else
  echo "❌ ERROR: No se creó el archivo de backup" | tee -a "${LOG_FILE}"
  exit 1
fi

echo "[$(date '+%Y-%m-%d %H:%M:%S')] Backup completado: $(du -h "${BACKUP_FILE}" | cut -f1)" | tee -a "${LOG_FILE}"

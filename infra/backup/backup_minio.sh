#!/bin/bash
# Backup de MinIO (S3) usando mc mirror
# Uso: ./backup_minio.sh [output_dir]

set -e

BACKUP_DIR="${1:-./backups/minio}"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
MINIO_CONTAINER="${MINIO_CONTAINER:-minio}"
MINIO_ALIAS="${MINIO_ALIAS:-sispoa}"
MINIO_USER="${MINIO_ROOT_USER:-sispoa_admin}"
MINIO_PASS="${MINIO_ROOT_PASSWORD:-sispoa_minio_secret}"
BUCKET="${MINIO_BUCKET_NAME:-sispoa-docs}"
BACKUP_PATH="${BACKUP_DIR}/${TIMESTAMP}"

mkdir -p "${BACKUP_PATH}"

echo "[$(date)] Iniciando backup de MinIO bucket '${BUCKET}'..."

# Configurar alias mc dentro del contenedor
docker compose exec -T "${MINIO_CONTAINER}" mc alias set \
  "${MINIO_ALIAS}" http://localhost:9000 "${MINIO_USER}" "${MINIO_PASS}"

# Mirror del bucket al host via volumen temporal
docker compose exec -T "${MINIO_CONTAINER}" mc mirror \
  "${MINIO_ALIAS}/${BUCKET}" "/tmp/minio_backup_${TIMESTAMP}"

# Copiar al host
docker compose cp \
  "${MINIO_CONTAINER}:/tmp/minio_backup_${TIMESTAMP}/." "${BACKUP_PATH}/"

# Limpiar
docker compose exec -T "${MINIO_CONTAINER}" rm -rf "/tmp/minio_backup_${TIMESTAMP}"

echo "✅ Backup MinIO completado: ${BACKUP_PATH}"
echo "   Archivos: $(find "${BACKUP_PATH}" -type f | wc -l)"

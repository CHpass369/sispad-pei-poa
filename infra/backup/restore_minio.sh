#!/bin/bash
# Restauración de MinIO usando mc mirror
# Uso: ./restore_minio.sh <backup_path>

set -e

BACKUP_PATH="${1}"
if [ -z "${BACKUP_PATH}" ]; then
  echo "❌ Uso: $0 <backup_path>"
  echo "   Ej: $0 ./backups/minio/20260101_120000"
  exit 1
fi

if [ ! -d "${BACKUP_PATH}" ]; then
  echo "❌ Directorio no encontrado: ${BACKUP_PATH}"
  exit 1
fi

MINIO_CONTAINER="${MINIO_CONTAINER:-minio}"
MINIO_ALIAS="${MINIO_ALIAS:-sispoa}"
# Fail-closed: no hay credenciales por defecto. Sin MINIO_ROOT_PASSWORD el
# script aborta antes de intentar autenticarse.
MINIO_USER="${MINIO_ROOT_USER:?MINIO_ROOT_USER debe estar definido en el entorno}"
MINIO_PASS="${MINIO_ROOT_PASSWORD:?MINIO_ROOT_PASSWORD debe estar definido en el entorno}"
BUCKET="${MINIO_BUCKET_NAME:-sispoa-docs}"

TIMESTAMP=$(basename "${BACKUP_PATH}")

echo "[$(date)] Restaurando MinIO bucket '${BUCKET}' desde ${BACKUP_PATH}..."

# Copiar al contenedor
docker compose cp "${BACKUP_PATH}/." "${MINIO_CONTAINER}:/tmp/minio_restore_${TIMESTAMP}/"

# Configurar alias y restaurar
docker compose exec -T "${MINIO_CONTAINER}" mc alias set \
  "${MINIO_ALIAS}" http://localhost:9000 "${MINIO_USER}" "${MINIO_PASS}"

docker compose exec -T "${MINIO_CONTAINER}" mc mirror --overwrite \
  "/tmp/minio_restore_${TIMESTAMP}" "${MINIO_ALIAS}/${BUCKET}"

# Limpiar
docker compose exec -T "${MINIO_CONTAINER}" rm -rf "/tmp/minio_restore_${TIMESTAMP}"

echo "✅ Restauración MinIO completada"

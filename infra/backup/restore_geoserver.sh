#!/bin/bash
# Restauración de GeoServer (data dir)
# Uso: ./restore_geoserver.sh <backup_path>

set -e

BACKUP_PATH="${1}"
if [ -z "${BACKUP_PATH}" ]; then
  echo "❌ Uso: $0 <backup_path>"
  echo "   Ej: $0 ./backups/geoserver/20260101_120000"
  exit 1
fi

if [ ! -d "${BACKUP_PATH}/data" ]; then
  echo "❌ Directorio de data no encontrado en: ${BACKUP_PATH}"
  exit 1
fi

GS_CONTAINER="${GS_CONTAINER:-geoserver}"

echo "[$(date)] Restaurando GeoServer desde ${BACKUP_PATH}..."

# Restaurar data directory
docker compose cp "${BACKUP_PATH}/data/." "${GS_CONTAINER}:/var/geoserver/data/"

# Restart GeoServer para recargar configuración
docker compose restart "${GS_CONTAINER}"

echo "✅ GeoServer reiniciado con la configuración restaurada"

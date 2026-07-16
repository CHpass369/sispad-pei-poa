#!/bin/bash
# Backup de GeoServer (data dir + REST export)
# Uso: ./backup_geoserver.sh [output_dir]

set -e

BACKUP_DIR="${1:-./backups/geoserver}"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
GS_CONTAINER="${GS_CONTAINER:-geoserver}"
GS_USER="${GEOSERVER_ADMIN_USER:-admin}"
GS_PASS="${GEOSERVER_ADMIN_PASSWORD:-geoserver_secret}"
GS_URL="http://${GS_CONTAINER}:8080/geoserver"
BACKUP_PATH="${BACKUP_DIR}/${TIMESTAMP}"

mkdir -p "${BACKUP_PATH}"

echo "[$(date)] Iniciando backup de GeoServer..."

# Exportar config REST API
echo "Exportando configuración REST..."
curl -s -u "${GS_USER}:${GS_PASS}" \
  "${GS_URL}/rest/workspaces.json" \
  -o "${BACKUP_PATH}/workspaces.json" || echo "⚠️ No se pudo exportar workspaces"

curl -s -u "${GS_USER}:${GS_PASS}" \
  "${GS_URL}/rest/layers.json" \
  -o "${BACKUP_PATH}/layers.json" || echo "⚠️ No se pudo exportar layers"

curl -s -u "${GS_USER}:${GS_PASS}" \
  "${GS_URL}/rest/styles.json" \
  -o "${BACKUP_PATH}/styles.json" || echo "⚠️ No se pudo exportar estilos"

# Backup del data directory
echo "Respaldando data directory..."
docker compose cp \
  "${GS_CONTAINER}:/var/geoserver/data/." "${BACKUP_PATH}/data/"

echo "✅ Backup GeoServer completado: ${BACKUP_PATH}"

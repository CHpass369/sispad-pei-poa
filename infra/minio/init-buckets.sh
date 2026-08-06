#!/bin/bash
# =============================================================================
# SISPAD-PEI-POA — Inicialización de buckets MinIO
# Ejecutar después de que MinIO esté saludable.
# =============================================================================
# Uso:
#   docker compose --profile full exec minio /bin/sh -c "$(cat infra/minio/init-buckets.sh)"
# O dentro del contenedor:
#   bash /infra/minio/init-buckets.sh
# =============================================================================

set -e

MC_HOST="${MC_HOST:-sispoa-minio:9000}"
MC_ALIAS="${MC_ALIAS:-sispoa}"
# Fail-closed: no hay credenciales por defecto. Sin MINIO_ROOT_PASSWORD el
# script aborta antes de intentar autenticarse.
MC_ROOT_USER="${MINIO_ROOT_USER:?MINIO_ROOT_USER debe estar definido en el entorno}"
MC_ROOT_PASSWORD="${MINIO_ROOT_PASSWORD:?MINIO_ROOT_PASSWORD debe estar definido en el entorno}"
BUCKET="${MINIO_BUCKET_NAME:-sispoa-docs}"

echo "Esperando a que MinIO esté listo..."
until mc alias set ${MC_ALIAS} http://${MC_HOST} ${MC_ROOT_USER} ${MC_ROOT_PASSWORD} 2>/dev/null; do
  echo "MinIO no está listo aún..."
  sleep 2
done

echo "Creando bucket ${BUCKET}..."
mc mb ${MC_ALIAS}/${BUCKET} --ignore-existing

echo "Configurando política private..."
mc anonymous set private ${MC_ALIAS}/${BUCKET}

echo "✅ Bucket ${BUCKET} listo"

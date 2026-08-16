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

MC_HOST="${MC_HOST:-pip-minio:9000}"
MC_ALIAS="${MC_ALIAS:-pip}"
MC_ROOT_USER="${MINIO_ROOT_USER:-pip_admin}"
MC_ROOT_PASSWORD="${MINIO_ROOT_PASSWORD:-pip_minio_secret}"
BUCKET="${MINIO_BUCKET_NAME:-pip-docs}"

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

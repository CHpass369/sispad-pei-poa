#!/bin/bash
# =============================================================================
# init-workspace.sh — Inicializa workspace + stores + layers en GeoServer
# =============================================================================
# Ejecutar DESPUÉS de que GeoServer esté saludable (healthcheck OK).
# Idempotente: se puede ejecutar múltiples veces sin duplicar resources.
#
# Uso:
#   docker compose exec geoserver bash /var/geoserver/data/init-workspace.sh
#
# O desde fuera:
#   docker compose run --rm geoserver bash -c "
#     apt-get update && apt-get install -y curl &&
#     /var/geoserver/data/init-workspace.sh
#   "
# =============================================================================

set -euo pipefail

# ---------------------------------------------------------------------------
# Configuración desde entorno (con defaults alineados con .env.example)
# ---------------------------------------------------------------------------
GS_URL="${GS_URL:-http://sispoa-geoserver:8080/geoserver}"
GS_USER="${GEOSERVER_ADMIN_USER:-admin}"
GS_PASS="${GEOSERVER_ADMIN_PASSWORD:-changeme-geoserver}"
WS_NAME="${GEOSERVER_WORKSPACE:-sispoa}"

DB_HOST="${DB_HOST:-sispoa-postgres}"
DB_PORT="${DB_PORT:-5432}"
DB_NAME="${DB_NAME:-gams_sis_poa}"
DB_USER="${DB_USER:-sispoa_user}"
DB_PASS="${DB_PASSWORD:-changeme-segura}"

STORE_NAME="sispoa_postgis"

# ---------------------------------------------------------------------------
# Layers a publicar (nombres de tabla = app_model en lowercase)
# ---------------------------------------------------------------------------
LAYERS=(
  "territorio_distrito"
  "territorio_unidadterritorial"
  "territorio_localizacionterritorial"
)

# ---------------------------------------------------------------------------
# Funciones auxiliares
# ---------------------------------------------------------------------------
log()  { echo "  👉 $*"; }
info() { echo "  ✅ $*"; }
warn() { echo "  ⚠️  $*"; }

gs_curl() {
  # Wrapper para llamadas REST a GeoServer con manejo básico de errores
  local method="$1"; shift
  local endpoint="$1"; shift
  curl -sf -X "${method}" "${GS_URL}${endpoint}" \
    -u "${GS_USER}:${GS_PASS}" \
    -H "Content-Type: application/json" \
    "$@" 2>/dev/null || return $?
}

# ---------------------------------------------------------------------------
# 0. Esperar a que GeoServer esté listo
# ---------------------------------------------------------------------------
echo "⏳ Esperando a GeoServer (${GS_URL})..."
until curl -sf "${GS_URL}/rest/about/manifest.json" \
       -u "${GS_USER}:${GS_PASS}" > /dev/null 2>&1; do
  echo "   GeoServer no está listo aún... reintentando en 5s"
  sleep 5
done
info "GeoServer listo!"

# ---------------------------------------------------------------------------
# 1. Crear workspace (idempotente — si existe, falla silenciosamente)
# ---------------------------------------------------------------------------
echo ""
echo "📦 Configurando workspace '${WS_NAME}'..."

if gs_curl GET "/rest/workspaces/${WS_NAME}" > /dev/null 2>&1; then
  info "Workspace '${WS_NAME}' ya existe, se reutiliza."
else
  gs_curl POST "/rest/workspaces" \
    -d "{\"workspace\":{\"name\":\"${WS_NAME}\"}}" || {
    warn "No se pudo crear workspace (puede que ya exista)"
  }
  info "Workspace '${WS_NAME}' creado."
fi

# ---------------------------------------------------------------------------
# 2. Crear store PostGIS (idempotente)
# ---------------------------------------------------------------------------
echo ""
echo "🗄️  Configurando store PostGIS '${STORE_NAME}'..."

if gs_curl GET "/rest/workspaces/${WS_NAME}/datastores/${STORE_NAME}" > /dev/null 2>&1; then
  info "Store '${STORE_NAME}' ya existe, se reutiliza."
else
  gs_curl POST "/rest/workspaces/${WS_NAME}/datastores" \
    -d "{
      \"dataStore\": {
        \"name\": \"${STORE_NAME}\",
        \"connectionParameters\": {
          \"entry\": [
            {\"@key\":\"host\",\"\$\":\"${DB_HOST}\"},
            {\"@key\":\"port\",\"\$\":\"${DB_PORT}\"},
            {\"@key\":\"database\",\"\$\":\"${DB_NAME}\"},
            {\"@key\":\"user\",\"\$\":\"${DB_USER}\"},
            {\"@key\":\"passwd\",\"\$\":\"${DB_PASS}\"},
            {\"@key\":\"dbtype\",\"\$\":\"postgis\"},
            {\"@key\":\"schema\",\"\$\":\"public\"},
            {\"@key\":\"Loose bbox\",\"\$\":\"true\"},
            {\"@key\":\"Estimated extends\",\"\$\":\"true\"}
          ]
        }
      }
    }" || warn "Store '${STORE_NAME}' ya existe o no se pudo crear"
  info "Store '${STORE_NAME}' configurado."
fi

# ---------------------------------------------------------------------------
# 3. Publicar capas desde PostGIS
# ---------------------------------------------------------------------------
echo ""
echo "🗺️  Publicando capas desde PostGIS..."

for LAYER in "${LAYERS[@]}"; do
  TABLE="${LAYER#territorio_}"   # quita prefijo "territorio_" para el title
  TITLE="$(echo "${TABLE}" | sed 's/_/ /g; s/\b\(.\)/\u\1/g')"  # snake_case → Title Case

  if gs_curl GET "/rest/workspaces/${WS_NAME}/datastores/${STORE_NAME}/featuretypes/${LAYER}" > /dev/null 2>&1; then
    info "Capa '${LAYER}' ya existe, se reutiliza."
  else
    log "Publicando '${LAYER}'..."
    gs_curl POST "/rest/workspaces/${WS_NAME}/datastores/${STORE_NAME}/featuretypes" \
      -d "{
        \"featureType\": {
          \"name\": \"${LAYER}\",
          \"nativeName\": \"${LAYER}\",
          \"title\": \"${TABLE^}\",
          \"srs\": \"EPSG:4326\",
          \"nativeCRS\": \"EPSG:32719\",
          \"projectionPolicy\": \"REPROJECT_TO_DECLARED\"
        }
      }" || warn "Capa '${LAYER}' ya existe o falló al publicarse"
    info "Capa '${LAYER}' publicada."
  fi
done

# ---------------------------------------------------------------------------
# 4. Asignar estilos por defecto
# ---------------------------------------------------------------------------
echo ""
echo "🎨 Configurando estilos por defecto..."

# polygon para capas poligonales
for LAYER in "territorio_distrito" "territorio_unidadterritorial"; do
  gs_curl PUT "/rest/workspaces/${WS_NAME}/layers/${LAYER}" \
    -d '{"layer":{"defaultStyle":{"name":"polygon"}}}' 2>/dev/null && \
    info "Estilo 'polygon' asignado a '${LAYER}'" || true
done

# point o geometry para LocalizacionTerritorial (puede ser cualquier geometría)
gs_curl PUT "/rest/workspaces/${WS_NAME}/layers/territorio_localizacionterritorial" \
  -d '{"layer":{"defaultStyle":{"name":"point"}}}' 2>/dev/null && \
  info "Estilo 'point' asignado a 'territorio_localizacionterritorial'" || true

# ---------------------------------------------------------------------------
# 5. Resumen
# ---------------------------------------------------------------------------
echo ""
echo "═══════════════════════════════════════════════════════════════"
echo "  ✅ GeoServer workspace '${WS_NAME}' configurado!"
echo "═══════════════════════════════════════════════════════════════"
echo ""
echo "  🌐 Admin Web:   ${GS_URL}/web/"
echo "  🗺️  WMS:         ${GS_URL}/${WS_NAME}/wms?service=WMS&request=GetCapabilities"
echo "  🗺️  WFS:         ${GS_URL}/${WS_NAME}/wfs?service=WFS&request=GetCapabilities"
echo ""
echo "  📦 Store:       ${STORE_NAME}"
echo "  🗃️  Capas:       ${LAYERS[*]}"
echo ""

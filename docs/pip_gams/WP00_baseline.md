# WP-00 — Baseline reproducible (PIP-GAMS)

**Fecha:** 2026-08-09
**Branch:** `refactor/pip-gams`
**Commit base:** `66c5e42c515b5e170fa6665c70852e7374e78ecf`
**Tag:** `baseline-pre-pip-gams`

Estado congelado de la plataforma antes de iniciar la refactorización
hacia PIP-GAMS (SIS-PE + SIS-POA + SIS-PRO). Cero cambios funcionales.

---

## 1. Estado de repositorio

- Commit previo al baseline: `66c5e42` — refactor de limpieza (capa muerta
  eliminada, duplicaciones unificadas).
- `PLAN_MAESTRO_REFAC_PIP_GAMS.md` incorporado como documento rector.
- `.env` NO está versionado (correcto); solo `.env.example` con placeholders.

## 2. Suites de prueba (registradas)

| Suite | Resultado |
|---|---|
| Backend pytest | **804 passed** (127 warnings, 239 subtests) — 686s |
| Frontend karma | **96 SUCCESS** |
| Frontend `ng build` | OK — hash `8b4e4de5abcb9afe` |

## 3. Base de datos

- **139 tablas** en esquema `public` (inventario con columnas y filas estimadas
  en `backups/wp00/inventario_tablas.txt`).
- PostgreSQL 16 + PostGIS 3.4.0, una sola base `gams_sis_poa`.

### Respaldos

| Archivo | Detalle |
|---|---|
| `backups/wp00/gams_sis_poa_pre_pip.dump` | pg_dump custom (-Fc), 769 KB — SHA256 `109D04C9...FE1` |
| `backups/wp00/gams_sis_poa_schema_only.sql` | schema-only, 469 KB |
| `backups/wp00/media_pre_pip.zip` | **No aplica** — no existe `backend/media` |

`backups/` está gitignored (no se versiona contenido).

## 4. OpenAPI V1

- Exportado vía drf-spectacular: `backups/wp00/openapi_v1.yml` (SHA256
  `D5C35075...F96`).
- **339 endpoints** documentados.
- **102 warnings (14 únicos)** — mayoría "unable to guess serializer"
  (fallback inofensivo en ViewSets sin serializer_class: `MatrizViewSet`,
  `ArticulacionViewSet`, `LogoutView`, `PasswordReset*`, `ConsolidacionViewSet`,
  `DashboardViewSet`).
- **1 error real pendiente de resolver en WP futuro:**
  `territorio/serializers.py:5` — `DistritoSerializer` no resuelve el campo
  `territorio` del modelo.

## 5. Auditoría de autorización (`AllowAny`)

Solo **3 ocurrencias**, todas en `apps/accounts/views.py` (auth pública
legítima):

- L115 — login
- L171 — password reset request
- L219 — consulta de estado de bloqueo (`LoginAttemptView`)

No hay `AllowAny` en ninguna otra app.

## 6. Auditoría de secretos

- `.env` correctamente excluido de git (`.gitignore`).
- `.env.example` solo con placeholders (`changeme-*`).
- Sin archivos `.pem`/`.key`/credentials versionados.
- Contraseña de desarrollo `admin2026` hardcodeada en `scripts/seed.py` y
  `scripts/seed_demo.py` (seeds locales; no es secreto productivo).
- `DJANGO_SECRET_KEY` del `.env` local es valor de desarrollo.

## 7. Variables de entorno

**Definidas en `.env` local (21):** `DJANGO_SECRET_KEY`, `DJANGO_DEBUG`,
`DJANGO_ALLOWED_HOSTS`, `DB_ENGINE`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`,
`DB_HOST`, `DB_PORT`, `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD`,
`REDIS_HOST`, `REDIS_PORT`, `REDIS_URL`, `CORS_ALLOWED_ORIGINS`,
`CELERY_BROKER_URL`, `CELERY_RESULT_BACKEND`, `USE_S3`,
`GDAL_LIBRARY_PATH`, `GEOS_LIBRARY_PATH`.

**Definidas solo en `.env.example` (18, pendientes de Fase 12):** MinIO
(`MINIO_*`, `AWS_*`), GeoServer (`GEOSERVER_*`), OIDC/Keycloak
(`OIDC_RP_*`, `KEYCLOAK_*`, `KC_BOOTSTRAP_*`).

## 8. Notas para work packages siguientes

- `territorio.DistritoSerializer` requiere corrección (ver §4).
- 14 de los 339 endpoints quedan sin schema de respuesta tipado (serializer
  no declarado) — candidatos a definir contratos en API V2 (WP-02).
- No hay media que respaldar; al activar MinIO (Fase 12) revisar política.
- El código de la plataforma no tiene endpoints `AllowAny` fuera de auth.

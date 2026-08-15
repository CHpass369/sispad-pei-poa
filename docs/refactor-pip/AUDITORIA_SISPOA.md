# FASE 1 — AUDITORÍA: barrido de identidad SISPOA → PIP

> Documento de la Fase 1 (auditoría) del refactor SISPOA → PIP-GAMS.
> Fuente primaria: barrido exhaustivo `barrido_sispoa.txt` (703 líneas, formato `archivo:línea: texto`).
> Este documento NO modifica código: clasifica cada referencia para guiar las fases 2-8.

---

## 1. Método y cifras

El barrido cubre todo el repositorio (código fuente, configuraciones, infraestructura, documentación y builds compilados). Cifras verificadas al crear este documento:

| Métrica | Valor | Nota |
|---|---|---|
| Archivos únicos con referencias | **162** | Verificado contra el txt del barrido |
| Líneas de referencia | **703** | Una línea puede contener varias referencias |
| Referencias totales (cifra del prompt maestro) | **865** | No reproducible exactamente: el conteo local da 528 ocurrencias de `sispoa` (case-insensitive) y 23 de `SISPOA_GASTOS_*`. La cifra 865 usa un criterio más amplio (incluye `SIS-POA`/`sis-poa`, que son correctos y no se renombran). **Recomendación: fijar el criterio de conteo en la fase 2.** |
| Ocurrencias `SISPOA_GASTOS_*` (valores de datos) | 23 | Riesgo de datos, ver sección 4 hallazgo 4 |

Distribución de archivos por extensión:

| Extensión | Archivos | Contenido |
|---|---|---|
| `.py` | 50 | Backend Django (apps, config, tests, scripts) |
| `.js` | 36 | Builds compilados en `backend/static_assets/` (NO TOCAR) |
| `.md` | 35 | Documentación |
| `.ts` | 28 | Frontend Angular |
| `.json` | 4 | Manifiestos y realm Keycloak |
| `.html` | 3 | `index.html` (frontend y build) + plantilla |
| `.yml` | 2 | docker-compose |
| `.conf` | 2 | nginx y gunicorn |
| `.env` | 1 | Variables de entorno local |
| `.scss` | 1 | Tema del frontend |

## 2. Regla de clasificación semántica (prompt maestro)

NUNCA hacer replace global `sispoa → pip`. Cada referencia se clasifica según lo que representa:

| Referencia representa | Clasificar como |
|---|---|
| TODA la plataforma (identidad, marca, título) | **PIP** (PIP_CORE) |
| Planificación operativa anual | **SIS-POA** (se mantiene) |
| Planificación estratégica | **SIS-PE** |
| Ciclo del proyecto / preinversión | **SIS-PRO** |
| Infraestructura compartida (IAM, workflow, documentos) | **PIP CORE** |
| Catálogos normativos | **PIP CATÁLOGOS** |
| Articulación PAD-PEI y transferencias entre sistemas | **PIP INTEGRACIÓN** |

## 3. Inventario clasificado por destino

### 3.1 PIP_CORE — identidad de plataforma (SISPOA = toda la plataforma → RENOMBRAR a PIP)

| Archivo | Línea/Componente | Referencia | Función actual | Dominio real | Destino propuesto | Riesgo | Acción requerida |
|---|---|---|---|---|---|---|---|
| `frontend/sispoa/src/index.html` | 5 | `<title>SISPOA Sacaba</title>` | Título del navegador | Plataforma | PIP | Bajo | RENAME en fase UI |
| `frontend/sispoa/src/styles.scss` | 1 | `/* SISPOA Sacaba - Tema institucional verde */` | Comentario de tema | Plataforma | PIP | Bajo | RENAME comentario |
| `frontend/sispoa/src/app/features/auth/login.component.ts` | 15 | `<h1>SISPOA Sacaba</h1>` | Pantalla de login | Plataforma | PIP | Medio (cambio visual visible) | RENAME; coordinar con identidad institucional |
| `frontend/sispoa/src/app/layout/header/header.component.ts` | 56 | `pageTitle = 'SISPOA Sacaba'` | Título del header | Plataforma | PIP | Bajo | RENAME |
| `frontend/sispoa/src/app/layout/sidebar/sidebar.component.ts` | 35 | `<strong>SISPOA</strong>` (marca del sidebar) | Marca | Plataforma | PIP | Bajo | RENAME a PIP |
| `backend/apps/core/admin.py` | 3-4 | `site_header`/`site_title` 'SISPOA Sacaba' | Django admin | Plataforma | PIP | Bajo | RENAME |
| `backend/apps/core/views_root.py` | 10 | `{'sistema': 'SISPOA Sacaba'}` | Endpoint raíz `/` | Plataforma | PIP | Bajo | RENAME |
| `backend/apps/accounts/views.py` | 141 | subject `'Restablecimiento de contraseña - SISPOA'` | Email de reset | Plataforma | PIP | Bajo | RENAME |
| `backend/apps/core/dashboard.py` | 2 | docstring "dominio SISPOA" | Docstring | Plataforma | PIP | Bajo | RENAME |
| `backend/apps/core/serializer_mixins.py` | 1 | docstring "dominio SISPOA" | Docstring | Plataforma | PIP | Bajo | RENAME |
| `backend/config/settings.py` | 209-211 | SPECTACULAR `TITLE: 'SISPOA Sacaba API'`, `DESCRIPTION: '...Administración del POA'` | Swagger/OpenAPI | Plataforma | PIP | Bajo | RENAME; DESCRIPTION además solo menciona el POA: ampliar a plataforma |
| `backend/config/settings.py` | 249 | `logs/sispoa.log` | Logging | Plataforma | PIP | Bajo (renombrar pierde rotación histórica) | RENAME con coexistencia temporal de archivos |
| `backend/config/celery.py` | 6 | `app = Celery('sispoa')` | Nombre de app Celery | Plataforma | PIP | Bajo | RENAME |
| `backend/config/settings_production.py` | 2, 20, 61, 89, 112-113 | dominio `sispoa.gamsacaba.gob.bo`, `ALLOWED_HOSTS`, CORS, `/var/log/sispoa/`, `/var/www/sispoa/` | Producción | Plataforma | PIP | **Alto** (DNS + certificados TLS) | Plan de despliegue con ventana; no es un rename de código |
| `backend/config/settings_storage.py` | 16-17 | bucket `sispoa-docs`, endpoint `http://sispoa-minio:9000` | MinIO | Plataforma | PIP | Medio (renombrar bucket requiere copiar objetos) | RENAME con migración de objetos S3 |
| `backend/tests/conftest.py` | 2 | docstring "tests de SISPOA" | Fixtures compartidas | Plataforma | PIP | Bajo | RENAME |
| `backend/scripts/seed.py` | 37 | `'last_name': 'SISPOA'` | Seed de desarrollo | Plataforma | PIP | Bajo | RENAME |
| `backend/scripts/seed_demo.py` | 173 | `'first_name': 'Admin', 'last_name': 'SISPOA'` | Seed demo | Plataforma | PIP | Bajo | RENAME |
| `.env` | 1 | `DJANGO_SECRET_KEY=dev-local-key-sispoa-2026-...` | Clave dev | Plataforma | PIP | Bajo (dev; rotar secret invalida tokens) | RENAME junto con rotación de secretos |
| `frontend/sispoa/src/environments/environment.ts` y `environment.prod.ts` | 5 | `tokenKey: 'sispoa_token'` | Clave de localStorage del JWT | Plataforma | PIP | **Medio-alto** (renombrar cierra sesión de todos los usuarios) | RENAME SOLO con estrategia de migración de sesión |
| `serve.py` | 8 | `FRONTEND_DIR = .../frontend/sispoa/dist/sispoa` | Servidor local | Plataforma | PIP | Bajo | RENAME de path |
| `frontend/sispoa/package.json` | 2, 4 | `"name": "sispoa"`, `"description": "SISPOA Sacaba - Frontend"` | Manifiesto npm | Plataforma | PIP | Bajo | RENAME |
| `frontend/sispoa/angular.json` | 6, 20, 56-57 | `"sispoa": {` , `outputPath: dist/sispoa` | Build Angular | Plataforma | PIP | Bajo (cambia outputPath → ajustar serve.py y nginx) | RENAME |
| `frontend/sispoa/package-lock.json` | 2, 8 | `"name": "sispoa"` | Lockfile | Plataforma | PIP | Bajo | Se regenera con `npm install` |
| `frontend/sispoa/karma.conf.js` | 20 | `coverage/sispoa` | Cobertura de tests | Plataforma | PIP | Bajo | RENAME |
| `README.md` | 1 | `# SISPOA Sacaba` | README | Plataforma | PIP | Bajo | RENAME |
| `backend/apps/workflow/consolidacion.py` | 2, 680 | docstring y encabezado impreso `"SISTEMA DE PLANIFICACIÓN OPERATIVA ANUAL — SISPOA SACABA"` | Consolidación institucional (documento oficial impreso) | Plataforma (documento oficial) | PIP | **Medio** (afecta documentos oficiales emitidos) | RENAME con fecha de corte; no reescribir documentos históricos |

### 3.2 SIS-POA operativo — CORRECTO, NO TOCAR (verificado)

| Archivo (representativo) | Líneas | Referencia | Clasificación |
|---|---|---|---|
| `frontend/sispoa/src/app/features/sis-poa/*` (módulo completo) | barrido 564-655 | Rutas `/sis-poa/*`, `SisPoaModule`, `SisPoaService`, `budget/*` | Correcto: bounded context operativo |
| `frontend/sispoa/src/app/layout/sidebar/sidebar.component.ts` | 168-189 | Sección `'sis-poa'` del `sistemasMenu` | Correcto |
| `backend/apps/budget/*` (models, views, urls, importer, services, tests) | barrido 124-183 | Docstrings "ciclo presupuestario SIS-POA", `/api/v2/sis-poa/budget/`, capacidades `sis_poa.budget.*` | Correcto |
| `backend/apps/accounts/migrations/0002, 0004, 0005` | barrido 99-123 | Capacidades `sis_poa.formulate`, `sis_poa.poau.edit`, `sis_poa.budget.*` | Correcto (valores de IAM) |
| `backend/apps/poau/*` (models, models_v2, views_v2, migration_v2) | barrido 204-210 | Jerarquía canónica V2 del SIS-POA | Correcto |
| `backend/apps/techos/views_v2.py` | barrido 211-213 | "techos presupuestarios del SIS-POA" | Correcto |
| `backend/config/urls_v2.py` + `urls_test_sqlite.py` | 92-98, 142-143, 229-237 | Namespace `/api/v2/sis-poa/` | Correcto |
| `backend/tests/test_sis_poa_v2.py`, `apps/budget/tests.py` | barrido 140, 296-312 | Contratos V2 SIS-POA | Correcto |
| `docs/sis-poa/presupuesto/*` (13 docs) | barrido 488-551 | Documentación del ciclo presupuestario | Correcto |
| `backend/apps/gestion/models.py` | 18 | "Estados del ciclo presupuestario SIS-POA (Fase 1)" | Correcto |

### 3.3 SIS-PRO / integración (SISPOA como sistema externo en `inversion` → REVISAR)

| Archivo | Línea | Referencia | Función actual | Dominio real | Destino propuesto | Riesgo | Acción requerida |
|---|---|---|---|---|---|---|---|
| `backend/apps/inversion/models_preinversion.py` | 7 | docstring "Outbox para integraciones con SISPOA/SISPRO" | Outbox de integración | El "SISPOA" aquí es el consumidor del paquete: SIS-POA | PIP_INTEGRACION | Bajo | Revisar terminología → "SIS-POA / SIS-PRO" o "sistemas consumidores" |
| `backend/apps/inversion/models_preinversion.py` | 188 | docstring "Solicitud de reformulación originada por SISPOA u otro sistema" | `SolicitudReformulacion` | SIS-POA | SIS_POA | Bajo | RENAME docstring → "originada por SIS-POA" |
| `backend/apps/inversion/models_preinversion.py` | 194 | `sistema_origen = models.CharField(max_length=50, default='SISPOA')` | **Valor persistido en filas** | SIS-POA | SIS_POA | **Alto** (renombrar el valor rompe histórico) | NO renombrar el valor; backfill o mapeo en fase de datos. Docstring/default solo tras migración de datos |
| `backend/apps/inversion/models_preinversion.py` | 792 | docstring "Códigos externos de SIS PAD-PEI, SISPOA, SISPRO y SISFIN" | `ReferenciaExterna` | Sistemas externos | PIP_INTEGRACION | Bajo | RENAME docstring (nombres oficiales SIS-POA/SIS-PRO) |
| `backend/apps/inversion/models_v2.py` | 91 | `(ENVIADO_POA, 'Enviado a SISPOA')` | Etiqueta de estado | SIS-POA | SIS_POA | Bajo (solo display; el valor `enviado_poa` no cambia) | RENAME etiqueta → 'Enviado a SIS-POA' |
| `backend/apps/inversion/services_preinversion.py` | 4, 182, 237 | docstrings "paquete de transferencia a SISPOA", "habilitación para POA (SISPOA)", "paquete de solo lectura para SISPOA" | Transferencia preinversión → POA | SIS-POA | SIS_POA | Bajo | RENAME docstrings; verificar en fase 5 si el consumidor es SIS-POA V2 |
| `frontend/sispoa/src/app/features/sis-pro/preinversion-detalle.component.ts` | 84 | botón "➜ Enviar a SISPOA" | UI preinversión | SIS-POA | SIS_POA | Bajo | RENAME → "Enviar a SIS-POA" |
| `frontend/sispoa/src/app/features/sis-pro/preinversion.service.ts` | 588 | `enviado_poa: 'Enviado a SISPOA'` | Display de estado | SIS-POA | SIS_POA | Bajo | RENAME display |
| `docs/pip_gams/adr/ADR-005-preinversion-sispro.md` | 12, 38, 45 | "transferencia a SISPOA", "Integración con SISPOA" | ADR vigente | SIS-POA | SIS_POA | Bajo | Actualizar ADR al ejecutar el rename |
| `CHANGELOG.md` | 19, 37 | "paquete de transferencia a SISPOA" | Histórico | SIS-POA | — | Nulo | NO reescribir histórico; nueva entrada al ejecutar |

### 3.4 LEGACY — infraestructura y datos (decidir mantener o migrar con plan)

| Archivo | Línea/Componente | Referencia | Función actual | Dominio real | Destino propuesto | Riesgo | Acción requerida |
|---|---|---|---|---|---|---|---|
| `.env` | 6-7, 12-14 | `DB_NAME=gams_sis_poa`, `DB_USER=sispoa`, `POSTGRES_DB`, `POSTGRES_USER` | Conexión BD local | Infraestructura | `gams_pip` (BD) | **Alto** (renombrar BD requiere migración real: dump/restore o ALTER DATABASE + roles) | Plan dedicado en fase de infraestructura; NO hacer en fase de código |
| `backend/config/settings.py` | 110-113 | default `'NAME': 'gams_sis_poa'` (fallback sin `.env`) | Config Django | Infraestructura | `gams_pip` | Medio (fallback solo sin `.env`) | Cambiar junto con el rename de BD |
| `docker-compose.yml` y `docker-compose.prod.yml` | names, DB defaults, realm URLs | `sispoa-postgres`, `sispoa-redis`, `sispoa-backend`, `sispoa-frontend`, `sispoa-nginx`, `sispoa-celery-worker/beat`, `sispoa-minio`, `sispoa-geoserver`, `sispoa-keycloak`, `MINIO_ROOT_USER=sispoa_admin`, `KC_DB_URL` a `sispoa-postgres` | Servicios Docker | Infraestructura | Nombres `pip-*` | **Alto** (DNS interno, healthchecks, proxy nginx, scripts de backup) | Plan con ventana de despliegue; renombrar rompe scripts y volúmenes existentes |
| `backend/config/settings_production.py` | 2, 20, 61, 89, 112-113 | Dominio `sispoa.gamsacaba.gob.bo`, rutas `/var/log/sispoa`, `/var/www/sispoa` | Producción | Infraestructura | `pip.*` / `/var/log/pip` | **Alto** | Plan de DNS + certificados |
| `backend/config/settings_storage.py` | 16-17 | bucket `sispoa-docs`, endpoint `sispoa-minio` | MinIO | Infraestructura | `pip-docs` | Medio | Migración de objetos |
| `infra/keycloak/realm-export.json` | 2, 11, 16, 29, 47, 51, 66-78 | realm `sispoa`, clients `sispoa-frontend`/`sispoa-backend`, secret, roles `default-roles-sispoa` | Keycloak | Infraestructura | realm `pip` | **Alto** (reimportar realm, rotar client secret, re-registrar usuarios) | Plan separado; no es rename de código |
| `infra/nginx/includes/geoserver.conf` y `keycloak.conf` | 15 / 8, 13 | `proxy_pass http://sispoa-geoserver:8080`, `sispoa-keycloak:8080` | Proxy nginx | Infraestructura | Nombres `pip-*` | Medio (junto a docker-compose) | RENAME coordinado con compose |
| `infra/docker/backend/gunicorn.conf.py` | 2 | "Gunicorn configuration for SISPOA backend" | Comentario | Infraestructura | PIP | Bajo | RENAME comentario |
| `docs/despliegue.md` | 52-54, 91-92, 145-181, 289-292, 340, 370, 403, 433-434, 546-572, 589, 614, 640 | usuario linux `sispoa`, `/home/sispoa`, `DB_*`, `MINIO_*`, `OIDC_*`, crontab, backups, workspace GeoServer `sispoa` | Guía de despliegue | Infraestructura | Nombres `pip-*` | Medio (doc desactualizada) | Actualizar al ejecutar cada rename |
| `docs/INSTALACION.md` | 93, 111, 125, 164-192, 214, 232, 251, 270, 276, 342 | `gams_sis_poa`, `sispoa_user`, `sispoa-redis`, `sispoa-minio`, `sispoa-keycloak`, realm, bucket | Guía de instalación | Infraestructura | Nombres `pip-*` | Medio | Actualizar con cada rename |
| `docs/manual_administrador.md` | 310-316, 362, 388-391, 417-421, 439, 447 | `docker ps` (servicios `sispoa-*`), comandos psql `-U sispoa_user -d gams_sis_poa`, alias mc | Manual de administración | Infraestructura | Nombres `pip-*` | Medio | Actualizar con cada rename |
| `docs/respaldo_restauracion.md` | 30-32, 49-64, 73-88, 104-130, 194-327, 383-510, 536-540 | `sispoa_db_*.dump`, `gams_sis_poa`, `sispoa_user`, alias `sispoa`, bucket `sispoa-docs`, `/home/sispoa/backups` | Respaldo/restauración | Infraestructura | Nombres `pip-*` | Medio | Actualizar; los backups viejos conservan el nombre original |
| `docs/seguridad.md` | 56-70, 657-658, 672 | realm `sispoa`, `sispoa-frontend`, BD dedicada `gams_sis_poa`, `sispoa_user`, bucket `sispoa-docs` | Documento de seguridad | Infraestructura | Nombres `pip-*` | Medio | Actualizar |
| `docs/auditoria_postgres.md` | 1 | "SIS PAD PEI (gams_sis_poa)" | Auditoría Postgres | Infraestructura | `gams_pip` | Bajo | Actualizar título |
| `docs/optimizacion_postgres_pip.md` | 4, 164-169 | BD `gams_sis_poa`, conexión local USER `sispoa` | Optimización Postgres | Infraestructura | `gams_pip` | Bajo | Actualizar |
| `README.md` | 27-28 | `createdb -p 5433 gams_sis_poa` | Instalación dev | Infraestructura | `gams_pip` | Bajo | Actualizar |
| `backend/static_assets/*.js` (36) + `index.html:5` + `main.*.js` + `polyfills.*.js` + `runtime.*.js` | 252-287 | `webpackChunksispoa`, `dist/sispoa`, `<title>SISPOA Sacaba</title>` | **Builds compilados** | Plataforma | — | Nulo | **NO TOCAR**: se regeneran con `ng build`; el title sale de `src/index.html` |
| `frontend/sispoa/package-lock.json` | 2, 8 | `"name": "sispoa"` | Lockfile | Plataforma | PIP | Bajo | Se regenera |

### 3.5 Ya correcto — verificado (SIS-PE / SIS-PRO / selector / namespaces)

| Archivo | Línea/Componente | Referencia | Verificación |
|---|---|---|---|
| `frontend/sispoa/src/app/features/sistemas/sistemas-seleccion.component.ts` | 76-110 | Selector SIS-PE/SIS-POA/SIS-PRO con rutas `/sis-pe/dashboard`, `/sis-poa/dashboard`, `/sis-pro/dashboard` y capacidades `sis_pe.instrumento.read`, `sis_poa.formulate`, `sis_pro.project.read` | Leído completo; correcto |
| `frontend/sispoa/src/app/layout/sidebar/sidebar.component.ts` | 152-206 | `sistemasMenu` con secciones `sis-pe`/`sis-poa`/`sis-pro` + `administracionMenu` de plataforma | Leído; correcto |
| `backend/config/urls_v2.py` | 139-146 | Namespaces `platform/`, `sis-pe/`, `sis-poa/` (+`sis-poa/budget/`), `sis-pro/`, `me/` | Leído; correcto |
| `backend/tests/test_api_v2.py` | 53-60 | Parametriza los 4 namespaces | Correcto |
| `backend/tests/test_sis_poa_v2.py` + `apps/budget/tests.py` | — | Contratos `/api/v2/sis-poa/` | Correctos |
| `docs/pip_gams/*` (glosario, ADRs, WP00, WP14) | — | Terminología PIP-GAMS oficial | Correcto; es el estado objetivo |
| `docs/ARQUITECTURA.md` | 4 | "Plataforma Integral de Planificacion del GAM Sacaba (SIS-PE + SIS-POA + ...)" | Correcto |

### 3.6 POR_CLASIFICAR — requieren decisión

| Archivo | Línea/Componente | Referencia | Análisis | Riesgo | Recomendación |
|---|---|---|---|---|---|
| `backend/apps/budget/models.py` | 872-878, 964 | `PerfilImportacion.SISPOA_GASTOS_HISTORICO` / `SISPOA_GASTOS_ACTUAL` (choices) | Valores de datos persistidos en `Importacion.perfil` | **Alto** (renombrar rompe histórico y tests) | **KEEP con coexistencia**: mantener los valores actuales; agregar perfiles nuevos `PIP_*` cuando se reemplace el formato de planilla. Decidir en fase de datos |
| `backend/apps/budget/importer.py` | 110, 115 | Mapeo de perfiles en el importador | Depende de la decisión anterior | Alto | Mismo tratamiento |
| `backend/apps/budget/migrations/0004_*` | 23 | choices `SISPOA_GASTOS_*` en migración | Histórico | Nulo | NO reescribir migraciones aplicadas |
| `backend/apps/budget/tests.py` | 1142, 1310, 1326 | `perfil='SISPOA_GASTOS_HISTORICO'` | Tests | Medio | Actualizar junto a la decisión de datos |
| `frontend/sispoa/src/app/features/sis-poa/budget/imports.component.html` | 28-29 | `<option value="SISPOA_GASTOS_HISTORICO">` | Valor enviado al backend | Medio (debe coincidir con choices) | Cambiar SOLO si cambian los choices del backend |
| `frontend/sispoa/src/app/features/sis-poa/budget/imports.component.ts` y `.spec.ts` | 67 / 21 | `perfil = 'SISPOA_GASTOS_HISTORICO'` | Default de UI + spec | Medio | Ídem |
| `docs/sis-poa/presupuesto/database.md` y `excel-importer.md` | 75 / 24-25 | Perfiles `SISPOA_GASTOS_*` | Documentación | Bajo | Actualizar al decidir |
| `backend/config/settings.py` | 210 | DESCRIPTION "Sistema Integrado de Formulación, Seguimiento y Administración del POA" | Describe solo POA, pero la plataforma es más amplia | Bajo | Inconsistencia de identidad: reformular como PIP |

## 4. Hallazgos clave

1. **El selector de sistemas ya existe.** `sistemas-seleccion.component.ts:76-110` define SIS-PE / SIS-POA / SIS-PRO con rutas y capacidades, y el header ya dice "Plataforma Integral de Planificación" (`:21-22`). La identidad PIP ya está presente en la entrada del frontend.
2. **El namespace de API V2 ya está separado.** `urls_v2.py:139-146`: `/api/v2/{platform,sis-pe,sis-poa,sis-poa/budget,sis-pro,me}` (ADR-002). No hay trabajo pendiente de ruteo.
3. **La identidad visible sigue diciendo SISPOA.** Login (`login.component.ts:15`), título (`index.html:5`), marca del sidebar (`sidebar.component.ts:35`), header (`header.component.ts:56`), Django admin (`core/admin.py:3-4`), endpoint raíz (`views_root.py:10`), email de reset (`accounts/views.py:141`) y Swagger (`settings.py:209`). Es el frente de trabajo más visible de la fase 2.
4. **`PerfilImportacion.SISPOA_GASTOS_*` son valores de datos con riesgo.** 23 ocurrencias (modelos, migración, tests, frontend y docs). Renombrarlos rompe registros históricos de importación; se recomienda coexistencia (KEEP) y decisión explícita en la fase de datos.
5. **La BD `gams_sis_poa` y los usuarios `sispoa*` son legacy de infraestructura.** Renombrar la BD a `gams_pip` (y los servicios docker `sispoa-*`, realm Keycloak, bucket MinIO, usuario Linux) requiere planes de migración reales con ventanas de despliegue; NO deben ejecutarse como renames de código.
6. **Hallazgo nuevo: doble identidad en el frontend.** La ventana de selección ya dice "Plataforma Integral de Planificación" (`sistemas-seleccion.component.ts:21`) mientras login, header y sidebar dicen "SISPOA Sacaba". La plataforma está a medio migrar en su propia identidad.
7. **Hallazgo nuevo: colisión de prefijos tras el rename 9961550.** La app `budget` renombrada a `presupuesto_*` comparte prefijo con la app legacy `presupuesto` (`presupuesto_categoria_programatica` de budget vs `presupuesto_categoriaprogramatica` del legacy). El sufijo diferencia (guiones vs camelCase), pero es frágil; ver `SCHEMA_MAPPING.md`.

## 5. Hallazgos adicionales del barrido (no cubiertos por la clasificación base)

- `frontend/sispoa/src/app/layout/header/header.component.ts:56` — `pageTitle = 'SISPOA Sacaba'` no estaba en la clasificación base (se suma a PIP_CORE).
- `backend/config/settings.py:209-211` — Swagger con título y descripción SISPOA (base no lo citaba).
- `backend/config/celery.py:6` — nombre de app Celery `'sispoa'` (no citado).
- `backend/config/settings_production.py` y `settings_storage.py` — dominio, rutas, bucket y endpoint (no citados en detalle).
- `frontend/sispoa/src/environments/environment.ts:5` y `environment.prod.ts:5` — `tokenKey: 'sispoa_token'`: renombrarlo cierra sesión a todos los usuarios; requiere estrategia de migración de sesión.
- `backend/scripts/seed.py:37` y `seed_demo.py:173` — `last_name: 'SISPOA'` en datos sembrados.
- `backend/tests/conftest.py:2` — docstring.
- `serve.py:8` — path de distribución compilada.
- `backend/apps/workflow/consolidacion.py:2,680` — el encabezado de la consolidación institucional impresa dice "SISPOA SACABA"; afecta documentos oficiales.
- `frontend/sispoa/src/app/features/sis-pro/preinversion-detalle.component.ts:84` y `preinversion.service.ts:588` — UI de preinversión "Enviar a SISPOA" (la base solo citaba `models_v2.py:91`).
- `CHANGELOG.md:19,37` — referencias históricas (no reescribir).
- Discrepancia de cifras verificada: 217 tablas (no 219), 92 migraciones (no 110), Django 6.0.7 (no 5.x), Angular 19 (no 17). Detalles en `ARQUITECTURA_ACTUAL.md`.
- El `.env` local usa `DB_USER=sispoa` pero el default de `settings.py:111` es `chpass369`; al migrar a `gams_pip` conviene unificar la fuente de verdad.

## 6. Secuencia sugerida para las fases 2-8

| Fase | Foco | Referencias a ejecutar |
|---|---|---|
| 2 | Identidad visible (UI + admin + emails + Swagger) | Sección 3.1 (riesgos bajos) |
| 3 | Backend: docstrings, config, celery, seeds, tests | Sección 3.1 + 3.3 (docstrings y etiquetas) |
| 4 | Datos: `sistema_origen`, `PerfilImportacion`, etiquetas de estado | Secciones 3.3 (fila 194) y 3.6 — con backfill |
| 5 | Integración SIS-PRO ↔ SIS-POA (outbox, transferencias) | Sección 3.3 |
| 6 | Documentación (README, CHANGELOG, docs/pip_gams) | Secciones 3.3 (ADRs) y 3.4 (docs) |
| 7 | Infraestructura (BD, docker, Keycloak, MinIO, DNS) | Sección 3.4 — planes dedicados |
| 8 | Verificación: regenerar builds, tests, criterio de conteo | Sección 1 + `static_assets` |

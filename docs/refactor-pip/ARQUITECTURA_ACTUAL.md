# FASE 1 — ARQUITECTURA ACTUAL (baseline SISPOA / PIP-GAMS)

> Estado de la arquitectura al inicio del refactor. Todo lo indicado como "verificado" fue confirmado contra el repo, el venv o la BD local (fecha: 2026-08-15). Fase 1 del plan maestro `PLAN_MAESTRO_REFAC_PIP_GAMS.md`.

## 1. Stack tecnológico (verificado)

### Backend (`backend/requirements.txt` + venv)

| Componente | Versión | Verificación |
|---|---|---|
| Python | 3.13.11 (venv en `backend/.venv`) | venv local |
| Django | **6.0.7** | `pip show django` (el prompt de contexto sugería 5.x; es 6.0.7) |
| Django REST Framework | 3.17.1 | `pip show djangorestframework` |
| django-extensions | 4.1 | requirements |
| drf-spectacular | 0.30.0 | OpenAPI/Swagger |
| djangorestframework-simplejwt | 5.5.1 | JWT |
| djangorestframework-gis | 1.2.1 | GeoDjango serializers |
| django-filter | 25.2 | Filtros DRF |
| django-cors-headers | 4.9.0 | CORS |
| psycopg2-binary | 2.9.12 | Driver PostgreSQL |
| celery | 5.6.3 + redis 8.0.1 | Colas y beat |
| openpyxl | 3.1.5 | Importador Excel del presupuesto |
| django-storages[boto3] | 1.14-2.0 | MinIO (S3) opcional (`USE_S3`) |
| mozilla-django-oidc | 4.0-5.0 | Keycloak opcional (solo si `OIDC_RP_CLIENT_ID` presente) |
| docxtpl / python-docx | 0.20-0.21 / 1.2-2 | Plantillas DOCX del expediente de preinversión |
| whitenoise | 6.12.0 | Static en producción |
| pytest / pytest-django | 9.1.1 / 4.12.0 | Tests |

### Base de datos (verificado contra la BD local)

| Ítem | Valor |
|---|---|
| Motor | PostgreSQL **16.0** (build MSVC 64-bit) |
| Extensiones | `plpgsql 1.0`, `postgis 3.4.0` |
| Nombre BD | `gams_sis_poa` (esquema único `public`) |
| Tablas BASE TABLE en `public` | **217** (el contexto decía ~219; conteo real vía `information_schema`) |
| Migraciones propias | **92** archivos `.py` (119 incluyendo `__init__.py`; el contexto decía 110 — no verificable) |
| Tamaño | 36 MB |
| Modelos Django de dominio | 200 (en 27 apps locales) |

### Frontend (`frontend/sispoa/package.json`)

| Componente | Versión |
|---|---|
| Angular | **19.0** (`@angular/core` ^19, CLI 19, Material 19) |
| rxjs | ~7.8 |
| echarts 5.5 + ngx-echarts 18 | Dashboards y gráficos |
| OpenLayers (`ol` ^10) | Mapas (territorio/inversiones) |
| TypeScript | ~5.6 |
| Tests | karma + jasmine (+ specs `it()/itAsync()`; 225 specs totales según `docs/sis-poa/presupuesto/testing.md`) |
| Build | `dist/sispoa`; también compilado en `backend/static_assets/` (NO editar) |

## 2. Estructura de directorios

### Backend (`backend/`)

```
backend/
├── apps/                  # 27 apps locales
│   ├── accounts/          # IAM: Usuario, Rol, Capacidad, AlcanceOrganizacional
│   ├── acciones_correctivas/
│   ├── articulacion/      # Cadena PAD-PEI + legado POA (18 modelos)
│   ├── auditoria/         # EventoAuditoria (1 modelo)
│   ├── budget/            # Ciclo presupuestario SIS-POA V2 (18 modelos)
│   ├── catalogos/         # Catálogos normativos versionados (15 modelos)
│   ├── codificacion/      # Codificación PGDESA/PDESA (10 modelos)
│   ├── core/              # Núcleo: admin, dashboard, vistas raíz (2 modelos)
│   ├── documentos/        # DocumentoAdjunto (1)
│   ├── evaluacion/        # Evaluación (5)
│   ├── gestion/           # Gestión fiscal legacy (3)
│   ├── indicadores/       # Indicadores (7; incluye jerarquía operativa legacy)
│   ├── inversion/         # SIS-PRO: proyectos + preinversión (37, la app más grande)
│   ├── modificaciones/    # Reformulaciones del POA (3)
│   ├── normativa/         # Marco legal (2)
│   ├── notificaciones/    # (3)
│   ├── organizacion/      # Estructura institucional (5)
│   ├── pad/               # PAD (8)
│   ├── planificacion/     # SIS-PE: planes, nodos, instrumentos, versiones (15)
│   ├── poau/              # POA/POAU: legacy + jerarquía canónica V2 (10)
│   ├── presupuesto/       # Legacy presupuestario (6; DEPRECATE)
│   ├── recursos/          # Estimación de recursos (2)
│   ├── reportes/          # ReporteGenerado (1)
│   ├── seguimiento/       # (4)
│   ├── techos/            # Techos legacy (3)
│   ├── territorio/        # Distrito, UnidadTerritorial, Localización (3)
│   └── workflow/          # Flujo legacy + motor V2 configurable (12)
├── config/                # settings(.py, _production, _storage, _oidc), urls(.py, _v2, _test_sqlite), celery
├── tests/                 # Tests de contrato V2 (test_api_v2, test_iam_v2, test_sis_poa_v2, ...)
├── static_assets/         # Build compilado del frontend (NO TOCAR)
├── templates/docx/        # Plantillas del expediente de preinversión
├── scripts/               # seed, seed_demo, measure_coverage, limpiador de caches
└── manage.py
```

### Frontend (`frontend/sispoa/src/`)

```
src/
├── index.html             # <title>SISPOA Sacaba</title> (línea 5) — PIP_CORE
├── styles.scss            # Tema institucional (línea 1) — PIP_CORE
├── environments/          # environment(.prod).ts: apiUrl=/api/v1, apiUrlV2=/api/v2, tokenKey='sispoa_token'
└── app/
    ├── core/              # config/cutover.config.ts, services (auth, permissions, capabilities), guards
    ├── layout/            # sidebar (sistemasMenu + administracionMenu), header
    ├── main/              # main.module.ts: 31 rutas lazy de features
    └── features/          # 31 módulos lazy por dominio:
        ├── sis-pe/ sis-poa/ (incl. budget/) sis-pro/   # V2 por sistema
        ├── sistemas/      # selector SIS-PE/SIS-POA/SIS-PRO
        ├── dashboard/ gestion/ organizacion/ catalogos/ normativa/ documentos/
        ├── auditoria/ reportes/ workflow/ notificaciones/
        ├── planificacion/ articulacion/ pad/ indicadores/ evaluacion/ territorio/
        ├── poau/ presupuesto/ techos/ recursos/ seguimiento/ modificaciones/ consolidacion/
        ├── inversion/     # legacy SIS-PRO (V1)
        └── admin-usuarios/ portal-publico/ auth/
```

## 3. Módulos por dominio actual (27 apps, 200 modelos)

| App | Modelos | Dominio actual | API V2 |
|---|---|---|---|
| accounts | 4 | IAM (Usuario por email, Rol, Capacidad atómica, AlcanceOrganizacional) | `me/` |
| organizacion | 5 | Estructura institucional (UE, Dirección Administrativa) | — |
| gestion | 3 | Gestión fiscal legacy (GestionFiscal, CicloFormulacion, EtapaFormulacion) | — (V2 usa budget.FiscalYear) |
| catalogos | 15 | Catálogos normativos versionados (VersionClasificador + checksum) | — |
| normativa | 2 | Marco legal (VersionNormativa, ReglaPresupuestariaLegal) | — |
| planificacion | 15 | SIS-PE: Plan, NodoPlanificacion, InstrumentoPlanificacion, VersionInstrumento | `sis-pe/*` |
| pad | 8 | PAD (SectorPAD → PoliticaPAD → Lineamiento → Resultado/ProductoTerritorial) | — (migration_v2 a planificacion) |
| articulacion | 18 | Cadena PAD-PEI + POA legacy (AccionPOA, OperacionPOAU, ...) | — |
| codificacion | 10 | Codificación PGDESA/PDESA | — (migration_v2) |
| indicadores | 7 | Indicadores + jerarquía operativa legacy (Operacion/Tarea/Producto) | — |
| recursos | 2 | Estimación de recursos | — |
| techos | 3 | Techos legacy | `sis-poa/techos` (TechoViewSetV2) |
| presupuesto | 6 | Presupuesto legacy | — |
| budget | 18 | Ciclo presupuestario SIS-POA V2 (FiscalYear, DirectiveCeiling, Apertura, Reforma, Importacion...) | `sis-poa/budget/*` |
| inversion | 37 | SIS-PRO: proyectos + preinversión (ITCP, TDR, EDTP, outbox) | `sis-pro/*` |
| territorio | 3 | Base geográfica | — |
| poau | 10 | POA/POAU: legacy + jerarquía canónica V2 (PoA, Accion, Operacion, Actividad, Tarea, Programacion) | `sis-poa/*` |
| evaluacion | 5 | Evaluación (Evaluacion, Criterio, Resultado, Leccion, Recomendacion) | `sis-pe/evaluaciones` |
| workflow | 12 | Flujo legacy (EnvioFormulacion, Revision, Aprobacion) + motor V2 (Definicion, Instancia, Tarea, Observacion, Aprobacion, Delegacion) | `platform/workflow-*` |
| auditoria | 1 | EventoAuditoria (traza JSON + índices optimizados P0) | — |
| documentos | 1 | Repositorio documental (MinIO/S3) | — |
| notificaciones | 3 | Notificaciones | — |
| seguimiento | 4 | Reportes/entradas/alertas/umbrales | — |
| modificaciones | 3 | Solicitudes de modificación del POA | — |
| acciones_correctivas | 2 | Mejora continua | — |
| reportes | 1 | ReporteGenerado (exportar POA vía Celery) | — |
| core | 2 | Núcleo (ManifestoDatasetDemo, MapaMigracionesLegacy) + admin + raíz | — |

## 4. Base de datos

- Esquema único `public` con **217 tablas**, extensiones PostGIS 3.4.0.
- Prefijos de tablas por app (renombrados a español en el commit **9961550** `refactor(db): tablas renombradas a espanol` — 51 modelos + 4 M2M):
  - `accounts_*` → `cuentas_*` (cuentas_rol, cuentas_capacidad, cuentas_alcance_organizacional, cuentas_usuario)
  - `core_*` → `nucleo_*` (nucleo_manifesto_dataset_demo, nucleo_mapa_migraciones_legacy)
  - `budget_*` → `presupuesto_*` (presupuesto_techo_directivo, presupuesto_apertura, presupuesto_reforma, ...)
  - `catalogos_*` → `catalogo_*` (catalogo_version_clasificador, catalogo_fuente_financiamiento, ...)
  - `workflow_*` → `flujo_*` (flujo_definicion, flujo_instancia, flujo_tarea, flujo_aprobacion_motor, ...)
- **Colisión de prefijos detectada**: la app legacy `presupuesto` también usa `presupuesto_*` (`presupuesto_programapresupuestario`, `presupuesto_categoriaprogramatica`, ...). Se distinguen por sufijo (guiones vs camelCase concatenado). Ver `SCHEMA_MAPPING.md`.
- Apps sin renombrar: `articulacion_*`, `inversion_*`, `poau_*`, `planificacion_*`, `pad_*`, `organizacion_*`, `gestion_*`, `techos_*`, `recursos_*`, `territorio_*`, `indicadores_*`, `codificacion_*`, `seguimiento_*`, `modificaciones_*`, `normativa_*`, `notificaciones_*`, `documentos_*`, `auditoria_*`, `reportes_*`, `evaluacion_*`, `acciones_correctivas_*`.
- Patrón de versionado de datos (T4): `VersionClasificador` en catalogos (append-only, triggers, checksum `hash_fuente`), `VersionInstrumento` en planificacion (checksum SHA-256 + inmutabilidad de versiones aprobadas). El patrón se replica en budget (`DirectiveCeilingVersion`, checksum en modelos de apertura, línea 123/165/486/533 de `budget/models.py`).

## 5. API

- **V1 legacy**: `/api/v1/` (frontend `environment.apiUrl = '/api/v1'`).
- **V2** (`config/urls_v2.py:139-146`), namespaces por sistema (ADR-002):
  - `/api/v2/platform/` — workflow definiciones/instancias/tareas (núcleo transversal)
  - `/api/v2/sis-pe/` — instrumentos, versiones, nodos, vínculos, tipos-instrumento, metodologías, evaluaciones, lecciones, recomendaciones
  - `/api/v2/sis-poa/` — poas, acciones, operaciones, actividades, tareas, programaciones, techos
  - `/api/v2/sis-poa/budget/` — sub-router de `apps.budget.urls` (fiscal-years, directive-ceilings, resources, mandatory-expenses, documents, distribution, importaciones, reformas, auditoría...)
  - `/api/v2/sis-pro/` — proyectos, condiciones, documentos, costos, vínculos + preinversión completa (itcps, tdrs, edtps, estudios-tecnicos, revisiones, observaciones, aprobaciones...)
  - `/api/v2/me/` — identidad y capacidades del usuario (`MeViewSet`)
- `urls_test_sqlite.py`: variante sin PostGIS para CI (platform, sis-pe, sis-poa).
- Swagger vía drf-spectacular (`SPECTACULAR_SETTINGS`, título "SISPOA Sacaba API" — PIP_CORE pendiente).
- Paginación DRF `PageNumberPagination` (25) + paginación dual cursor (test_paginacion_dual.py), filtros django-filter + search + ordering, throttle anon 50/h, user 200/h, login 5/min, exception handler propio en `apps.core.exceptions`.

## 6. Autenticación y RBAC

- **SimpleJWT** (`settings.py:189-194`): access 4 h, refresh 1 día, rotación de refresh, header `Bearer`. `AUTH_USER_MODEL = 'accounts.Usuario'` (login por email, `USERNAME_FIELD='email'`).
- **OIDC opcional** (Keycloak, `mozilla-django-oidc`): solo se activa si `OIDC_RP_CLIENT_ID` está presente; convive con SimpleJWT.
- **RBAC por capacidades atómicas** (ADR-003, `accounts/models.py`): `Capacidad.codigo = "<sistema>.<dominio>.<accion>"` (p. ej. `sis_poa.budget.manage`, `sis_pe.instrumento.read`, `sis_pro.project.read`), agrupadas en `Rol` (M2M `cuentas_rol_capacidades`), asignadas a `Usuario` (M2M `cuentas_usuario_roles`). `AlcanceOrganizacional` restringe a unidades. El frontend construye menú y acciones desde `/api/v2/me/capabilities` (`CapabilitiesService`, `CapabilityGuard`, `PermissionsService`).
- Capacidades sembradas por data migrations: `accounts/0002` (WP-03), `0004` (budget approve/import/reform), `0005` (budget audit_read).

## 7. Palanca de cutover V2 (frontend)

`frontend/sispoa/src/app/core/config/cutover.config.ts` — `LEGACY_MENU_VISIBLE` oculta ítems V1 del menú (ADR-004/WP-14). Las rutas siguen accesibles por URL (reversible). Orden de retiro documentado: planificacion legacy → pad+articulacion → indicadores → poau → inversion → resto de V1. El sidebar marca los ítems legacy con la etiqueta "V1" (`sidebar.component.ts:54`).

## 8. Motor de workflow V2

`backend/apps/workflow/models_v2.py` (tablas `flujo_*`): `WorkflowDefinition` (plantilla por `tipo_entidad`, p. ej. `VersionInstrumento`), `WorkflowStepDefinition`, `WorkflowTransition` (con `capacidades_requeridas` y `requiere_aprobacion`), `WorkflowInstance` (genérica por `entidad_tipo`+`entidad_id`, única instancia abierta por entidad), `WorkflowTask` (bandeja con índice parcial `flujo_tarea_bandeja_idx`), `WorkflowObservacion` (severidades) y `WorkflowAprobacion` (aprobado/observado/rechazado) + `Delegacion`. Expuesto en `/api/v2/platform/workflow-*`; `workflow/services_v2.py` enlaza el paso final con acciones de dominio (p. ej. `VersionInstrumento.aprobar`).

## 9. Auditoría

`backend/apps/auditoria/models.py`: `EventoAuditoria` (tabla `auditoria_eventoauditoria`) con acciones (login, logout, crear, modificar, anular, restaurar, enviar, devolver, aprobar, reabrir, importar, exportar, consolidar, cerrar), snapshots JSON `datos_previos`/`datos_posteriores`, IP, gestión, e índices optimizados (`audit_entidad_historial_idx`, `audit_gestion_accion_idx`; trabajo P0 del commit `d21d683`). El frontend consume auditoría del presupuesto vía `/api/v2/sis-poa/budget/audit` con capacidad `sis_poa.budget.audit_read`.

## 10. Otros componentes

- **Celery + beat**: tarea `exportar-poa-completo-diario` (1:00 am, `apps.reportes.tasks`).
- **Logging**: consola + archivo rotativo `logs/sispoa.log` (PIP_CORE pendiente).
- **Almacenamiento**: FileSystemStorage local; MinIO/S3 con `USE_S3=True` (`settings_storage.py`, bucket `sispoa-docs`).
- **GeoServer + Keycloak**: servicios docker auxiliares (workspace `sispoa`, realm `sispoa`) referenciados desde nginx y docs.
- **Tests**: pytest 9 + pytest-django (BD test con `template_postgis`), specs Angular con karma; suites de contrato V2 en `backend/tests/`.

# AS-IS: Arquitectura Actual del PIP-GAMS Sacaba

Estado de la plataforma PIP-GAMS (Planificación, Articulación, Presupuesto y Gestión Municipal) al 2026-08-16, verificada contra el código fuente. Cada afirmación lleva una marca de confiabilidad: [CONFIRMADO] = verificado en código; [INFERIDO] = razonable pero no verificado; [DESCONOCIDO] = no se pudo determinar.

## 1. Stack

| Componente | Versión | Notas | Confiabilidad |
|---|---|---|---|
| Python | 3.14 | runtime backend | [CONFIRMADO] |
| Django | 6.0.7 | backend | [CONFIRMADO] |
| Django REST Framework | 3.17.1 | API V1/V2 | [CONFIRMADO] |
| djangorestframework-simplejwt | 5.5.1 | JWT | [CONFIRMADO] |
| drf-spectacular | 0.30.0 | OpenAPI 3 | [CONFIRMADO] |
| django-filter | 25.2 | filtros | [CONFIRMADO] |
| Celery | 5.6.3 | tareas async, broker Redis | [CONFIRMADO] |
| redis | 8.0.1 | broker/backend Celery | [CONFIRMADO] |
| PostgreSQL | 17 | base de datos | [CONFIRMADO] |
| PostGIS | 3.4 | extensión geoespacial | [CONFIRMADO] |
| Angular | 21.2 | frontend, Material, NgModules | [CONFIRMADO] |
| Gunicorn | 26.0.0 | servidor WSGI | [CONFIRMADO] |
| docker-storages + boto3 | 1.x | almacenamiento MinIO S3 | [CONFIRMADO] |
| mozilla-django-oidc | 4.x | OIDC (sin uso activo) | [CONFIRMADO] |
| docxtpl / python-docx | — | generación de documentos | [CONFIRMADO] |
| pytest + pytest-django + pytest-xdist | 9.1 / 4.12 / 3.8 | testing backend | [CONFIRMADO] |

## 2. Estructura del repositorio

[INFERIDO a partir de la auditoría; la raíz contiene:]

```
/backend                 — Django 6, 27 apps en backend/apps/, config en backend/config/
/frontend/sispoa         — Angular 21.2, 32 features lazy en src/app/features/
/docs                    — documentación (refactor-pip, pip_gams, sis-poa, prototipos)
/docker-compose.*        — entornos dev/full/prod [INFERIDO]
/Makefile                — targets make (make test-frontend roto) [CONFIRMADO]
```

## 3. Aplicaciones backend (27)

Ver inventario completo en `MODULE_INVENTORY.md`. Agrupación:

| Grupo | Apps |
|---|---|
| CORE | core, accounts, organizacion, territorio, workflow, documentos, notificaciones, auditoria, reportes, acciones_correctivas, normativa |
| SHARED | catalogos, codificacion |
| SIS-PE | planificacion, pad, articulacion, evaluacion, indicadores |
| SIS-POA | gestion, budget, poau, recursos, techos, presupuesto, modificaciones, seguimiento |
| SIS-PRO | inversion |

[CONFIRMADO] 27 apps: acciones_correctivas, accounts, articulacion, auditoria, budget, catalogos, codificacion, core, documentos, evaluacion, gestion, indicadores, inversion, modificaciones, normativa, notificaciones, organizacion, pad, planificacion, poau, presupuesto, recursos, reportes, seguimiento, techos, territorio, workflow.

## 4. Librerías principales

- Backend: ver sección 1. Adicionales: djangorestframework-gis (PostGIS), django-extensions, django-cors-headers, whitenoise, openpyxl (importación Excel), pillow.
- Frontend [CONFIRMADO]: Angular Material, rxjs; dependencias muertas detectadas: `@angular/material` (parcial), echarts, ngx-echarts, ol (OpenLayers), keycloakUrl/minioPublicUrl/geoserverUrl en environment.

## 5. Módulos funcionales (frontend, 32 features)

auth, admin-usuarios, auditoria, catalogos, documentos, gestion, normativa, notificaciones, organizacion, reportes, sistemas, workflow, dashboard, portal-publico, sis-pe, articulacion, matrices-pad, pad, indicadores, territorio, evaluacion, sis-poa, planificacion, poau, presupuesto, techos, recursos, seguimiento, modificaciones, consolidacion, inversion, sis-pro. [CONFIRMADO] — ver `MODULE_INVENTORY.md`.

## 6. Dominios encontrados

| Dominio | Apps | Estado |
|---|---|---|
| CORE (identidad, unidades, workflow, auditoría) | core, accounts, organizacion, territorio, workflow, documentos, notificaciones, auditoria, reportes, acciones_correctivas, normativa | activo |
| SHARED (catálogos, codificación) | catalogos, codificacion | activo (codificacion sin API) |
| SIS-PE (planificación estratégica, PAD, articulación, evaluación, indicadores) | planificacion, pad, articulacion, evaluacion, indicadores | dual V1/V2 |
| SIS-POA (presupuesto) | gestion, budget, poau, recursos, techos, presupuesto, modificaciones, seguimiento | dual, legacy declarado |
| SIS-PRO (inversión) | inversion | dual V1/V2 + preinversión |

## 7. Dependencias entre aplicaciones

Ver `DEPENDENCY_MAP.md`. Resumen [CONFIRMADO]: core es dependido Y dependiente (ciclo latente); hubs de lectura: reportes, budget, workflow, articulacion.

## 8. Base de datos

- PostgreSQL 17 + PostGIS 3.4, base `gams_pip`. [CONFIRMADO]
- 9 esquemas vía search_path en `backend/config/settings.py`: public, pip_core, pip_catalogo, sis_pe, sis_poa, sis_pro, pip_integracion, pip_auditoria, pip_geo, reportes. [CONFIRMADO, settings.py:116-124]
- ~213 tablas [INFERIDO]; inventario fino en `docs/refactor-pip/SCHEMA_MAPPING.md` (217 tablas mapeadas). [CONFIRMADO referencia]
- Renombrado masivo de tablas 2026-08-15: budget_*→presupuesto_*, workflow_*→flujo_*, catalogos_*→catalogo_*, accounts_*→cuentas_*, core_*→nucleo_*. Queries externas con nombres viejos quedan rotas. [CONFIRMADO]
- 127 migraciones, cero `DeleteModel`: nada se retira físicamente. [CONFIRMADO]

## 9. Autenticación

- JWT propio vía SimpleJWT (access/refresh), tokenKey `pip_token`. [CONFIRMADO]
- Keycloak/OIDC preparado (mozilla-django-oidc, settings_oidc.py, keycloakUrl) sin uso activo. [CONFIRMADO]
- Modelo de usuarios: Usuario/Rol/Capacidad/AlcanceOrganizacional en accounts (tablas cuentas_*). [CONFIRMADO]

## 10. Autorización

- Permisos por Capacidad en backend; frontend `PermissionsService` (accede a campo privado `authService['userSubject']`). [CONFIRMADO]
- Rutas legacy sin CapabilityGuard. [CONFIRMADO]

## 11. Frontend

- Angular 21.2, NgModules, 32 features lazy, tokens CSS `--pip-*`. [CONFIRMADO]
- `ApiService` antepone `environment.apiUrl` (`/api/v1`) a cada ruta. [CONFIRMADO, api.service.ts]
- tsconfig con `strict:false` y `strictTemplates:false`. [CONFIRMADO]
- `environment.prod.ts` hardcodea `http://localhost:9999/api/v1`. [CONFIRMADO]
- 28/32 features sin specs; Karma+Jasmine 32 specs. [CONFIRMADO]

## 12. Backend

- Modular monolith (ADR-009), 27 apps en `backend/apps/`. [CONFIRMADO]
- Middleware `DeprecationV1Middleware` (V1 Sunset 2027-01-01, RFC 8594). [CONFIRMADO]
- Monolitos de código: budget/models.py 1512 líneas, views 1532, services ~2100; budget.service.ts 1081 líneas. [CONFIRMADO]
- `core/validators.py:119` importa `apps.pad.models.PlanAnual` que no existe → ImportError si se invoca. [CONFIRMADO]

## 13. Contratos API (V1/V2)

- API V1: ~118 rutas, prefijo `api/v1/`, Sunset 2027-01-01 (RFC 8594). [CONFIRMADO]
- API V2: ~102 rutas, prefijo `api/v2/`, namespaces: platform, core, catalogos, geo, integracion, auditoria, sis-pe, sis-poa, sis-poa/budget, sis-pro, me. [CONFIRMADO, config/urls_v2.py]
- Schema OpenAPI y docs en `api/v2/schema/` y `api/v2/docs/`. [CONFIRMADO]
- Mapeo V1/V2: `docs/refactor-pip/API_MAPPING.md`. [CONFIRMADO referencia]

## 14. Infraestructura

- Docker Compose multi-entorno (dev/full/prod). [INFERIDO — docker-compose.* presente]
- Gunicorn + Nginx; MinIO S3 (storages/boto3); GeoServer; backups. [CONFIRMADO parcial: servicios referenciados en environment y compose]
- celery CMD con `-B` hardcodeado; healthcheck celery inválido. [CONFIRMADO]
- SIN CI/CD. [CONFIRMADO]

## 15. Testing

- Backend: pytest 9, 81 archivos, 1252 tests / 7m03s, xdist `-n auto --dist loadscope`. [CONFIRMADO]
- pytest.ini contradice make test-backend. [CONFIRMADO]
- Frontend: Karma + Jasmine, 32 specs; `make test-frontend` roto (apunta a contenedor nginx sin npm). [CONFIRMADO]

## 16. Build

- Backend: requirements.txt, sin empaquetado de distribución. [CONFIRMADO]
- Frontend: angular.json con budgets realistas (reciente saneo). [CONFIRMADO, commit e150161]

## 17. Deployment

- `docker-compose` dev/full/prod + Makefile. [INFERIDO]
- Sin pipeline CI/CD (build y deploy manuales). [CONFIRMADO]

## 18. Observaciones

1. V1 es el contrato que consume casi todo el frontend, pese al Sunset 2027-01-01. [CONFIRMADO]
2. `LEGACY_MENU_VISIBLE=true` total en cutover.config.ts. [CONFIRMADO]
3. Duplicaciones estructurales amplias — ver `DUPLICATION_ANALYSIS.md`.
4. Bug doble prefijo `/api/v1/api/v1` en features/organizacion. [CONFIRMADO, organizacion-ue.component.ts:35,79; organizacion-da.component.ts:35,79; organizacion-tree.component.ts:25]
5. No hay retiro físico de datos (estrategia correcta, peso muerto creciente).

## Referencias

- `docs/refactor-pip/ARQUITECTURA_ACTUAL.md` — detalle por aplicación.
- `docs/refactor-pip/ARQUITECTURA_OBJETIVO.md` — objetivo ya documentado.
- `docs/refactor-pip/SCHEMA_MAPPING.md` — 217 tablas mapeadas.
- `docs/refactor-pip/DOMAIN_MAP.md`, `docs/refactor-pip/API_MAPPING.md`, `docs/refactor-pip/FINAL_REPORT.md`.
- `docs/refactor-pip/LEGACY_DEPRECATION.md`, `docs/pip_gams/WP14_retiro_legacy.md`.
- `docs/modelo_datos.md`, `docs/ARQUITECTURA.md`, `docs/API.md`.
- `docs/sis-poa/presupuesto/architecture.md`, `docs/sis-poa/presupuesto/database.md`.
- ADRs: `docs/refactor-pip/ADR/ADR-001..ADR-010`.

Documento de gobernanza — creado en bootstrap ETAPA B (2026-08-16). No reemplaza a docs/refactor-pip/*; los complementa.

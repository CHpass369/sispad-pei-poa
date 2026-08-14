# Changelog

All notable changes to this project will be documented in this file.

## [0.10.0] - SIS-PRO Preinversión (SISPRE / RM 115)

### Added
- WP-11b: módulo de preinversión SISPRE dentro de SIS-PRO V2 (apps/inversion):
  - `Proyecto` extendido: tipología RM 115, geometría (PostGIS), presupuestos,
    puntaje de madurez, habilitación POA y estado del expediente.
  - Modelos de expediente: ITCP + condiciones previas, TDR + actividades/
    productos/personal/presupuesto referencial, EDTP + secciones dinámicas por
    tipología (catálogo RM 115), estudios técnicos, costos, financiamiento,
    cronograma, plan O&M, indicadores de evaluación, componentes, beneficiarios,
    alternativas, reformulaciones, documentos versionados con hash SHA-256,
    revisiones/observaciones/aprobaciones y patrón Outbox.
  - Servicios: clasificación RM 115, inicialización ITCP/EDTP, validaciones de
    aprobación (condiciones críticas, consistencia costo-financiamiento, O&M),
    cálculo de madurez 0-100 y paquete de transferencia a SISPOA.
  - Generación documental DOCX (docxtpl) con plantillas ITCP/EDTP y tarea
    Celery asíncrona; dependencias docxtpl/python-docx.
  - API V2 bajo `/api/v2/sis-pro/`: proyectos-preinversion (clasificar,
    inicializar ITCP/EDTP, madurez, validación, generación, transferencia,
    reformulación, elegibles para POA), itcps, itcp-condiciones, tdrs, edtps,
    secciones, estudios, costos, financiamiento, cronograma, plan O&M,
    indicadores, componentes, beneficiarios, alternativas, documentos,
    revisiones, observaciones y aprobaciones.
  - Semilla idempotente `seed_sispro_preinversion` y 26 tests de contrato
    (`tests/test_sis_pro_preinversion.py`).
- WP-11b-fr: frontend del módulo de preinversión (SIS-PRO):
  - `PreinversionService` tipado para los endpoint `/api/v2/sis-pro/` del
    expediente (ITCP, condiciones, TDR, EDTP, secciones, costos,
    financiamiento, componentes, documentos, transferencia).
  - Cartera de preinversión (filtros por gestión/tipología/habilitado POA y
    barra de madurez), expediente del proyecto (ficha, clasificación RM 115,
    inicializar ITCP/EDTP, calcular madurez, validar, generar DOCX, paquete
    de transferencia, enviar a SISPOA).
  - Asistentes ITCP (matriz de condiciones con semáforo), TDR (actividades,
    productos, personal y presupuesto referencial) y EDTP (secciones
    dinámicas, componentes, estudios, costos y financiamiento).
  - Rutas `/sis-pro/preinversion(/:id(/:asistente))` con CapabilityGuard y
    entrada de menú habilitada en el sidebar; 11 tests de servicio
    (`preinversion.service.spec.ts`).

## [0.9.0] — PIP-GAMS (refactor/pip-gams)

Plataforma Integral de Planificación del GAM Sacaba (SIS-PE + SIS-POA +
SIS-PRO sobre núcleo transversal). Ver `docs/pip_gams/` para arquitectura.

### Added
- WP-00 Baseline: tag `baseline-pre-pip-gams`, respaldos, OpenAPI V1 (339
  endpoints), inventario de 139 tablas.
- WP-01: glosario, domain map (68 modelos), política de metodologías, ADRs
  001-004 (base única, API V2, IAM, migración).
- WP-02: API V2 `/api/v2/` con namespaces platform/sis-pe/sis-poa/sis-pro/me
  + OpenAPI V2 dedicado.
- WP-03: IAM por capacidades (26 capacidades, alcances organizacionales,
  `me/capabilities`, permisos DRF `TieneCapacidad`/`TieneAlgunaCapacidad`).
- WP-04: kernel estratégico V2 (8 modelos: instrumentos, metodologías,
  nodos, vínculos; versiones inmutables con checksum SHA-256).
- WP-05: `LegacyMigrationMap` + comando `legacy_audit` (inventario,
  dry-run, marcar migrado, reconciliación por checksum).
- WP-06: importación del marco superior PGDESA/PDESA al kernel.
- WP-07: migración del PAD (jerarquía + articulación SIPEB como vínculos).
- WP-08: workflow configurable V2 (definiciones, instancias, tareas,
  observaciones, aprobaciones, delegaciones) + evaluación SIS-PE V2.
- WP-09: frontend SIS-PE V2 (módulo lazy, menú por capacidades,
  CapabilityGuard).
- WP-10: SIS-POA V2 (jerarquía canónica, programación físico-financiera,
  validación de techos, conexión PEI obligatoria).
- WP-11: SIS-PRO V2 (ciclo del proyecto de 11 fases, trazabilidad
  ascendente, documentos/condiciones/costos).
- WP-12: infraestructura (health checks con DB, celery beat, logging
  rotativo, pinning de imágenes, Keycloak con base separada).
- WP-13: calidad (cobertura de servicios 70-95%, tests de N+1, E2E del
  camino crítico, índices compuestos, restauración de respaldo ensayada).
- WP-14: plan de retiro de legacy (auditoría y roadmap, sin borrados).

### Changed
- `settings.py`: LOGGING, CELERY_BEAT_SCHEDULE, STORAGES (Django 6).
- `accounts`: modelos Capacidad y AlcanceOrganizacional (migraciones 0002-0003).
- Frontend: sidebar dinámico por capacidades; `environment.apiUrlV2`.

### Fixed
- Suite backend: de 678 errores de colección a 926 tests verdes.
- Infra de tests frontend: karma.conf.js, @types/jasmine, specs con drift
  (96 → 112 tests).
- Contratos API V2 paginados y consistentes.

## [Unreleased]

### Added
- Backend: evaluacion app (models, services, views, serializers)
- Backend: modificaciones app (models, services, views, serializers)
- Backend: notificaciones app (models, services, views, serializers)
- Backend: seguimiento app (models, services, views, serializers)
- Backend: acciones_correctivas app (models, services, views, serializers)
- Backend: MovimientoTecho model and services for budget movements
- Backend: PlanVersion model for plan versioning
- Backend: Core validators (Section 37 critical validations)
- Backend: Core alerts engine
- Backend: 15 new report functions
- Backend: Demo seed script (seed_demo.py)
- Frontend: admin-usuarios module
- Frontend: seguimiento module with dashboard
- Frontend: evaluacion module
- Frontend: modificaciones module
- Frontend: consolidacion module
- Frontend: portal-publico (public, no auth)
- Frontend: notificaciones module
- Frontend: dashboard (role-based)
- Frontend: Breadcrumbs component
- Frontend: Permissions service
- Frontend: Responsive layout improvements
- Tests: 163+ backend tests (workflow, techos, poau, pad)
- Tests: 8 frontend test specs
- Documentation: Installation guide
- Documentation: Architecture documentation
- Documentation: API reference
- Documentation: Roles documentation

### Changed
- settings.py: registered 5 new apps
- urls.py: added 5 new URL patterns
- app-routing.module.ts: added new routes

### Fixed
- Budget validation rules enforcement
- Workflow state transition guards
- Seguridad: flujo de restablecimiento de contraseña reescrito con
  `PasswordResetTokenGenerator` de Django (token de un solo uso, 24 h):
  - Eliminado `set_password` duplicado que rompía la contraseña del usuario
    si el reset no se completaba (regresión verificada con tests).
  - El email ya no contiene un bearer token de sesión (JWT), sino un token
    de reset con hash; el endpoint de confirmación requiere ahora `email` +
    `token` + `new_password` + `confirm_password`.
  - `PASSWORD_RESET_TIMEOUT = 86400` hace cierta la promesa de 24 h del email.
  - 8 tests nuevos de contrato del flujo (`apps/accounts/tests.py`).
- Docs: versión real de PostgreSQL/PostGIS (17/3.4) en ARQUITECTURA.md,
  INSTALACION.md y README.md.
- Backend: settings de prueba sin Docker (`config/settings_test_sqlite.py` +
  `config/urls_test_sqlite.py`) para correr tests de apps no-geo con SQLite:
  `pytest apps/accounts/tests.py --ds=config.settings_test_sqlite`.

## [1.0.0] — 2026-07-15

### Added — Fase 1: Núcleo institucional
- Proyecto Django 6.0.7 + DRF 3.17 + PostGIS 3.6
- 16 apps modulares: core, accounts, organizacion, gestion, catalogos, normativa,
  planificacion, indicadores, recursos, techos, presupuesto, inversion, territorio,
  workflow, documentos, reportes, auditoria
- Modelo de datos: 50+ entidades con migraciones
- Autenticación JWT (SimpleJWT), usuarios por email, RBAC con 12 roles
- Gestión fiscal con ciclo de vida (8 estados: preparación → archivada)
- Estructura organizacional jerárquica: Secretaría → DA → UE
- Auditoría completa de eventos con trazabilidad
- API REST bajo `/api/v1/` con paginación, filtros, búsqueda

### Added — Fase 2: Catálogos y planificación
- 13 clasificadores presupuestarios versionados con control de vigencia
- Importación masiva XLSX/CSV con hash SHA-256 y transacciones atómicas
- 34 categorías programáticas municipales semilla
- Planificación estratégica: PEI, PTDI, nodos, AMP/ACP
- Indicadores con fórmula, línea base, meta y programación trimestral
- Asistente Angular de formulación POA (wizard 5 pasos)

### Added — Fase 3: Recursos, techos y presupuesto
- Estimación de recursos anual y plurianual
- Techos presupuestarios con distribución por DA/UE/Programa
- Línea presupuestaria con llave completa (Entidad + DA + UE + Programa + ... + Objeto + Importe)
- Decimal para todos los montos (nunca float)
- Reglas presupuestarias legales parametrizadas con severidad y vigencia
- 9 reglas implementadas: funcionamiento (60%), SUS (10%), Renta Dignidad (0.75%),
  Seguridad Ciudadana (10%), consistencia plurianual, proyecto SISIN, etc.

### Added — Fase 4: Workflow y consolidación
- Máquina de estados: envío → revisión → devolución → subsanación → aprobación
- Observaciones con tipo, severidad, estado y conversación
- Consolidación institucional con alertas tipadas por programa
- Verificación de consistencia presupuestaria (5 comprobaciones)
- Acta de consolidación generada automáticamente
- Proyectos de inversión con código SISIN y priorización

### Added — Fase 5: Territorialización
- PostGIS con EPSG:32719 (métrica) y EPSG:4326 (web)
- Distritos, OTB/comunidades con geometrías
- Localización territorial de acciones y proyectos
- Validación de geometría dentro de jurisdicción municipal

### Added — Fase 6: Reportes
- XLSX: POA por unidad, consolidado institucional, proyectos de inversión
- CSV: observaciones
- GeoJSON: mapa de inversión territorial
- PDF: acta de aprobación
- Hash SHA-256 en cada archivo generado

### Added — Fase 7: Pruebas y seguridad
- 46 tests con pytest (reglas, API, consolidación, permisos)
- Base de datos PostGIS de prueba
- Settings de producción con HSTS, SSL, rate limiting
- Logging estructurado con rotación

### Added — Datos reales GAM Sacaba
- 8 Secretarías: SMFA, CM, SMPDT, SMMTDP, SMS, SMIS, SMDHI, STAFF
- 5 Direcciones Administrativas
- 12 Unidades Ejecutoras
- 112 Programas presupuestarios reales (000-351)
- 14 Fuentes de financiamiento (CT, RE, ORE, IDH, TGN)
- 72 Acciones de mediano plazo del PEI
- 13 Indicadores de seguimiento
- Estructura POA 2026 con techos por fuente (776 filas)

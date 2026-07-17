# Changelog

All notable changes to this project will be documented in this file.

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

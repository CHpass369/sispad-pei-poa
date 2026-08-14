# SIS-POA — Ciclo Presupuestario: Plan de Implementación

**Fecha**: 2026-08-14 · **Estado**: FASE 0 completada (auditoría) — plan aprobado para ejecución por fases
**Dominio**: Gestión Fiscal → Techo Directivo → Distribución → Aperturas → Fijación → POA/POAU → Objetos del Gasto → Reformulaciones → Seguimiento

---

## 1. Arquitectura encontrada

- **Backend**: Django 6.0.7 + DRF 3.17, PostgreSQL 16 + PostGIS 3.4 (nativo local; Docker roto en esta máquina), Celery + Redis, JWT SimpleJWT + OIDC, 26 apps en `backend/apps/`.
- **API**: `/api/v1/` (legacy) y `/api/v2/` con namespaces por sistema (ADR-002): `platform`, `sis-pe`, `sis-poa`, `sis-pro`, `me`. El namespace `sis-poa` ya existe con routers de `poau` y `techos` (`config/urls_v2.py`).
- **IAM (ADR-003)**: capacidades atómicas `<sistema>.<dominio>.<accion>` + roles; frontend construye menú por capacidades. Ya existe `sis_poa.budget.manage` en uso.
- **Frontend**: Angular (features/), módulos lazy, `CapabilityGuard` por ruta, sidebar con palanca de cutover V2 (commit 45f1f6d). `SisPoaService` (features/sis-poa/sis-poa.service.ts) es el patrón V2: HttpClient directo contra `apiUrlV2` con interfaces en el propio service.
- **Verificación base**: 963 tests backend + 150 tests frontend verdes en PostgreSQL local.

## 2. Componentes reutilizables (NO duplicar)

| Componente | Ubicación | Uso en el ciclo presupuestario |
|---|---|---|
| `GestionFiscal` | `apps/gestion/models.py` | Entidad de gestión (única por `anio`). Estados actuales: preparacion/abierta/formulacion/revision/consolidacion/aprobacion/cerrada/archivada. **Se extiende** con el ciclo del prompt (CONFIGURACION/HABILITADA/EN_FORMULACION/VIGENTE/CERRADA) sin romper los existentes. |
| `CicloFormulacion`/`EtapaFormulacion` | `apps/gestion/models.py` | Fechas y etapas por ciclo; el stepper de preparación puede apoyarse acá. |
| `FuenteFinanciamiento` (2 díg), `OrganismoFinanciador` (3 díg), `ObjetoGasto` (5 díg jerárquico), `RubroRecurso`, `EntidadTransferencia`, `VersionClasificador` (con `hash_fuente` SHA-256) | `apps/catalogos/models.py` | Catálogos corporativos versionados: fuentes, organismos, objetos del gasto, rubros de ingreso. **Siempre** con `version_clasificador`. |
| `CategoriaProgramatica` (entidad+DA+UE+programa+proyecto+actividad, `codigo_compuesto` autogenerado) | `apps/presupuesto/models.py` | Base programática de las aperturas (programa/subprograma/proyecto/actividad). |
| `AsignacionPresupuestariaUnidad`, `LineaPresupuestaria` | `apps/presupuesto/models.py` | Referencia de formulación actual; el control nuevo no los reemplaza, los complementa. |
| `DireccionAdministrativa`, `UnidadEjecutora` (FK DA), `UnidadOrganizacional` (árbol) | `apps/organizacion/models.py` | Dimensiones DA/UE/UO de la distribución. |
| `Distrito` (+ geometría) | `apps/territorio/models.py` | Distribución territorial. |
| `TechoPresupuestario`, `DistribucionTecho`, `MovimientoTecho` | `apps/techos/models.py` | Legacy actual de techos por DA; NO se mezcla con el techo directivo nuevo (se documenta su coexistencia y retiro futuro). |
| `EventoAuditoria` (transversal, `datos_previos/posteriores` JSON) | `apps/auditoria/models.py` | Trazabilidad del ciclo (CREATE/UPDATE/SUBMIT/APPROVE/FREEZE/REFORM…). |
| Motor `WorkflowDefinition/Instance/Task` | `apps/workflow/models_v2.py` | Flujo BORRADOR→EN_REVISION→APROBADO→FIJADO/OBSERVADO para techo y distribución (integración posterior, sin tocar el kernel). |
| Patrón de versionado inmutable: `VersionInstrumento.aprobar()` → `inmutable` + checksum SHA-256 de datos semánticos | `apps/planificacion/models_v2.py` | **Plantilla** para `DirectiveCeilingVersion` y `DistributionVersion` (inmutabilidad §25/§51/§96). |
| `TimeStampedModel`, `ActivableModel`, `VigenciaModel` | `apps/core/models.py` | Mixins base de las entidades nuevas. |
| `BudgetControlService` inexistente | — | **Crear**: núcleo financiero transaccional (§85-87). |

## 3. Tablas existentes que se reutilizan (sin duplicar)

`gestion_gestionfiscal`, `gestion_cicloformulacion`, `catalogos_fuentefinanciamiento`, `catalogos_organismofinanciador`, `catalogos_objetogasto`, `catalogos_rubrorecurso`, `catalogos_entidadtransferencia`, `catalogos_versionclasificador`, `presupuesto_categoriaprogramatica`, `organizacion_direccionadministrativa`, `organizacion_unidadejecutora`, `organizacion_unidadorganizacional`, `territorio_distrito`, `auditoria_eventoauditoria`.

## 4. Decisiones de arquitectura

1. **App nueva `apps/budget`**: el ciclo presupuestario del prompt (~20 entidades: techo directivo + versiones + recursos + gastos obligatorios + documentos, aperturas + asignaciones por fuente normalizadas, reservas, importaciones staging, versiones de distribución, reformulaciones + movimientos) NO existe y es un dominio coherente. Se crea como app Django propia (`budget`), siguiendo el patrón de apps por dominio del proyecto. Las entidades heredan de `TimeStampedModel`/`ActivableModel` y reutilizan los catálogos corporativos (sección 2) mediante FK.
2. **Gestión fiscal = `GestionFiscal` extendida**: no se crea `poa_gestion` duplicada. Migración que amplía `choices` del campo `estado` con CONFIGURACION/HABILITADA/EN_FORMULACION/VIGENTE/CERRADA (los estados actuales se mapean: preparacion≈CONFIGURACION, abierta≈HABILITADA, formulacion≈EN_FORMULACION, cerrada≈CERRADA). El bloqueo por gestión (§10) se implementa en los services de `budget`.
3. **Dinero**: `NUMERIC(18,2)` en todas las tablas nuevas; `Decimal` en Python; nunca float. Validación de no negativos con CheckConstraints (patrón de `AsignacionPresupuestariaUnidad`).
4. **Apertura programática**: `budget.Allocation` referencia `presupuesto.CategoriaProgramatica` (o sus componentes) + `territorio.Distrito` + DA/UE/UO + `codigo_sisin` (VARCHAR, ceros iniciales preservados). Asignación **normalizada por FF/OF** en `AllocationSource` (§31) — nunca columnas `monto_ct/monto_re/...`.
5. **Totales**: nunca filas de total en BD (§33); siempre agregaciones SQL.
6. **Fijación e inmutabilidad**: `DirectiveCeilingVersion`/`DistributionVersion` replican el patrón `VersionInstrumento` (inmutable + checksum SHA-256). POST /freeze valida consistencia y congela; PATCH sobre versión fijada → 409. Ajustes posteriores = `Adjustment`/`Reform` con histórico (§25, §97).
7. **Concurrencia (§87)**: `select_for_update()` dentro de `transaction.atomic` en el `BudgetControlService` para consumos de saldo; test de doble consumo (§134).
8. **Control central**: `BudgetControlService` con `get_directive_ceiling/get_distributable_ceiling/get_distributed/get_reserved/get_available_for_distribution/get_allocation_ceiling/get_allocated_to_expense_objects/get_allocation_available/validate_distribution/validate_expense_object/validate_reform/reserve/release/apply_movement`. Reglas §151 innegociables, todas en backend.
9. **API**: namespace `/api/v2/sis-poa/budget/` (ADR-002, V2 + capacidades) con routers por dominio: `fiscal-years`, `directive-ceilings`, `resources`, `sigep-imports`, `mandatory-expenses`, `allocations`, `distributions`, `programmatic-categories`, `imports`, `reforms`, `control`, `audit`. Swagger vía drf-spectacular (ya configurado).
10. **RBAC**: capacidades nuevas `sis_poa.budget.*` (create/edit/submit/approve/freeze/import/reform/audit-read) sembradas por data migration y mapeadas a roles (superadmin, tecnico_admin, planificador, jefe_ue, director) — patrón IAM de `accounts.0002`.
11. **Auditoría**: integración con `auditoria.EventoAuditoria` (operaciones del §113); no se crea tabla paralela.
12. **Frontend**: módulo lazy `features/sis-poa/budget/` con subcarpetas por dominio (fiscal-year, directive-ceiling, distribution, programmatic, imports, reforms, audit) + `BudgetService` tipado (patrón `SisPoaService`) + pipe `moneda` nuevo (`Bs 1.234.567,89`) + stepper de preparación de gestión (§115). Rutas con `CapabilityGuard` y capacidades `sis_poa.budget.*`. Sin tocar los módulos v1 (techos/presupuesto legacy) en esta fase.
13. **Importador Excel**: `openpyxl` (nueva dependencia backend) para XLSX/CSV; staging `Importacion/ImportacionDetalle/ImportacionError` con severidades INFO/WARNING/ERROR/CRITICAL; detección de header configurable; normalización (§61-62); nunca aplicar directo (§60). Perfiles `SISPOA_GASTOS_HISTORICO`/`SISPOA_GASTOS_ACTUAL`.
14. **SIGEP**: importador de reporte Techo (estructura §14) con documento de respaldo (tipo REPORTE_SIGEP/NOTA_MEF/...) y `sha256`; el PDF SIGEP se guarda como respaldo, el techo se registra normalizado por rubro/FF/OF.

## 5. Integraciones necesarias

- `config/urls_v2.py`: router `budget` dentro del namespace `sis-poa`.
- `config/settings.py`: registrar `apps.budget` en `INSTALLED_APPS` (LOCAL_APPS).
- Catálogo de capacidades IAM (data migration) + mapeo de roles.
- `frontend/sispoa/src/app/main.module.ts`: `loadChildren` del módulo budget.
- Sidebar: ítems del menú SIS-POA → Preparación de Gestión / Presupuesto (solo ítems V2 con capacidades).
- `docs/sis-poa/presupuesto/*.md` (documentación por dominio, Fase 13).

## 6. Riesgos

1. **Triple cadena POA existente** (poau_v2, articulacion.*POAU, planificacion.AccionCortoPlazo): el ciclo nuevo NO debe acoplarse a ninguna hasta la Fase 9 (objetos del gasto); se documenta el puente.
2. **Coexistencia techos v1 vs techo directivo nuevo**: `techos.TechoPresupuestario` sigue en uso por la UI legacy; el techo directivo es una entidad aparte. Riesgo de confusión → documentación y naming claro (`directive_ceiling` vs `techo_presupuestario`).
3. **GestionFiscal compartida**: extender `choices` es seguro; NO cambiar estados existentes ni su semántica.
4. **Importador Excel**: estructuras históricas variables (headers desplazados, filas combinadas, #REF!) — mitigado por staging + severidades + corrección.
5. **Volumen**: miles de aperturas → paginación server-side + índices en FK compuestas (gestion, version, programa, fuente).
6. **Concurrencia monetaria**: sin locks, se puede exceder saldo — mitigado con `select_for_update` + tests.
7. **Docker roto en esta máquina**: la verificación corre con venv local + PostgreSQL 16 nativo (DB_HOST=localhost) y npm/ng local. Las migraciones se aplican a la BD local.

## 7. Plan de implementación por fases

| Fase | Entregable | Verificación |
|---|---|---|
| 0 | Este plan + auditoría | — |
| 1 | **Gestión Fiscal**: estados de ciclo en `GestionFiscal` (migración), API `fiscal-years` (CRUD + enable/close con validaciones de bloqueo), UI `budget/fiscal-year` + stepper de preparación, tests | pytest + ng test |
| 2 | **Techo Directivo**: `DirectiveCeiling`+`Version`+`CeilingResource`+`MandatoryExpense`+`TechoDocumento`, API recursos/SIGEP/gastos obligatorios, dashboard de composición, fijación inmutable con checksum, tests | pytest |
| 3 | **Catálogos del ciclo**: categorías programáticas (árbol + duplicar a gestión), fuentes/organismos desde catálogos corporativos, seeds demo, tests | pytest |
| 4 | **Distribución**: `Allocation`+`AllocationSource`+`Reserve`, editor de grilla (CRUD + saldos por FF/OF + control ≤ techo distribuible), dashboard, tests | pytest + ng test |
| 5 | **Importador Excel**: staging + normalización + validación + corrección + perfiles, UI wizard, tests (GASTOS 2023/actual, #REF!, 097, SISIN) | pytest |
| 6 | **Distribución territorial**: reparto por distrito (manual/monto fijo/porcentaje/población con ajuste de redondeo exacto), reservas, tests | pytest |
| 7 | **Fijación de distribución**: versión inmutable + checksum + validación Σfuente = techo − reservas, UI, tests | pytest + ng test |
| 8 | **Control presupuestario**: `BudgetControlService` transaccional con locks, integración con Fase 9, tests de concurrencia | pytest |
| 9 | **Objetos del gasto**: programación por apertura con techo/programado/disponible, rechazo 409 BUDGET_EXCEEDED, tests | pytest + ng test |
| 10 | **Reformulaciones**: tipos + workflow de estados + movimientos atómicos con saldos antes/después, inmutabilidad de fijadas, tests | pytest + ng test |
| 11 | **Auditoría**: integración `EventoAuditoria` en todas las operaciones + UI de consulta, tests | pytest |
| 12 | **Testing**: E2E del flujo completo (§135), casos de fijación/inmutabilidad/concurrencia/importación | pytest + ng test |
| 13 | **Documentación**: 13 docs de `docs/sis-poa/presupuesto/` + CHANGELOG | — |

**Después de cada fase**: build + lint + tests + migraciones aplicadas + corrección + reporte (archivos creados/modificados, funcionalidad, pendientes) — sin acumular errores (§145).

## 8. Criterios de aceptación

Los §146-147 del prompt maestro: administrador completa el ciclo 2027 de punta a punta (habilitar → techo → distribución → fijar → formulación → objetos del gasto → reformulación → reportes → auditoría); una unidad no puede programar más que su disponible. Reglas §151 innegociables en backend.

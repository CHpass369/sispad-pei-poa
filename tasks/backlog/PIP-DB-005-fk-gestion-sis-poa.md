# TASK PIP-DB-005: FK gestión fiscal — SIS-POA legacy (techos, presupuesto, recursos, seguimiento, modificaciones, poau)

## DOMINIO

`sis-poa`

## OBJECTIVE

Fase 2: convertir los campos de gestión de SIS-POA legacy a FK sobre `GestionFiscal` con `ON DELETE PROTECT`. Requiere data migration: `poau.PoAInstitucional` (V2) tiene año huérfano **2028** (2 filas). `poau.POAU` y resto vacías.

## SCOPE

- Apps: `techos` (TechoPresupuestario), `presupuesto` (ProgramaPresupuestario, ProyectoPresupuestario, ActividadPresupuestaria, AsignacionPresupuestariaUnidad, LineaPresupuestaria), `recursos` (EstimacionRecurso, EstimacionPlurianual.anio), `seguimiento` (ReporteSeguimiento), `modificaciones` (SolicitudModificacion.gestion_fiscal), `poau` (POAU, PoAInstitucional, ProgramacionActividad.anio).
- Renombres de convención: `modificaciones.gestion_fiscal` → `gestion`.
- Data migration para `PoAInstitucional` 2028 (crear GestionFiscal 2028 solo si es gestión operativa real; verificar con negocio).
- Migración por app: integer → FK `PROTECT`.

## OUT OF SCOPE

- `budget` (ya FK, CASCADE) — deuda separada.
- Reformas `presupuesto_reforma` (budget) vs `modificaciones_*`: no mezclar.

## INVARIANTS

- `GestionFiscal` canónica intacta.
- No inventar gestiones falsas.

## DATABASE IMPACT

Data migration (PoAInstitucional 2028) + FKs por app. Índices `gestion` existentes conservados.

## API IMPACT

Contratos V1 (`/api/v1/sis-poa/...`) que exponen `gestion` entero: revisar serializers de techos/presupuesto/seguimiento.

## DEPENDENCIES

- `docs/architecture/GESTION_FISCAL_AUDIT.md` §4-5.

## ROLLBACK

Reversa de data migration + FKR por app.

## DECISIÓN DE DOMINIO (2026-08-16, §4.1 GESTION_FISCAL_AUDIT)

`poau.PoAInstitucional` P-2028 es **carga errónea probable** (creado 2026-08-10 por la corrida de importación de formulación del POA 2027; 0 acciones; 1 `ProgramacionActividad anio=2028` colgada de ACT-01 del P-2027). Acción: **validar con el equipo que cargó la planilla y limpiar** (eliminar P-2028; re-asignar o eliminar la programación 2028) ANTES de la FK. **NO crear GestionFiscal 2028** salvo validación explícita de negocio. El resto de SIS-POA legacy (techos, presupuesto, recursos, seguimiento, modificaciones, POAU) no tiene huérfanos → FK directa + renombres de convención (`modificaciones.gestion_fiscal` → `gestion`).

## FINAL REPORT

Decisión 2028 (creada o excluida), tablas migradas, contratos verificados.
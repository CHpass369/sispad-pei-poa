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

## FINAL REPORT

Decisión 2028 (creada o excluida), tablas migradas, contratos verificados.
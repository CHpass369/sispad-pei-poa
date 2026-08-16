# TASK PIP-DB-007: FK gestión fiscal — casos complejos (articulacion, planificacion, normativa)

## DOMINIO

`sis-pe` / `core` — la más compleja

## OBJECTIVE

Fase 2: resolver los casos complejos de gestión fiscal. **No es una FK simple**: mezcla datos operativos válidos (articulacion 2026/2027) con huérfanos reales (planificacion 2021/2025, 604+61 filas; normativa 2015/2021) y rangos plurianuales (Plan 2015-2050) que NO son gestiones fiscales.

## SCOPE

- Apps: `articulacion` (AccionPOA, SeguimientoPresupuesto, AsignacionObjetoGasto, BorradorMatrizPAD, LineamientoPAD.gestion_desde/hasta), `planificacion` (NodoPlanificacion, ArticulacionPlanificacion, AccionCortoPlazo, Plan.gestion_inicio/fin, AccionMedianoPlazo.gestion_inicio/fin), `normativa` (VersionNormativa, ReglaPresupuestariaLegal.gestion_desde/hasta).
- Data migration por tabla con huérfanos: clasificar CADA año como "gestión operativa real" (crear GestionFiscal con evidencia de negocio) o "horizonte plurianual" (excluir de FK).
- Aprovechar para alinear tipo: `articulacion` `IntegerField` → `PositiveIntegerField`.
- Documentar la excepción gobernada de rangos plurianuales (Plan, ReglaPresupuestariaLegal, LineamientoPAD): NO forzar FK; mantener entero con regla escrita.
- Migración: integer → FK `PROTECT` solo donde aplique.

## OUT OF SCOPE

- Crear gestiones falsas para satisfacer FK (prohibido).
- Cambiar la canónica o los estados del ciclo presupuestario.

## INVARIANTS

- `GestionFiscal` canónica intacta y sin inventos.
- Excepción plurianual documentada explícitamente.

## DATABASE IMPACT

Múltiples data migrations (articulacion, planificacion, normativa) + FKs. Índices `gestion`/`gestion_inicio` conservados.

## API IMPACT

Contratos V1/V2 de articulación y planificación que exponen `gestion` entero: revisar serializers (matrices A/B, nodos).

## DEPENDENCIES

- `docs/architecture/GESTION_FISCAL_AUDIT.md` §4-6.
- Coordinar con PIP-PE-001 (cadena operativa) por solapamiento en articulacion.

## ROLLBACK

Reversa de cada data migration + FKR por tabla.

## FINAL REPORT

Clasificación por año (creado vs excluido), excepción plurianual aprobada, tablas migradas, contratos verificados.
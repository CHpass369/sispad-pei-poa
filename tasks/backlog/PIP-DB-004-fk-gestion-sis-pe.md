# TASK PIP-DB-004: FK gestión fiscal — SIS-PE (pad, indicadores, evaluacion)

## DOMINIO

`sis-pe`

## OBJECTIVE

Fase 2: convertir los campos de gestión de SIS-PE simple a FK sobre `GestionFiscal` con `ON DELETE PROTECT`. Sin data migration: `pad.*` con gestión 2027 válida; `indicadores.MetaProgramada` y `evaluacion.Evaluacion` vacías. Uniformar convención de nombre.

## SCOPE

- Apps: `pad` (PoliticaPAD, LineamientoEstrategico, ResultadoTerritorial, ProductoTerritorial, ArticulacionSIPEB, ProgramacionAnualPAD.anio), `indicadores` (MetaProgramada), `evaluacion` (Evaluacion.fiscal_year).
- Renombres de convención: `pad.ProgramacionAnualPAD.anio` → `gestion` (si aplica); `evaluacion.fiscal_year` → `gestion`.
- Migración por app: integer → FK `PROTECT`.

## OUT OF SCOPE

- `articulacion` y `planificacion` (complejas → PIP-DB-007).
- `pad.ProgramacionAnualPAD` si resulta ser programación plurianual (decidir con evidencia; ver §5 GESTION_FISCAL_AUDIT).

## INVARIANTS

- `GestionFiscal` canónica intacta.
- Contratos V1 (Sunset 2027-01-01) sincronizados en el renombre.

## DATABASE IMPACT

Migraciones Django por app. Posibles renombres de columna + data migration trivial si hay datos.

## API IMPACT

Serializers/servicios que consumen `fiscal_year`/`anio`: revisar `pad`, `indicadores`, `evaluacion` V1/V2.

## DEPENDENCIES

- `docs/architecture/GESTION_FISCAL_AUDIT.md` §5 (decisiones).

## ROLLBACK

FKR + reversa de renombres.

## FINAL REPORT

Tablas migradas, renombres aplicados, contratos verificados.
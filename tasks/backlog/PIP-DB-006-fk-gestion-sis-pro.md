# TASK PIP-DB-006: FK gestión fiscal — SIS-PRO (inversion)

## DOMINIO

`sis-pro`

## OBJECTIVE

Fase 2: convertir los campos de gestión de SIS-PRO a FK sobre `GestionFiscal` con `ON DELETE PROTECT`. Requiere data migration: `inversion.CostoProyecto` (V2) tiene año huérfano **2028** (2 filas). `inversion.Proyecto` (V2) tiene 3 filas válidas (2027).

## SCOPE

- Apps: `inversion` (ProyectoInversion V1 gestion_inicio/gestion_fin, ProgramacionPlurianualProyecto.anio, ProgramacionFisicaFinanciera.gestion, Proyecto V2.gestion, CostoProyecto V2.anio).
- Data migration para `CostoProyecto` 2028 (crear GestionFiscal 2028 solo si es gestión operativa real; verificar con negocio).
- `ProyectoInversion.gestion_inicio/gestion_fin`: evaluar si son horizonte plurianual → excepción gobernada (ver §6 GESTION_FISCAL_AUDIT) o FK.
- Migración por app: integer → FK `PROTECT`.

## OUT OF SCOPE

- Otras apps de SIS-PRO sin campo `gestion` (preinversión usa `proyecto.gestion` por relación).
- Cambios de API (vincular con V2 contracts en tarea de cutover).

## INVARIANTS

- `GestionFiscal` canónica intacta.
- No inventar gestiones falsas.

## DATABASE IMPACT

Data migration (CostoProyecto 2028) + FKs. Índices `gestion` existentes conservados.

## API IMPACT

Serializers V2 de `proyectos`/`costos` que exponen `gestion`/`anio`.

## DEPENDENCIES

- `docs/architecture/GESTION_FISCAL_AUDIT.md` §4-5.

## ROLLBACK

Reversa de data migration + FKR.

## FINAL REPORT

Decisión 2028, tablas migradas, contratos verificados, decisión plurianual de ProyectoInversion.
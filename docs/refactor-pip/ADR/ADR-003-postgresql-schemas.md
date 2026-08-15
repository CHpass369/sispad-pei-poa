# ADR-003 — Esquemas PostgreSQL objetivo (pip_* / sis_*) y migración por fases

- **Fecha:** 2026-08-15
- **Estado:** Aceptado
- **Relacionado con:** ADR-001, ADR-002, ADR-005, ADR-010; plan maestro §16; `SCHEMA_MAPPING.md`; `DATA_MIGRATION_PLAN.md`

## Contexto

La base `gams_sis_poa` (PostgreSQL 16 + PostGIS 3.4.0) contiene las 217 tablas en un esquema único `public`, con prefijos por app que ya colisionan: tras el rename `9961550`, `presupuesto_categoria_programatica` (budget V2) y `presupuesto_categoriaprogramatica` (legacy) coexisten y se distinguen solo por el sufijo (guiones vs camelCase), una ambigüedad frágil. El plan maestro §16.2 proponía evaluar la separación por schemas "después de estabilizar V2" sin exigirla; sin embargo, la colisión de prefijos, el peso de las tablas legacy y la necesidad de límites físicos por bounded context hacen conveniente la separación por esquemas como soporte de los ADR-001/002.

## Decisión

1. **Esquemas objetivo** (todos dentro de la misma base `gams_pip` futura / `gams_sis_poa` hoy):
   `pip_core`, `pip_catalogo`, `sis_pe`, `sis_poa`, `sis_pro`, `pip_integracion`, `pip_auditoria`, `pip_geo` y `reportes` (distribución completa en `SCHEMA_MAPPING.md`).
2. **Migración por fases con backup verificable**: AUDIT → MAP → BACKUP (`pg_dump -Fc` + verificación) → CREATE TARGET → MIGRATE → VALIDATE (conteos, FKs, triggers, vistas, checksums) → SWITCH → DEPRECATE → REMOVE LEGACY (`DATA_MIGRATION_PLAN.md`).
3. **El esquema `public` es legacy**: se conserva íntegro durante la migración, se renombra a `public_legacy` al final del SWITCH y se elimina solo tras validación en producción con ventana de mantenimiento y respaldo verificado. **NUNCA se ejecuta `DROP SCHEMA ... CASCADE` al inicio.**
4. **Mecanismo de apuntado**: `search_path` por rol/`OPTIONS` en Django (recomendado) o `Meta.db_table = '"esquema"."tabla"'` con migración Django; `public` siempre al final del search_path para evitar resolver la colisión de prefijos.
5. **Tablas de sistema/PostGIS (`auth_*`, `django_*`, `geometry_columns`, `spatial_ref_sys`) permanecen en `public`** (KEEP_SYSTEM).
6. **Los nombres de tabla no cambian al mover** (KEEP); los renombrados semánticos (`techo_directivo`, `documento_adjunto`, etc.) son opcionales, posteriores y siempre con mapeo.

## Consecuencias

Positivas:

- La colisión `presupuesto_categoria_programatica` vs `presupuesto_categoriaprogramatica` se resuelve físicamente: budget → `sis_poa`, legacy → `public_legacy`.
- Los permisos se otorgan por esquema (mínimo privilegio por contexto) y las FKs quedan explícitas incluso entre esquemas.
- Los límites del monolito modular se reflejan en el catálogo de la BD: un error de dependencia entre contexts es visible en el esquema.

Negativas:

- El movimiento físico debe acompañarse SIEMPRE de ajuste Django (search_path o db_table + migración): desincronizar ORM y BD rompe el sistema en producción.
- Las funciones PL/pgSQL y triggers que referencian tablas movidas requieren recalificación o search_path correcto (riesgo R3 del plan de datos).
- Las extensiones (PostGIS) y sus vistas (`geometry_columns`) dependen del search_path: renombrar `public` exige verificación espacial real por entorno.
- La migración es irreversible una vez eliminado `public_legacy`; por eso el plan exige respaldo `-Fc` verificado y ventana de mantenimiento.

## Alternativas consideradas

1. **Mantener todo en `public`** (opción original del plan maestro §16.2): descartada como estado final por la colisión de prefijos y la falta de límites físicos entre contexts; se mantiene solo como fase intermedia.
2. **Una base por SIS (postgres separado por subsistema)**: descartada por el plan maestro §16.1: rompería la consistencia transaccional y la trazabilidad entre SIS-PE, SIS-POA y SIS-PRO.
3. **Renombrar tablas en `public` en lugar de esquemas**: descartada: multiplica las migraciones de `db_table` y no resuelve la separación por contexto.

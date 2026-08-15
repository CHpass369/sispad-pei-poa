# ADR-006 — Estructura organizacional única compartida

- **Fecha:** 2026-08-15
- **Estado:** Aceptado
- **Relacionado con:** ADR-001, ADR-002, ADR-003; plan maestro §15.2, §18.2; `SCHEMA_MAPPING.md` §1

## Contexto

La estructura institucional del GAMS está modelada una sola vez en `organizacion` (`UnidadOrganizacional`, `UnidadEjecutora`, `DireccionAdministrativa`, `TipoUnidad`, `AsignacionUsuarioUnidad`, tablas `organizacion_*`) y el IAM la consume vía `AlcanceOrganizacional` (`cuentas_alcance_organizacional`). Sin embargo, la tentación de cada subsistema es modelar su propia unidad: "unidad del PEI", "unidad del POA", "unidad del POAU" (p. ej. `AccionPOA` con responsables embebidos, jerarquías operativas en `articulacion`/`poau` con campos de unidad repetidos). Eso duplicaría la fuente de verdad de la organización y rompería los alcances de autorización: un usuario con alcance sobre una unidad debería ver la misma organización en los tres SIS.

## Decisión

1. **Existe UNA sola estructura organizacional compartida**: `organizacion.*` → `pip_core.unidadorganizacional` (+ `unidadejecutora`, `direccionadministrativa`, `tipounidad`, `asignacionusuariounidad`). Es la fuente de verdad para los tres SIS y para el IAM (alcances).
2. **PROHIBIDO crear `unidad_pe`, `unidad_poa`, `unidad_poau` o equivalentes** (ni en modelos, ni en tablas, ni en columnas que repliquen la jerarquía institucional por subsistema). Cualquier entidad que requiera una unidad organizacional la referencia por FK a `pip_core.unidadorganizacional`.
3. **Los responsables de acciones, operaciones y tareas del SIS-POA son FKs a la estructura compartida**, no textos ni jerarquías propias; los cargos o responsabilidades específicos se modelan como roles sobre esa estructura (p. ej. vía `AlcanceOrganizacional` o tablas de responsabilidad con FK).
4. **La asignación de usuarios a unidades se hace una sola vez** (`cuentas_alcance_organizacional`/`asignacionusuariounidad`), y el frontend deriva la navegación y los permisos desde `/api/v2/me/capabilities` + alcances (plan maestro §15.4).
5. **El alcance territorial** (`AlcanceTerritorial` futuro, plan maestro §15.2) sigue el mismo principio: referencia a `pip_geo.unidad_territorial`, sin duplicados por SIS.

## Consecuencias

Positivas:

- La autorización por alcance funciona igual en SIS-PE, SIS-POA y SIS-PRO: una unidad es una unidad en toda la plataforma.
- Los reportes y la consolidación institucional cruzan estructuras sin reconciliar jerarquías paralelas.
- La migración de esquemas es simple: `organizacion_*` se mueve completa a `pip_core` (MOVE en `SCHEMA_MAPPING.md` §1).

Negativas:

- Las entidades legacy que hoy embeben estructura (campos de unidad en tablas de `articulacion`, `poau`, `seguimiento`, `inversion`) requieren backfill de FKs antes de retirar las columnas duplicadas.
- El SIS-PRO (proyectos) y el SIS-PE (planes) deben aceptar la unidad compartida incluso cuando su modelo conceptual previo usaba unidades propias.
- La flexibilidad por subsistema se pierde deliberadamente: una estructura por SIS solo podría existir como vista derivada, no como fuente.

## Alternativas consideradas

1. **Estructura organizacional por subsistema (`unidad_pe`, `unidad_poa`, `unidad_poau`)**: descartado: duplica la fuente de verdad, rompe alcances y multiplica la reconciliación.
2. **Unidad genérica única + catálogo de "tipo de unidad por SIS"**: descartado como fuente de verdad: el tipo existe en `TipoUnidad` (`organizacion_tipounidad`) y se comparte; no se reimplementa por subsistema.
3. **Mantener la estructura en cada SIS y sincronizar**: descartado: la sincronización de datos maestros sin transaccionalidad reintroduce los problemas que el monolito modular evita.

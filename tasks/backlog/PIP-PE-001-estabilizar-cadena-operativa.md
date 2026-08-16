# TASK PIP-PE-001: Estabilizar cadena operativa (plan + auditoría de divergencia)

## DOMINIO

`sis-pe` (articulación) — impacto `sis-poa`

## OBJECTIVE

Producir el documento de equivalencia y el plan de convergencia de la triple cadena operativa (acción → operación → actividad → tarea) entre las implementaciones `articulacion_*`, `indicadores_*` y `poau_*`, más la auditoría de divergencia de datos. Esta tarea NO implementa la convergencia.

## CONTEXT

Auditoría ETAPA A (2026-08-16). La jerarquía operativa canónica V2 vive en `backend/apps/articulacion/models.py`: `AccionPOA` (:434), `OperacionPOAU` (:528), `ActividadPOAU` (:606), `TareaPOAU` (:704) — tablas `articulacion_*`. Existen dos implementaciones duplicadas del mismo concepto:

- `backend/apps/indicadores/models.py`: `Operacion` (:70), `Tarea` (:97), `Producto` (:114) — tablas `indicadores_*`; `docs/refactor-pip/LEGACY_DEPRECATION.md:36` las marca como duplicado de la jerarquía canónica con `REMOVE_LATER: retirar tras cutover V2 y reconciliación (WP-14)`.
- `backend/apps/poau/models.py`: `POAU` (:7), `POAUActividad` (:48) — tablas `poau_*`, conectadas a la cadena canónica mediante el puente manual `backend/apps/poau/migration_v2.py` (existe, verificado).

La convergencia es de riesgo medio (datos duplicados) según LEGACY_DEPRECATION y requiere reconciliación de datos antes del retiro.

## CURRENT BEHAVIOR

- Tres implementaciones coexisten para la misma cadena concepto (acción/operación/actividad/tarea) con esquemas y datos propios.
- `poau/migration_v2.py` puentea manualmente hacia la cadena canónica (proceso manual, sin idempotencia garantizada).
- La tabla de `LEGACY_DEPRECATION.md` indica retiro futuro de `indicadores_*` (REMOVE_LATER, WP-14) sin plan detallado.

## EXPECTED BEHAVIOR

- Documento de equivalencia completo: mapeo semántico y de campos entre `articulacion_*` (canónica), `indicadores_*` (legacy) y `poau_*` (puente), con reglas de negocio por nivel.
- Auditoría de divergencia de datos ejecutada: conteos por gestión, registros que existen en una y no en otra, estados inconsistentes, impactos en el cálculo de indicadores y seguimiento.
- Plan de convergencia por fases con `corte` de `indicadores_*` alineado a REMOVE_LATER (WP-14), registrado como tareas derivadas.
- Sin cambios de código funcional.

## IN SCOPE

- [ ] Documento de equivalencia (artefacto en `docs/architecture/` o `docs/refactor-pip/` sin duplicar contenido existente).
- [ ] Auditoría de divergencia de datos (queries read-only por gestión y por nivel).
- [ ] Plan de convergencia con fases y tareas derivadas en `tasks/backlog/` (incluye el corte de `indicadores_*` según REMOVE_LATER).
- [ ] Identificar y documentar el impacto en frontend de `indicadores` (features) al cortar.

## OUT OF SCOPE

- Implementar la convergencia (migraciones, merges de datos, refactor de puente `poau/migration_v2.py`).
- Retirar tablas `indicadores_*`.
- Cambios a modelos canónicos de `articulacion`.

## INVARIANTS

- La cadena canónica es `articulacion_*` (ADR-004 articulation-model, `docs/refactor-pip/ADR/ADR-004-articulation-model.md`).
- El retiro de `indicadores_*` respeta la secuencia REMOVE_LATER de LEGACY_DEPRECATION (tras cutover V2 y reconciliación).
- Nada de esta tarea altera datos ni endpoints.

## DATABASE IMPACT

`ninguno` en esta fase (auditoría read-only). Las fases de convergencia tendrán data migrations aprobadas en sus propias tareas.

## API IMPACT

`ninguno` en esta fase.

## FRONTEND IMPACT

`ninguno` en esta fase (solo inventario de features afectadas para el plan: `indicadores`, `poau`, `articulacion` en `frontend/sispoa/src/app/features/`).

## FILES EXPECTED

- `docs/architecture/` o `docs/refactor-pip/` — documento de equivalencia de cadena operativa — crear
- `tasks/backlog/` — tareas derivadas de convergencia (corte `indicadores_*`, refactor puente `poau/migration_v2.py`) — crear
- Posible actualización de `docs/refactor-pip/LEGACY_DEPRECATION.md` — modificar si la auditoría cambia el alcance de REMOVE_LATER (registrar evidencia)

## DEPENDENCIES

- `PIP-POA-001` (cutover techos) informativa: comparte el namespace V2 y el concepto de corte legacy; no bloqueante.
- Revisar `WP-14` de `LEGACY_DEPRECATION.md` para alinear el plan.

## ACCEPTANCE CRITERIA

- [ ] Documento de equivalencia con mapeo completo de los tres niveles en las tres implementaciones (con rutas y líneas de modelos).
- [ ] Auditoría de divergencia con números reales (registros por gestión y nivel; divergencias detectadas).
- [ ] Plan de convergencia por fases aprobado y tareas derivadas registradas en `tasks/backlog/`.
- [ ] Impacto frontend del corte documentado (features que consumen `indicadores_*`).

## TESTS

```bash
cd backend; python -m pytest apps/articulacion apps/indicadores apps/poau -q
# Auditoría read-only (ejemplos, ajustar a modelos reales):
cd backend; python manage.py shell -c "from apps.articulacion.models import AccionPOA; print(AccionPOA.objects.count())"
cd backend; python manage.py shell -c "from apps.indicadores.models import Operacion; print(Operacion.objects.count())"
cd backend; python manage.py shell -c "from apps.poau.models import POAU; print(POAU.objects.count())"
```

## RISKS

Medio. Riesgos: divergencia de datos mayor a lo estimado (reconciliación costosa), consumidores externos de `indicadores_*` (V1/V2), cálculo de metas que dependa de la cadena legacy. Mitigación: auditoría primero, corte solo tras reconciliación aprobada (REMOVE_LATER), deprecación blanda antes del retiro. Riesgo de duplicar documentación ya existente en `docs/refactor-pip/`; mitigación: referenciar sin duplicar (regla de ADR-011).

## ROLLBACK

No aplica en esta fase (sin cambios funcionales). Las fases de convergencia tendrán su propio ROLLBACK (migraciones de reversa, restore de datos antes del corte).

## FINAL REPORT

Completar al cerrar con `/task-close`: documento de equivalencia, números de la auditoría, tareas derivadas creadas, impacto frontend documentado, riesgos y deuda detectada (p.ej. puente `poau/migration_v2.py` sin idempotencia).

# TASK PIP-ARCH-003: Actualizar docs/ARQUITECTURA.md tras eliminación de validadores

## DOMINIO

`core/infra` (docs)

## OBJECTIVE

Sincronizar `docs/ARQUITECTURA.md` (sección ~484-495) que aún documenta las 6 validaciones eliminadas en PIP-CORE-002, referenciando el estado real y la decisión de dominio.

## CONTEXT

Deuda registrada en PIP-CORE-002 (cerrada 2026-08-16): `docs/ARQUITECTURA.md:484-495` lista las funciones `validar_accion_poa_sin_pei`, `validar_accion_pei_sin_pad`, `validar_meta_sin_indicador`, `validar_indicador_sin_unidad`, `validar_actividad_fuera_periodo`, `validar_presupuesto_mayor_techo` como diseño original de core. Las 6 fueron eliminadas: sus reglas viven en el motor de articulación y budget V2.

## CURRENT BEHAVIOR

- El documento describe validadores que ya no existen en el código.

## EXPECTED BEHAVIOR

- La sección refleja la decisión (reglas trasladadas a su dominio canónico) y referencia `tasks/completed/PIP-CORE-002-...` y `docs/architecture/DOMAIN_BOUNDARIES.md`.

## IN SCOPE

- [ ] Localizar y actualizar la sección de validadores en `docs/ARQUITECTURA.md`.
- [ ] No reescribir el resto del documento.

## OUT OF SCOPE

- Otras actualizaciones del documento.

## INVARIANTS

- Sin cambios de código.

## DATABASE IMPACT

`ninguno`

## API IMPACT

`ninguno`

## FRONTEND IMPACT

`ninguno`

## FILES EXPECTED

- `docs/ARQUITECTURA.md` — modificar (solo la sección de validadores)

## DEPENDENCIES

- PIP-CORE-002

## ACCEPTANCE CRITERIA

- [ ] La sección ya no lista las 6 funciones como activas.
- [ ] Referencia la decisión y su tarea.

## TESTS

`ninguno` (docs). Verificación: grep del nombre de las funciones en el doc → solo menciones históricas/decisión.

## RISKS

Ninguno.

## ROLLBACK

`git revert <commit>`.

## FINAL REPORT

Completar al cerrar: líneas modificadas, referencias agregadas.

# TASK PIP-PE-003: Corte de `indicadores_*` (REMOVE_LATER WP-14)

## DOMINIO

`sis-pe` (indicadores legacy) — impacto frontend y backend

## OBJECTIVE

Retirar la jerarquía operativa legacy `indicadores_*` (`Operacion`, `Tarea`, `Producto` y modelos asociados `Indicador`/`MetaProgramada`/`MedioVerificacion`/`Supuesto`) según REMOVE_LATER de `LEGACY_DEPRECATION.md` (punto 17, WP-14), siguiendo la deprecación escalonada (§1, §4): marcar → ventana → retirar. La auditoría PIP-PE-001 confirmó que **la tabla está vacía** (0 registros), por lo que NO requiere reconciliación de datos.

## CONTEXT

`docs/architecture/CADENA_OPERATIVA_EQUIVALENCIA.md` §8 documenta el impacto: frontend `features/indicadores` y `features/portal-publico` (público) consumen `GET /indicadores/`; sidebar ítem `/indicadores` (`legacy: true`); palanca `LEGACY_MENU_VISIBLE['/indicadores']=true` (cutover paso 3). Backend que referencia `indicadores_*`: `planificacion/views.py` (FormulacionViewSet crea Indicador/MetaProgramada/Operacion), `workflow/consolidacion.py`, `reportes/services.py`, `scripts/seed_demo.py`, `poau/migration_v2.py:228` (`comparar_duplicados_poa`), comandos `importar_matriz_base`/`importar_reales`, tests. Rutas V1: `config/urls.py:29` monta `apps.indicadores.urls` en la raíz.

## CURRENT BEHAVIOR

- Endpoints V1 raíz `/api/v1/{indicadores,operaciones,tareas,productos,metas-programadas,medios-verificacion,supuestos}/` activos y visibles.
- `Indicador`/`MetaProgramada` usados por reportes, formulación y portal público.

## EXPECTED BEHAVIOR

- Indicadores legacy ocultos (palanca `false`) y deprecados (`DeprecationWarning` + header `Deprecation`).
- Portal público e indicadores del municipio sirviéndose de la fuente V2 (`articulacion.IndicadorCadena` vía `/api/v2/integracion/indicadores/`).
- Tablas `indicadores_*` retiradas tras ventana de observación, con respaldo `-Fc` y registro en `nucleo_mapa_migraciones_legacy`.

## IN SCOPE

- [ ] Deprecación blanda: ocultar menú (palanca), warnings backend, header `Deprecation` en endpoints V1 de indicadores.
- [ ] Migrar `features/portal-publico` a fuente V2 de indicadores.
- [ ] Migrar/neutralizar consumidores backend (`FormulacionViewSet`, `consolidacion`, `reportes`, `seed_demo`, `comparar_duplicados_poa`, comandos, tests).
- [ ] Ventana de observación (1 ciclo de gestión según §4).
- [ ] Retiro: eliminar modelos de `indicadores_*` y endpoints tras ventana (tarea de retiro aprobada).

## OUT OF SCOPE

- Cambiar `articulacion` (canónica se conserva).
- Reconciliación de datos (no hay: tablas vacías — verificado PIP-PE-001).
- Refactor de `poau/migration_v2.py` (PIP-PE-004).

## INVARIANTS

- Respetar secuencia REMOVE_LATER: tras cutover V2 y reconciliación (PIP-PE-002).
- Nunca romper el portal público ni reportes: migrarlos antes del retiro.
- No borrar tablas sin respaldo verificado y registro (regla DATABASE AGENTS.md).

## DATABASE IMPACT

Fase final: eliminación de tablas `indicadores_*` (6-7 tablas) por migración con respaldo previo. Deprecación: sin cambios de esquema.

## API IMPACT

- V1: endpoints de `indicadores` deprecados (header `Deprecation`) y luego 404.
- V2: `articulacion.IndicadorCadena` como fuente oficial de indicadores.

## FRONTEND IMPACT

- `features/indicadores` → ocultar/retirar.
- `features/portal-publico` → apuntar a `/api/v2/integracion/indicadores/`.
- `sidebar.component.ts` ítem `/indicadores` oculto.
- `cutover.config.ts` `/indicadores` → `false`.

## FILES EXPECTED

- Migración de deprecación y de retiro en `backend/apps/indicadores/migrations/`.
- Cambios en `planificacion/views.py`, `workflow/consolidacion.py`, `reportes/services.py`, `scripts/seed_demo.py`, `poau/migration_v2.py`, tests.
- Frontend: `portal-publico.service.ts`, `portal-indicadores.component.ts`, `sidebar.component.ts`, `cutover.config.ts`.

## DEPENDENCIES

- `PIP-PE-002` (reconciliación previa).
- `PIP-PE-001` (auditoría: impacto frontend/backend).

## ACCEPTANCE CRITERIA

- [ ] Palanca `/indicadores` oculta el ítem del menú.
- [ ] Portal público muestra indicadores desde V2 (sin llamar `/api/v1/indicadores/`).
- [ ] Ningún test ni servicio consume `indicadores_*` tras la migración.
- [ ] Retiro con respaldo verificado y registro en `nucleo_mapa_migraciones_legacy`.

## TESTS

```bash
cd backend; python -m pytest apps/articulacion apps/indicadores apps/poau apps/workflow apps/reportes -q
cd frontend/sispoa; npx ng test --watch=false
```

## RISKS

Medio-bajo: tablas vacías (riesgo de datos nulo), pero el portal público y reportes dependen de `Indicador`. Riesgo de romper `FormulacionViewSet` (formulación V1) → mitigado: migrar escritura a V2 o deprecar la formulación V1 en la misma ventana.

## ROLLBACK

Restore `-Fc` previo al retiro; revertir palanca del menú; restaurar endpoints deprecados (reversible hasta el 404).

## FINAL REPORT

Features/servicios migrados, endpoints deprecados y retirados, respaldo verificado, deuda detectada.
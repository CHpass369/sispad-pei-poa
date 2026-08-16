# TASK PIP-POA-001: Cutover de techos legacy a DirectiveCeiling en API V2

## DOMINIO

`sis-poa`

## OBJECTIVE

Definir y ejecutar el contrato de migración entre `/api/v2/sis-poa/techos/` (legacy `techos.TechoPresupuestario`) y `/api/v2/sis-poa/budget/directive-ceilings/` (canónico `budget.DirectiveCeiling`), migrar el frontend (4 vistas de techos) y deprecar la ruta legacy V2 — sin retirar tablas.

## CONTEXT

Auditoría ETAPA A (2026-08-16). En el mismo namespace V2 conviven dos APIs del mismo concepto:

- **Legacy**: `/api/v2/sis-poa/techos/` — `TechoViewSetV2` de `backend/apps/techos/views_v2.py`, registrado en `backend/config/urls_v2.py:149` (`sis_poa_router.register('techos', TechoViewSetV2, basename='v2-techos')`). Modelo `TechoPresupuestario` en `apps/techos/models.py`.
- **Canónico**: `/api/v2/sis-poa/budget/directive-ceilings/` — `DirectiveCeilingViewSet` en `backend/apps/budget/urls.py:32-33` (`basename='v2-directive-ceilings'`), más la action de composición `directive-ceilings/<int:pk>/composition/` (línea 63). El include está en `backend/config/urls_v2.py:242`.

Decisión arquitectónica previa: `ADR-005 budget-inside-sis-poa` (`docs/refactor-pip/ADR/ADR-005-budget-inside-sis-poa.md`) — budget es el dominio canónico de SIS-POA; `techos` es legacy V1. Frontend: la feature `frontend/sispoa/src/app/features/techos/` consume la ruta legacy.

## CURRENT BEHAVIOR

- El frontend de techos (feature `techos/`) llama a `/api/v2/sis-poa/techos/` (o V1 según configuración `LEGACY_MENU_VISIBLE` / `cutover.config.ts`).
- Las dos rutas V2 coexisten exponiendo el mismo concepto con modelos y contratos distintos (TechoPresupuestario vs DirectiveCeiling).

## EXPECTED BEHAVIOR

- Contrato de migración documentado: mapeo de campos TechoPresupuestario ↔ DirectiveCeiling, equivalencias de endpoints (list/retrieve/create/update/delete + composition), manejo de `gestion` y montos.
- Frontend migrado: las 4 vistas de la feature `techos/` consumen `directive-ceilings`.
- Ruta legacy `/api/v2/sis-poa/techos/` deprecada (header de deprecación o respuesta 410 con cuerpo de migración, según contrato V2) — sin retirar tablas ni endpoints V1.

## IN SCOPE

- [ ] Documento de equivalencia TechoPresupuestario ↔ DirectiveCeiling (campos, tipos, reglas de negocio: techos por gestión, límites).
- [ ] Migración del frontend de techos (4 vistas) al contrato canónico.
- [ ] Deprecación de la ruta V2 legacy `techos` con contrato de deprecación explícito (definir: header `Deprecation`/`Sunset` o 410; registrar en `docs/refactor-pip/LEGACY_DEPRECATION.md`).

## OUT OF SCOPE

- Retiro de tablas (`techos_*`) o de endpoints V1 (Sunset 2027-01-01 se respeta).
- Cambios al modelo `DirectiveCeiling` o su API.
- Cutover de `LEGACY_MENU_VISIBLE` (decisión separada; ver `frontend/sispoa/src/config/cutover.config.ts`).

## INVARIANTS

- `budget.DirectiveCeiling` es la única fuente canónica de techos directivos (ADR-005).
- Los datos legacy no se borran ni se transforman sin data migration aprobada.
- API V1 sigue viva hasta su Sunset.

## DATABASE IMPACT

`ninguno` en esta fase (solo API + frontend). Si el mapeo exige sync de datos legacy→canónico, se crea tarea separada con data migration.

## API IMPACT

- Deprecación de `/api/v2/sis-poa/techos/` (contrato de deprecación).
- Consumo nuevo de `/api/v2/sis-poa/budget/directive-ceilings/` (y `.../composition/`).

## FRONTEND IMPACT

- Feature `frontend/sispoa/src/app/features/techos/` — 4 vistas migradas al nuevo contrato (servicios, modelos TS, templates si cambian campos).

## FILES EXPECTED

- `docs/refactor-pip/LEGACY_DEPRECATION.md` — modificar: registrar deprecación de `techos` V2 (fila de la tabla existente)
- `frontend/sispoa/src/app/features/techos/` — modificar: servicios y vistas (4)
- `backend/apps/techos/views_v2.py` o `urls_v2.py` — modificar: deprecación de la ruta (según contrato definido)
- Posible `docs/architecture/INTEGRATION_CONTRACTS.md` — modificar: contrato de cutover

## DEPENDENCIES

- `PIP-DB-001` (gestión fiscal) solo informativa; no bloqueante.
- Verificar `cutover.config.ts` y `LEGACY_MENU_VISIBLE` para no romper el menú legacy.

## ACCEPTANCE CRITERIA

- [ ] Documento de equivalencia aprobado y versionado (o sección en INTEGRATION_CONTRACTS).
- [ ] Las 4 vistas de techos consumen `directive-ceilings` y responden 200 contra backend real.
- [ ] `/api/v2/sis-poa/techos/` responde según contrato de deprecación definido (header o 410), sin romper V1.
- [ ] Suite frontend en verde (252/252) y suite backend en verde (1252).

## TESTS

```bash
cd backend; python -m pytest apps/techos apps/budget -q
cd frontend/sispoa; npm test -- --watch=false
# Verificación manual de contrato:
curl -s http://localhost:8000/api/v2/sis-poa/budget/directive-ceilings/ | head
curl -s -D - http://localhost:8000/api/v2/sis-poa/techos/ | head -20
```

## RISKS

Medio. Riesgo principal: divergencia de contrato entre TechoPresupuestario y DirectiveCeiling (montos, agrupación por gestión, composición de objetos de gasto) que rompa las 4 vistas. Mitigación: documento de equivalencia primero; pruebas de contrato contra backend real. Riesgo: consumidores externos de `/api/v2/sis-poa/techos/`; mitigación: deprecación blanda con header y aviso, no 410 inmediato.

## ROLLBACK

- Frontend: revert del commit (restaurar servicios a `techos/`).
- Backend: revert del commit de deprecación (la ruta legacy vuelve a servir).
- No hay migración de datos en esta fase → rollback sin impacto de datos.

## FINAL REPORT

Completar al cerrar con `/task-close`: contrato definido, vistas migradas, contrato de deprecación aplicado, tests ejecutados, consumidores detectados, deuda (p.ej. sync de datos legacy si aplica).

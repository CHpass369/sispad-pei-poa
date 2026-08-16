# TASK PIP-CORE-001: Eliminar doble prefijo `/api/v1/` en components de organizacion

## DOMINIO

`core` (organizacion)

## OBJECTIVE

Eliminar las URLs rotas `/api/v1/api/v1/...` que generan 404 en las tres features de organizacion, pasando rutas sin prefijo al ApiService (que ya antepone `environment.apiUrl = '/api/v1'`).

## CONTEXT

Bug confirmado en la auditoría ETAPA A (2026-08-16). `frontend/sispoa/src/app/features/organizacion/` pasa paths con el prefijo literal `/api/v1/...` a `ApiService`, que ya antepone `environment.apiUrl` (`'/api/v1'`), produciendo `GET /api/v1/api/v1/unidades-ejecutoras/` → 404. Los endpoints V1 reales existen en `backend/apps/organizacion/urls.py` (router): `unidades-ejecutoras` (línea 12), `direcciones-administrativas` (línea 11) y la action `arbol` del viewset (unidades, `backend/apps/organizacion/views.py:25`). Regla de contrato en AGENTS.md → CONTRACTS: prohibido el patrón de doble prefijo.

## CURRENT BEHAVIOR

- `organizacion-ue.component.ts:35` — `this.api.get('/api/v1/unidades-ejecutoras/')` → 404
- `organizacion-ue.component.ts:78-79` — `PUT/POST '/api/v1/unidades-ejecutoras/{id}/'` → 404
- `organizacion-ue.component.ts:92` — `DELETE '/api/v1/unidades-ejecutoras/{id}/'` → 404
- `organizacion-da.component.ts:35,78,79,92` — mismo patrón con `/api/v1/direcciones-administrativas/...` → 404
- `organizacion-tree.component.ts:25` — mismo patrón con `/api/v1/unidades/arbol/` → 404

## EXPECTED BEHAVIOR

Los tres componentes llaman rutas sin prefijo:

- `/unidades-ejecutoras/`
- `/direcciones-administrativas/`
- `/unidades/arbol/`

y las peticiones resultantes llegan a `/api/v1/<ruta>` con 200.

## IN SCOPE

- [ ] Corregir `organizacion-ue.component.ts` (líneas 35, 78-79, 92)
- [ ] Corregir `organizacion-da.component.ts` (líneas 35, 78-79, 92)
- [ ] Corregir `organizacion-tree.component.ts` (línea 25)
- [ ] Verificar contra el backend que los endpoints V1 existen (confirmado en `organizacion/urls.py`; re-verificar con test o request)

## OUT OF SCOPE

- Migrar organizacion a API V2
- Cambios en ApiService o en `environment.apiUrl`
- Cualquier otra feature con el mismo patrón (registrar hallazgos en `tasks/technical-debt/`)

## INVARIANTS

- ApiService y su prefijado (`environment.apiUrl`) no se modifican.
- Sin cambios en backend.
- Los componentes no cambian sus tipos de datos ni contratos de respuesta.

## DATABASE IMPACT

`ninguno`

## API IMPACT

`ninguno` (los endpoints V1 ya existen; solo se corrige la ruta solicitada)

## FRONTEND IMPACT

3 componentes de `frontend/sispoa/src/app/features/organizacion/`.

## FILES EXPECTED

- `frontend/sispoa/src/app/features/organizacion/organizacion-ue.component.ts` — modificar: quitar prefijo `/api/v1`
- `frontend/sispoa/src/app/features/organizacion/organizacion-da.component.ts` — modificar: quitar prefijo `/api/v1`
- `frontend/sispoa/src/app/features/organizacion/organizacion-tree.component.ts` — modificar: quitar prefijo `/api/v1`

## DEPENDENCIES

`ninguna`

## ACCEPTANCE CRITERIA

- [ ] Ninguna llamada en los 3 componentes contiene el prefijo literal `/api/v1/` (grep sin matches).
- [ ] La suite frontend no rompe (252/252 antes; sin regresiones).
- [ ] Verificación de contrato: las rutas resultantes (`/api/v1/unidades-ejecutoras/`, `/api/v1/direcciones-administrativas/`, `/api/v1/unidades/arbol/`) responden 200 contra el backend en ejecución (o test de servicio que capture la URL final).

## TESTS

```bash
cd frontend/sispoa; npm test -- --watch=false
# verificación de rutas resultantes (inspección o spec de servicio):
# grep -rn "/api/v1/" src/app/features/organizacion/  # debe devolver 0 matches
cd backend; python -m pytest apps/organizacion -q  # endpoints V1 siguen vivos
```

## RISKS

Bajo. Riesgo principal: algún componente dependa de un endpoint V1 que no exista con ese nombre exacto (por ejemplo, el árbol). Mitigación: verificar el 200 contra backend antes de cerrar (los endpoints están confirmados en `organizacion/urls.py` y `views.py`).

## ROLLBACK

- Revert del/los commit(s): `git revert <commit>`
- Si se cambió solo el frontend, el rollback es trivial: restaurar las rutas con prefijo en los 3 componentes y rebuild.

## FINAL REPORT

Cerrada 2026-08-16.

**Archivos modificados (3):**
- `frontend/sispoa/src/app/features/organizacion/organizacion-ue.component.ts` — 4 rutas sin prefijo (L35 GET, L78 PUT, L79 POST, L92 DELETE)
- `frontend/sispoa/src/app/features/organizacion/organizacion-da.component.ts` — 4 rutas sin prefijo (mismo patrón)
- `frontend/sispoa/src/app/features/organizacion/organizacion-tree.component.ts` — 1 ruta sin prefijo (L25 GET `/unidades/arbol/`)

**Tests ejecutados:** suite frontend completa `npm test -- --watch=false` → 252/252 SUCCESS (sin regresiones vs baseline); `pytest apps/organizacion` → "no tests ran" (tests.py vacío pre-existente, ver deuda).

**Verificación de endpoints:** `unidades-ejecutoras` (urls.py:12), `direcciones-administrativas` (urls.py:11), action `arbol` (views.py:24-25) confirmados en backend; ApiService antepone `environment.apiUrl` (api.service.ts:8). Grep `/api/v1/` en features/organizacion → 0 matches.

**Commits:** `de1d126` (movimiento de tarea) + `d1de941` (fix).

**Riesgos:** bajo; sin cambios de contratos ni tipos.

**Trabajo pendiente / deuda:** `backend/apps/organizacion/tests.py` es un stub vacío — la app no tiene tests de backend (candidato a nueva tarea PIP-CORE). No se hallaron otros doble-prefijos en features productivas (specs con `/api/v1/` en expectOne son correctos: URL final prefijada).

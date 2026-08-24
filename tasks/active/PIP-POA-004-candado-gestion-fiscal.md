# TASK PIP-POA-004: Candado de gestión fiscal para SIS-POA

## DOMINIO

`sis-poa` (con impacto transversal en el núcleo `gestion`)

## OBJECTIVE

Implementar el candado general de gestión fiscal: una sola gestión habilitada a la vez, garantizada por la base, absorbida automáticamente por todos los módulos de SIS-POA. Ejecuta la decisión ya aceptada en `docs/refactor-pip/ADR/ADR-007-multiyear-model.md` (2026-08-15), que prohíbe hardcodear gestiones y exige que la gestión activa se propague por contexto.

## CONTEXT

`GestionFiscal` (`backend/apps/gestion/models.py`) ya era la entidad canónica y la base ya declaraba la gestión de trabajo (2026 CERRADA/inactiva, 2027 HABILITADA/activa). Ese dato no lo leía nadie:

- El gate (`gestion_habilitada`, `validar_gestion_para_techo`) vivía en `apps/budget/services.py` y solo protegía `apps.budget`.
- Los viewsets de SIS-POA usaban el patrón `if gestion: qs.filter(...)`: sin `?gestion=` devolvían **todas** las gestiones mezcladas.
- ~20 componentes del frontend clavaban el año a mano, unos en 2027 y otros en **2026, una gestión cerrada** (`poa-wizard`, `poa-matriz-viewer`, `poau-matriz-viewer`).
- El sidebar y el header mostraban `Gestión 2027 / Formulación activa` como texto fijo.
- `PATCH /api/v1/gestiones/{id}` permitía mover `estado` sin permiso, sin auditoría y sin validar la transición.

## CURRENT BEHAVIOR

- `activa` era `default=True` sin restricción: toda gestión nacía activa y podía haber N activas.
- `obtener_gestion_actual()` (`apps/gestion/services.py`) era código muerto.
- Siete pantallas de budget repetían el mismo desplegable de gestión y autoseleccionaban `results[0]`.
- `programmatic-categories` hacía `Number(g.id)` sobre un UUID y mandaba `NaN`.

## EXPECTED BEHAVIOR

- A lo sumo una `GestionFiscal` con `activa=True`, garantizado por índice único parcial.
- `habilitar_gestion` toma el candado y rechaza si otra gestión lo tiene, nombrándola; `cerrar_gestion` lo suelta.
- `GET /api/v2/sis-poa/budget/fiscal-years/activa/` publica la gestión habilitada.
- Los módulos de SIS-POA resuelven la gestión desde el candado; `?gestion=` distinto → 409.
- El frontend carga el candado al arranque, un guard bloquea SIS-POA sin gestión habilitada y el shell muestra el estado real.

## IN SCOPE

- [x] `UniqueConstraint` parcial + `activa` con `default=False` + migración de normalización.
- [x] `apps/gestion/candado.py` (autoridad única) y `apps/gestion/mixins.py` (filtro de lectura y gate de escritura 409).
- [x] Cierre de la puerta trasera V1 (`estado`/`activa` read-only, escritura por capacidad).
- [x] Endpoint `fiscal-years/activa/`.
- [x] Aplicación opt-in a los viewsets SIS-POA (priorización, POA/POAU, budget, poau, presupuesto, techos, recursos, seguimiento, modificaciones, dashboards de core).
- [x] `GestionHabilitadaService`, `GestionHabilitadaGuard`, indicadores de shell.
- [x] Retiro de los desplegables de gestión y de los años literales en SIS-POA.
- [x] Preservación del `code` de error en `ErrorInterceptor`.

## OUT OF SCOPE

- SIS-PE (PAD, PEI, `matrices-pad`, `planificacion`): la planificación es quinquenal 2026-2030 y sus años son horizontes de plan, no gestiones fiscales operativas (excepción plurianual, `GESTION_FISCAL_AUDIT.md` §6).
- SIS-PRO.
- La campaña FK `PIP-DB-005/006/007`: el candado opera sobre el año, funcione o no la FK.
- El filtro de gestión de la **auditoría**: la bitácora es el registro histórico y tiene que poder leer gestiones cerradas.
- Unificar los dos vocabularios de `GestionFiscal.Estado` y los dos `cerrar_gestion` divergentes (deuda registrada aparte).

## INVARIANTS

- `GestionFiscal` sigue siendo la canónica; no se crea entidad nueva.
- Las firmas `gestion_habilitada(g)` y `validar_gestion_para_techo(g)` de `apps.budget.services` se conservan (191 tests dependen de ellas); delegan en `apps.gestion.candado`.
- El contrato V2 `/api/v2/sis-poa/budget/fiscal-years/` no cambia; solo se le suma la action `activa`.
- Sembrar una gestión (importadores, migraciones) NO le da el candado.

## DATABASE IMPACT

`apps/gestion/migrations/0005_candado_gestion_habilitada.py`: `AlterField` de `activa` (`default=False`), `RunPython` de normalización y `AddConstraint` del índice único parcial `unica_gestion_habilitada`. En la base de desarrollo no cambia ninguna fila (2027 ya era la única activa).

## API IMPACT

- Nueva: `GET /api/v2/sis-poa/budget/fiscal-years/activa/` → `{habilitada, gestion}`.
- `POST .../{id}/enable/` rechaza con 400 si otra gestión tiene el candado.
- Los endpoints SIS-POA responden 409 `{error: {detail, code}}` ante `?gestion=` distinto de la habilitada, o cuando no hay ninguna.
- `/api/v1/gestiones/`: `estado`, `activa`, `fecha_apertura` y `fecha_cierre` pasan a read-only; escribir exige `sis_poa.budget.manage`.
- Endpoints que exigían `?gestion=` (presupuesto-gastos, saldos, semáforo, dashboard de seguimiento) ya no lo piden.

## FRONTEND IMPACT

`GestionHabilitadaService` y `GestionHabilitadaGuard` nuevos en `core/`; carga al arranque en `AppComponent`; header y sidebar leen el candado; se retiran siete desplegables de gestión y los años literales de SIS-POA; `ErrorInterceptor` preserva `code`.

## DEPENDENCIES

`ADR-007` (aceptado), `GESTION_FISCAL_AUDIT.md`, endpoint V2 de gestión fiscal existente.

## ACCEPTANCE CRITERIA

- [x] No se pueden tener dos gestiones habilitadas ni por API ni por ORM.
- [x] Habilitar con otra gestión en curso falla nombrando la gestión en curso.
- [x] Todas las pantallas de SIS-POA muestran el mismo año, y es el habilitado.
- [x] Cambiar de gestión habilitada cambia toda la plataforma sin tocar código.
- [x] Sin gestión habilitada, SIS-POA redirige a la pantalla de habilitación.
- [x] `PATCH /api/v1/gestiones/{id}` con `estado` no mueve el estado.
- [x] SIS-PE sigue operando sobre el quinquenio 2026-2030.

## TESTS

```bash
cd backend && python -m pytest apps/gestion apps/budget apps/priorizacion -o addopts="" -q
cd frontend/sispoa && TMPDIR="$HOME/karma-tmp" CHROME_BIN=/snap/bin/chromium npx ng test --watch=false --browsers=ChromeHeadlessNoSandbox
cd frontend/sispoa && npm run build
```

## RISKS

Toca los viewsets de nueve apps. Riesgo principal: aplicar el candado a un módulo plurianual (PAD/PEI) y romper el quinquenio; mitigado aplicándolo opt-in viewset por viewset y dejando `views_matrices.py` intacto. Segundo riesgo: colisión con el worktree hermano `fiscal-year-gestiones-2027-2028`, que tiene cambios sin commitear sobre `apps/budget/{services,views,serializers,tests}.py` y `fiscal-year.component.*`.

## ROLLBACK

Migración inversa `0005` (suelta la constraint y devuelve `activa=True`) y revertir los archivos de la tarea.

## FINAL REPORT

Implementado. 78 archivos, +975 −422.

**El candado.** `GestionFiscal.activa` con índice único parcial
(`unica_gestion_habilitada`, migración `gestion.0005`) y `default=False`.
`apps/gestion/candado.py` es la autoridad única; `apps/gestion/mixins.py` la
aplica opt-in viewset por viewset. `apps.budget.services.gestion_habilitada`
delega, así que las 191 pruebas de budget no cambiaron de firma.

**Verificado en el navegador** contra la base de desarrollo (migración
`gestion.0005` aplicada):

- Sidebar y encabezado muestran `Gestión 2027 · Habilitada`, leída del backend.
- Asistente POA: el campo de gestión pasó de `2026` (una gestión **cerrada**) a
  `2027`, solo lectura.
- `GET /matriz-poau/` sin parámetro devuelve 5.287 filas de 2027;
  `?gestion=2026` responde 409 `fuera_de_gestion_habilitada`.
- `GET /matriz-poau/<accion 2026>/` responde 404; la de 2027, 200.
- Soltando el candado, `/sis-poa/poaus` redirige a la habilitación y ambos
  indicadores del shell pasan a aviso.

**Pruebas.**

- Frontend: **352/352** (`ng test`).
- Backend, sobre `apps/{budget,priorizacion,articulacion,seguimiento,poau,gestion,core}`:
  **53 failed, 780 passed, 10 errors**, contra una línea base medida en un
  worktree limpio de `a847579` de **59 failed, 756 passed, 10 errors**. Ningún
  fallo nuevo; los 53 restantes son los pre-existentes por colisión con datos
  sembrados en migraciones (`poau` 41, `limpieza_datos_simulados` 8,
  `categoria_catalogo` 3, `migration_0006` 1) más los 10 errores de
  `demo_articuladores`, todos reproducidos idénticos en la base.
- Aplicar el candado tumbó ~290 tests que asumían `?gestion=` libre. Se
  adaptaron con `apps/gestion/testing.habilitar_gestion_para_tests` en el
  `setUp` de priorización, seguimiento y articulación; los que cruzaban
  gestiones a propósito ahora fijan el rechazo 409 en vez de borrarse.

**Deuda registrada, fuera de alcance:** los dos vocabularios de
`GestionFiscal.Estado` y los dos `cerrar_gestion` divergentes
(`apps/gestion/services.py:32` sin auditoría vs `apps/budget/services.py`);
`obtener_gestion_actual()` quedó como código muerto, lo reemplaza
`candado.gestion_habilitada()`.

**Colisión pendiente:** el worktree `fiscal-year-gestiones-2027-2028` tiene
cambios sin commitear sobre `apps/budget/{services,views,serializers,tests}.py`
y `fiscal-year.component.*` (agrega `reabrir_gestion` y `eliminar`). Hay que
integrarlos antes de mezclar — y `reabrir_gestion` resuelve un callejón real:
una gestión cerrada por error hoy no se puede volver a habilitar.

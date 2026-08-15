# SIS-POA — Referencia de la API V2 (`/api/v2/sis-poa/budget/`)

Namespace montado en `config/urls_v2.py` → `apps.budget.urls`. Swagger vía
drf-spectacular. Montos serializados como string (convención
`COERCE_DECIMAL_TO_STRING`); errores de dominio `400 {error: {detail}}` y
`BUDGET_EXCEEDED` con `code` + `details` (400 por fuente, 409 por apertura).

## 1. Router `fiscal-years` (`FiscalYearViewSet`)

| Método | Ruta | Propósito | Permiso |
|---|---|---|---|
| GET | `/fiscal-years/` | listar (filtros `anio/estado/activa`, búsqueda `anio/descripcion`) | autenticado |
| POST | `/fiscal-years/` | crear (`heredar_de` = año de la gestión origen) | autenticado |
| GET/PATCH | `/fiscal-years/{id}/` | detalle/edición | autenticado |
| POST | `/fiscal-years/{id}/enable/` | → HABILITADA | `budget.manage` |
| POST | `/fiscal-years/{id}/close/` | → CERRADA | `budget.manage` |

## 2. Router `directive-ceilings` (`DirectiveCeilingViewSet`)

| Método | Ruta | Propósito | Permiso |
|---|---|---|---|
| GET/POST | `/directive-ceilings/` | listar (filtros `gestion/estado`) / crear (techo + v1 BORRADOR) | manage (POST) |
| GET/PATCH/DELETE | `/directive-ceilings/{id}/` | detalle / edición | manage |
| POST | `/directive-ceilings/{id}/submit/` | → EN_REVISION | `budget.approve` |
| POST | `/directive-ceilings/{id}/observe/` | → OBSERVADO (body `observaciones`) | `budget.approve` |
| POST | `/directive-ceilings/{id}/approve/` | → APROBADO | `budget.approve` |
| POST | `/directive-ceilings/{id}/freeze/` | → FIJADO (valida §24, checksum) | `budget.approve` |
| GET | `/directive-ceilings/{id}/composition/` | composición (§22) | autenticado |

## 3. Routers `resources`, `mandatory-expenses`, `documents`

| Método | Ruta | Propósito | Permiso |
|---|---|---|---|
| CRUD | `/resources/?version=` | recursos del techo (409 en versión fijada) | manage (escritura) |
| CRUD | `/mandatory-expenses/?version=` | gastos obligatorios (409 en versión fijada) | manage (escritura) |
| GET/POST/DELETE | `/documents/` (`?gestion=`, `?tipo=`) | documentos de respaldo; POST multipart (máx. 20 MB) | manage (create/destroy) |

## 4. Router `programmatic-categories`

| Método | Ruta | Propósito | Permiso |
|---|---|---|---|
| GET/POST | `/programmatic-categories/?gestion=&nivel=` | listar/crear (solo gestión habilitada) | autenticado / default |
| PATCH/DELETE | `/programmatic-categories/{id}/` | editar/eliminar | autenticado |
| GET | `/programmatic-categories/tree/?gestion=` | árbol jerárquico (parámetro obligatorio) | autenticado |
| POST | `/programmatic-categories/{id}/duplicar_a_gestion/` | copiar categoría + subárbol (body `gestion_destino`) | autenticado |

`GET /catalogs/` (CatalogOptionsView): fuentes, organismos, rubros,
objetos_gasto, entidades_transferencia, distritos, direcciones,
unidades_ejecutoras, unidades_organizacionales (≤ 500 c/u).

## 5. Router `distributions` (`DistributionVersionViewSet`)

| Método | Ruta | Propósito | Permiso |
|---|---|---|---|
| GET/POST | `/distributions/` · `GET/PATCH/DELETE /{id}/` | versiones | manage (escritura) |
| GET | `/distributions/{id}/versions/?gestion=` | versiones por gestión | autenticado |
| POST | `/distributions/{id}/submit|observe|approve|freeze/` | ciclo de estados | `budget.approve` |
| GET | `/distributions/{id}/validate/` | diferencias por fuente | autenticado |
| POST | `/distributions/{id}/ajuste/` | versión siguiente (BORRADOR) | manage |
| GET | `/distributions/dashboard/?gestion=` | dashboard §48 | autenticado |

## 6. Router `allocations`

| Método | Ruta | Propósito | Permiso |
|---|---|---|---|
| GET/POST | `/allocations/` | listar (filtros `gestion/version/distrito/categoria/estado`, búsqueda denominación/SISIN) / crear con `fuentes: [{fuente, organismo, monto}]` | manage |
| PATCH/DELETE | `/allocations/{id}/` | editar (reemplaza fuentes) / eliminar | manage |
| POST | `/allocations/{id}/cerrar/` | cerrar (revalida disponible) | manage |

`BUDGET_EXCEEDED` → `400 {code, details: {fuente, requested, available, difference}}`.

## 7. Router `expense-objects`

| Método | Ruta | Propósito | Permiso |
|---|---|---|---|
| GET | `/expense-objects/?allocation=` | programación por apertura | autenticado |
| POST | `/expense-objects/` | upsert `{allocation, objeto_gasto, monto}` (requiere distribución FIJADA) | manage |
| PATCH/DELETE | `/expense-objects/{id}/` | actualizar/eliminar | manage |

Exceso → **409** `{code: 'BUDGET_EXCEEDED', details: {requested, available, difference}}`.

## 8. Router `reserves`

| Método | Ruta | Propósito | Permiso |
|---|---|---|---|
| GET/POST | `/reserves/` | listar (filtros `gestion/version/estado/tipo/fuente`) / crear | manage |
| PATCH/DELETE | `/reserves/{id}/` | editar/eliminar (409 en versión fijada) | manage |
| POST | `/reserves/{id}/liberar/` | liberar (devuelve disponible) | manage |

## 9. Router `imports` (`BudgetImportViewSet`)

| Método | Ruta | Propósito | Permiso |
|---|---|---|---|
| GET/POST | `/imports/` | listar (filtros `gestion/estado/perfil`) / upload + parseo | `budget.import` (POST) |
| GET | `/imports/{id}/hojas/` | hojas del libro | autenticado |
| POST | `/imports/{id}/map/` | hoja + mapeo y re-parseo | `budget.import` |
| POST | `/imports/{id}/validate/` | validación por severidad | `budget.import` |
| GET | `/imports/{id}/errors/?severidad=` | hallazgos | autenticado |
| POST | `/imports/{id}/apply/` | aplicar → aperturas BORRADOR | `budget.import` |

## 10. Router `territorial-distributions`

| Método | Ruta | Propósito | Permiso |
|---|---|---|---|
| GET/POST | `/territorial-distributions/` | listar (filtros `gestion/estado/metodo/fuente`) / crear con `distritos: [{distrito, poblacion?, porcentaje?, monto?}]` | manage |
| PATCH/DELETE | `/territorial-distributions/{id}/` | editar/eliminar (no APLICADA) | manage |
| POST | `/{id}/calcular/` | calcular reparto (body opcional `distritos`) | manage |
| POST | `/{id}/aplicar/` | materializar reservas DISTRITALES | manage |
| POST | `/{id}/liberar/` | liberar reservas → CALCULADA | manage |

## 11. Router `reforms`

| Método | Ruta | Propósito | Permiso |
|---|---|---|---|
| GET/POST | `/reforms/` | listar (filtros `gestion/estado/tipo`) / crear con `movimientos: [...]` | `budget.reform` |
| PATCH/DELETE | `/reforms/{id}/` | editar/eliminar (solo BORRADOR) | `budget.reform` |
| POST | `/reforms/{id}/submit/` | → EN_REVISION | `budget.reform` |
| POST | `/reforms/{id}/observe/` · `approve/` · `reject/` | observación (motivo) / aprobación / rechazo (motivo) | `budget.approve` |
| POST | `/reforms/{id}/apply/` | APLICADA (movimientos atómicos) | `budget.approve` |

## 12. Control y auditoría (APIView)

| Método | Ruta | Propósito | Permiso |
|---|---|---|---|
| GET | `/control/summary/?gestion=` | resumen consolidado por fuente | autenticado |
| POST | `/control/validate/` | `{tipo: distribution\|expense-object\|allocation}` → `{valido, errores}` (+ `techo/programado/disponible` en allocation) | autenticado |
| GET | `/audit/?gestion=&entidad=&registro_id=&usuario=&accion=&desde=&hasta=` | `EventoAuditoria` del ciclo, paginado | `budget.audit_read` |

`entidad` acepta slugs (`allocation`, `reserve`, `directive-ceiling`,
`distribution`, `expense-object`, `reform`, `import`, `territorial`,
`fiscal-year`) o nombre de modelo; `accion` acepta códigos del catálogo o
semánticos (`CREATE`/`UPDATE`/`FREEZE`/…).

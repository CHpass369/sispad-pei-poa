# SIS-POA — Gestión Fiscal (`services.py`, `fiscal-year`)

## 1. Entidad

La gestión fiscal del ciclo es `apps.gestion.GestionFiscal` (única por `anio`),
**no** se creó una entidad duplicada. La Fase 1 extendió sus estados con los
códigos del ciclo (migración) y los bloqueos por estado se implementan en
`services.py` de `budget`.

## 1.1 El candado de SIS-POA (ADR-007)

`GestionFiscal.activa` es **el candado**: marca la única gestión sobre la que
se planifica y programa en SIS-POA. Lo garantiza la base con un índice único
parcial (`unica_gestion_habilitada`, migración `gestion.0005`), no la buena
voluntad del código: **a lo sumo una fila con `activa=True`**.

`activa` nace en `False`. Sembrar una gestión —importadores, migraciones,
`POST /fiscal-years/`— **no** le da el candado; lo toma `habilitar_gestion` y
lo suelta `cerrar_gestion`. Habilitar con otra gestión en curso se rechaza
nombrando la gestión en curso: cerrar antes de abrir es el circuito.

Es ortogonal a `estado`: `estado` es la fase del ciclo presupuestario,
`activa` es el candado de la plataforma.

**No aplica fuera de SIS-POA.** El SIS-PE (PAD, PEI) es quinquenal 2026-2030 y
sus años son horizontes de plan, no gestiones fiscales operativas (excepción
plurianual, `docs/architecture/GESTION_FISCAL_AUDIT.md` §6). Por eso el candado
se aplica **viewset por viewset** y nunca de forma global.

### Autoridad y consumo

| Pieza | Rol |
|---|---|
| `apps/gestion/candado.py` | Autoridad única: `gestion_habilitada()`, `resolver_gestion(request)`, `validar_gestion()` |
| `apps/gestion/mixins.py` | `GestionHabilitadaFilterMixin` (lectura), `CandadoGestionMixin` (escritura, 409), `CandadoSisPoaMixin` (ambos) |
| `GET /fiscal-years/activa/` | Lo que el frontend absorbe al arrancar: `{habilitada, gestion}` |
| `GestionHabilitadaService` (Angular) | Publica la gestión a todos los módulos; se carga en `AppComponent` |
| `GestionHabilitadaGuard` (Angular) | Sin gestión habilitada, `/sis-poa/*` y `/priorizacion/*` redirigen a la habilitación |

Los endpoints de SIS-POA ya **no** aceptan `?gestion=` de otra gestión:
responden `409 {error: {detail, code}}` con `code` `fuera_de_gestion_habilitada`
o `gestion_no_habilitada`. Cuando el parámetro falta, se absorbe la habilitada;
antes ese hueco devolvía **todas las gestiones mezcladas**.

`/api/v1/gestiones/` dejó de ser puerta trasera: `estado`, `activa`,
`fecha_apertura` y `fecha_cierre` son de solo lectura y escribir exige
`sis_poa.budget.manage`.

**Excepción deliberada**: `POST /programmatic-categories/{id}/duplicar_a_gestion/`
cruza gestiones a propósito — es como se siembra el catálogo de la gestión
siguiente antes de habilitarla. La auditoría tampoco se acota: la bitácora
tiene que poder leer gestiones cerradas.

## 2. Estados del ciclo

```
CONFIGURACION → HABILITADA → EN_FORMULACION → VIGENTE → CERRADA
```

Definidos como constantes en `services.py`:

- `ESTADO_CONFIGURACION = 'CONFIGURACION'`
- `ESTADO_HABILITADA = 'HABILITADA'`
- `ESTADO_EN_FORMULACION = 'EN_FORMULACION'`
- `ESTADO_VIGENTE = 'VIGENTE'`
- `ESTADO_CERRADA = 'CERRADA'`

Los estados legacy de `GestionFiscal.Estado` se conservan intactos (semántica
V1 intacta). Los helpers reconocen ambos para no romper la UI legacy:
`preparacion≈CONFIGURACION`, `abierta≈HABILITADA`, `formulacion≈EN_FORMULACION`,
`cerrada≈CERRADA`.

## 3. Helpers de estado y bloqueos

| Función | Semántica |
|---|---|
| `gestion_habilitada(g)` | `estado ∈ {HABILITADA, abierta}` — puerta de todo el ciclo |
| `gestion_en_formulacion(g)` | `estado ∈ {EN_FORMULACION, formulacion}` |
| `validar_gestion_para_techo(g)` | lanza `ValidationError` si no habilitada (Fase 2) |
| `validar_gestion_para_distribucion(g)` | idem para distribución/reformas (Fases 4-10) |

Todas las escrituras del ciclo (techo, distribución, fijación, reservas,
reformulaciones, territorial) validan la gestión habilitada **antes** de
operar; sin gestión habilitada el error es `400` con el estado actual.

## 4. `habilitar_gestion` (POST `/fiscal-years/{id}/enable/`)

`@transaction.atomic`. Validaciones:

1. Si ya está habilitada (`gestion_habilitada`) → error.
2. Si el estado está en `ESTADOS_NO_HABILITABLES` (`VIGENTE`, `CERRADA`,
   `cerrada`, `archivada`) → no se puede habilitar.

3. Si **otra** gestión tiene el candado (`activa=True`) → se rechaza
   nombrándola: SIS-POA opera sobre una sola gestión (§1.1).

Toma `select_for_update` sobre todas las gestiones antes de decidir: sin eso
`activa` sería un check-then-act y dos habilitaciones simultáneas chocarían
contra el índice único con un `IntegrityError` en vez de un error de dominio.

Efectos: `estado = HABILITADA`, `activa = True`, `fecha_apertura = now()` y
`EventoAuditoria` (`accion=modificar`; el catálogo no tiene acción
"habilitar" — se distingue por el resumen) con `datos_previos/posteriores`.

## 5. `cerrar_gestion` (POST `/fiscal-years/{id}/close/`)

`@transaction.atomic`. Validaciones:

1. Ya cerrada (`CERRADA`/`cerrada`) → error.
2. Archivada (`archivada`) → no se puede cerrar.

Efectos: `estado = CERRADA`, `activa = False` (suelta el candado) y
`fecha_cierre = now()`, con auditoría `accion=cerrar`. Al cerrar, SIS-POA queda
sin gestión habilitada hasta que se habilite la siguiente.

## 5.1 `reabrir_gestion` (POST `/fiscal-years/{id}/reopen/`)

`CERRADA → HABILITADA`. Es la flecha que faltaba: hasta acá el cierre era de
ida. `habilitar_gestion` rechaza las cerradas, así que un cierre por error
dejaba congelados el techo directivo, la distribución y el POA de esa gestión
—y desde que existe el candado, dejaba además a SIS-POA entero sin gestión
sobre la que operar—. La única salida era entrar a la base por consola, donde
no queda rastro de nada.

Validaciones:

1. La gestión tiene que estar cerrada (`ESTADOS_REABRIBLES`).
2. **El motivo es obligatorio.** Reabrir revierte un acto formal: la
   diferencia entre «no se puede» y «se puede, pero dejás tu nombre y el
   porqué».
3. Si **otra** gestión tiene el candado se rechaza nombrándola: reabrir no
   puede robárselo a la que está en curso.

Efectos: `estado = HABILITADA`, `activa = True` (retoma el candado),
`fecha_cierre = None` y `EventoAuditoria` con `accion=reabrir`, donde el
resumen incluye el motivo.

## 5.2 `eliminar_gestion` (DELETE `/fiscal-years/{id}/`)

Solo cubre el caso real: la gestión abierta por error. Se rechaza si

- tiene el candado (apagar SIS-POA no puede ser el efecto lateral de un
  DELETE: hay que cerrarla primero), o
- tiene **cualquier** registro dependiente.

El conteo de dependencias usa `get_fields(include_hidden=True)`, y eso no es
un detalle: casi todas las FK hacia `GestionFiscal` usan `related_name='+'`
—catálogos, organización, workflow— y quedan fuera de `_meta.related_objects`.
Sin las ocultas, una gestión con catálogos y unidades cargados parecería
vacía, y las FK de budget son CASCADE: el borrado se llevaría por delante
techos, distribuciones y reformas en silencio.

La auditoría es la única excepción: sus eventos se desvinculan
(`gestion = NULL`) en vez de bloquear, y conservan el rastro por
`entidad`/`entidad_id`, que son texto.

## 5.3 Quién puede reabrir y eliminar

Estas dos no van con `sis_poa.budget.manage`: esa capacidad la tiene
cualquiera que administre el presupuesto. Reabrir y eliminar revierten o
borran un acto formal del ciclo, así que exigen **`sis_poa.budget.reopen`**
(migración `accounts.0008`), sembrada en `jefe_poa`, `admin_poa` y
`superadmin`. La jefatura de POA y administración, y nadie más.

## 6. `heredar_configuracion(gestion_nueva, gestion_origen)`

Copia **solo configuración** (sin datos de formulación) de la gestión origen a
la nueva, dentro de la transacción de creación:

- `CicloFormulacion` → copia nombre, descripción, fechas, `activo`, `orden`.
- `EtapaFormulacion` por ciclo → copia código, nombre, descripción, fechas,
  `orden`; **siempre `completada=False`**.

Se dispara al crear una gestión vía API con el campo write-only `heredar_de`
(año de la gestión origen). Es el mecanismo de preparación de una nueva
gestión para el ciclo.

## 7. API (`FiscalYearViewSet`)

| Método/Ruta | Propósito | Permiso |
|---|---|---|
| `GET /fiscal-years/activa/` | la gestión con el candado: `{habilitada, gestion}` | autenticado |
| `GET/POST /fiscal-years/` | listar/crear (filtros `anio/estado/activa`, búsqueda `anio/descripcion`; `heredar_de` al crear) | autenticado (default global) |
| `GET/PATCH /fiscal-years/{id}/` | detalle/edición | autenticado |
| `POST /fiscal-years/{id}/enable/` | → `HABILITADA` | `sis_poa.budget.manage` |
| `POST /fiscal-years/{id}/close/` | → `CERRADA` | `sis_poa.budget.manage` |
| `POST /fiscal-years/{id}/reopen/` | → `HABILITADA` (cuerpo: `motivo`) | `sis_poa.budget.reopen` |
| `DELETE /fiscal-years/{id}/` | elimina la gestión vacía y sin candado | `sis_poa.budget.reopen` |

`estado`, `fecha_apertura`, `fecha_cierre` y `gestion_anterior` son
read-only (los gestionan los servicios). El serializer publica además
`puede_habilitar`, `puede_reabrir`, `puede_cerrar` y `puede_eliminar`: las
transiciones válidas se calculan en el backend porque la pantalla duplicaba
las listas de estados y se desincronizaba con los servicios. Los errores de dominio se
mapean a `400 {error: {detail}}`.

## 8. Bloqueos del ciclo (resumen)

| Operación | Bloqueo |
|---|---|
| Techo directivo (crear/editar/fijar) | gestión habilitada |
| Distribución (aperturas, reservas, territorial) | gestión habilitada + techo FIJADO |
| Fijación de distribución | gestión habilitada + Σfuente = techo − reservas |
| Objetos del gasto | apertura ACTIVA + versión de distribución FIJADA |
| Reformulaciones (crear/aplicar) | gestión habilitada + distribución FIJADA |
| Ajustes (techo/distribución) | versión previa FIJADA (inmutable) |

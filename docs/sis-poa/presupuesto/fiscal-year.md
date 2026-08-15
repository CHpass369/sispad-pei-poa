# SIS-POA — Gestión Fiscal (`services.py`, `fiscal-year`)

## 1. Entidad

La gestión fiscal del ciclo es `apps.gestion.GestionFiscal` (única por `anio`),
**no** se creó una entidad duplicada. La Fase 1 extendió sus estados con los
códigos del ciclo (migración) y los bloqueos por estado se implementan en
`services.py` de `budget`.

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

Efectos: `estado = HABILITADA`, `fecha_apertura = now()` y
`EventoAuditoria` (`accion=modificar`; el catálogo no tiene acción
"habilitar" — se distingue por el resumen) con `datos_previos/posteriores`.

## 5. `cerrar_gestion` (POST `/fiscal-years/{id}/close/`)

`@transaction.atomic`. Validaciones:

1. Ya cerrada (`CERRADA`/`cerrada`) → error.
2. Archivada (`archivada`) → no se puede cerrar.

Efectos: `estado = CERRADA`, `fecha_cierre = now()` y auditoría con
`accion=cerrar`.

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
| `GET/POST /fiscal-years/` | listar/crear (filtros `anio/estado/activa`, búsqueda `anio/descripcion`; `heredar_de` al crear) | autenticado (default global) |
| `GET/PATCH /fiscal-years/{id}/` | detalle/edición | autenticado |
| `POST /fiscal-years/{id}/enable/` | → `HABILITADA` | `sis_poa.budget.manage` |
| `POST /fiscal-years/{id}/close/` | → `CERRADA` | `sis_poa.budget.manage` |

`estado`, `fecha_apertura`, `fecha_cierre` y `gestion_anterior` son
read-only (los gestionan los servicios). Los errores de dominio se
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

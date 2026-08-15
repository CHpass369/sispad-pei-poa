# SIS-POA — Distribución Presupuestaria (`budget-distribution`)

## 1. Concepto

La distribución reparte el techo distribuible de la gestión entre **aperturas
programáticas** (`Allocation`) con montos **normalizados por FF/OF**
(`AllocationSource` — nunca columnas `monto_ct/monto_re/...`), más **reservas**
(`Reserve`) que decrecen el disponible. Vive en versiones
(`DistributionVersion`) con el mismo patrón inmutable del techo.

## 2. Versiones de distribución

- `UNIQUE (gestion, numero)`; estados reutilizan `EstadosTecho`
  (BORRADOR → EN_REVISION → APROBADO → FIJADO, con OBSERVADO).
- **Versión activa** (`version_distribucion_activa`): la no fijada de mayor
  número. Si no existe (primer uso) se **crea la v1** en BORRADOR; si la
  última está FIJADA **no auto-crea**: exige `ajuste_distribucion` explícito
  (error si se intenta operar).
- **Fijación** (§49-52): valida Σfuente = techo − reservas por cada fuente
  del techo fijado, calcula el checksum y congela (inmutable).

## 3. Aperturas (`Allocation`)

| Aspecto | Detalle |
|---|---|
| Dimensiones | `categoria` (programática), `da`, `ue`, `unidad_organizacional`, `distrito` (opcionales) |
| Códigos | `codigo_sisin`, `proyecto_codigo`, `actividad_codigo` VARCHAR (ceros iniciales preservados) |
| Estado | `BORRADOR` / `ACTIVA` / `CERRADA` |
| Montos | SOLO en `AllocationSource` (fuente, organismo, monto); `total` = `SUM(fuentes.monto)` (agregación) |
| Cierre | `cerrar_allocation`: revalida cada fuente contra el disponible (excluyendo la propia apertura); una CERRADA no se edita ni elimina |

## 4. Asignaciones normalizadas (`AllocationSource`)

- Una fila por llave `(allocation, fuente, organismo)` — `UNIQUE` con
  `nulls_distinct=False` (aun con fuente/organismo NULL).
- `CheckConstraint monto >= 0`.
- **Llave presupuestaria** del ciclo: `(fuente, organismo)`; todos los
  saldos (techo, distribuido, reservado, disponible) se agregan por fuente.

## 5. Reservas (`Reserve`)

- Tipos: `DISTRITAL` (reparto territorial, Fase 6), `DISTRIBUCION` (global),
  `OTRA`. Estados: `ACTIVA` / `LIBERADA`.
- Las ACTIVAS restan del disponible por fuente; liberarlas lo devuelve.
- No pueden crearse/liberarse sobre una versión de distribución fijada
  (inmutable → 409).

## 6. Saldos por fuente (agregados, nunca filas)

```
techo[f]      = Σ recursos[f] − Σ obligatorios[f]  (versión FIJADA del techo)
distribuido[f]= Σ AllocationSource[f]              (aperturas no CERRADAS)
reservado[f]  = Σ Reserve ACTIVAS[f]
disponible[f] = techo[f] − distribuido[f] − reservado[f]
```

Implementaciones: `techo_distribuible_por_fuente`, `distribuido_por_fuente`,
`reservado_por_fuente`, `disponible_por_fuente` (services) / métodos
`get_*` del `BudgetControlService` (control.py).

## 7. Control Σdistribuido+reservado ≤ techo

`crear_allocation`/`actualizar_allocation`/`crear_reserva`/`cerrar_allocation`
validan contra el disponible por fuente **dentro de la transacción**, con
lock de las filas del techo fijado (`_bloquear_fuentes` → `select_for_update`).
Si `monto > disponible` → `ErrorDisponibilidad` (`code='BUDGET_EXCEEDED'`,
`details={fuente, requested, available, difference}`) → **HTTP 400** en la
API. `actualizar_allocation` excluye los montos actuales de la propia
apertura (permite subas/rebajas).

## 8. Fijación (§49-52) — `fijar_distribucion(version, usuario)`

1. Versión debe estar `APROBADO` y no inmutable; gestión habilitada.
2. `validar_distribucion_completa(gestion)`: para **cada fuente del techo
   fijado**, `diferencia = techo − (distribuido + reservado)`; `|d| ≤ 0.01`
   se tolera como 0 (redondeo a 2 decimales, `UMBRAL_DIFERENCIA`).
3. Si no valida → `ValidationError` listando diferencias por fuente.
4. `version.fijar()`: estado FIJADO, `inmutable=True`, checksum SHA-256
   (`services.checksum_distribucion`: asignaciones de aperturas ACTIVAS +
   reservas de la versión, ordenadas por contenido — **única**
   implementación, el modelo delega), fecha y autor; auditoría.

**Inmutabilidad**: `DistributionVersion.save()` rechaza modificaciones;
escrituras de aperturas/reservas/versiones fijadas → 409; el checksum
`verificar_hash()` permite auditar integridad.

## 9. Ajuste de distribución (§51) — `ajuste_distribucion(version)`

Solo sobre versión FIJADA: crea `numero + 1` en BORRADOR **sin copiar
montos** (contenedor vacío; los cambios los define la reformulación, Fase 10).

## 10. Dashboard (§48) — `resumen_distribucion(gestion)`

Cards + tabla por fuente: `techo_distribuible`, `distribuido`, `reservado`,
`disponible`, `porcentaje` (float 0-100), `aperturas_count` (no CERRADAS) y
`por_fuente[]`. Invariante exacta: `techo = distribuido + reservado +
disponible`. Expuesto en `GET /distributions/dashboard/?gestion=`.

## 11. API (resumen)

| Ruta | Propósito |
|---|---|
| `GET/POST /distributions/` · `GET/PATCH/DELETE /{id}/` | versiones (escritura → manage) |
| `GET /distributions/{id}/versions/?gestion=` | lista versiones por gestión |
| `POST /distributions/{id}/submit|observe|approve|freeze/` | ciclo de estados (→ approve) |
| `GET /distributions/{id}/validate/` | diferencias por fuente |
| `POST /distributions/{id}/ajuste/` | versión siguiente (→ manage) |
| `GET/POST /allocations/` · `PATCH/DELETE /{id}/` · `POST /{id}/cerrar/` | aperturas (`fuentes` anidado `[{fuente, organismo, monto}]`; BUDGET_EXCEEDED → 400) |
| `GET/POST /reserves/` · `POST /{id}/liberar/` | reservas |
| `GET /distributions/dashboard/?gestion=` | dashboard (§48) |

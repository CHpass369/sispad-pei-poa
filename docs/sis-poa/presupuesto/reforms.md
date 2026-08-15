# SIS-POA — Reformulaciones Presupuestarias (`reforms`)

## 1. Concepto

La reformulación modifica **cómo se distribuye** el presupuesto de una
gestión ya fijada (saldos entre aperturas/fuentes). El ajuste de techo
(modifica recursos) es otra operación (Fase 2, `ajuste_de_techo`); la
reformulación opera sobre la **distribución fijada**.

## 2. Tipos (`TipoReform` — cabecera)

`TRASPASO` (entre aperturas), `INCREMENTO`, `DISMINUCION`,
`NUEVA_APERTURA`, `CIERRE_APERTURA`, `CAMBIO_FUENTE`,
`AJUSTE_DISTRIBUCION`.

Los tipos de cabecera `NUEVA_APERTURA`/`CIERRE_APERTURA`/
`AJUSTE_DISTRIBUCION` en esta fase se componen con movimientos de los tipos
operativos; su ciclo de vida completo (crear/cerrar aperturas) queda para
fases posteriores.

## 3. Tipos de movimiento (`TipoMovimientoReform` — líneas)

`TRASPASO`, `INCREMENTO`, `DISMINUCION`, `CAMBIO_FUENTE`.

| Tipo | Reglas de estructura |
|---|---|
| `TRASPASO` | requiere `apertura_origen` **y** `apertura_destino` |
| `INCREMENTO` | requiere destino, **sin** origen |
| `DISMINUCION` | requiere origen, **sin** destino |
| `CAMBIO_FUENTE` | opera sobre la MISMA apertura (`apertura_destino` omitido o igual a origen) |

Todos llevan `fuente` obligatoria (identifica el saldo) y `monto > 0`;
aperturas/fuente/organismo deben pertenecer a la gestión
(`_validar_movimientos_reform`).

## 4. Workflow de estados (`EstadosReform`)

```
BORRADOR ──→ EN_REVISION ──→ APROBADA ──→ APLICADA
   ↑            │  │
   │            │  └──→ RECHAZADA (definitivo; se registra como anular)
   └────────────┘
   OBSERVADA ──→ EN_REVISION (con motivo obligatorio)
```

- `crear_reform`: BORRADOR con movimientos; exige gestión habilitada y una
  distribución **FIJADA** (`version_origen` apunta a ella).
- `enviar_reform_a_revision` (BORRADOR|OBSERVADA → EN_REVISION),
  `observar_reform` (motivo obligatorio), `aprobar_reform` (registra
  `aprobada_por`), `rechazar_reform` (motivo obligatorio).
- El documento solo se edita/elimina en **BORRADOR** (400 si no).

## 5. Aplicación atómica (§97) — `aplicar_reform(reform, usuario)`

`@transaction.atomic`, requisitos: estado `APROBADA` + gestión habilitada.

1. **Versión activa**: si la distribución está FIJADA y no hay versión
   activa, abre la siguiente vía `ajuste_distribucion` (contenedor BORRADOR).
2. Aplica cada movimiento en orden de creación (`movimientos.order_by('id')`):
   - `TRASPASO` → `BudgetControlService.apply_movement` (lock origen +
     bloqueo de fuente; `saldo_origen >= monto`).
   - `INCREMENTO` → `_incrementar_movimiento`: el saldo resultante del
     destino no supera el techo distribuible de su fuente (§96).
   - `DISMINUCION` → `_disminuir_movimiento`: `saldo_origen >= monto`;
     devuelve el saldo al pool de la fuente.
   - `CAMBIO_FUENTE` → `_cambio_fuente_movimiento`: reduce la fuente vieja y
     aumenta la nueva (misma apertura, §96). La fuente vieja no se persiste
     en el modelo (una sola FK): se **infiere** de forma determinista — el
     `AllocationSource` de la apertura distinto de (fuente nueva, organismo
     nuevo) con saldo suficiente; si hay varios, el de **mayor saldo**
     (empate → menor id).
3. Cada movimiento registra `saldo_antes`/`saldo_despues` del
   `AllocationSource` afectado (histórico en `ReformMovement`).
4. **Si CUALQUIER movimiento falla → rollback completo** (ni saldos, ni la
   versión abierta, ni el estado).
5. Éxito: estado `APLICADA`, `fecha_aplicacion`, auditoría (`aprobar`).

### Reglas de no exceso

- `saldo_origen >= monto` en TRASPASO/DISMINUCION/CAMBIO_FUENTE
  (BUDGET_EXCEEDED con requested/available/difference → 400).
- El saldo resultante del destino **nunca supera el techo distribuible de
  la fuente** en INCREMENTO/TRASPASO/CAMBIO_FUENTE (red de seguridad §96).

## 6. Decisión de arquitectura (Fase 10, documentada en el código)

- La reformulación opera **DIRECTAMENTE sobre las filas `AllocationSource`/
  `Reserve` existentes** (no duplica filas ni re-apunta versiones): el
  "nuevo saldo efectivo" ES el saldo tras el movimiento; el histórico queda
  en `ReformMovement` + `EventoAuditoria`.
- La versión fijada conserva sus filas; su checksum queda obsoleto **por
  diseño**: el congelamiento protege la edición del documento, no los
  saldos que la reformulación modifica legítimamente con trazabilidad.
- `version_resultante` se deja **NULL** en esta fase.

## 7. Auditoría

Toda transición y la aplicación registran `EventoAuditoria` (acciones
`enviar/devolver/aprobar/anular` del catálogo). El mapeo semántico vive en
`services.ACCIONES_AUDITORIA` (REEFORM→aprobar).

## 8. API

| Ruta | Propósito | Permiso |
|---|---|---|
| `POST /reforms/` | crear (body `movimientos`: [{tipo, apertura_origen?, apertura_destino?, fuente?, organismo?, monto, motivo?}]) | `sis_poa.budget.reform` |
| `GET /reforms/?gestion=&estado=&tipo=` · `PATCH/DELETE /{id}/` (solo BORRADOR) | consulta/edición | reform (escritura) |
| `POST /{id}/submit/` | → EN_REVISION | reform |
| `POST /{id}/observe/` · `approve/` · `reject/` · `apply/` | transiciones/aprobación/aplicación | `sis_poa.budget.approve` |

## 9. Tests clave

`ReformulacionCreacionTests`, `ReformulacionFlujoTests`,
`ReformulacionTiposTests` (TRASPASO/INCREMENTO/DISMINUCION/CAMBIO_FUENTE),
`ReformulacionAtomicidadTests` (rollback total ante fallo) y
`ReformulacionAuditoriaTests` (ver `testing.md`).

# SIS-POA — Control Presupuestario Central (`BudgetControlService`)

## 1. Rol

`control.py` es el **núcleo financiero transaccional** del ciclo (Fase 8):
centraliza TODAS las reglas monetarias (§85-88, §109). Servicio **sin
estado**: todos los métodos son estáticos; el estado vive en la BD. Las
funciones históricas de `services.py` (`crear_allocation`, `crear_reserva`,
`liberar_reserva`, `_bloquear_fuentes`, …) delegan en él sin cambiar firmas.

## 2. Lecturas (no lockean)

| Método | Resultado |
|---|---|
| `get_directive_ceiling(gestion)` | `{gestion, version, techo_bruto, por_fuente}` de la versión FIJADA; `{}` si no hay |
| `get_distributable_ceiling(gestion)` | `{fuente_id: bruto − obligatorios}` (solo fuentes con recursos) |
| `get_distributed(gestion)` | `{fuente_id: monto}` distribuido por aperturas no CERRADAS |
| `get_reserved(gestion)` | `{fuente_id: monto}` reservado (ACTIVAS) |
| `get_available_for_distribution(gestion)` | `{fuente_id: disponible}` = techo − distribuido − reservado; `{}` bloquea |
| `get_allocation_ceiling(allocation)` | techo de la apertura = `SUM(fuentes)` |
| `get_allocated_to_expense_objects(allocation)` | Σ programado en `ExpenseObjectAllocation` (§90) |
| `get_allocation_available(allocation)` | techo de apertura − programado |
| `get_summary(gestion)` | resumen consolidado (invariante exacta `techo = distribuido + reservado + disponible`) |

## 3. Validaciones

- `validate_distribution(gestion)` → `validar_distribucion_completa`
  (`{valida, diferencias}`, tolerancia 0.01).
- `validate_expense_object(allocation, objeto_gasto_id, monto)` → lanza
  `ValidationError` si no pasa, `{'valido': True}` si sí; valida apertura
  ACTIVA, versión de distribución FIJADA, objeto del gasto existente y
  `monto <= disponible` (`ErrorObjetoGastoExcedido`).

## 4. Escrituras transaccionales (lock + saldos)

Todas corren en `transaction.atomic`:

| Método | Comportamiento |
|---|---|
| `reserve(gestion, fuente, organismo, monto, motivo, usuario, tipo)` | crea reserva ACTIVA si no excede el disponible (BUDGET_EXCEEDED si no); rechaza sobre versión fijada |
| `release(reserva, usuario)` | LIBERADA (devuelve el disponible); lockea la fuente para serializarse contra reservas concurrentes |
| `apply_movement(orig, dest, fuente, organismo, monto, motivo, usuario)` | TRASPASO origen→destino por fuente con saldos antes/después; crea el source destino si no existe; devuelve `{valido, movido, origen, destino, fuente, saldo_antes, saldo_despues}` |

### Locks y concurrencia (§87)

- `_bloquear_fuentes(gestion, fuente_ids)`: `select_for_update()` sobre las
  filas `CeilingResource` de la versión FIJADA del techo (inmutables; el
  lock solo serializa). Es el **punto de serialización de TODAS las
  escrituras del ciclo** (services, territorial, reformas lo reutilizan).
- `apply_movement` además lockea las filas `Allocation` origen/destino y
  los `AllocationSource` afectados (`select_for_update`).
- Escenario garantizado: Usuario A reserva 80.000 y Usuario B 50.000 sobre
  un techo de 100.000 → el segundo falla con BUDGET_EXCEEDED (re-lee los
  agregados ya commiteados), **nunca se consume más que el saldo**.
- Test de doble consumo: `ControlConcurrenciaTests` (TransactionTestCase,
  threads) en `tests.py`.

## 5. Códigos de error

| Excepción | HTTP | Cuerpo |
|---|---|---|
| `ErrorDisponibilidad` (saldo por fuente) | **400** | `{error: {detail}, code: 'BUDGET_EXCEEDED', details: {fuente, requested, available, difference}}` |
| `ErrorObjetoGastoExcedido` (disponible de la apertura, §91) | **409** | `{error: {detail}, code: 'BUDGET_EXCEEDED', details: {requested, available, difference}}` |

`ErrorDisponibilidad` NO lleva `fuente` (es contra el techo de la APERTURA);
`ErrorObjetoGastoExcedido` sí. Los `ValidationError` de dominio van como
`400 {error: {detail}}`.

## 6. Llave presupuestaria

La llave del ciclo es **(fuente, organismo)**: cada `AllocationSource`,
`Reserve` y `ReformMovement` la lleva; todos los saldos se agregan por
`fuente_id`. `AllocationSource` tiene `UNIQUE (allocation, fuente,
organismo)` con `nulls_distinct=False` (una fila por llave, aun con NULL).

## 7. API

| Ruta | Propósito | Permiso |
|---|---|---|
| `GET /control/summary/?gestion=` | resumen consolidado por fuente (`get_summary`) | autenticado |
| `POST /control/validate/` | `{tipo: distribution}` → `{valido, errores}`; `{tipo: expense-object, allocation, objeto_gasto, monto}` → valida programación (o 400 `{valido: false}`); `{tipo: allocation, allocation}` → `{techo, programado, disponible}` | autenticado |

## 8. Reglas §151 (innegociables, en backend)

1. Nunca consumir más que el saldo (por fuente y por apertura).
2. El destino de un movimiento no excede el techo distribuible de su fuente.
3. Versiones fijadas inmutables (modelo + 409 en la API).
4. Todos los montos `Decimal`/`NUMERIC(18,2)`.
5. Totalidad en agregaciones SQL (sin filas de total).

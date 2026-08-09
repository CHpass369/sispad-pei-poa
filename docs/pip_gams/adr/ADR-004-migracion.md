# ADR-004 — Estrategia de migración Expand / Migrate / Contract

- **Estado:** Aprobado (WP-01)
- **Fecha:** 2026-08-09
- **Decisores:** Arquitectura PIP-GAMS

## Contexto

Existen duplicidades críticas (PAD en `pad` y `articulacion`; operación/tarea
en `indicadores` y `articulacion`; estrategia en `planificacion`,
`articulacion` y `codificacion`). Mover o borrar sin control pierde datos.
El app label de Django y las migraciones forman el estado histórico de la BD.

## Decisión

**Refactor incremental con la secuencia oficial:**

> **preservar → normalizar → versionar → migrar → validar → cortar → retirar**

Concretamente por módulo:

### Expand
- Agregar tablas V2 **sin borrar** nada existente.
- Migraciones aditivas; nunca editar ni squash de migraciones históricas.
- API V2 en paralelo.

### Migrate
- Congelar edición del módulo legacy que se migra (ventana de freeze).
- Backfill vía comandos idempotentes usando `LegacyMigrationMap`.
- Reconciliar: conteos, códigos, sumas presupuestarias, articulaciones,
  huérfanos y muestras manuales.

### Cutover
- Frontend usa V2; V1 queda read-only o adaptada.
- Monitoreo de errores; rollback disponible.

### Contract
- Retirar endpoints legacy y escritura legacy.
- Eliminar modelos/columnas obsoletos solo tras versión estable, respaldo
  verificable y periodo de observación.

## Componente técnico obligatorio

`LegacyMigrationMap` (tabla) — app/model legacy, UUID legacy, tipo destino,
UUID destino, lote, checksum, estado, fecha, observaciones. Comandos de
dry-run y reconciliación (WP-05).

## Reglas no negociables

1. No borrar migraciones históricas.
2. No squash de migraciones durante la migración V2.
3. No cambiar códigos oficiales sin tabla de homologación.
4. No editar datos productivos manualmente.
5. Duplicados se resuelven por código + versión + significado, nunca por texto.
6. Ningún modelo legacy se marca read-only sin gate de reconciliación.

## Alternativas descartadas

- Big-bang (reescribir todo de una vez): prohibido por el plan (§32).
- Dual-write permanente: solo si imprescindible y acotado; se prefiere
  ventanas de freeze por módulo.

# TASK PIP-PE-004: Refactor puente `poau/migration_v2.py` (idempotencia)

## DOMINIO

`sis-poa` (poau V2) — impacto `sis-pe` (articulacion origen)

## OBJECTIVE

Hacer idempotente y verificable el puente `backend/apps/poau/migration_v2.py` que importa la cadena operativa de `articulacion_*` a la canónica `poau V2`, eliminando la deuda detectada en PIP-PE-001: sin re-sincronización de filas existentes, sin transacción por lote, estados forzados a `borrador` y copia de campos a JSON no tipado.

## CONTEXT

Auditoría PIP-PE-001 (`docs/architecture/CADENA_OPERATIVA_EQUIVALENCIA.md` §6, §10): `importar_poa_v2` usa `get_or_create` por `(poa, codigo)` (evita duplicados) pero NO actualiza filas ya creadas si el origen cambió; no hay transacción global ni rollback; `estado` V2 siempre `borrador` aunque el origen esté `APROBADO`; `LegacyMigrationMap` se sobrescribe por lote sin checksum por corrida. Datos actuales: 1-1-1-1 en ambas cadenas, `reconciliado` en mapa (lote `poa-2027`).

## CURRENT BEHAVIOR

- `_crear_instancia` (:118) copia `presupuesto_programado/meta_gestion/meta_anual/total_programado/responsable` a `atributos` (JSON sin tipado).
- `_registrar_mapa` (:160) sobrescribe el mapa sin validar checksum.
- Sin `dry_run` completo por lote ni modo "solo verificar".

## EXPECTED BEHAVIOR

- Puente idempotente: re-ejecución = no-op si no hay cambios; re-sincroniza campos y estados si el origen cambió (o reporta discrepancia).
- Transacción por gestión/lote con rollback ante error.
- Mapeo de estados origen → V2 explícito y configurable.
- `dry_run` y modo verificación (`--check`) sin escritura.

## IN SCOPE

- [ ] Refactor de `importar_poa_v2`/`_crear_instancia`/`_registrar_mapa`.
- [ ] Transacción por lote + rollback.
- [ ] Mapeo de estados `articulacion` (`REFERENCIAL/ENVIADO/APROBADO/OBSERVADO`) → `EstadosPoA` V2.
- [ ] `dry_run` y verificación de checksum por corrida.
- [ ] Comando de gestión o mejora del existente para invocar el puente con opciones.

## OUT OF SCOPE

- Retirar `indicadores_*` (PIP-PE-003).
- Reconciliación de datos (PIP-PE-002).
- Cambios a modelos canónicos de `articulacion`.

## INVARIANTS

- La cadena canónica es `poau V2`.
- No duplicar registros en V2 ni romper `LegacyMigrationMap` existente.
- Compatibilidad con la corrida ya realizada (lote `poa-2027`).

## DATABASE IMPACT

Sin cambios de esquema (solo comportamiento del puente y datos V2 si se re-sincroniza).

## API IMPACT

`ninguno` (el puente no expone endpoints).

## FRONTEND IMPACT

`ninguno`.

## FILES EXPECTED

- `backend/apps/poau/migration_v2.py` — refactor.
- Comando/management o opciones nuevas para invocar el puente.
- Tests del puente (idempotencia, transacción, estados, dry_run).

## DEPENDENCIES

- `PIP-PE-001` (documento de equivalencia: mapeo de estados §5).

## ACCEPTANCE CRITERIA

- [ ] Re-ejecutar el puente sobre datos ya migrados no crea ni modifica nada (idempotencia).
- [ ] Un cambio en el origen (p.ej. estado `APROBADO`) se refleja en V2 tras re-sincronizar.
- [ ] Fallo a mitad del lote revierte (transacción).
- [ ] `dry_run`/`--check` no escriben.

## TESTS

```bash
cd backend; python -m pytest apps/poau apps/articulacion -q
# Idempotencia manual:
cd backend; .venv\Scripts\python manage.py shell -c "from apps.poau.migration_v2 import importar_poa_v2; print(importar_poa_v2(dry_run=True)); print(importar_poa_v2())"
```

## RISKS

Medio: re-sincronización puede sobrescribir datos V2 editados manualmente. Mitigación: modo `--check` por defecto; la escritura solo tras confirmación; backups antes de la primera corrida de escritura.

## ROLLBACK

Reversa del commit del refactor; la transacción del lote evita estados parciales; backup de V2 antes de re-sincronizar.

## FINAL REPORT

Cambios al puente, tests agregados, resultados de idempotencia, estados mapeados, deuda pendiente.
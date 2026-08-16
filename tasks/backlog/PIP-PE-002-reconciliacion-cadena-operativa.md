# TASK PIP-PE-002: Reconciliación de datos cadena operativa (articulacion → poau V2)

## DOMINIO

`sis-pe` (articulación) — impacto `sis-poa`

## OBJECTIVE

Reconciliar los datos de la cadena operativa `articulacion_*` → `poau V2` (checksums, estados, POA 2028 huérfano, programaciones) para dejar la canónica V2 consistente ANTES del corte de `indicadores_*` (PIP-PE-003). Documentado en `docs/architecture/CADENA_OPERATIVA_EQUIVALENCIA.md` §7.

## CONTEXT

Auditoría PIP-PE-001 (2026-08-16): cadena `articulacion` (1-1-1-1, gestión 2027, `REFERENCIAL`) ya puenteada a `poau V2` (1-1-1-1, `borrador`) con `LegacyMigrationMap` en `reconciliado` (lote `poa-2027`). Divergencias detectadas:

- `PoAInstitucional` P-2028 existe sin acciones, pero hay `ProgramacionActividad` `anio=2028` colgada de ACT-01 del POA P-2027.
- `PoAInstitucional.gestion=2028` es huérfana (GestionFiscal solo 2026/2027).
- `indicadores_*` vacío (0 registros) — sin datos que reconciliar ahí.
- `poau` V1 y `planificacion.AcccionCortoPlazo` vacíos.

## CURRENT BEHAVIOR

- `poau/migration_v2.py` copia `atributos` a JSON no tipado y fuerza `estado=borrador` en V2 sin reflejar el origen.
- `LegacyMigrationMap` no se re-sincroniza por corrida del puente (solo `legacy_audit --reconciliar`).
- POA 2028 sin acciones y programación 2028 bajo POA 2027 conviven sin validez.

## EXPECTED BEHAVIOR

- Checksums de la cadena A→D verificados (lote `poa-2027`).
- POA P-2028 resuelto: eliminar, anexar a P-2027 o re-asignar programación 2028, según aprobación de datos.
- Estados origen/v2 auditados y sin conflictos (o plan de mapeo de estados documentado).
- Informe de reconciliación con conteos pre/post.

## IN SCOPE

- [ ] Verificar `legacy_audit --reconciliar` sobre lote `poa-2027`.
- [ ] Auditar estados por nivel en origen y V2.
- [ ] Resolver POA P-2028 + `ProgramacionActividad` anio 2028 (decisión de datos, data migration aprobada).
- [ ] Documentar decisiones en el informe.

## OUT OF SCOPE

- Retirar `indicadores_*` (PIP-PE-003).
- Refactor de `poau/migration_v2.py` (PIP-PE-004).
- Cambios a modelos canónicos de `articulacion`.

## INVARIANTS

- La cadena canónica es `poau V2` (DUPLICATION_ANALYSIS D4).
- Nada se borra sin respaldo y tarea de datos aprobada (regla DATABASE de AGENTS.md).
- `GestionFiscal` no cambia.

## DATABASE IMPACT

Data migration aprobada en esta tarea (decisión del POA 2028). Esquema sin cambios.

## API IMPACT

`ninguno`.

## FRONTEND IMPACT

`ninguno`.

## FILES EXPECTED

- `tasks/completed/` — informe de reconciliación (o `tasks/active/PIP-PE-002-*.md` con FINAL REPORT).

## DEPENDENCIES

- `PIP-PE-001` (documento de equivalencia y auditoría).
- `PIP-DB-005` (gestión fiscal SIS-POA legacy, informativa).

## ACCEPTANCE CRITERIA

- [ ] `legacy_audit --reconciliar --lote poa-2027`: 4/4 reconciliados (o discrepancias resueltas).
- [ ] POA 2028 y programación 2028 con resolución registrada.
- [ ] Conteos pre/post en FINAL REPORT.

## TESTS

```bash
cd backend; python -m pytest apps/articulacion apps/poau -q
cd backend; .venv\Scripts\python manage.py shell -c "from apps.poau.models_v2 import PoAInstitucional; print(list(PoAInstitucional.objects.values_list('gestion', flat=True)))"
```

## RISKS

Bajo: datos vigentes 2026/2027 (2028 es huérfano). Riesgo de borrar datos con trazabilidad → mitigado por respaldo y decisión explícita.

## ROLLBACK

Restore del respaldo previo a la data migration; reversa de la decisión del POA 2028.

## FINAL REPORT

Conteos pre/post, decisiones de datos, checksums verificados, deuda detectada.
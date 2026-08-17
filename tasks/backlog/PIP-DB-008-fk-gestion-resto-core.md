# TASK PIP-DB-008: FK gestión fiscal — resto de CORE (workflow, auditoria, documentos, territorio, VersionableModel)

## DOMINIO

`core` — continuación de PIP-DB-002

## OBJECTIVE

Completar la conversión de los campos `gestion` de las apps CORE restantes a FK sobre `GestionFiscal` con `ON DELETE PROTECT`, aplicando el patrón validado en PIP-DB-002 (secuencia AddField→RunPython→RemoveField→RenameField, `db_column` conservada, `gestion_anio` en serializers, filtro por año en viewsets, adaptación de tests/commands).

## CONTEXT

PIP-DB-002 (cerrada 2026-08-16) convirtió solo `organizacion` (24 filas, sin huérfanos). Pendiente del mismo dominio CORE: `workflow` (EnvioFormulacion, Observacion, Aprobacion), `auditoria` (EventoAuditoria — conservar null=True), `notificaciones`, `documentos`, `acciones_correctivas`, `reportes`, `territorio`, y `core.VersionableModel` (abstracto → FK materializada en 13 subclases, migración de 14 tablas a la vez). Detalle en `docs/architecture/GESTION_FISCAL_AUDIT.md` §5.

## CURRENT BEHAVIOR

- Campos `gestion` como PositiveIntegerField (año) sin integridad referencial en esas apps.

## EXPECTED BEHAVIOR

- FK a GestionFiscal con PROTECT (auditoria conserva null=True), `db_column='gestion'`.
- Contrato de año mantenido: `gestion_anio` (ro) en serializers; `?gestion=<año>` filtrando por año.
- Suite completa en verde (1282 baseline) y commands/seed adaptados.

## IN SCOPE

- [ ] Convertir workflow, auditoria, notificaciones, documentos, acciones_correctivas, reportes, territorio, core.VersionableModel + DemoDatasetManifest.
- [ ] Data migrations donde haya filas (verificar huérfanos ANTES; no inventar gestiones).
- [ ] Revisar triggers SQL que asuman gestion entero (patrón presupuesto/0007).
- [ ] Adaptar tests/commands/seed afectados.

## OUT OF SCOPE

- Apps de otros dominios (PIP-DB-003 a 007).
- budget/gestion FKs con CASCADE (deuda separada).

## INVARIANTS

- `GestionFiscal` intacta; no inventar gestiones; `auditoria.gestion` sigue null=True.

## DATABASE IMPACT

Migraciones Django por app + data migrations según datos; posibles recreaciones de triggers.

## API IMPACT

Serializers/viewsets que exponen gestion (año) → gestion_anio.

## FRONTEND IMPACT

Ninguno si se mantiene el año en el contrato (patrón PIP-DB-002).

## FILES EXPECTED

Models/migrations/serializers/views de las apps listadas + tests afectados.

## DEPENDENCIES

- PIP-DB-002 (patrón validado)
- GESTION_FISCAL_AUDIT.md §5

## ACCEPTANCE CRITERIA

- [ ] Todas las tablas CORE con FK PROTECT (auditoria null=True).
- [ ] Suite completa verde; contratos de año intactos.
- [ ] FINAL REPORT con conteos y huérfanos encontrados.

## TESTS

```bash
cd backend; .venv\Scripts\python -m pytest -q
```

## RISKS

Medio-alto: VersionableModel materializa en 13 tablas (migración amplia); workflow tiene datos de ciclo (verificar gestiones); mismo patrón de ~200 tests a adaptar que en PIP-DB-002.

## ROLLBACK

FKR por app + reversa de data migrations.

## FINAL REPORT

Tablas migradas, huérfanos, triggers recreados, tests adaptados, suite total.

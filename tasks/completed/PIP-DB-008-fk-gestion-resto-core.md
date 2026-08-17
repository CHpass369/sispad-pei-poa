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

Cerrada 2026-08-16 — **CORE completo con FK a GestionFiscal PROTECT** (organizacion quedo en PIP-DB-002; esta tarea cerro el resto).

**Tablas migradas (11 campos en 8 archivos de models):** workflow (EnvioFormulacion, Observacion, Aprobacion), auditoria (EventoAuditoria — **null=True conservado**), notificaciones (Notificacion), documentos (DocumentoAdjunto), acciones_correctivas (AccionCorrectiva — ordering a `-gestion__anio`), reportes (ReporteGenerado), territorio (LocalizacionTerritorial), core (VersionableModel abstracto + DemoDatasetManifest).

**Migraciones creadas (8):** secuencia Add→Remove→Rename→Alter (PostgreSQL no castea int→uuid ni en tabla vacia — hallazgo que invalido el AlterField directo de Django); `db_column='gestion'` conservada; auditoria con RunPython (1 fila real 2027 mapeada sin inventar gestiones).

**Correcciones de auditoria previa:** Distrito/UnidadTerritorial/CompromisoAccionCorrectiva NO tienen campo gestion (la auditoria GESTION_FISCAL_AUDIT los listo por error); `VersionableModel` NO tiene subclases (import muerto en planificacion) — el "impacto 13 tablas" no existia.

**Servicios normalizados (punto unico de contratos):** auditoria/services.py (`_resolver_gestion` — anio→instancia, inexistente→None; filtros por `gestion__anio`; export expone anio), workflow/services.py, acciones_correctivas/services.py, notificaciones/services.py, territorio/services.py (resolucion explicita con error claro; NO se inventan gestiones), demo_articuladores.py (manifest), budget AuditLogView + AuditEventSerializer (contrato `?gestion=<anio>` + `gestion`=anio conservado, `gestion_id`=uuid nuevo).

**Tests adaptados (~230 sitios):** budget (160), workflow (22), acciones_correctivas (20), notificaciones (14), test_importar_techo_sigep, test_paginacion_dual, test_permisos, test_api, demo_articuladores, demo_matrix — payloads POST de creacion con uuid (contrato de escritura de workflow/notificaciones/AC ahora recibe uuid; el frontend no envia gestion en esos forms).

**Suite:** **1282 passed** (baseline), ruff limpio. Nota: en Windows el cierre de pytest-xdist a veces no termina el proceso tras el 100% (log sin resumen) — ejecutar con `-p no:cacheprovider` y verificar el log.

**Commit:** `32b1906` (32 archivos, 639+/96-).

**Riesgos documentados:** queries externas que filtren `WHERE gestion=<anio>` sobre estas tablas requieren JOIN a gestion_gestionfiscal; contratos de escritura (POST) de observaciones/notificaciones/acciones-correctivas ahora aceptan uuid de gestion (el anio se expone como `gestion_anio`/`gestion` en lectura segun serializer).

**Deuda detectada:** budget/gestion FKs con CASCADE (uniformar a PROTECT — pendiente); `buscar_por_usuario`/`contar_por_entidad` de auditoria normalizados por anio (queries con uuid siguen soportadas).

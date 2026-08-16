# TASK PIP-DB-001: Auditoría y FK de gestión fiscal (fase 1)

## DOMINIO

`core` (gestion) — impacto transversal

## OBJECTIVE

Fase 1: auditar los ~12 campos de gestión sin FK que guardan el año fiscal como entero suelto en distintas apps y planificar la migración a FK sobre `GestionFiscal` (canónica) con `ON DELETE PROTECT`. En esta fase NO se ejecuta la migración de datos masiva: se audita, se documenta y se propone el plan por app.

## CONTEXT

Auditoría ETAPA A (2026-08-16). `backend/apps/gestion/models.py:7` define `GestionFiscal` (tabla `gestion_gestionfiscal`), canónica para la gestión fiscal. Sin embargo, múltiples apps guardan `gestion` como `PositiveIntegerField` (o `IntegerField`) sin FK:

| App | Líneas verificadas (models.py) | Campo |
|---|---|---|
| techos | 15 | gestion |
| presupuesto | 24, 47, 66, 265, 405 | gestion |
| recursos | 10 | gestion |
| organizacion | 37, 54, 85, 112 | gestion |
| pad | 26, 46, 100, 191, 338 | gestion |
| poau | 25 | gestion |
| seguimiento | 18 | gestion |
| modificaciones | 35 | gestion_fiscal |
| workflow | 14, 111, 126 | gestion |
| indicadores | 51 | gestion |
| articulacion | 483, 796, 902, 1039 (IntegerField) | gestion |
| auditoria | 36 (null=True, blank=True) | gestion |
| (otras) | core, catalogos, codificacion, normativa, territorio, notificaciones, reportes, inversion, planificacion, acciones_correctivas | varios |

Nota: la lista del ~12 apps se confirma en la auditoría; algunas usan `IntegerField` y otras `PositiveIntegerField`; hay apps (evaluacion) por verificar con nombre de campo distinto. La canónica `GestionFiscal` no tiene que cambiar en esta fase.

## CURRENT BEHAVIOR

- La gestión fiscal es un entero libre en ~12+ apps: sin integridad referencial, sin validación de existencia, sin protección ante borrado de gestiones usadas, y con convención inconsistente (gestion / gestion_fiscal / gestion_inicio / gestion_fin).

## EXPECTED BEHAVIOR

- Documento de auditoría (en la tarea o `docs/architecture/`) que lista, por app y tabla, el campo de gestión, su uso, volumen estimado y riesgo.
- Plan de convergencia por app (fase 2+): data migration que enlaza a `GestionFiscal` + FK `ON DELETE PROTECT`.
- Recomendaciones: apps donde la FK es segura hoy vs apps donde el dato es huérfano (años sin GestionFiscal registrada).

## IN SCOPE

- [ ] Auditoría completa de cada campo `gestion*` en las apps listadas (grep por `gestion` en `models.py` de todas las apps) con conteo de uso (columnas, valores).
- [ ] Verificar cuántas gestiones referenciadas existen en `gestion_gestionfiscal` y cuántos años están huérfanos.
- [ ] Redactar el plan de migración por app (fase 1 termina con el plan aprobado).
- [ ] Documentar la decisión de `ON DELETE PROTECT` y el orden de migración (apps con datos → data migration → FK).

## OUT OF SCOPE

- Ejecutar las migraciones de datos y FKs (fase 2, tareas por app: PIP-DB-002+).
- Cambiar `GestionFiscal` (modelo canónico).
- Cambios de API o frontend.

## INVARIANTS

- No se crean ni alteran tablas en esta fase (solo auditoría y documentación).
- `GestionFiscal` sigue siendo la única fuente canónica de gestión fiscal.
- No se rompen contratos V1/V2.

## DATABASE IMPACT

`ninguno` en esta fase (auditoría read-only). Fase 2: data migrations + FKs `ON DELETE PROTECT` por app, cada una con su propia tarea.

## API IMPACT

`ninguno` en esta fase.

## FRONTEND IMPACT

`ninguno` en esta fase.

## FILES EXPECTED

- `docs/architecture/` — documento de auditoría de gestión fiscal (o sección en DATA_OWNERSHIP) — crear
- `tasks/backlog/` — plan detallado por app y tareas derivadas (PIP-DB-002, PIP-DB-003, ...) — crear

## DEPENDENCIES

`ninguna`

## ACCEPTANCE CRITERIA

- [ ] Inventario completo: todas las apps con campo `gestion*` listadas con línea de `models.py` y tipo de campo (PositiveIntegerField/IntegerField/FK).
- [ ] Análisis de huérfanos: años referenciados sin registro en `gestion_gestionfiscal` (conteo real vía query o estimación documentada).
- [ ] Plan de migración por app aprobado y registrado como tareas en `tasks/backlog/` con orden de ejecución.
- [ ] Decisión de `ON DELETE PROTECT` documentada (con justificación de integridad).

## TESTS

```bash
# Auditoría read-only (ejemplos):
cd backend; python -m pytest apps/gestion -q
# Queries de auditoría (shell):
cd backend; python manage.py shell -c "from apps.gestion.models import GestionFiscal; print(GestionFiscal.objects.count())"
```

## RISKS

**Alto** (la más riesgosa del backlog): toca ~12+ apps con datos reales de producción. Riesgos: años huérfanos sin GestionFiscal (la FK los rompería → data migration debe crearlos o excluirlos), apps con convenciones distintas (`gestion_fiscal`, `gestion_inicio/fin`), sincronización con workflows externos. Mitigación: fase 1 100% read-only; las migraciones se ejecutan app por app en tareas separadas con su propio ROLLBACK; nunca renombrar la tabla canónica (recordatorio: el renombrado masivo del 15-08-2026 ya rompió queries externas).

## ROLLBACK

En fase 1 no aplica (no se altera nada). Para fases 2+: por cada app, migración de reversa (FKR) y restore del data migration antes de aplicar; plan de rollback por app en su propia tarea.

## FINAL REPORT

Cerrada 2026-08-16.

**Inventario final:** 24 apps con campo `gestion*` entero sin FK (76 campos: 63 `gestion*` + 13 con nombre distinto como `anio`/`fiscal_year`); 71 `PositiveIntegerField`, 5 `IntegerField` (articulacion); 2 campos abstractos propagados (core.VersionableModel, catalogos.CatalogoBase → 13 subclases). Detalle completo en `docs/architecture/GESTION_FISCAL_AUDIT.md`.

**Conteos de huérfanos (DB local accesible, GestionFiscal count=2 → 2026/2027):** huérfanos confirmados en 7 tablas: `planificacion.NodoPlanificacion` (604 filas, 2021/2025), `ArticulacionPlanificacion` (61, 2021), `codificacion.VersionCatalogoPlan` (2021/2025), `normativa.VersionNormativa` (2015/2021), `poau.PoAInstitucional` (2028), `inversion.CostoProyecto` (2028), `planificacion.Plan` (rangos plurianuales — NO gestiones operativas). ~30 tablas vacías → FK directa sin data migration.

**Plan por app creado en backlog (6 tareas derivadas):** PIP-DB-002 (CORE, sin data migration), PIP-DB-003 (SHARED, data migration VersionCatalogoPlan), PIP-DB-004 (SIS-PE, renombres `fiscal_year`→`gestion`), PIP-DB-005 (SIS-POA, PoAInstitucional 2028), PIP-DB-006 (SIS-PRO, CostoProyecto 2028), PIP-DB-007 (casos complejos articulacion/planificacion/normativa).

**Decisión documentada:** `ON DELETE PROTECT` en toda FK nueva; rangos plurianuales NO fuerzan FK (excepción gobernada); unificar convención `gestion` + `PositiveIntegerField`.

**Commit:** `2812836`.

**Riesgos confirmados:** R1 alto (data migration que invente gestiones falsas 2015/2021/2025/2028 corrompería la canónica), R2 alto (604+ filas huérfanas), R3 medio (IntegerField articulacion), R4 medio (5 convenciones de nombre, renombrar rompe contratos V1), R5 bajo (bases abstractas → 14 tablas a la vez).

**Deuda detectada:** budget/gestion usan FK con CASCADE (gobernanza pide PROTECT — tarea separada); `auditoria.gestion` null=True; excepción plurianual sin regla escrita.

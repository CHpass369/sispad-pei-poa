# TASK PIP-DB-002: FK gestión fiscal — CORE (organizacion, auditoria, workflow, etc.)

## DOMINIO

`core` — impacto transversal CORE

## OBJECTIVE

Fase 2: convertir los campos `gestion` de las apps CORE a FK sobre `GestionFiscal` con `ON DELETE PROTECT`. Sin data migration: todas las tablas están vacías o con gestiones válidas (2027). Plan completo en `docs/architecture/GESTION_FISCAL_AUDIT.md` §5.

## SCOPE

- Apps: `organizacion` (UnidadOrganizacional, DireccionAdministrativa, UnidadEjecutora, AsignacionUsuarioUnidad), `auditoria` (EventoAuditoria, mantener null=True), `notificaciones`, `documentos`, `acciones_correctivas`, `reportes`, `territorio`, `workflow` (EnvioFormulacion, Observacion, Aprobacion), `core` (DemoDatasetManifest, VersionableModel abstracto).
- Migración Django por app: integer → FK `GestionFiscal` `on_delete=PROTECT`, `db_column` mantenido si aplica.
- No renombrar `gestion_gestionfiscal`.

## OUT OF SCOPE

- Apps de otros dominios (ver PIP-DB-003 a PIP-DB-007).
- budget/gestion ya con FK (CASCADE): uniformar a PROTECT es deuda separada.
- Cambios de API/frontend (sincronizar contratos en tarea de cutover).

## INVARIANTS

- `GestionFiscal` no cambia.
- No se borran datos; auditoria.gestion sigue null=True.

## DATABASE IMPACT

Migraciones Django por app (schema only). `core.VersionableModel` es abstracto: la FK se materializa en cada tabla hija.

## API IMPACT

Solo serializers si exponen el entero: revisar `filterset_fields`/`ordering` que usan `gestion` (no cambian).

## DEPENDENCIES

- `docs/architecture/GESTION_FISCAL_AUDIT.md` (plan).

## ROLLBACK

Migración de reversa por app (revertir FK a entero). Sin data migration: reversa trivial.

## FINAL REPORT

Cerrada 2026-08-16 — **alcance ajustado por hallazgo real**: la tarea original subestimó el impacto. La conversión de `gestion` (año int) → FK a `GestionFiscal` (UUID) cambia el CONTRATO (año → UUID) y rompe ~200 tests + seed + commands + 2 triggers PostgreSQL que asumían entero. Se completó el sub-bloque **organizacion** (el más crítico); el resto de CORE queda en PIP-DB-008.

**Tablas migradas (organizacion, 4 modelos + 24 filas reales):** `UnidadOrganizacional` (8), `DireccionAdministrativa` (5), `UnidadEjecutora` (11), `AsignacionUsuarioUnidad` (0) — todas con gestión 2027 válida (GestionFiscal 2026/2027 existentes; sin huérfanos → sin gestiones inventadas).

**Migraciones creadas (2):**
- `organizacion/0002` — secuencia AddField → RunPython (año→uuid) → RemoveField → RenameField → AlterField, `db_column='gestion'` conservada, `ON DELETE PROTECT`.
- `presupuesto/0007` — recrea los triggers `presupuesto_validar_coherencia_asignacion` y `presupuesto_validar_categoria_programatica` con JOIN a `gestion_gestionfiscal` (los originales 0003/0004/0005 asumían gestion entero y fallaban con UUID).

**Contratos:** serializers exponen `gestion` (UUID) + `gestion_anio` (año, ro) — patrón budget; `?gestion=<año>` sigue filtrando por año vía `gestion__anio` en los 4 viewsets y la action `arbol` (sin romper frontend).

**Consumidores adaptados (31 archivos):** seed_demo, commands (importar_catalogos_sacaba, importar_reales, importar_techo_sigep — `_catalogo` robusto FK/int, importar_matriz_base — degradación documentada para año 2021 sin GestionFiscal, cargar_demo_articuladores), service formulacion_poau_2027, demo_articuladores, y ~15 archivos de tests (fixtures con GestionFiscal get_or_create).

**Conteos pre/post:** 24 filas mapeadas año→uuid sin pérdida; suite completa **1282 passed** (baseline exacto), ruff limpio.

**Commits:** `ce4b972` (31 archivos, 689+/131-).

**Riesgos documentados:** queries externas que filtren `WHERE gestion=2027` sobre tablas de organizacion requieren JOIN a gestion_gestionfiscal (contrato cambiado); mitigado con `db_column='gestion'` (nombre de columna intacto).

**Deuda detectada:** (1) resto de CORE (workflow EnvioFormulacion/Observacion/Aprobacion, auditoria null=True, notificaciones, documentos, acciones_correctivas, reportes, territorio, `core.VersionableModel` → 13 subclases) → **PIP-DB-008** creada en backlog; (2) `budget`/`gestion` FKs existentes con CASCADE → uniformar a PROTECT (deuda separada); (3) `importar_matriz_base` usa 2021 sin GestionFiscal → pendiente de PIP-DB-007 (excepción histórica).
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

Conteos pre/post, tablas migradas, contratos verificados, deuda detectada.
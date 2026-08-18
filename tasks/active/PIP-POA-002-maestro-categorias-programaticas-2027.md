# TASK PIP-POA-002: Import the Gestión 2027 programmatic-category master

## DOMAIN

`sis-poa` (budget V2)

## OBJECTIVE

Load the `CLASIFICADOR` sheet from the POAU 2027 formulation workbook into the canonical `budget.ProgrammaticCategory` table as an idempotent, validated Gestión 2027 master.

## CONTEXT

`apps.budget.ProgrammaticCategory` is the canonical V2 model backed by `presupuesto_categoria_programatica`; the legacy `apps.presupuesto.CategoriaProgramatica` must not receive new records. The source workbook has header row 8 and 360 data rows (79 programs and 281 activities). Column E is the canonical composite category code used by the POAU formulation parser.

## CURRENT BEHAVIOR

No focused command loads this workbook into `budget.ProgrammaticCategory`. Existing category rows for historical fiscal years must remain untouched.

## EXPECTED BEHAVIOR

The command validates the workbook and GestiónFiscal 2027 before writing, links every activity to its program, preserves segment leading zeros and source provenance, supports a no-write dry run, and commits atomically with `(gestion, codigo)` idempotency.

## IN SCOPE

- [ ] Add parser, validation, and management command under `apps.budget`.
- [ ] Add focused tests for validation, hierarchy, provenance, dry-run, and idempotency.
- [ ] Execute and verify the supplied workbook import.

## OUT OF SCOPE

- Legacy `apps.presupuesto` categories.
- New tables, catalog duplicates, synthetic project rows, or API/frontend changes.
- Deleting, deactivating, or rewriting categories absent from the source.

## INVARIANTS

- `ProgrammaticCategory.codigo` remains the padded composite from column E.
- Historical Gestión 2026 rows remain unchanged.
- The accepted source activity `200 0 0150` remains text and is never truncated.
- All writes use one atomic transaction.

## DATABASE IMPACT

No migration. Idempotent data load into `presupuesto_categoria_programatica`, requiring an existing `GestionFiscal` with `anio=2027`.

## API IMPACT

None.

## FRONTEND IMPACT

None.

## FILES EXPECTED

- `backend/apps/budget/importer_programmatic_category.py` — parser, validation, and transactional loader.
- `backend/apps/budget/management/commands/importar_catalogo_programatico_2027.py` — CLI wrapper.
- `backend/apps/budget/test_programmatic_category_import.py` — focused tests.

## DEPENDENCIES

Existing `budget.ProgrammaticCategory` and `gestion.GestionFiscal` models; `openpyxl` in the backend environment.

## ACCEPTANCE CRITERIA

- [ ] Missing file/sheet, malformed rows, duplicate codes, unknown levels, missing parents, and missing Gestión 2027 fail closed.
- [ ] Dry run performs no writes and commit is atomic and idempotent.
- [ ] Supplied workbook imports as 79 programs and 281 activities and preserves absent existing rows.
- [ ] Key codes and parent links are verified through the ORM.

## TESTS

```bash
cd backend; .venv/bin/python -m pytest apps/budget/test_programmatic_category_import.py -q -n 0
```

## RISKS

The source workbook contains formulas in column E and one accepted width anomaly (`ACTIV.=0150`). Validation must use cached values and explicit text normalization without silently repairing malformed input.

## ROLLBACK

The command does not delete or deactivate rows. If a committed load must be reverted, restore the affected Gestión 2027 rows from the pre-import database backup or manually restore their prior field values; historical rows are not affected.

## FINAL REPORT

Implementation completed without a migration. Added the canonical budget parser/loader, management command, and focused tests. The supplied workbook was committed to `presupuesto_categoria_programatica` for Gestión 2027: 360 rows (79 programs, 281 activities), first run 360 created, second run 360 unchanged, and no rows preserved outside the source on the live database. ORM verification confirmed all activity parents, key codes, active state, 2027 validity date, and non-absolute provenance. Focused tests: 7 passed. `manage.py check` and `makemigrations --check --dry-run budget` passed. Ruff was unavailable in the backend virtual environment.

# PIP-POA-005: Complete UO-scoped POAU tree import

Continue the partially implemented Excel/Google Sheets ETL for
`/pip/sis-poa/poaus`. The final behavior is not the current behavior: one import
must rebuild the complete POAU tree for one organizational unit and fiscal year,
including every action, operation, activity, task, and monthly physical target
found in the matrix.

## Quick resume path

1. Preserve every uncommitted file listed below; there is no commit or push.
2. Read the current importer, API, model/migration, tests, and matrix component.
3. Ask the user the open organizational-unit schema question before editing.
4. Replace the current single-action, identity-preserving apply design with the
   confirmed full-unit reconstruction contract, in the ordered work units below.
5. Re-run the focused checks and perform a real preview before any apply test.

## Confirmed user decisions

| Topic | Required behavior |
| --- | --- |
| Import scope | Exactly one organizational unit and one fiscal year. |
| Actions | One matrix may contain multiple short-term actions; import all of them. |
| Replacement | Warn the user, then rebuild the entire POAU tree for that UO/year. |
| Existing dependencies | The warning must cover execution, budget, approval, and tracking data; after confirmation, reconstruct all in-scope operational data. |
| Audit | Preserve immutable history: actor, time, source metadata, validation result, and what was replaced/created. Never store source file bytes or credentials. |
| Missing UO | If the unit is absent from the selector/filter, create it from matrix data. |
| Sources | Accept temporary `.xlsx` uploads and Google Sheets URL plus sheet name/GID. |
| Safety | Preview is read-only; apply is atomic; any failure leaves the old tree intact. |

## Open decision — ask before implementing

The real matrix identifies an organizational unit by name but does not supply an
institutional UO code, unit type/class, or parent unit. The user has not answered
whether creation must require these matrix columns:

- `Código UO`
- `Nombre UO`
- `Tipo/Clase UO`
- `Unidad superior`

Do not invent these values, silently attach the unit to an arbitrary parent, or
derive an institutional code from the name. Ask whether all four fields are
mandatory and whether a missing value must block preview/apply.

## Current implementation and mismatch

The implementation already provides:

- in-memory `.xlsx` parsing and bounded Google Sheets export download;
- normalized preview staging with source metadata, summary, digest, and row
  errors, without persisted file bytes;
- validation for hierarchy, dates, decimals, periods, annual totals, units of
  measure, operation types, duplicates, and required references;
- preview/apply V2 endpoints under `/api/v2/sis-poa/poau-imports/`;
- `transaction.atomic()` and row locking;
- an accessible import dialog with Google/Excel source selection, preview,
  errors, confirmation, result summary, and matrix refresh.

However, it still implements the superseded contract:

- the UI requires the user to select one target `AccionPOA`;
- the API/importer scopes preview/apply to that action;
- apply diffs/upserts matching rows and preserves primary keys;
- apply blocks approved or depended-on leftovers instead of warning and then
  rebuilding all data for the UO/year;
- organizational units are treated as pre-existing shared dependencies rather
  than created from matrix data;
- audit/staging metadata exists, but the immutable before/after reconstruction
  audit required by the new contract is not yet designed or implemented.

The visible matrix is backed by the transitional articulation hierarchy:
`AccionPOA -> OperacionPOAU -> ActividadPOAU -> TareaPOAU`. Do not redirect the
feature to `apps.poau.models_v2` without proving the UI/runtime migration; the
current screen reads monthly programming from `apps.articulacion`.

## Completed parser correction

The source parser originally rejected sheets without `unidad_codigo`. It now
uses the organizational unit selected in PIP as a fallback when the column is
absent, while still rejecting a conflicting code if one is present. Tests cover
the fallback and mismatch behavior. Preserve this correction while redesigning
the import around UO scope.

## Real source evidence

Use this non-secret test source only for preview unless the user explicitly
authorizes a data-changing local apply:

- Google Sheet:
  `https://docs.google.com/spreadsheets/d/186MvPW_jh2VWnaOUn0wZ8DGAn2e04HZSndp6hy9UXJE/edit?usp=drive_link`
- Exact sheet name: `PROPUESTA POAU FINAL`

After the missing-unit-code fallback, the last real parse produced:

| Measure | Result |
| --- | ---: |
| Rows read | 57 |
| Hierarchy nodes detected | 54 |
| Valid nodes | 4 |
| Rejected nodes | 50 |
| Validation errors | 66 |

Most failures were data-consistency errors, including annual targets that do not
equal monthly totals. Preview must display these errors, and apply must remain
unavailable while the source is invalid.

## Working-tree inventory

The following status was verified before this handoff. Preserve all files.

### Modified

- `backend/apps/articulacion/models.py`
- `backend/config/urls_test_sqlite.py`
- `backend/config/urls_v2.py`
- `frontend/sispoa/src/app/features/sis-poa/matriz-poau.component.spec.ts`
- `frontend/sispoa/src/app/features/sis-poa/matriz-poau.component.ts`

### Untracked

- `CLAUDE.md`
- `backend/apps/articulacion/migrations/0019_importacion_programacion_fisica.py`
- `backend/apps/articulacion/poau_importer.py`
- `backend/apps/articulacion/tests/test_poau_import.py`
- `backend/apps/articulacion/views_poau_import.py`
- `tasks/active/PIP-POA-005-poau-physical-programming-import.md`

No commit or push exists for this work.

## Database and deployment state

- Migration `articulacion.0019_importacion_programacion_fisica` was applied only
  to the local development database.
- No migration or feature code has been deployed to production.
- Previously started frontend/backend processes are ephemeral. Verify process
  state and restart them; do not assume they survived another agent session.
- Preview tests and inspections did not mutate production data.

## Last verified checks

Before the new full-reconstruction requirement, the implementation passed:

- Django system check;
- migration drift check (`No changes detected`);
- Ruff on the importer, import view, and focused backend tests;
- the full 15-test focused backend module on SQLite after the organizational-unit
  fallback change;
- 13 focused backend tests on PostgreSQL before the two fallback tests were
  added; the full 15-test PostgreSQL rerun is still pending;
- Angular production build;
- TypeScript compilation of the matrix component spec.

The browser Karma runner could not bind its local port in the restricted agent
environment. That was an environment limitation, not an observed test failure.
Re-run it outside that restriction.

These results prove only the current superseded diff/upsert design. After the
redesign, add/replace tests and run the entire verification set again.

## Ordered implementation plan

Keep each unit reviewable and pair behavioral changes with tests.

- [ ] **1. Resolve the UO creation schema.** Record mandatory source columns,
  catalog resolution rules, parent-unit rules, and blocking errors.
- [ ] **2. Define the replacement boundary.** Enumerate every UO/year-owned
  operational and dependent table that must be deleted/rebuilt. Confirm foreign
  key order and deletion policy from real models; do not rely on cascade guesses.
- [ ] **3. Design immutable audit.** Capture actor, timestamp, UO/year, source
  type/safe locator, preview digest, validation summary, confirmation, and exact
  replaced/created counts. Preserve audit rows across reconstruction and rollback.
- [ ] **4. Change preview scope.** Remove target-action input. Resolve/create-plan
  the UO, validate multiple actions and their full descendants, detect duplicate
  natural keys across the complete matrix, and preview destructive impact.
- [ ] **5. Change apply semantics.** Inside one `transaction.atomic()` block,
  lock UO/year scope, verify the immutable preview digest and confirmation,
  preserve audit, delete all explicitly approved in-scope dependents/tree rows in
  proven order, and bulk-create the new hierarchy. Any exception must roll back
  both deletion and creation.
- [ ] **6. Update the UI.** Remove action selection, show UO/year and destructive
  impact, require explicit confirmation after the warning, and show audit/import
  results. Keep apply disabled for invalid or stale previews.
- [ ] **7. Expand tests.** Cover multiple actions, missing-UO creation, ambiguous
  or incomplete UO metadata, full dependent reconstruction, warning/confirmation,
  immutable audit, duplicate trees, stale digest, injected failure rollback,
  Excel/Google equivalence, and rejected invalid source structures.
- [ ] **8. Run real preview and all checks.** Do not apply the real sheet while it
  remains invalid. Verify that existing data is unchanged after every failed run.
- [ ] **9. Review and delivery.** Do not commit, push, or deploy without explicit
  user authorization and the repository's required gates.

## Data-safety constraints

- Never persist uploaded workbook bytes or external credentials.
- Restrict Google downloads to validated spreadsheet exports, with redirect,
  timeout, size, and XLSX-signature limits.
- Treat the selected fiscal year and effective organizational scope as authority.
- Never create a UO from incomplete or ambiguous metadata until the open schema
  decision is answered.
- Preview must be mutation-free, including when the UO does not exist. Represent
  planned creation in staging; create only during confirmed atomic apply.
- Bind apply to an unexpired, unchanged preview digest and exact UO/year.
- Display destructive impact before confirmation.
- Lock the target scope. Delete and recreate only the confirmed UO/year boundary.
- Preserve immutable audit outside the deletable operational boundary.
- Reject partial import. Any validation or write error must leave all prior
  operational and dependent records unchanged.
- Do not test destructive apply against production or the shared sample source.

## Commands

Run from the repository root. If the virtual environment or database differs,
inspect repository configuration first; never print secret environment values.

### Inspect

```bash
git status --short
git diff --check
git diff -- backend/apps/articulacion frontend/sispoa/src/app/features/sis-poa backend/config
rg -n "accion_codigo|unidad_codigo|transaction.atomic|select_for_update|bulk_create|ImportacionProgramacion" \
  backend/apps/articulacion frontend/sispoa/src/app/features/sis-poa backend/config
```

### Backend checks

```bash
cd backend
../.venv/bin/python manage.py check
../.venv/bin/python manage.py makemigrations --check --dry-run
../.venv/bin/python -m ruff check \
  apps/articulacion/poau_importer.py \
  apps/articulacion/views_poau_import.py \
  apps/articulacion/tests/test_poau_import.py
DJANGO_SETTINGS_MODULE=config.settings_test_sqlite \
  ../.venv/bin/python -m pytest -n 0 apps/articulacion/tests/test_poau_import.py
```

For the repository's configured PostgreSQL verification, load the existing local
development environment through the project's established mechanism, then run:

```bash
cd backend
../.venv/bin/python -m pytest -n 0 apps/articulacion/tests/test_poau_import.py
```

### Frontend checks

```bash
cd frontend/sispoa
npx tsc -p tsconfig.spec.json --noEmit
npm test -- --watch=false --browsers=ChromeHeadlessNoSandbox \
  --include='src/app/features/sis-poa/matriz-poau.component.spec.ts'
npm run build
```

### Run locally

Use two terminals from the repository root:

```bash
cd backend
../.venv/bin/python manage.py runserver localhost:8000
```

```bash
cd frontend/sispoa
NG_CLI_ANALYTICS=false npm start -- --host localhost --port 4200
```

Then open `http://localhost:4200/`, navigate to SIS-POA -> POAU, select the
fiscal year/UO, and run preview with the source above.

## Review-provider status

Native Gentle AI review could not start because the installed provider exposed
no `review` command. A privacy-scrubbed occurrence was added to the existing
[Gentle AI issue #3400](https://github.com/Gentleman-Programming/gentle-ai/issues/3400#issuecomment-5507142371).
Do not bypass or fabricate a review receipt. Resume native review only after a
published fix is installed or a maintainer supplies a documented supported
recovery. Ordinary local tests remain valid evidence but do not replace that gate.

## Rollback boundary

Before any confirmed apply, rollback is code-only: remove the V2 route, importer,
view, staging model/migration, focused tests, UI changes, and this task document,
then reverse local migration `articulacion.0019`. Do not use destructive Git
commands because the changes are uncommitted and may contain user work.

After a successful future reconstruction, code rollback does not restore deleted
operational data. Recovery must use the immutable audit/snapshot strategy designed
before implementation or a verified database backup. The apply transaction is
the failure boundary: before commit, any exception must restore the complete old
tree and dependents; after commit, restoration is an explicit recovery operation,
never an automatic best-effort partial rewrite.

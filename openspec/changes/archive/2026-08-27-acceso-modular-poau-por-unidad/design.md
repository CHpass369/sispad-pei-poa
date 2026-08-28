# Design: Interactive Modular POAU Access by Organizational Unit

## Technical Approach

Keep `AlcanceOrganizacional` as CORE's generic scope model: SIS-PE-only scopes may be yearless, while `sis_poa.*` assignments require a canonical `GestionFiscal` UUID. Preserve the authorization, V2 year-isolation, preview, and incremental Angular approach. Correct recorded-0013/physical-schema drift with a separate, state-neutral, forward-only migration; cycling edited 0013 is not a repair because Django sees nullable state on both sides.

## Architecture Decisions

| Decision | Choice | Alternatives considered | Rationale |
|---|---|---|---|
| Fiscal-year contract | Nullable CORE FK, capability-aware validation, `PROTECT`, four-field `UniqueConstraint(..., nulls_distinct=False)` | Global non-null or synthetic year | Preserves valid yearless SIS-PE state without weakening POAU boundaries. |
| Physical repair | New `0014`, using historical model metadata, database introspection, and `schema_editor.alter_field()` | Edit/cycle 0013; fake migration; raw SQL | Migration names have no content hash; only later versioned DDL repairs already-recorded drift. |
| Reverse behavior | State/data no-op | Restore `NOT NULL` | Nullable is authoritative in model and 0013 state; restoring obsolete nullability would corrupt domain-valid behavior. |
| Deployment authority | Renumber baseline to `0015`, dependent on 0014 | Keep baseline at 0014 | Establishes deterministic ordering after physical convergence. |
| Delivery | Isolated corrective WU2b within the seven stacked-to-main slices, ≤400 authored lines | Mix with WU4 or UI work | Keeps review, runtime proof, and rollback independently auditable. |

## Data Flow

```text
0013 state (nullable) ─┬─ fresh physical nullable ──┐
                      └─ recorded 0013 + NOT NULL ─┤
                              0014 introspection → schema-editor repair/skip
                                                   ↓
                         nullable column + FK + four-field uniqueness → 0015
```

Assignment and preview flows continue through shared effective-access evaluation. V2 resolves `gestion_id` once and filters both scopes and records by the owning POA year.

## File Changes

| File | Action | Description |
|---|---|---|
| `backend/apps/accounts/migrations/0013_poau_scope_backfill.py` | Freeze | Version before 0014; never edit after dependent delivery. |
| `backend/apps/accounts/migrations/0014_repair_alcance_fiscal_year_nullability.py` | Create | State-neutral physical nullability repair; depends on 0013. |
| `backend/apps/accounts/tests/test_migration_0014_nullability_repair.py` | Create | PostgreSQL drift, convergence, data, FK, and uniqueness proofs. |
| `backend/apps/accounts/migrations/0015_access_authorization_baseline.py` | Create | Idempotent capabilities/roles/grants baseline; depends on 0014. |
| Existing backend/frontend files listed by the prior design | Modify | Authorization, domain validation, V2 isolation, preview, metadata, UI, and empty-state behavior remain unchanged. |

## Interfaces / Contracts

`0014` resolves the historical `AlcanceOrganizacional` table and `fiscal_year` column from `apps`, then reads `connection.introspection.get_table_description()`. Missing table/column fails loudly; `null_ok=True` skips safely. Otherwise it copies the historical nullable field, marks only the old copy `null=False`, and calls `schema_editor.alter_field(Model, old_field, nullable_field, strict=True)` inside `SeparateDatabaseAndState(database_operations=[RunPython(...)], state_operations=[])`. No raw SQL or current-model import is allowed.

Django's FK alteration path drops and recreates the `GestionFiscal` FK inside the atomic migration; the named four-field unique constraint is not intentionally removed. This DDL takes strong PostgreSQL table locks, and FK recreation may extend validation/lock time, so run in a controlled window and audit both constraints afterward.

## Testing Strategy

| Layer | What to Test | Approach |
|---|---|---|
| Migration RED | Recorded 0013 with physical `NOT NULL` | Reach 0013, use historical fields plus `schema_editor.alter_field()` to create drift without raw SQL, retain recorder entry, apply 0014, assert introspected `null_ok=True`. |
| Convergence | Fresh and repaired paths | Prove 0012→0013→0014, already-nullable skip, reverse to 0013, and reapply all leave physical nullability unchanged. |
| Integrity/domain | Data and constraints | Persist yearless SIS-PE scope; prove FK behavior and named four-field uniqueness remain; retain POAU missing-year rejection tests. |

## Threat Matrix

N/A — no routing, shell, subprocess, VCS/PR automation, executable-file classification, or process-integration boundary.

## Migration / Rollout

First version and freeze 0013. Validate WU2b on disposable PostgreSQL for both fresh and manufactured-drift paths, including physical/model/recorder/constraint evidence. Then, only with authorization, migrate the target database through 0014 and perform a read-only Django introspection audit of `null_ok`, model state, migration recorder, FK, and uniqueness. Reverse removes the 0014 recorder entry but deliberately leaves the nullable physical schema, matching authoritative 0013 and the domain contract. Do not begin WU4 until local drift is reconciled. Remap later seven-slice contents around isolated WU2b; retain stacked-to-main, ask-on-risk, and the 400-line budget.

## Open Questions

None.

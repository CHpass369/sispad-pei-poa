# Tasks: Interactive Modular POAU Access by Organizational Unit

## Review Workload Forecast

|Estimate|Risk|Chained|Split|Delivery|Chain|
|---|---|---|---|---|---|
|1,800–2,500 lines|High|Yes|PR1→PR2→PR3→PR4→PR5→PR6→PR7; base `main`, ≤400 each|ask-on-risk|stacked-to-main|

Decision needed before apply: No
Chained PRs recommended: Yes
Chain strategy: stacked-to-main
400-line budget risk: High

Progress: 24/24 complete; 0 pending. Seven stacked-to-main slices are approved; no size exception is requested. `apply-progress` remains authoritative evidence.

### Suggested Work Units

Command prefixes: **B** `../.venv/bin/python -m pytest -n 0`; **F** `npm test -- --watch=false`.

|Unit|Goal|Likely PR|Focused test command|Runtime harness|Rollback boundary|
|---|---|---|---|---|---|
|1|Legacy gates|PR1|**B** `apps/organizacion/tests.py`|`APIClient` read/write matrix|`backend/apps/organizacion/{views.py,tests.py}`|
|2|0013 safety + WU2b repair|PR2: 120 + ≤280 = ≤400|**B** `apps/accounts/tests/test_migration_001{3_poau_scope,4_nullability_repair}.py`|Disposable PostgreSQL fresh/drift/repaired/reverse-reapply; authorized local apply/audit|Freeze 0013; revert only 0014/test; reverse retains nullable physical schema|
|3|Domain validation|PR3|**B** `apps/accounts/tests/{test_user_assignments_v2.py,test_register.py,test_scope_resolver.py,test_access_preview_v2.py}`|`APIClient` preview/save/approve rollback|Assigned `backend/apps/accounts/` hunks|
|4|V2 isolation|PR4|**B** `apps/poau/tests/test_scope_integration.py`|Two-year `APIClient` query|`backend/apps/poau/{views_v2.py,tests/test_scope_integration.py}` hunks|
|5|0015 authority baseline|PR5|**B** `apps/accounts/tests/test_seed_roles_permisos.py`|Clean migrate/reapply; seed parity|`backend/apps/accounts/{migrations/0015_access_authorization_baseline.py,management/commands/seed_roles_permisos.py,tests/test_seed_roles_permisos.py}`|
|6|Metadata/client|PR6|**F** module-config/service specs|`npm start`: registry/preview|`frontend/sispoa/src/app/{core/config,features/admin-usuarios}` files|
|7|Module-first UI|PR7|**F** assignment/dialog/matrix specs|`npm start`: assignment/empty-UO|`frontend/sispoa/src/app/features/{admin-usuarios,sis-poa}` components|

## Phase 1: Legacy Assignment Authorization
- [x] 1.1 **RED:** `organizacion/tests.py`: prove 403 reads and denied-write atomicity in both models.
- [x] 1.2 **GREEN:** `organizacion/views.py`: gate reads/mutations; retain sync.
- [x] 1.3 **REFACTOR:** Share gating; preserve dual-model transactions.

## Phase 2: Migration Safety
- [x] 2.1 **RED:** Prove PE null retention, POAU-only backfill, uniqueness, interruption retries.
- [x] 2.2 **GREEN:** Reconcile model/`0013`: nullable `PROTECT`, `nulls_distinct=False`, atomicity.
- [x] 2.3 **REFACTOR:** Isolate operations; reverse/forward without fake, reset, SQL, or history rewrite.
- [x] 2.4 **RED:** Add `backend/apps/accounts/tests/test_migration_0014_nullability_repair.py`; manufacture recorded-0013/physical-`NOT NULL` drift with `schema_editor`, never SQL; prove fresh/drifted/repaired paths, `null_ok=True`, yearless PE, FK/unique preservation, reverse/reapply convergence.
- [x] 2.5 **GREEN:** Freeze/version `0013` before 0014 and never edit it again; create state-neutral `backend/apps/accounts/migrations/0014_repair_alcance_fiscal_year_nullability.py` using introspection and `schema_editor.alter_field()`.
- [x] 2.6 **REFACTOR/VERIFY:** Prove disposable PostgreSQL first; only after authorization apply local 0014, then read-only audit physical/model/recorder/FK/unique state; reverse removes only 0014 recorder entry and stays nullable.

## Phase 3: Domain-Aware Validation
- [x] 3.1 **RED:** Prove POAU-year rejection, PE nulls, rollback, SELF uniqueness, preview/save parity.
- [x] 3.2 **GREEN:** Apply domain-year policy across serializers, approval, replacement, permissions, resolver.
- [x] 3.3 **REFACTOR:** Share validation/evaluation; retain exactly `capabilities`, `effective_uos`, `modules`.

## Phase 4: V2 Fiscal Isolation
- [x] 4.1 **RED:** After WU2b local proof passes, use real two-year rows to prove invalid/missing UUID rejection and isolation.
- [x] 4.2 **GREEN:** Filter `poau/views_v2.py` scopes and owning-POA year.
- [x] 4.3 **REFACTOR:** Resolve UUID/year once; fail closed.

## Phase 5: Authorization Baseline
- [x] 5.1 **RED:** Prove clean/reapplied 0015 state; grant `FORMULADOR_POAU` `sis_poa.formulate`.
- [x] 5.2 **GREEN:** Add idempotent `backend/apps/accounts/migrations/0015_access_authorization_baseline.py`, dependent on 0014; align seed.
- [x] 5.3 **REFACTOR:** Reuse codes/roles; reject duplicate grants.

## Phase 6: Metadata and Preview Client
- [x] 6.1 **RED:** Prove typed PE/POA registry, reused codes, PRO exclusion, response shape.
- [x] 6.2 **GREEN:** Add `modules.config.ts`; type the preview client.
- [x] 6.3 **REFACTOR:** Reuse DTOs; retain endpoint/unpaginated contract.

## Phase 7: Incremental UI
- [x] 7.1 **RED:** Prove module flow, conditional year, accentless search, canonical IDs, empty state.
- [x] 7.2 **GREEN:** Add flow/panel; incrementally wire dialog/module/matrix.
- [x] 7.3 **REFACTOR:** Remove role-first UI; preserve autocomplete/recent tests.

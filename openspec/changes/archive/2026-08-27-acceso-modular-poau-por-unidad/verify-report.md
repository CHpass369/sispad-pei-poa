```yaml
schema: gentle-ai.verify-result/v1
evidence_revision: sha256:f54047025e179d4cfe7224859ab989657f204c50c4dc698b6356d9097c662561
verdict: pass_with_warnings
blockers: 0
critical_findings: 0
requirements: 14/14
scenarios: 30/30
test_command: "cd backend && ../.venv/bin/python -m pytest -n 0 apps/organizacion/tests.py ; cd backend && ../.venv/bin/python -m pytest -n 0 apps/accounts/tests/test_migration_0013_poau_scope.py apps/accounts/tests/test_migration_0014_nullability_repair.py ; cd backend && ../.venv/bin/python -m pytest -n 0 apps/accounts/tests/test_user_assignments_v2.py apps/accounts/tests/test_register.py apps/accounts/tests/test_scope_resolver.py apps/accounts/tests/test_access_preview_v2.py ; cd backend && ../.venv/bin/python -m pytest -n 0 apps/poau/tests/test_scope_integration.py ; cd backend && ../.venv/bin/python -m pytest -n 0 apps/accounts/tests/test_seed_roles_permisos.py ; cd frontend/sispoa && CHROME_BIN=/snap/bin/chromium npm test -- --watch=false --include='src/app/core/config/modules.config.spec.ts' --include='src/app/features/admin-usuarios/admin-usuarios.service.spec.ts' ; cd frontend/sispoa && CHROME_BIN=/snap/bin/chromium npm test -- --watch=false --include='src/app/features/admin-usuarios/assignment-flow.component.spec.ts' --include='src/app/features/admin-usuarios/usuario-edicion-dialog.component.spec.ts' --include='src/app/features/sis-poa/matriz-poau.component.spec.ts'"
test_exit_code: 0
test_output_hash: sha256:ad8e3a4924a1e1d134324bf5982b83abec3e1ac57b528d3db6c4dcdc41271ef6
build_command: "cd frontend/sispoa && npm run build"
build_exit_code: 0
build_output_hash: sha256:8cdbdfde4841691928b95ee1e980fc79858a09d5f19ab25eda28703bf51997be
```

## Verification Report

**Change**: acceso-modular-poau-por-unidad
**Version**: N/A
**Mode**: Strict TDD; hybrid persistence

### Completeness
| Metric | Value |
|--------|-------|
| Tasks total | 24 |
| Tasks complete | 24 |
| Tasks incomplete | 0 |
| Separately audited prerequisite | Corrective WU3 prerequisite — complete, no task checkbox attributed |

### Build & Tests Execution
**Build**: ✅ Passed
- Command: `cd frontend/sispoa && npm run build`
- Exit: `0`
- Output hash: `sha256:8cdbdfde4841691928b95ee1e980fc79858a09d5f19ab25eda28703bf51997be`
- Angular production build completed; initial total 484.30 kB and admin lazy chunk 379.27 kB.

**Tests**: ✅ 273 passed, 0 failed
| Command | Result | Output hash |
|---|---:|---|
| `cd backend && ../.venv/bin/python -m pytest -n 0 apps/organizacion/tests.py` | 43 passed, exit 0 | `sha256:79a446edacc9916b067bfb7c9392bbea34669682114c3bee6fa370aa7dd3850b` |
| `cd backend && ../.venv/bin/python -m pytest -n 0 apps/accounts/tests/test_migration_0013_poau_scope.py apps/accounts/tests/test_migration_0014_nullability_repair.py` | 7 passed, exit 0 | `sha256:8d46db4ce624876aad46515ea1ecd8879af1f437c2d115445791c039f4b130a9` |
| `cd backend && ../.venv/bin/python -m pytest -n 0 apps/accounts/tests/test_user_assignments_v2.py apps/accounts/tests/test_register.py apps/accounts/tests/test_scope_resolver.py apps/accounts/tests/test_access_preview_v2.py` | 108 passed, exit 0 | `sha256:750ff5ea46e092aa0894bb23bb351f0ffa8114a71e55408b5dd47746c6479e1b` |
| `cd backend && ../.venv/bin/python -m pytest -n 0 apps/poau/tests/test_scope_integration.py` | 42 passed, exit 0 | `sha256:327a08dc38253e39cfdb3871bf8a58d12110f9d69fee8bf9bd966ce4af33963c` |
| `cd backend && ../.venv/bin/python -m pytest -n 0 apps/accounts/tests/test_seed_roles_permisos.py` | 4 passed, exit 0 | `sha256:972b217b096dfda17c8b973787d4545da3fa6b9dd3dc8ce6e38986dddcae1d50` |
| `cd frontend/sispoa && CHROME_BIN=/snap/bin/chromium npm test -- --watch=false --include='src/app/core/config/modules.config.spec.ts' --include='src/app/features/admin-usuarios/admin-usuarios.service.spec.ts'` | 16 passed, exit 0 | `sha256:5d1f6c5be511709c8cb507309b0088b86650c001741d0ea0de645abd793a3216` |
| `cd frontend/sispoa && CHROME_BIN=/snap/bin/chromium npm test -- --watch=false --include='src/app/features/admin-usuarios/assignment-flow.component.spec.ts' --include='src/app/features/admin-usuarios/usuario-edicion-dialog.component.spec.ts' --include='src/app/features/sis-poa/matriz-poau.component.spec.ts'` | 53 passed, exit 0 | `sha256:154ac13ef615e16270b82206ac56c014a5970091814ef69aaea6daf6a7dc16bc` |

Combined test output hash, using the table order above: `sha256:ad8e3a4924a1e1d134324bf5982b83abec3e1ac57b528d3db6c4dcdc41271ef6`.

Additional checks:
| Command | Exit | Output hash | Result |
|---|---:|---|---|
| `cd backend && ../.venv/bin/python manage.py makemigrations --check --dry-run` | 0 | `sha256:8e08b2040ed312079ad7785c9945359a8550f8154f19525c6e0f33551bf856a2` | No changes detected |
| `cd backend && ../.venv/bin/python manage.py check` | 0 | `sha256:7a2e9edc5f0d096c25fb1736b9e97e8438dea9b4ec1470b78934887934ad135d` | 0 issues |
| Targeted `../.venv/bin/ruff check` on changed backend files | 0 | `sha256:82b3e6a6c090a57601d22943bd23fca9218d1031dbe5a7b754092f9a156b4f18` | All checks passed |
| `git diff --check` | 0 | `sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` | Clean |

**Coverage**: ➖ Not available; no configured changed-file coverage tool was detected. No coverage command was run.

### Read-only Schema and Authorization Audit
Command: `cd backend && ../.venv/bin/python manage.py shell` with Django ORM, migration-recorder, physical-schema introspection, and read-only frontend-registry inspection. Exit `0`; output hash `sha256:104b4ac85ae1bab5f86d64934b837c75d62a13aec4a403a85701b3d4485272a4`.

- Applied accounts tail ends exactly at `0013_poau_scope_backfill`, `0014_repair_alcance_fiscal_year_nullability`, and `0015_access_authorization_baseline`; no later unexpected accounts migration is recorded.
- `fiscal_year_id` is nullable in model state and physical PostgreSQL (`null_ok=true`).
- The physical FK targets `gestion_gestionfiscal(id)`.
- `uniq_alcance_usuario_rol_unidad_gestion` is present and unique over `usuario_id, rol_id, unidad_id, fiscal_year_id`.
- Authorization baseline is complete: 39/39 required capabilities, 6/6 required roles, all five required `FORMULADOR_POAU` grants including `sis_poa.formulate`, and no duplicate capability codes, role codes, or M2M grants.
- The module registry contains 44 SIS-PE/SIS-POA capability references; none are missing from the catalog and SIS-PRO is absent.
- `makemigrations --check --dry-run` independently confirmed no pending model migrations.

### Spec Compliance Matrix
| Requirement | Scenario | Passing runtime coverage | Result |
|---|---|---|---|
| Production-Equivalent Preview | Preview proposed access | `test_hypothetical_preview_does_not_persist_assignments` | ✅ COMPLIANT |
| Production-Equivalent Preview | Preview matches saved access | `test_preview_matches_effective_access_after_production_assignment` | ✅ COMPLIANT |
| Production-Equivalent Preview | Empty proposal | `test_empty_proposal_returns_current_unpaginated_effective_access` | ✅ COMPLIANT |
| Preview Response Contract | Response includes all required fields | Preview contract backend test and Angular HTTP response-shape test | ✅ COMPLIANT |
| Module Metadata Registry | Supported registry | `modules.config.spec.ts` registry/catalog assertions plus read-only audit | ✅ COMPLIANT |
| Interactive Assignment Flow | Complete module-first flow | `assignment-flow.component.spec.ts` module-first flow test | ✅ COMPLIANT |
| Interactive Assignment Flow | Search and selection survive reconciliation | Dialog accent-insensitive search and canonical-ID tests | ✅ COMPLIANT |
| Domain-Aware Fiscal-Year Contract | POAU year required | Assignment-flow conditional-year test and backend omitted/null rejection tests | ✅ COMPLIANT |
| Domain-Aware Fiscal-Year Contract | SIS-PE remains yearless | Yearless PE backend tests and conditional-year frontend test | ✅ COMPLIANT |
| Domain-Aware Fiscal-Year Contract | Persisted SIS-PE assignment remains yearless | Yearless preview/save and migration tests | ✅ COMPLIANT |
| Domain-Aware Fiscal-Year Contract | Unit and year mismatch rejected | Assignment and approval atomic rollback tests | ✅ COMPLIANT |
| Single-SELF Constraint | Duplicate SELF assignment rejected | `test_rejects_second_formulator_self_unit_in_same_year` | ✅ COMPLIANT |
| Empty State for Formulators Without POAU | Formulator sees empty state message | Matrix selected-unit non-error empty-state component test | ✅ COMPLIANT |
| Legacy Assignment API Authorization | Read capability enforced | V1 alias list/retrieve capability test | ✅ COMPLIANT |
| Legacy Assignment API Authorization | Denied mutation is atomic | V1 create/update/delete denial and two-model snapshot test | ✅ COMPLIANT |
| V1 POAU Scope Enforcement | User sees only scoped POAUs | V1 unit/year filtering and child/execution isolation tests | ✅ COMPLIANT |
| V1 POAU Scope Enforcement | User with no scope sees nothing | Empty/403 no-scope tests | ✅ COMPLIANT |
| V1 Workflow Action Scope Checks | Action rejected without complete authority | Workflow capability/unit/year state-preservation test | ✅ COMPLIANT |
| V2 Record Fiscal-Year Isolation | Two-year records are isolated | `test_lists_filter_every_resource_by_owning_poa_year` | ✅ COMPLIANT |
| V2 Record Fiscal-Year Isolation | Missing or invalid identifier fails closed | Superuser missing/malformed/unknown UUID test | ✅ COMPLIANT |
| Versioned Authorization Baseline | Clean deployment is complete | 0015 clean apply/reapply test and read-only audit | ✅ COMPLIANT |
| Versioned Authorization Baseline | Reapplication does not duplicate authority | Seed/0015 parity test and duplicate audit | ✅ COMPLIANT |
| Backfill Migration 0013 | Migration creates missing rows | Backfill and yearless-PE preservation test | ✅ COMPLIANT |
| Backfill Migration 0013 | Retry after normalization | Normalization-boundary convergence test | ✅ COMPLIANT |
| Backfill Migration 0013 | Retry after field alteration | Field-alteration-boundary convergence test | ✅ COMPLIANT |
| Backfill Migration 0013 | Retry around uniqueness enforcement | Uniqueness-boundary convergence test | ✅ COMPLIANT |
| Physical Nullability Repair 0014 | Recorded migration drift is repaired | Drift repair/reverse/reapply integration test | ✅ COMPLIANT |
| Physical Nullability Repair 0014 | Data, constraints, and domain rules remain valid | 0014 integration, yearless PE, and POA rejection tests | ✅ COMPLIANT |
| Physical Nullability Repair 0014 | Repair converges safely | 0014 nullable/drift/reapply branches | ✅ COMPLIANT |
| Physical Nullability Repair 0014 | Reverse preserves authoritative nullability | 0014 reverse/reapply test | ✅ COMPLIANT |

**Compliance summary**: 30/30 scenarios compliant; every scenario has a passing runtime covering test.

### Correctness (Static Evidence)
| Requirement | Status | Notes |
|---|---|---|
| Production-Equivalent Preview | ✅ Implemented | Preview uses the shared effective-access evaluator and does not persist proposals. |
| Preview Response Contract | ✅ Implemented | Exactly `capabilities`, `effective_uos`, and `modules`; unpaginated. |
| Module Metadata Registry | ✅ Implemented | Typed SIS-PE/SIS-POA registry; no SIS-PRO or missing catalog reference. |
| Interactive Assignment Flow | ✅ Implemented | Module-first ordering, canonical IDs, preview, and retained legacy detail editing. |
| Domain-Aware Fiscal-Year Contract | ✅ Implemented | POA capability assignments require a matching canonical year; PE-only assignments remain nullable. |
| Single-SELF Constraint | ✅ Implemented | Duplicate role/year SELF assignments reject before replacement. |
| Empty State | ✅ Implemented | Authorized selected unit with no POAU rows gets a non-error status message. |
| Legacy Assignment API Authorization | ✅ Implemented | Separate read/write capability gates preserve transactional synchronization. |
| V1 POAU Scope Enforcement | ✅ Implemented | Capability, effective UO, and fiscal-year constraints cover query/object paths. |
| V1 Workflow Action Scope Checks | ✅ Implemented | `enviar`, `aprobar`, and `rechazar` validate full authority before mutation. |
| V2 Record Fiscal-Year Isolation | ✅ Implemented | Canonical year resolution and owning-POA predicates isolate every V2 resource. |
| Versioned Authorization Baseline | ✅ Implemented | Migration 0015 and the operational seed are additive, idempotent, and preserve custom grants. |
| Backfill Migration 0013 | ✅ Implemented | Deterministic transactional normalization/backfill and convergence checks. |
| Physical Nullability Repair 0014 | ✅ Implemented | State-neutral introspection repair leaves nullable authoritative in reverse. |

### Design Coherence
| Decision | Followed? | Notes |
|---|---|---|
| Nullable CORE FK with capability-aware fiscal policy | ✅ Yes | CORE remains nullable; SIS-POA policy is enforced at assignment boundaries. |
| State-neutral forward-only 0014 repair | ✅ Yes | Historical field metadata, introspection, and `schema_editor.alter_field`; no raw SQL. |
| Reverse does not restore obsolete NOT NULL | ✅ Yes | Migration test and current physical audit confirm it. |
| Versioned 0015 baseline after 0014 | ✅ Yes | Dependency and recorder order are correct. |
| Shared preview/save evaluation and V2 owning-year filter | ✅ Yes | Preview parity and real two-year isolation tests passed. |
| Module-first UI with UI-only metadata | ✅ Yes | Backend remains authority; frontend registry only organizes existing capabilities. |
| Seven reviewable stacked slices | ✅ Yes | Every corrective slice stayed within its authorized 400-line budget; WU7 closed at 393 lines. |
| Accessibility and motion constraints | ✅ Yes | Material labels, fieldset/legend grouping, live status semantics, and reduced-motion styling are present; focused component compilation/tests passed. |

### Strict TDD Evidence Remediation

The previous failed verification report (`sha256:3f6015192db14a0267ce7aa69a93cc32de8951b2abef67f73400c393c88a1f96`) found only 12/24 independently auditable task rows. Apply-progress #943 revision 21+ now contains a dedicated task-level Strict-TDD index for every task. This verification independently checked each row against the referenced test files and reran every listed aggregate final suite. Aggregate evidence is accepted only where its recorded RED, GREEN, triangulation/refactor, and current runtime result together prove the task lifecycle.

| Task | RED evidence audited | GREEN/current runtime audited | Triangulation/refactor evidence | Result |
|---|---|---|---|---|
| 1.1 | WU1 aggregate 10 failed/33 passed; denial/atomicity tests exist | Organization suite 43 passed | Both aliases, reads, and denied writes | ✅ Complete |
| 1.2 | Same WU1 aggregate, permission-gate cases | Organization suite 43 passed | Separate view/assign gates and allowed matrix | ✅ Complete |
| 1.3 | Same WU1 aggregate | Organization suite 43 passed | Shared constants preserve sync transactions | ✅ Complete |
| 2.1 | Interruption RED 1 failed | Migration aggregate 7 passed | Normalization/conflict/duplicate/interruption branches | ✅ Complete |
| 2.2 | WU2 interruption RED | Transactional GREEN passed; aggregate 7 passed | Nullable PROTECT plus transactional rollback | ✅ Complete |
| 2.3 | WU2 interruption RED | Migration aggregate 7 passed | Deferred flush and native named constraint | ✅ Complete |
| 2.4 | Absent-0014 drift RED 1 failed | Drift GREEN passed; aggregate 7 passed | Fresh and physical-drift branches | ✅ Complete |
| 2.5 | Tests preceded production | Migration aggregate 7 passed | Repair/skip paths, exact FK and uniqueness | ✅ Complete |
| 2.6 | Reverse/reapply expectations preceded production | New 0014 tests and aggregate 7 passed | Reverse/reapply convergence | ✅ Complete |
| 3.1 | Five domain-policy cases exposed invalid behavior | Accounts access aggregate 108 passed | Omitted/null, PE yearless, mismatch, SELF, approval | ✅ Complete |
| 3.2 | Same five-case RED | Selected GREEN passed; aggregate 108 passed | Capability-derived policy before writes | ✅ Complete |
| 3.3 | Same five-case RED | Accounts access aggregate 108 passed | Shared validator/evaluator and preview parity | ✅ Complete |
| 4.1 | 9 failed/42 passed, then 16 failed/2 passed | POAU scope suite 42 passed | Two years, six resources, invalid IDs, actions | ✅ Complete |
| 4.2 | Six owning-year predicates failed | POAU scope suite 42 passed | Explicit owning-POA predicates | ✅ Complete |
| 4.3 | Invalid UUIDs bypassed by superuser | POAU scope suite 42 passed | Cached canonical year resolution before bypass | ✅ Complete |
| 5.1 | Three expected failures before 0015 | Seed/migration suite 4 passed | Clean/reapplied completeness | ✅ Complete |
| 5.2 | Same pre-0015 RED | Seed/migration suite 4 passed | Apply/reverse/reapply and seed parity | ✅ Complete |
| 5.3 | Same pre-0015 RED | Seed/migration suite 4 passed | Custom grants and duplicate prevention | ✅ Complete |
| 6.1 | Missing registry import failed compilation | Metadata/client suite 16 passed | PE/POA registry and PRO exclusion | ✅ Complete |
| 6.2 | Missing preview DTO/method failed compilation | Metadata/client suite 16 passed | Proposed and omitted assignments | ✅ Complete |
| 6.3 | Exact URL/fields preceded implementation | Metadata/client suite 16 passed | V2 URL, JSON query, unpaginated shape | ✅ Complete |
| 7.1 | Missing flow/empty-state references failed compilation | UI suite 53 passed | Conditional year, accents, IDs, empty state | ✅ Complete |
| 7.2 | Component/wiring tests preceded production | UI suite 53 passed; build passed | Production-shaped preview and panel contract | ✅ Complete |
| 7.3 | Regression assertions preceded refactor | UI suite 53 passed | Collapsed legacy details and retained behavior | ✅ Complete |
| WU3 prerequisite (not a task) | Stale expectation failed 1 | Two focused cases and 103-test baseline passed | Corrected domain baseline only | ✅ Separately verified |

**Task-level TDD evidence**: 24/24 tasks complete and independently auditable. The prior 12-row documentary blocker is remediated by distinct apply-progress evidence revision `sha256:f54047025e179d4cfe7224859ab989657f204c50c4dc698b6356d9097c662561` plus this independent 273-test rerun.

### TDD Compliance
| Check | Result | Details |
|---|---|---|
| TDD Evidence reported | ✅ | Apply-progress #943 contains a 24-row corrective task index plus the separately labelled WU3 prerequisite. |
| All tasks have tests | ✅ | 24/24 task rows identify existing related test files. |
| RED confirmed (tests exist) | ✅ | 24/24 rows contain recorded pre-GREEN failure evidence; referenced files exist. |
| GREEN confirmed (tests pass) | ✅ | All current referenced suites passed: 273/273 tests. |
| Triangulation adequate | ✅ | Aggregate or isolated evidence covers multiple domain, year, scope, failure, retry, and UI branches for all work units. |
| Safety Net for modified files | ⚠️ | Safety nets are recorded for every work unit, but WU6's pre-change Karma safety command could not launch Chrome; its production build passed and current Chromium suite is green. |

**TDD Compliance**: 5/6 checks fully passed; 1 warning. No incomplete task-level evidence remains.

### Test Layer Distribution
| Layer | Tests | Files | Tools |
|---|---:|---:|---|
| Backend integration | 204 | 9 | pytest + Django/PostgreSQL |
| Frontend unit/HTTP contract | 16 | 2 | Karma + Chromium |
| Frontend component integration | 53 | 3 | Karma + Chromium |
| E2E | 0 | 0 | Not installed/used |
| **Total** | **273** | **14** | |

### Changed File Coverage
Coverage analysis skipped — no configured changed-file coverage tool was detected. This is not a failure under the Strict-TDD verification policy.

### Assertion Quality
| File | Assertion / test | Issue | Severity |
|---|---|---|---|
| `frontend/sispoa/src/app/features/sis-poa/matriz-poau.component.spec.ts` | `observar sin motivo no llega a pegarle al backend` | Karma reports no Jasmine expectations; `HttpTestingController.expectNone` remains a meaningful behavioral request-absence check. | WARNING |
| `frontend/sispoa/src/app/features/sis-poa/matriz-poau.component.spec.ts` | `cancelar la confirmación no borra nada` | Karma reports no Jasmine expectations; `HttpTestingController.expectNone` remains a meaningful behavioral request-absence check. | WARNING |

**Assertion quality**: 0 CRITICAL, 2 WARNING. The change-specific tests contain no tautologies, orphan empty-only assertions, type-only standalone assertions, ghost loops, or tests that avoid production code.

### Quality Metrics
**Linter**: ✅ No errors (targeted Ruff)
**Type checker/templates**: ✅ No errors (Angular production build)
**Django system check**: ✅ 0 issues
**Migration check**: ✅ No changes detected
**Diff whitespace check**: ✅ Clean

### Issues Found
**CRITICAL**: None.

**WARNING**:
1. WU6's historical pre-change Karma safety-net command could not launch Chrome. The pre-change production build passed, and the current Chromium-backed metadata/service suite passed 16/16.
2. Karma emitted two no-expectations warnings for request-absence tests that use `HttpTestingController.expectNone`; both tests passed and do exercise production behavior.
3. Repository-prescribed backend commands emitted the existing `sys.prefix`/`sys.exec_prefix` RuntimeWarning; every backend command exited 0.

**SUGGESTION**:
1. Add explicit Jasmine expectations alongside the two `expectNone` checks so the runner reports counted expectations.
2. Add dedicated automated accessibility checks if this flow later receives browser-level E2E coverage; current accessibility evidence is static plus component compilation/runtime coverage.

### Native Settle Evidence
- outcome: `passed`
- evidence_revision: `sha256:f54047025e179d4cfe7224859ab989657f204c50c4dc698b6356d9097c662561`
- diagnosis: The prior verification's only critical finding was incomplete row-level Strict-TDD documentation for 12/24 tasks. Apply-progress #943 now provides task-level evidence for all 24 tasks; independent reruns confirm 273/273 tests, 14/14 requirements, and 30/30 scenarios. Remaining findings are warnings only.
- harness_disposition: `reused` — focused PostgreSQL/Django and Chromium/Karma suites were rerun independently; the current production build and read-only schema/authorization audit passed.
- cleanup_evidence: No source, test, proposal, spec, design, task, DB, staging, commit, push, PR, review, or Judgment Day change was made. The initial dirty tree was preserved; before report persistence its status hash was `sha256:e54ddf6b257ee305b0cdac49607690ffe85d2dcd55fc1faacb876d3676eb090e` and `git diff --check` remained clean. Test databases/browser runners exited cleanly.
- process_evidence: Parent-owned attempt `sha256:7410d2ce8228e1e24a434a1efef34d223d4365c68a6712eb8f28acae2a15ad64` was neither acquired nor settled by this executor. Verification changed zero implementation lines and did not mutate the attempt budget.

### Final Verdict
**PASS WITH WARNINGS**

All 14 requirements and 30 scenarios are runtime-compliant, all 24 tasks now have independently auditable Strict-TDD evidence, and build/schema/static gates pass. Non-blocking warnings are limited to historical WU6 safety-net availability, two Jasmine expectation-count warnings, and the existing interpreter-path warning.

### Skill Resolution
`paths-injected` — PIP architecture, backend, database, frontend, testing, SIS-POA, work-unit-commits, shared SDD protocol, and Strict-TDD verification guidance were loaded.

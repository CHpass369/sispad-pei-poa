# Archive Report: Interactive Modular POAU Access by Organizational Unit

## Closure

The hybrid SDD change `acceso-modular-poau-por-unidad` was archived on 2026-08-27. Native pre-archive status reported `nextRecommended: archive`, `dependencies.archive: ready`, no blocked reasons, and 24/24 completed tasks. `reviewGate` was structurally absent, so ordinary repository policy applied and no review artifacts were read or created.

## Final State

| Gate | Final result |
|---|---|
| Implementation | Complete across seven stacked-to-main work units |
| Tasks | 24/24 complete; 0 pending |
| Verification | PASS WITH WARNINGS; final native retry settled `complete` |
| Runtime evidence | 273 tests passed, 0 failed; Angular production build passed |
| Compliance | 14/14 requirements and 30/30 scenarios |
| Strict TDD | 24/24 tasks independently auditable after documentary repair of apply-progress #943 revision 21+ |
| Critical findings | 0 |

Canonical final verify-report hash: `sha256:3f5cc2e2c810f38db1684c69ccaf24d5171dfb66895b56584057a33578889a8d`.

The failed verification revision `sha256:3f6015192db14a0267ce7aa69a93cc32de8951b2abef67f73400c393c88a1f96` recorded the earlier 12/24 documentary blocker. That blocker was remediated in apply-progress #943 revision 21+ and independently reverified in final verify-report #1000 revision 3. Any blocked language retained inside intermediate evidence-repair history is not the close state.

## Non-blocking Warnings

1. WU6 historical pre-change Karma safety-net availability.
2. Two Jasmine no-expectations warnings around meaningful `HttpTestingController.expectNone` checks.
3. Existing Python interpreter-path warnings.
4. No configured changed-file coverage tool.

## Schema and Authorization Audit

Final verification recorded migrations through accounts 0015, physical `fiscal_year_id null_ok=True`, the exact GestionFiscal foreign key and named four-field uniqueness, 39/39 required capabilities, 6/6 base roles, all five `FORMULADOR_POAU` grants, and no duplicate authority.

## Specification Synchronization

No canonical OpenSpec specs existed before archive. Each complete new spec was copied mechanically without transformation.

| Domain | Action | Requirements | Scenarios | Canonical path |
|---|---|---:|---:|---|
| `poau-access-preview` | Created | 2 | 4 | `openspec/specs/poau-access-preview/spec.md` |
| `poau-module-metadata` | Created | 5 | 9 | `openspec/specs/poau-module-metadata/spec.md` |
| `poau-v1-scope-hardening` | Created | 7 | 17 | `openspec/specs/poau-v1-scope-hardening/spec.md` |

All source-to-temporary, source-to-canonical, source-to-snapshot, and snapshot-to-archive `diff -r` readbacks were empty.

## Archive Location and Contents

Archive destination: `openspec/changes/archive/2026-08-27-acceso-modular-poau-por-unidad/`.

The archive preserves `proposal.md`, `exploration.md`, all three specs, `design.md`, `tasks.md`, and `verify-report.md`. This report is additive and was created after the byte-identity archive readback. The active change directory no longer exists.

## Post-Archive Native State

The post-archive `gentle-ai sdd-status acceso-modular-poau-por-unidad` readback returned `changeRoot: null`, `nextRecommended: sdd-new`, and `Active OpenSpec change not found`. This is the coherent closed-state sentinel for a command that inspects active changes: the active root is absent while the dated archive and canonical specs are retrievable.

## Engram Traceability

The following full observations were read:

| Observation | Topic or role |
|---:|---|
| #935 | Product-decision lineage (`sdd/acceso-modular-poau-por-unidad/product-decisions`) |
| #936 | Proposal (`sdd/acceso-modular-poau-por-unidad/proposal`; historical project key `chpass369`) |
| #937 | Initial spec summary (`sdd/acceso-modular-poau-por-unidad/spec`; historical project key `chpass369`) |
| #938 | Design (`sdd/acceso-modular-poau-por-unidad/design`) |
| #941 | Tasks (`sdd/acceso-modular-poau-por-unidad/tasks`) |
| #943 | Apply progress revision 21+ (`sdd/acceso-modular-poau-por-unidad/apply-progress`) |
| #973 | Current specification revision (`sdd/acceso-modular-poau-por-unidad/spec`) |
| #1000 | Final verify report revision 3 (`sdd/acceso-modular-poau-por-unidad/verify-report`) |

The final Engram archive report is observation #1003 at topic `sdd/acceso-modular-poau-por-unidad/archive-report`.

The proposal's historical two-PR plan and older six-slice records are planning lineage only. Persisted tasks #941 and final close authority establish seven stacked-to-main work units.

## Preservation

Archive operations changed only authorized OpenSpec paths and this archive report. No implementation or test file was edited; no test, build, migration, database, staging, commit, push, PR, review, or Judgment Day command was run. The repository's unrelated dirty state was preserved.

Pre-archive preservation fingerprints outside `openspec/`:

- Git status: `sha256:d5b426addd36e6b6e6bd314f68888e7d262f091245caae9aef39f7b9b0b4ae1b`
- Unstaged binary diff: `sha256:0cb6da28009d4f13ffcf78f682654f87ecdcfb050839cd7e9f4fecfc7b36d9aa`
- Staged diff: `sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`
- Tracked/untracked content manifest: `sha256:6ac3c9e1a6471d15f420980f09e43d7295311f6487afe9e6e626c00b59ba53fe`

## Result

The SDD cycle is complete with non-blocking warnings. The source of truth now contains all 14 requirements and 30 scenarios, and both OpenSpec and Engram retain the final archive record.

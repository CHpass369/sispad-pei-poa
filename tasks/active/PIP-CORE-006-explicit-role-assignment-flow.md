# TASK PIP-CORE-006: Require explicit roles in the module-first assignment flow

## DOMAIN

`CORE/accounts authorization`

## OBJECTIVE

Prevent the Angular module-first administrator flow from silently choosing a role. Require an explicit compatible role and submit that role with its valid fixed scope and fiscal-year shape.

## CURRENT BEHAVIOR

`assignment-flow.component.ts` selects the first system-compatible role and can replace it with the first role sharing a module capability. The UI presents capability checkboxes although the V2 payload persists only `role_code`, organizational unit, scope, and fiscal year.

## IN SCOPE

- Remove automatic role selection and add an explicit compatible-role choice.
- Reuse the existing fixed-scope policy helper when a role is selected.
- Present the selected role's effective module capabilities as derived, read-only information.
- Add focused Jasmine regression coverage and verify the production build.

## OUT OF SCOPE

- Backend V2 contract changes, canonical authorization-model migration, or legacy cleanup.
- Database models, migrations, records, seeds, or unrelated admin flows.
- Redesign of the complete user administration screen.

## IMPACT

- **Database:** None.
- **API:** None; retain the existing V2 assignment and preview DTOs.
- **Frontend:** The module-first assignment component requires an explicit compatible role, synchronizes fixed scope, and makes capability semantics honest.

## FILES EXPECTED

- `tasks/active/PIP-CORE-006-explicit-role-assignment-flow.md` — task boundary and verification record.
- `frontend/sispoa/src/app/features/admin-usuarios/assignment-flow.component.ts` — explicit-role state and payload validation.
- `frontend/sispoa/src/app/features/admin-usuarios/assignment-flow.component.html` — role selector and derived capability presentation.
- `frontend/sispoa/src/app/features/admin-usuarios/assignment-flow.component.spec.ts` — focused regressions.

## DUPLICATION CHECK / REUSE

Reuse `fixedScopeForRole` from `admin-role-scope.ts`, `MODULES_CONFIG` for module grouping, the role capabilities returned by `AdminUsuariosService`, and the existing `AdminAssignmentInput` DTO. `DUPLICATION_ANALYSIS.md` identifies no equivalent assignment-flow component; no policy map, DTO, endpoint, or capability catalog will be added.

## ACCEPTANCE CRITERIA

- [x] Role order, including `SUPER_ADMIN` first, never selects a role automatically.
- [x] Preview and save remain blocked until an administrator explicitly selects a compatible role.
- [x] Selecting `SUPER_ADMIN` synchronizes `GLOBAL` and the payload contains `SUPER_ADMIN`.
- [x] Capability information is visibly derived/read-only and is not represented as a persisted subset.
- [x] Focused Karma tests and the Angular production build pass.

## TESTS

```bash
cd frontend/sispoa && TMPDIR="$HOME/karma-tmp" CHROME_BIN=/snap/bin/chromium npm test -- --watch=false --browsers=ChromeHeadlessNoSandbox --include='src/app/features/admin-usuarios/assignment-flow.component.spec.ts'
cd frontend/sispoa && npm run build -- --configuration production
```

## RISKS

Filtering must not hide valid cross-module roles. Compatibility remains based on the selected system plus effective capability overlap with the selected module, matching the existing flow's intent without changing backend authority.

## ROLLBACK BOUNDARY

Remove this task record and revert only the three `assignment-flow.component.*` files. No backend, API, database, or other frontend behavior is part of this work unit.

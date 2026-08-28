# TASK PIP-CORE-007: Support the full lifecycle for every role

## DOMAIN AND OBJECTIVE
`CORE/accounts authorization`. Allow authorized administrators to edit, replace capabilities on, and delete every role, including `SUPER_ADMIN` and `es_sistema=true` roles, without deleting live authorization references.

## IN SCOPE
- Remove system-role-only PATCH and capability-replacement rejections.
- Add guarded DELETE to `/api/v2/admin/roles/{id}/` using `accounts.rol.edit`.
- Return HTTP 409 with stable code `role_in_use`, a clear message, and reference counts.
- Show edit, capability, and delete actions for every role under existing actor capabilities.
- Reuse the role dialogs, `adminApiErrorMessage`, and `window.confirm`; add focused tests.

## OUT OF SCOPE
- User assignments, approvals, logout, SIS-PE selectors, sidebar, and POAU preview work.
- Role-code or `es_sistema` changes, deprecated-role administration, or new capabilities.
- Models, migrations, seeds, database records, global formatting, commits, or cleanup.

## IMPACT
- **Database:** None; existing relations and transaction locking only.
- **API:** Detail DELETE returns 204 or `{code,error,references}` with 409; PATCH and capability PUT accept system roles subject to unchanged actor authorization and visibility.
- **Frontend:** Existing Roles UI/dialogs gain full lifecycle behavior and conflict feedback.

## FILES
- `backend/apps/accounts/views_admin.py`, `backend/apps/accounts/tests/test_role_admin_v2.py`.
- `frontend/sispoa/src/app/features/admin-usuarios/admin-usuarios.service{,.spec}.ts`.
- `frontend/sispoa/src/app/features/admin-usuarios/{roles-admin-tab,role-form-dialog,role-capabilities-dialog}.component.{ts,html,spec.ts}`.
- `tasks/active/PIP-CORE-007-all-role-lifecycle.md`.

## SAFEGUARDS AND REUSE
- Lock the role atomically; reject any `Usuario.roles` membership or `AlcanceOrganizacional.rol` row, including inactive history, before delete.
- Pending approval stores no role reference; its role exists only in the request payload. Role-capability M2M rows are owned role configuration.
- `DATA_OWNERSHIP.md` confirms accounts ownership. Static model/migration inspection and `DUPLICATION_ANALYSIS.md` found no parallel lifecycle. Reuse the existing URL, `accounts.rol.edit`, dialogs, error helper, and confirmation pattern.

## TESTS
```bash
cd backend && ../.venv/bin/python -m pytest -n 0 apps/accounts/tests/test_role_admin_v2.py
cd frontend/sispoa && TMPDIR="$HOME/karma-pip-core-007" CHROME_BIN=/snap/bin/chromium npm test -- --watch=false --browsers=ChromeHeadlessNoSandbox --include='src/app/features/admin-usuarios/admin-usuarios.service.spec.ts' --include='src/app/features/admin-usuarios/roles-admin-tab.component.spec.ts' --include='src/app/features/admin-usuarios/role-form-dialog.component.spec.ts' --include='src/app/features/admin-usuarios/role-capabilities-dialog.component.spec.ts'
cd frontend/sispoa && npm run build -- --configuration production
cd backend && ../.venv/bin/python -m ruff check apps/accounts/views_admin.py apps/accounts/tests/test_role_admin_v2.py
git diff --check -- <touched-files>
```

## RISKS AND ROLLBACK
Authorized edits remain intentionally destructive; PostgreSQL row locking prevents concurrent FK-backed assignment during reference checks. Roll back only this task and the listed role lifecycle hunks: DELETE returns to 405 and system roles return to read-only. No migration, seed, assignment-flow, or unrelated dirty work belongs to this unit.

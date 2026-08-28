# Proposal: Interactive Modular POAU Access by Organizational Unit

## Intent

POAU authorization is fragmented: V1 endpoints have zero scope enforcement (any authenticated user sees all POAUs), V2 `gestion_id_param` is never wired so fiscal year filtering doesn't reach querysets, and the admin assignment flow is role-first with no preview of effective access. This change hardens V1 with `CapacidadConScope`, adds a module-based interactive assignment UI with preview, and closes the dual-model synchronization gap.

## Scope

### In Scope
- Frontend module metadata dictionary mapping capabilities → modules → systems (SIS-PE, SIS-POA only)
- `GET /api/v2/admin/preview-access/` endpoint reusing `ScopeResolver` + `listar_capacidades`
- Interactive assignment flow: System → Module → Permissions → Scope → Year → Preview
- V1 POAU hardening: `CapacidadConScope` on `POAUViewSet`, `POAUActividadViewSet`, `EjecucionFisicaViewSet`, `EjecucionFinancieraViewSet`
- V1 POAU queryset filtering by effective UO
- V1 workflow action scope checks (`enviar`, `aprobar`, `rechazar`)
- Wire `gestion_id_param` in V2 ViewSet constructors
- Single-SELF constraint validation in `AsignacionesUsuarioView`

### Out of Scope
- V1 POAU migration to V2 models (deferred, V1 sunset is a separate change)
- PermissionsService Angular cleanup (PR3 follow-up)
- SIS-PRO integration (excluded per product decision)
- Role/profile template editing UI (superadmin-only, existing flow)

## Capabilities

### New Capabilities
- `poau-module-metadata`: Frontend module→capability→system mapping dictionary and interactive assignment UI with preview
- `poau-access-preview`: Backend endpoint that evaluates effective capabilities, UOs, and module visibility for a hypothetical assignment set
- `poau-v1-scope-hardening`: V1 POAU endpoints enforce `CapacidadConScope` + UO queryset filtering

### Modified Capabilities
- None (no existing specs to modify — first SDD change in this project)

## Approach

**Staged into 2 PRs** following Approach 2 from exploration:

**PR1 (~300 lines) — Module Metadata + Preview + Interactive Flow**
- `core/config/modules.config.ts`: module→capability→system mapping
- Rewrite `admin-usuarios/` assignment UI: System→Module→Permissions→Scope→Year
- Backend `GET /api/v2/admin/preview-access/` endpoint (reuses `ScopeResolver` + `listar_capacidades`)
- Single-SELF constraint validation in `AsignacionesUsuarioView`
- Preview panel in assignment UI

**PR2 (~400 lines) — V1 Scope Hardening + V2 Queryset Fix**
- Add `CapacidadConScope` to V1 POAU ViewSets
- Filter V1 POAU queryset by effective UO
- Add scope validation to `POAUActividadViewSet`, `EjecucionFisicaViewSet`, `EjecucionFinancieraViewSet`
- Add role + scope checks to workflow actions
- Wire `gestion_id_param` in V2 ViewSet constructors

## Affected Areas

| Area | Impact | Description |
|------|--------|-------------|
| `features/admin-usuarios/` | Modified | New interactive assignment flow, preview panel |
| `core/config/modules.config.ts` | New | Module→capability→system mapping dictionary |
| `apps/accounts/views_admin.py` | Modified | Preview endpoint, single-SELF validation |
| `apps/accounts/serializers.py` | Modified | Preview request/response serializers |
| `apps/poau/views.py` | Modified | V1 POAU ViewSets: add `CapacidadConScope`, filter queryset |
| `apps/core/permissions.py` | Modified | V1 workflow actions: add scope checks |
| `apps/poau/views_v2.py` | Modified | Wire `gestion_id_param` in constructors |
| `core/services/permissions.service.ts` | Modified (PR3) | Remove hardcoded role checks |

## Risks

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| V1 hardening revokes access for users without `AlcanceOrganizacional` rows | High | Backfill migration: create `AlcanceOrganizacional` rows from existing `AsignacionUsuarioUnidad` data before deploying PR2 |
| Preview endpoint uses different evaluation path than production | Low | Reuse `ScopeResolver` + `listar_capacidades` exactly — same code path |
| `AsignacionUsuarioUnidad` vs `AlcanceOrganizacional` drift | Medium | PR1 validates single-SELF; PR2 documents migration path; full sync is deferred |
| Sidebar capability mismatch (`sis_poa.poau.submit` etc.) | Low | Document as tech debt; does not block this change |

## Rollback Plan

- **PR1**: Revert frontend changes (module config, assignment UI, preview endpoint). No data model changes — clean revert.
- **PR2**: Revert permission classes from V1 ViewSets, remove `gestion_id_param` wiring. If backfill migration was applied, it's additive (new rows) — safe to leave. Users without `AlcanceOrganizacional` will regain access immediately on revert.

## Dependencies

- `AlcanceOrganizacional` model must support fiscal year filtering (already does)
- `ScopeResolver.alcances_vigentes()` and `ScopeResolver.unidades_efectivas()` are stable
- Backfill migration for V1→V2 `AlcanceOrganizacional` rows must be ready before PR2 deploys

## Success Criteria

- [ ] Admin can assign POAU access through System→Module→Permissions→Scope→Year flow
- [ ] Preview endpoint returns identical capabilities/UOs as production endpoints
- [ ] V1 `POAUViewSet` enforces `CapacidadConScope` — unauthorized users get 403
- [ ] V1 POAU queryset returns only UOs the user has scope for
- [ ] V2 `gestion_id_param` is wired in all ViewSet constructors
- [ ] Single-SELF constraint: formulator has exactly one SELF assignment per role
- [ ] Empty state: formulator sees explicit message when UO has no POAU
- [ ] Fiscal year is mandatory for all POAU access assignments (NULL rejected)

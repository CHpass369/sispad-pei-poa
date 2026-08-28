# Exploration: Interactive Modular POAU Access by Organizational Unit

**Change**: `acceso-modular-poau-por-unidad`
**Date**: 2026-08-25
**Scope**: Backend authorization (accounts, poau), Frontend admin assignment flow, Angular sidebar/navigation, system selection

---

## Current State

### Domain Objects (Canonical)

| Object | Model | Location | Key Fields |
|--------|-------|----------|------------|
| **Usuario** | `Usuario(AbstractUser)` | `apps/accounts/models.py` | `email`, `estado`, `activo`, `roles` (M2M) |
| **Rol** | `Rol` | `apps/accounts/models.py` | `codigo`, `capacidades` (M2M), `es_sistema` |
| **Capacidad** | `Capacidad` | `apps/accounts/models.py` | `codigo` (`<sistema>.<dominio>.<accion>`), `sistema` |
| **AlcanceOrganizacional** | `AlcanceOrganizacional` | `apps/accounts/models.py` | `usuario`, `unidad` (FK→UO), `scope_type` (SELF/DESCENDANTS/GLOBAL), `rol`, `fiscal_year`, `activo` |
| **UnidadOrganizacional** | `UnidadOrganizacional` | `apps/organizacion/models.py` | `codigo`, `padre` (FK→self), `gestion` (FK→GestionFiscal), `tipo` |
| **AsignacionUsuarioUnidad** | `AsignacionUsuarioUnidad` | `apps/organizacion/models.py` | `usuario`, `unidad`, `es_responsable_poa`, `gestion` — **legacy model, NOT used by V2 auth** |
| **POAU (V1)** | `POAU` | `apps/poau/models.py` | `unidad` (FK→UO), `gestion` (integer), `codigo`, `estado` |
| **PoAInstitucional (V2)** | `PoAInstitucional` | `apps/poau/models_v2.py` | UUID PK, `gestion` (integer), `codigo`, `estado` — **no unidad at top level** |
| **AccionCortoPlazo (V2)** | `AccionCortoPlazo` | `apps/poau/models_v2.py` | `poa` (FK→PoA), `unidad` (FK→UO, nullable) |
| **Operacion (V2)** | `Operacion` | `apps/poau/models_v2.py` | `accion` (FK), `unidad` (FK→UO, nullable) |
| **GestionFiscal** | `GestionFiscal` | `apps/gestion/models.py` | `anio`, `estado`, `activa` (boolean — the candado) |

### Authorization Architecture

**Two coexisting permission systems:**

1. **Legacy (V1)** — `apps/core/permissions.py`: Role-based classes (`IsSuperAdmin`, `IsPlanificador`, `WorkflowPermission`, `InstitutionPermission`). Hardcoded role code tuples. `WorkflowPermission` uses `TRANSICIONES_WORKFLOW` dict. `InstitutionPermission` checks `asignaciones_unidad` — the **legacy model**.

2. **V2 (ADR-003)** — `apps/accounts/permissions.py`: `CapacidadConScope` combines atomic capability check (`tiene_capacidad`) with organizational scope resolution (`ScopeResolver`). `ScopeResolver` reads `AlcanceOrganizacional` with `gestion_id` filtering. Fail-closed: no `AlcanceOrganizacional` → no access.

**Scope Resolution** (`apps/accounts/services_scope.py`):
- `ScopeResolver.alcances_vigentes(user, gestion_id)` — active scopes filtered by fiscal year
- `ScopeResolver.unidades_efectivas(user, gestion_id)` — BFS expansion of SELF/DESCENDANTS, GLOBAL shortcircuit
- `ScopeResolver.puede_operar(user, unidad_id, gestion_id)` — single UO check

### API Surface

| Layer | Endpoint Pattern | Scope Enforcement |
|-------|-----------------|-------------------|
| **V1 POAU** | `/api/v1/poau/poaus/` | `CandadoSisPoaMixin` (gestion lock only), NO scope filtering |
| **V1 POAU actions** | `/api/v1/poau/poaus/{id}/enviar/` | State check only, no role/scope validation |
| **V1 Activity** | `/api/v1/poau/actividades/` | No permission class at all |
| **V1 Ejecucion** | `/api/v1/poau/ejecucion-fisica/` | No permission class at all |
| **V2 PoA** | `/api/v2/sis-poa/poas/` | `CapacidadConScope` + UO filtering via `acciones__unidad_id__in` |
| **V2 Accion** | `/api/v2/sis-poa/acciones/` | `CapacidadConScope` + UO filtering + `_autorizar_uo_destino` on create/update |
| **V2 Operacion** | `/api/v2/sis-poa/operaciones/` | `CapacidadConScope` + nullable UO fallback to `accion.unidad` |
| **V2 Actividad** | `/api/v2/sis-poa/actividades/` | `CapacidadConScope` + filters via `operacion__accion__unidad_id__in` |
| **V2 Tarea** | `/api/v2/sis-poa/tareas/` | `CapacidadConScope` + filters via `actividad__operacion__accion__unidad_id__in` |
| **V2 Programacion** | `/api/v2/sis-poa/programaciones/` | `CapacidadConScope` + filters via `actividad__operacion__accion__unidad_id__in` |
| **Admin assignments** | `/api/v2/admin/users/{id}/assignments/` | `TieneCapacidad('accounts.alcance.assign')` — no scope check on write |

### Frontend Admin Assignment Flow

**Current Angular flow** (role-first, `admin-usuarios/`):
1. Admin selects user from list (filterable by UO, role, system, state)
2. Clicks into user detail → Assignments tab
3. Adds rows: each row = `{ role, organizational_unit, scope_type, fiscal_year }`
4. `PUT /admin/users/{id}/assignments/` — replaces ALL replaceable-role assignments atomically

**`admin-role-scope.ts`** defines fixed scope defaults per role code:
- `SUPER_ADMIN` → GLOBAL
- `JEFE_PE` → GLOBAL
- `JEFE_POA` → GLOBAL
- `SECRETARIO_MUNICIPAL` → DESCENDANTS
- `DIRECTOR` → DESCENDANTS
- `FORMULADOR_POAU` → SELF

**CapabilitiesService** (`core/services/capabilities.service.ts`): Loads from `/api/v2/me/capabilities/`. Returns flat `capabilities[]` array and `alcances[]`. Sidebar and route guards consume this.

### Sidebar & Navigation Capability Bundles

The sidebar (`layout/sidebar/sidebar.component.ts`) defines capability arrays per module:

**POAU V2 (sis-poa/poaus route)**:
```typescript
['sis_poa.poau.view', 'sis_poa.poau.create', 'sis_poa.poau.edit',
 'sis_poa.poau.submit', 'sis_poa.poau.review', 'sis_poa.poau.approve']
```

**POAU V1 (poau route — legacy)**:
```typescript
['sis_poa.programacion.view', 'sis_poa.programacion.edit', 'sis_poa.formulate']
```

**V2 POA ViewSet** (`views_v2.py`):
```python
CAPACIDADES_POR_VIEWSET = {
    'PoAViewSet': ('sis_poa.poa.view', 'sis_poa.poa.edit'),
    'AccionViewSet': ('sis_poa.poau.view', 'sis_poa.poau.edit'),
    ...
}
```

**`PermissionsService`** (Angular `core/services/permissions.service.ts`) still has hardcoded role checks:
```typescript
canAccessPOAU(): boolean {
    return this.hasAnyRole(['superadmin', 'tecnico_admin', 'jefe_ue', 'director']);
}
```
This is **inconsistent** with the V2 capability-driven model. The backend never checks role codes directly for V2 endpoints.

### System Selection

`SistemasSeleccionComponent` filters visible systems by capabilities:
- SIS-PE: `['sis_pe.instrumento.read']`
- SIS-POA: `['sis_poa.formulate']`

SIS-PRO is excluded from the capabilities filter (per the prior finding).

---

## Affected Areas

### Backend

| File | Why Affected |
|------|-------------|
| `apps/accounts/models.py` — `AlcanceOrganizacional` | May need multiple SELF constraint validation |
| `apps/accounts/permissions.py` — `CapacidadConScope` | Preview endpoint reuse; UO-reparent validation for V1 |
| `apps/accounts/services_scope.py` — `ScopeResolver` | Preview endpoint; fiscal year passthrough |
| `apps/accounts/views_admin.py` — `AsignacionesUsuarioView` | Multiple SELF validation; preview API endpoint |
| `apps/poau/views.py` — `POAUViewSet`, `POAUActividadViewSet`, etc. | V1 scope enforcement (add `CapacidadConScope`, filter queryset) |
| `apps/poau/views_v2.py` — `PoAViewSet`, etc. | Fiscal year gap in `get_queryset`; nullable UO reparent check |
| `apps/core/permissions.py` | V1 POAU actions need workflow + scope |
| `apps/organizacion/models.py` | `AsignacionUsuarioUnidad` — clarify relationship to `AlcanceOrganizacional` |

### Frontend

| File | Why Affected |
|------|-------------|
| `features/admin-usuarios/` (all assignment components) | New interactive flow: System→Module→Permissions→Scope→Year→Preview |
| `features/admin-usuarios/admin-role-scope.ts` | Module metadata source |
| `features/admin-usuarios/admin-usuarios.service.ts` | Preview API call; multiple SELF support |
| `core/services/permissions.service.ts` | Remove hardcoded role checks, use capabilities only |
| `layout/sidebar/sidebar.component.ts` | Module→capability mapping metadata |
| `features/sistemas/sistemas-seleccion.component.ts` | Module listing per system |
| `core/guards/capability.guard.ts` | May need module-scoped guards |

---

## Security Gap Analysis

### V1 Gaps (Critical)

| Path | Gap | Severity |
|------|-----|----------|
| `POAUViewSet` (list) | No `CapacidadConScope` — any authenticated user sees all POAUs for the gestion | **HIGH** |
| `POAUViewSet` (create/update/delete) | Only `CandadoSisPoaMixin` (gestion lock) — no UO scope | **HIGH** |
| `POAUActividadViewSet` | No permission class at all | **HIGH** |
| `EjecucionFisicaViewSet` | No permission class at all | **HIGH** |
| `EjecucionFinancieraViewSet` | No permission class at all | **HIGH** |
| `POAUViewSet.enviar/aprobar/rechazar` | State transition only — no role or scope check | **MEDIUM** |
| `por_unidad` action | Uses `AsignacionUsuarioUnidad` (legacy) instead of `AlcanceOrganizacional` | **MEDIUM** |

### V2 Gaps (Medium)

| Path | Gap | Severity |
|------|-----|----------|
| `PoAViewSet.get_queryset` | `gestion_id_param` not wired — fiscal year not filtered in queryset (permission checks it but queryset returns cross-year data) | **MEDIUM** |
| `AccionViewSet.perform_update` | Reparenting to null UO allowed without scope check | **LOW** |
| `OperacionViewSet.perform_create` | Nullable UO → falls back to parent validation, but `accion` could be null at create time | **LOW** |
| `ActividadViewSet` | No `perform_create/perform_update` UO validation — relies entirely on queryset filter | **MEDIUM** |
| `TareaViewSet` | Same as ActividadViewSet | **MEDIUM** |
| All V2 ViewSets | `gestion_id_param` not passed to `CapacidadConScope` constructor | **MEDIUM** |
| `AsignacionesUsuarioView.put` | No validation for multiple SELF assignments; no fiscal_year consistency check | **LOW** |

### Cross-cutting Gaps

| Gap | Detail |
|-----|--------|
| `PermissionsService` hardcoded roles | Angular `canAccessPOAU()`, `canEdit()`, `canApprove()` use role codes instead of capabilities — inconsistent with V2 backend |
| Sidebar capability bundles vs backend | Sidebar lists `sis_poa.poau.submit`, `sis_poa.poau.review`, `sis_poa.poau.approve` but V2 ViewSet uses `sis_poa.poau.view`/`sis_poa.poau.edit` — mismatch |
| Module metadata absent | No central registry mapping capabilities → modules → systems. Sidebar hardcodes arrays inline |
| `AsignacionUsuarioUnidad` vs `AlcanceOrganizacional` | Two UO-assignment models coexist. V1 `por_unidad` uses the legacy one. V2 scope uses the new one. Not synchronized |

---

## Approaches

### Approach 1: Metadata Grouping Only (Module Dictionary)

Add a frontend-only module→capability mapping dictionary. No backend changes for grouping. Interactive flow builds on existing V2 APIs.

**Pros**: Zero backend changes for module display. Fastest to ship. No risk of dual authorization truth.
**Cons**: No backend validation that a module's capabilities form a coherent set. Module boundaries can drift from sidebar.
**Effort**: Low (~150 lines frontend)

### Approach 2: Module Metadata + Preview Endpoint + V1 Hardening

1. Add module metadata dictionary (frontend).
2. Add `GET /api/v2/admin/preview-access/` endpoint that accepts `(user_id, assignments[])` and returns effective capabilities, UOs, and module visibility — reusing `ScopeResolver` + `listar_capacidades`.
3. Harden V1 critical paths with `CapacidadConScope` + queryset filtering.
4. Normalize the interactive assignment flow on the frontend.

**Pros**: Preview gives admins a safety net. V1 hardening closes real security gaps. Module metadata stays frontend-only.
**Cons**: V1 hardening touches many files. Preview endpoint is new surface.
**Effort**: Medium (~350-400 lines total, fits one review budget if staged)

### Approach 3: Full V2 Migration of POAU + Interactive Flow

Migrate V1 POAU endpoints to use V2 models/views. Build the interactive flow exclusively on V2.

**Pros**: Eliminates dual-model confusion. Single authorization path.
**Cons**: V1 POAU is still actively used (sidebar shows both V1 and V2 POAU routes). Migration requires data backfill. Exceeds single review budget.
**Effort**: High (~800+ lines, requires chained PRs)

### Approach 4: V2-Only Interactive Flow + V1 Freeze

Build the interactive assignment flow targeting V2 endpoints only. Freeze V1 POAU (no new features, mark as deprecated). Leave V1 security gaps as documented tech debt.

**Pros**: Clean scope. V2 has strong scope enforcement. No V1 touch risk.
**Cons**: V1 security gaps remain. Users still see V1 routes. Mixed UX.
**Effort**: Medium (~300 lines, fits one review budget)

---

## Recommendation

**Approach 2 (staged into 2 PRs)**:

**PR 1 — Module Metadata + Preview Endpoint (~300 lines)**
- Frontend: `core/config/modules.config.ts` — module→capability→system mapping
- Frontend: Rewrite assignment UI to use System→Module→Permissions→Scope→Year flow
- Backend: `GET /api/v2/admin/preview-access/` endpoint
- Backend: Validate multiple SELF constraint in `AsignacionesUsuarioView`
- Frontend: Preview panel showing effective access before save

**PR 2 — V1 Scope Hardening (~400 lines)**
- Add `CapacidadConScope` to `POAUViewSet` and action endpoints
- Filter V1 POAU queryset by effective UO
- Add scope validation to `POAUActividadViewSet`, `EjecucionFisicaViewSet`, `EjecucionFinancieraViewSet`
- Add role + scope checks to workflow actions (`enviar`, `aprobar`, `rechazar`)
- Wire `gestion_id_param` in V2 ViewSet constructors

This avoids duplicating authorization truth. Modules stay as UI metadata. The preview endpoint reuses the same backend evaluator the production endpoints use. V1 hardening uses the same `CapacidadConScope` + `ScopeResolver` primitives.

---

## Product Decisions Required

These questions must be answered before proposal:

1. **Multiple SELF assignments**: Should a formulator be allowed multiple explicit SELF assignments (e.g., "covering for someone on leave"), or strictly one SELF per role? The current `AlcanceOrganizacional` model allows multiple rows with the same user+role. Need business rule.

2. **Module granularity**: The sidebar currently shows POAU as a single module. Should the interactive flow break POAU into sub-modules (e.g., "Formulación POAU", "Seguimiento POAU", "Recursos POAU"), or treat it as one capability group?

3. **V1 lifecycle**: Should the V1 POAU paths be deprecated (sunset date) or kept as a parallel interface? This determines whether PR 2 hardens V1 or just documents it as tech debt.

4. **Fiscal year in assignment**: Should the `fiscal_year` field on `AlcanceOrganizacional` be required for POAU assignments (so a formulator's access auto-expires next year), or optional (current behavior — NULL means all years)?

5. **Cross-UO visibility**: When a formulator logs in and their UO has no POAU yet, should they see an empty state with a "Create POAU" button, or should the system pre-create a POAU skeleton?

---

## Staged Boundaries (Review Budget)

| Stage | PR | Files Changed | ~Lines | Risk |
|-------|-----|--------------|--------|------|
| Module metadata + Preview | PR1 | `modules.config.ts`, assignment components, `views_admin.py`, `serializers.py` | 300 | Low |
| V1 scope hardening | PR2 | `poau/views.py`, `core/permissions.py`, `poau/views_v2.py` | 400 | Medium |
| PermissionsService cleanup | PR3 | `permissions.service.ts`, `capability.guard.ts` | 100 | Low |
| V1 sunset (optional) | PR4 | `sidebar.component.ts`, route config | 50 | Low |

---

## Risks

1. **Dual authorization model drift**: V1 uses role-based (`core/permissions.py`), V2 uses capability+scope (`CapacidadConScope`). If PR 2 hardens V1 with `CapacidadConScope`, V1 endpoints suddenly require `AlcanceOrganizacional` rows for all users — existing users without scopes lose access.
2. **`AsignacionUsuarioUnidad` vs `AlcanceOrganizacional`**: The legacy model is used by V1 `por_unidad` and `InstitutionPermission`. Adding scope enforcement to V1 may require syncing or migrating existing `AsignacionUsuarioUnidad` data.
3. **Sidebar capability mismatch**: Sidebar lists capabilities not in V2 `CAPACIDADES_POR_VIEWSET` (e.g., `sis_poa.poau.submit`, `sis_poa.poau.review`). These may be phantom capabilities that exist in the `Capacidad` table but have no backend enforcement.
4. **Fiscal year nullable gap**: `AlcanceOrganizacional.fiscal_year` is nullable (NULL = all years). If the product decides to require it for POAU, existing NULL rows need backfill migration.
5. **Preview endpoint false confidence**: If the preview endpoint uses a different evaluation path than production, it could give incorrect previews. It must reuse `ScopeResolver` + `listar_capacidades` exactly.

---

## Named Evidence / Tests Needed

| Evidence | What to Verify |
|----------|---------------|
| `test_scope_integration.py` | Already covers V2 Accion/Operacion/Actividad/Tarea scope. Need to add: V1 POAU scope, workflow action scope, fiscal year filtering |
| `CapacidadConScope` constructor call sites | Verify `gestion_id_param` is wired in all V2 ViewSets |
| `PermissionsService` call sites | Find all Angular components using hardcoded role checks (`canAccessPOAU`, `canEdit`, etc.) |
| `AsignacionUsuarioUnidad` usage | Map all consumers of the legacy model to plan migration |
| `TRANSICIONES_WORKFLOW` | Verify all POAU workflow transitions have scope checks (currently role-only) |
| Sidebar capability arrays | Cross-reference with `Capacidad` table entries and `CAPACIDADES_POR_VIEWSET` |

---

## Key Learnings

1. The V2 authorization (`CapacidadConScope` + `ScopeResolver`) is well-designed with fail-closed semantics and BFS descendant expansion, but `gestion_id_param` is not wired in any V2 ViewSet constructor — fiscal year filtering works at the permission level but not at the queryset level.
2. V1 POAU endpoints have no scope enforcement at all — `POAUActividadViewSet` and `EjecucionFisica/FinancieraViewSet` have zero permission classes.
3. Two UO-assignment models coexist (`AsignacionUsuarioUnidad` legacy + `AlcanceOrganizacional` V2) and are not synchronized — V1 `por_unidad` uses the legacy model while V2 scope uses the new one.
4. The Angular `PermissionsService` still has hardcoded role checks (`canAccessPOAU()`) that are inconsistent with the V2 capability-driven model, creating a parallel authorization path in the frontend.
5. The sidebar defines capability arrays inline with no central module→capability registry, and some listed capabilities (`sis_poa.poau.submit`, `sis_poa.poau.review`) may not map to any backend enforcement.

# POAU Access Safety Specification

## Purpose

Define capability, unit, fiscal-year, deployment, and migration safety for POAU access.

## Requirements

### Requirement: Legacy Assignment API Authorization

`/api/v1/asignaciones-usuario-unidad/` SHALL require `accounts.alcance.view` for reads and `accounts.alcance.assign` for creates, updates, and deletes.

#### Scenario: Read capability enforced

- GIVEN an authenticated user lacks `accounts.alcance.view`
- WHEN the user lists or retrieves legacy assignments
- THEN the request returns 403 Forbidden

#### Scenario: Denied mutation is atomic

- GIVEN a user can read but lacks `accounts.alcance.assign`
- WHEN the user attempts any legacy assignment mutation
- THEN the request returns 403 Forbidden
- AND neither legacy assignments nor canonical scopes change

### Requirement: V1 POAU Scope Enforcement

V1 POAU, activity, and execution endpoints SHALL enforce the action capability plus effective organizational unit and fiscal year.

#### Scenario: User sees only scoped POAUs

- GIVEN a user has valid scope for unit A in one fiscal year
- WHEN POAU records are queried
- THEN only records for that unit and year are returned

#### Scenario: User with no AlcanceOrganizacional sees nothing

- GIVEN a user has no effective scope
- WHEN a list is requested
- THEN an empty result is returned without exposing other units

### Requirement: V1 Workflow Action Scope Checks

Workflow actions `enviar`, `aprobar`, and `rechazar` MUST validate their action capability, unit, and fiscal year atomically.

#### Scenario: Action rejected without complete authority

- GIVEN any required capability, unit scope, or fiscal year does not match
- WHEN a workflow action is requested
- THEN it is denied and the POAU state does not change

### Requirement: V2 Record Fiscal-Year Isolation

V2 POAU endpoints MUST use a canonical fiscal-year UUID to filter both effective scopes and the actual records' owning POA year.

#### Scenario: Two-year records are isolated

- GIVEN a user has scopes and real V2 records in two fiscal years
- WHEN records are requested with one fiscal year's UUID
- THEN only records whose owning POA belongs to that fiscal year are returned

#### Scenario: Missing or invalid identifier fails closed

- GIVEN a V2 POAU request omits or supplies an invalid fiscal-year UUID
- WHEN the request is evaluated
- THEN the request is rejected and no records are returned

### Requirement: Versioned Authorization Baseline

Feature-required atomic capabilities and base-role grants MUST be reproducible on a clean deployment through versioned state, reusing existing codes and roles. `FORMULADOR_POAU` SHALL include `sis_poa.formulate`.

#### Scenario: Clean deployment is complete

- GIVEN an empty supported database is deployed
- WHEN versioned state is applied
- THEN required existing capabilities and base roles are present
- AND `FORMULADOR_POAU` can formulate POAU

#### Scenario: Reapplication does not duplicate authority

- GIVEN capability codes and base roles already exist
- WHEN deployment state is reapplied
- THEN no duplicate capability, role, or grant is created

### Requirement: Backfill Migration for AlcanceOrganizacional

Migration `accounts.0013_poau_scope_backfill` MUST normalize and backfill deterministically, enforce mandatory POAU years and uniqueness, and safely converge after interruption at every operation boundary.

#### Scenario: Migration creates missing rows

- GIVEN valid legacy assignments lack canonical scopes
- WHEN migration 0013 completes
- THEN matching year-safe scopes exist without duplicates

#### Scenario: Retry after normalization

- GIVEN execution stops after normalization and before field alteration
- WHEN migration 0013 is retried
- THEN it converges without data loss or duplicate scopes

#### Scenario: Retry after field alteration

- GIVEN execution stops after field alteration and before uniqueness enforcement
- WHEN migration 0013 is retried
- THEN final field and uniqueness state is correct and scopes remain valid

#### Scenario: Retry around uniqueness enforcement

- GIVEN execution stops while uniqueness enforcement is being recorded
- WHEN migration 0013 is retried
- THEN the constraint exists once and valid scopes remain unchanged

### Requirement: Forward-Only Physical Nullability Repair

A supported database that records `accounts.0013_poau_scope_backfill` as applied while migration and model state declare `fiscal_year` nullable but the physical column retains stale `NOT NULL` MUST be repaired through later versioned state. Nullable SHALL remain authoritative, and acceptance MUST include physical schema evidence equivalent to `null_ok=true`; migration-recorder and model-state evidence alone SHALL NOT suffice.

#### Scenario: Recorded migration drift is repaired

- GIVEN accounts 0013 is recorded as applied and state declares the field nullable
- AND the physical `fiscal_year_id` column still rejects null
- WHEN the versioned repair is applied
- THEN physical schema evidence confirms that the column accepts null

#### Scenario: Data, constraints, and domain rules remain valid

- GIVEN the drifted database contains valid scopes and constraints
- WHEN repair completes and assignments are subsequently validated
- THEN existing rows and constraints remain valid and yearless SIS-PE scopes can persist
- AND SIS-POA assignments without a required year remain rejected at assignment boundaries

#### Scenario: Repair converges safely

- GIVEN the physical column is already nullable or a prior repair attempt reached that state
- WHEN the versioned repair is applied or convergence is evaluated again
- THEN the column remains nullable without changing valid rows or duplicating constraints

#### Scenario: Reverse preserves authoritative nullability

- GIVEN the versioned repair has made the physical column nullable
- WHEN the repair is reversed
- THEN the obsolete `NOT NULL` condition is not restored
- AND valid yearless SIS-PE scopes remain persistable

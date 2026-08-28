# POAU Module Metadata and Assignment Specification

## Purpose

Define module-driven assignment behavior while preserving the established organizational-unit selector contract.

## Requirements

### Requirement: Module Metadata Registry

The system SHALL map SIS-PE and SIS-POA modules to existing capability codes and MUST NOT create duplicate capabilities or expose SIS-PRO.

#### Scenario: Supported registry

- GIVEN the capability catalog is available
- WHEN module metadata is loaded
- THEN SIS-PE and SIS-POA modules reference existing capability codes
- AND SIS-PRO is absent

### Requirement: Interactive Assignment Flow

The UI SHALL replace role-first assignment with System → Module → Permissions → Organizational Unit → Scope → applicable year → Preview, while preserving current unit search and selected-ID behavior.

#### Scenario: Complete module-first flow

- GIVEN an administrator selects a system and module
- WHEN permissions, unit, scope, applicable year, and preview are confirmed
- THEN the submitted assignment contains the selected canonical identifiers

#### Scenario: Search and selection survive reconciliation

- GIVEN unit autocomplete contains searchable names, codes, and accents
- WHEN the administrator filters and selects a unit
- THEN matching behavior remains case- and accent-insensitive
- AND preview and submission preserve that unit's canonical ID

### Requirement: Domain-Aware Fiscal-Year Contract

Frontend and backend SHALL require a canonical fiscal-year UUID for assignments granting POAU capabilities, but MUST accept an omitted or null fiscal year for SIS-PE-only assignments that have no POAU year semantics. Persisted SIS-PE-only assignments with a null fiscal year MUST remain valid, readable, and usable after deployment or migration and MUST NOT receive a backfilled, inferred, or synthetic fiscal year.

#### Scenario: POAU year required

- GIVEN an assignment grants a POAU capability
- WHEN no fiscal-year UUID is submitted
- THEN frontend submission is blocked and backend validation rejects the request

#### Scenario: SIS-PE remains yearless

- GIVEN an assignment grants only SIS-PE capabilities
- WHEN its fiscal year is omitted or null
- THEN frontend and backend accept the domain-valid assignment

#### Scenario: Persisted SIS-PE assignment remains yearless

- GIVEN a persisted SIS-PE-only assignment has `fiscal_year=null` before deployment or migration
- WHEN deployment or migration completes and its access is evaluated
- THEN the assignment remains valid, readable, and usable for SIS-PE authorization
- AND `fiscal_year` remains null without an inferred, backfilled, or synthetic POAU fiscal year

#### Scenario: Unit and year mismatch rejected

- GIVEN approval or assignment references a unit from one fiscal year and another fiscal-year UUID
- WHEN the request is validated
- THEN it is rejected and approval state, roles, and scopes remain unchanged

### Requirement: Single-SELF Constraint

When POAU access is assigned, each formulator MUST have exactly one SELF assignment per role and fiscal year.

#### Scenario: Duplicate SELF assignment rejected

- GIVEN a formulator already has a SELF assignment for a role and fiscal year
- WHEN another unit is submitted for that same role and year
- THEN the atomic request is rejected without changing assignments

### Requirement: Empty State for Formulators Without POAU

The UI SHALL display an explicit empty state when the selected authorized unit has no POAU records.

#### Scenario: Formulator sees empty state message

- GIVEN a formulator's authorized unit has no POAU records
- WHEN its POAU view is opened
- THEN a non-error empty-state message is shown

# POAU Access Preview Specification

## Purpose

Define a read-only preview of effective modular access before assignments are saved.

## Requirements

### Requirement: Production-Equivalent Preview

`GET /api/v2/admin/preview-access/` SHALL evaluate production-shaped assignments through the same authorization rules as saved access and MUST NOT persist the proposal.

#### Scenario: Preview proposed access

- GIVEN an authorized administrator supplies a user and proposed assignments
- WHEN the preview endpoint is called
- THEN it returns the effective capabilities, organizational units, and visible modules
- AND no assignment or scope is changed

#### Scenario: Preview matches saved access

- GIVEN a valid proposal has been previewed
- WHEN the same proposal is saved
- THEN its effective capabilities and organizational units match the preview

#### Scenario: Empty proposal

- GIVEN assignments are omitted or empty
- WHEN preview is requested
- THEN the user's current effective access is returned without modification

### Requirement: Preview Response Contract

The response MUST be unpaginated and contain exactly `capabilities`, `effective_uos`, and `modules` as its top-level fields.

#### Scenario: Response includes all required fields

- GIVEN a valid preview request
- WHEN the response is produced
- THEN each capability identifies its code, name, system, and module
- AND each effective organizational unit identifies its canonical ID, code, and name

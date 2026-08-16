# Architecture Decision Records (ADR)

Un **Architecture Decision Record (ADR)** es un documento corto que registra una decisión de arquitectura importante, su contexto, las alternativas consideradas y sus consecuencias. Los ADR se escriben cuando la decisión se establece — no como anticipación — y se conservan de forma permanente para que el equipo entienda *por qué* el sistema es como es, sin depender de la memoria.

## Registro de ADR

Este directorio es el registro canónico de nuevas decisiones de arquitectura del repositorio. Los ADR del refactor SISPOA→PIP viven en `docs/refactor-pip/ADR/` y los del plan maestro PIP-GAMS en `docs/pip_gams/adr/`; se listan abajo para referencia y no se reubican.

| ID | Título | Estado | Ruta |
|---|---|---|---|
| ADR-001 | PIP root platform | Aceptado | `docs/refactor-pip/ADR/ADR-001-pip-root-platform.md` |
| ADR-002 | SIS-POA bounded context | Aceptado | `docs/refactor-pip/ADR/ADR-002-sis-poa-bounded-context.md` |
| ADR-003 | PostgreSQL schemas | Aceptado | `docs/refactor-pip/ADR/ADR-003-postgresql-schemas.md` |
| ADR-004 | Articulation model | Aceptado | `docs/refactor-pip/ADR/ADR-004-articulation-model.md` |
| ADR-005 | Budget inside SIS-POA | Aceptado | `docs/refactor-pip/ADR/ADR-005-budget-inside-sis-poa.md` |
| ADR-006 | Shared organizational structure | Aceptado | `docs/refactor-pip/ADR/ADR-006-shared-organizational-structure.md` |
| ADR-007 | Multiyear model | Aceptado | `docs/refactor-pip/ADR/ADR-007-multiyear-model.md` |
| ADR-008 | Instrument versioning | Aceptado | `docs/refactor-pip/ADR/ADR-008-instrument-versioning.md` |
| ADR-009 | Modular monolith | Aceptado | `docs/refactor-pip/ADR/ADR-009-modular-monolith.md` |
| ADR-010 | SISPOA to PIP migration | Aceptado | `docs/refactor-pip/ADR/ADR-010-sispoa-to-pip-migration.md` |
| ADR-001 | Base única | Aceptado | `docs/pip_gams/adr/ADR-001-base-unica.md` |
| ADR-002 | API V2 | Aceptado | `docs/pip_gams/adr/ADR-002-api-v2.md` |
| ADR-003 | IAM | Aceptado | `docs/pip_gams/adr/ADR-003-iam.md` |
| ADR-004 | Migración | Aceptado | `docs/pip_gams/adr/ADR-004-migracion.md` |
| ADR-005 | Preinversión SIS-PRO | Aceptado | `docs/pip_gams/adr/ADR-005-preinversion-sispro.md` |
| ADR-011 | Gobernanza de desarrollo | Aceptado | `docs/adr/ADR-011-gobernanza-de-desarrollo.md` |

## Nuevas decisiones

Las decisiones nuevas se registran aquí como **ADR-011+** usando [ADR_TEMPLATE.md](ADR_TEMPLATE.md). Reglas:

- Un ADR por decisión, una decisión por ADR.
- Registrar solo decisiones efectivamente establecidas, nunca decisiones ficticias o propuestas de código que no exista.
- Si un ADR queda obsoleto, marcarlo como *Superseded por ADR-XXX* en su estado; no reescribir el historial.

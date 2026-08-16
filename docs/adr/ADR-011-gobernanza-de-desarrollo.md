# ADR-011: Gobernanza de desarrollo

## TITLE

Capa de gobernanza de desarrollo en el repositorio (AGENTS.md, docs/architecture/, tasks/, .opencode/, ADR).

## STATUS

Aceptado

## CONTEXT

El repositorio PIP-GAMS es un sistema maduro: el refactor SISPOA→PIP completó sus 10 fases (`docs/refactor-pip/FINAL_REPORT.md`), con ~213 tablas en 9 esquemas, ~220 endpoints, 1252 tests de backend y una base Angular 21 con 32 features. Sin embargo, no existe gobernanza de desarrollo:

- No hay `AGENTS.md` con reglas operativas; cada sesión de agente parte de cero o reinventa convenciones.
- No hay `skills/`, `agents/` ni `commands/` en `.opencode/`; el conocimiento de dominio no es reutilizable entre sesiones.
- No hay sistema formal de tareas (`tasks/`); el trabajo se realiza sin plan, scope o criterios de aceptación verificables.
- La documentación de arquitectura es rica en `docs/refactor-pip/` y `docs/pip_gams/`, pero no está referenciada desde reglas operativas ni sincronizada con un inventario AS-IS verificado.
- No existe CI/CD y hay fallas operativas conocidas (doble prefijo `/api/v1/api/v1` en features de organizacion, imports rotos en `core/validators.py`, targets rotos en el Makefile) que no tienen canal de registro formal.

## DECISION

Adoptar una capa de gobernanza versionada en el repositorio, compuesta por:

- `AGENTS.md` — reglas universales de desarrollo (SEARCH BEFORE CREATE, PLAN BEFORE BUILD, SCOPE CONTROL, NO OPPORTUNISTIC REFACTORING, DATABASE, CONTRACTS, DONE, FINAL REPORT, COMMITS, REFERENCIAS).
- `docs/architecture/` — inventario arquitectónico AS-IS verificado + TO-BE + límites de dominio (DOMAIN_BOUNDARIES) + propiedad de datos (DATA_OWNERSHIP) + contratos de integración (INTEGRATION_CONTRACTS) + mapa del sistema (PIP_SYSTEM_MAP) + roadmap, referenciando `docs/refactor-pip/` sin duplicarlo.
- `tasks/` — sistema formal de tareas: template obligatorio (`tasks/TASK_TEMPLATE.md`), estados backlog → active → completed, cierre vía `/task-close`, deuda en `tasks/technical-debt/`.
- `.opencode/{skills,agents,commands}` — conocimiento de dominio, roles especializados y comandos de desarrollo asistido.
- `docs/adr/` — registro canónico de ADR (índice + template); los ADR 001-010 del refactor permanecen en `docs/refactor-pip/ADR/` y los del plan maestro en `docs/pip_gams/adr/`, referenciados desde el índice sin reubicación.

Este ADR no modifica código funcional; su alcance es documentación y configuración. El código solo se toca a través de tareas formales registradas en `tasks/`.

## ALTERNATIVES

- **(a) Fusionar la gobernanza en `docs/refactor-pip/`** — rechazado: mezcla el registro histórico del refactor con reglas operativas vigentes; el histórico es un documento de cierre, no un marco de trabajo.
- **(b) Solo `AGENTS.md`, sin skills/agents/commands** — rechazado: resuelve las reglas generales pero el conocimiento de dominio (matrices PAD, cadena presupuestaria, esquemas PostGIS) seguiría reinventándose en cada sesión.
- **(c) No hacer nada** — rechazado: continuaría la deriva — bugs sin canal formal, convenciones inconsistentes entre sesiones, contexto reiniciado en cada tarea.

## CONSEQUENCES

**Positivas**

- Arquitectura versionada y referenciada desde las reglas operativas; los agentes cargan contexto por tarea.
- Trabajo delimitado por tareas con scope, criterios de aceptación y final report.
- Deuda y hallazgos con canal de registro (`tasks/backlog/`, `tasks/technical-debt/`).
- Auditoría de dominio: cada módulo consultado tiene referencias a su documentación.

**Negativas**

- Dos capas documentales (`docs/refactor-pip/` y `docs/architecture/`) que deben mantenerse sincronizadas. Mitigación: `docs/architecture/` referencia y no duplica el contenido del refactor; regla explícita de no duplicación.
- Costo de mantenimiento continuo de `tasks/` y `.opencode/`. Mitigación: templates y comandos que hacen el ciclo de vida explícito y barato.

## MIGRATION IMPACT

Nulo sobre datos y código: este ADR no altera esquema, endpoints ni frontend. Los bugs detectados en la auditoría (doble prefijo, validadores muertos, targets del Makefile, FKs de gestión fiscal, cutover de techos, cadena operativa) se registran como tareas en `tasks/backlog/` y se ejecutan en fases posteriores, cada una con su propia tarea formal.

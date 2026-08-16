# PIP

PIP es una Plataforma Integral de Planificación modular (GAM Sacaba). El repositorio implementa cuatro dominios:

| Dominio | Alcance |
|---|---|
| **CORE** | Identidad, organización, periodos, catálogos, normativa, territorio, workflow, documentos, auditoría |
| **SIS-PE** | Planificación estratégica: PGDES/PDESA, PAD, PEI, instrumentos, articulación |
| **SIS-POA** | Planificación operativa: POA/POAU, presupuesto, techos, distribuciones, asignaciones, seguimiento — techos/distribuciones/asignaciones son de SIS-POA, no sistemas independientes |
| **SIS-PRO** | Ciclo del proyecto: cartera, preinversión ITCP/EDTP, ejecución |

## SEARCH BEFORE CREATE

Antes de crear cualquier entity, model, table, DTO, interfaz, enum, servicio, repository, controller, endpoint, component, helper, validator o catálogo: buscar un equivalente primero (grep, codegraph, docs/architecture/DUPLICATION_ANALYSIS.md). Preferir **REUSE → EXTEND → LOCAL REFACTOR** antes que DUPLICATE.

Procedimiento:

1. Search entity / model existente.
2. Search tabla existente.
3. Search DTO / schema existente.
4. Search servicio / repository existente.
5. Search controller / endpoint existente.
6. Search component / vista existente.
7. Search enum / constantes existentes.
8. Search catálogo existente.
9. Determinar equivalencia semántica (mismo concepto de dominio, aunque el nombre difiera).
10. Reutilizar; si no hay equivalente, documentar la decisión en la tarea.

## PLAN BEFORE BUILD

Toda tarea no trivial comienza por análisis. Identificar: dominio afectado, archivos a tocar, dependencias, impacto en base de datos, impacto en API, impacto en frontend, tests afectados. El plan se registra en la tarea (tasks/) antes de escribir código.

## SCOPE CONTROL

No modificar módulos ajenos a la tarea salvo necesidad demostrable. El scope de cada tarea está definido en sus secciones IN SCOPE / OUT OF SCOPE; respetarlo.

## NO OPPORTUNISTIC REFACTORING

No hacer refactorizaciones adyacentes a la tarea. La deuda detectada se documenta (tasks/technical-debt/ o docs/architecture/DUPLICATION_ANALYSIS.md), se propone como TASK y se ejecuta en su propia tarea.

## DATABASE

PostgreSQL es la fuente estructural de verdad. No duplicar catálogos. No crear tablas sin buscar equivalentes (ver SEARCH BEFORE CREATE). Toda alteración de esquema vía migraciones Django existentes. No renombrar ni borrar tablas sin tarea aprobada (recordatorio: el renombrado masivo del 15-08-2026 ya rompió queries externas).

## CONTRACTS

Frontend y backend mantienen contratos explícitos:

- **API V1**: legado, con Sunset 2027-01-01.
- **API V2**: por dominios `/api/v2/{platform,core,catalogos,geo,integracion,auditoria,sis-pe,sis-poa,budget,sis-pro,me}/`.

Prohibido el patrón de doble prefijo: ApiService ya antepone `/api/v1`; las rutas de features no deben repetirlo.

## DONE

Una tarea solo termina cuando aplica todo lo siguiente:

- Compila (backend y frontend).
- Tests relevantes pasan.
- Lint pasa.
- Type-check pasa.
- Migraciones válidas.
- Contratos coinciden (frontend ↔ backend).
- Sin errores introducidos.
- Scope respetado.

## FINAL REPORT

Toda tarea termina mostrando: archivos modificados, archivos creados, migraciones, endpoints, tests ejecutados, riesgos, deuda detectada, trabajo pendiente.

## COMMITS

Conventional commits con scope:

- `feat(core)`, `feat(sis-pe)`, `feat(sis-poa)`, `feat(sis-pro)`
- `fix(...)`, `refactor(...)`, `test(...)`, `docs(...)`, `chore(...)`, `perf(...)`

Sin push automático, sin reescribir historial.

## REFERENCIAS

- `docs/architecture/PIP_SYSTEM_MAP.md` — mapa del sistema
- `docs/architecture/DOMAIN_BOUNDARIES.md` — límites de dominio
- `docs/architecture/DATA_OWNERSHIP.md` — propiedad de datos
- `docs/architecture/INTEGRATION_CONTRACTS.md` — contratos de integración
- `tasks/` — tareas formales
- `.opencode/skills/` — conocimiento de dominio
- `.opencode/agents/` — roles especializados
- `.opencode/commands/` — comandos (incluye /task-close)

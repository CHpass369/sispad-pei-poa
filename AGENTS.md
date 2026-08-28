# PIP — instrucciones del repositorio

Monorepo de la Plataforma Integral de Planificación del GAM Sacaba: backend Django/DRF en `backend/` y frontend Angular en `frontend/sispoa/`.

## Gobernanza durable

- `opencode.json` ya inyecta este archivo, `docs/architecture/PIP_SYSTEM_MAP.md` y `docs/architecture/DOMAIN_BOUNDARIES.md`; consultar `DATA_OWNERSHIP.md`, `INTEGRATION_CONTRACTS.md` y `DUPLICATION_ANALYSIS.md` cuando una tarea cruce dominios. No repetirlos en planes locales.
- Ownership: CORE no depende de negocio; SHARED es el único escritor de catálogos/codificación; SIS-PE, SIS-POA y SIS-PRO solo escriben tablas propias y se integran mediante contratos. `gestion`, `budget`, `poau`, recursos, techos, asignaciones, reformas y seguimiento pertenecen a SIS-POA; `budget` es V2 canónico y `techos`/`presupuesto` son legacy.
- Antes de crear modelo, tabla, migración, DTO, serializer, endpoint, servicio, componente, interfaz, enum o catálogo, buscar equivalencia semántica en código y `DUPLICATION_ANALYSIS.md`. Preferir **REUSE → EXTEND → LOCAL REFACTOR**; documentar por qué no existe equivalente.
- Toda tarea no trivial debe registrar antes su dominio, alcance, archivos, impacto DB/API/frontend y tests en `tasks/` o en el artefacto de cambio autorizado. Respetar IN/OUT OF SCOPE; deuda adyacente se registra, no se refactoriza oportunistamente.
- PostgreSQL/PostGIS es la verdad estructural. Cambiar esquema solo mediante migraciones Django; no duplicar catálogos ni renombrar/eliminar tablas sin tarea aprobada. El renombrado masivo de 2026-08-15 rompió consumidores externos.
- API V1 (`/api/v1/`) es legacy, Sunset `2027-01-01`; código nuevo usa V2 por dominio. `ApiService` ya antepone `/api/v1`: una feature V1 no debe repetir el prefijo. Mantener contrato explícito frontend↔backend.
- Preservar cambios ajenos: inspeccionar `git status` y diffs antes de editar; no usar restauraciones, staging masivo ni reescritura de historial sobre un árbol sucio. Commits convencionales con scope; no hacer push automático.

## Entorno y límites ejecutables

- Python 3.14 y el virtualenv viven en `.venv/` en la raíz; desde `backend/` usar `../.venv/bin/python`. Django/DRF están fijados en `backend/requirements.txt` (Django 6.0.7, DRF 3.17.1).
- Angular 21 usa Node 22 en CI y `frontend/sispoa/package-lock.json`; instalar con `npm ci`, no regenerar el lock sin cambio de dependencias.
- `.env` está en la raíz y Make lo carga. `.env.example` usa host/nombre de contenedor (`pip-postgres`, `gams_sis_poa`), mientras CI usa PostgreSQL/PostGIS local y `gams_pip`: ajustar el entorno, no copiar esos valores como contrato de datos.
- `pytest.ini` usa `config.settings`, PostgreSQL/PostGIS y `-n auto --dist loadscope`; las pruebas de migración o depuración determinista deben usar `-n 0`. La suite completa es costosa.
- Ruff solo bloquea el subconjunto configurado en `backend/pyproject.toml`; no limpiar deuda ignorada fuera de alcance.
- No existe target Angular de lint aunque `package.json` declare `npm run lint`. El gate frontend verificado de CI es el build de producción, que también ejecuta compilación TypeScript/templates.

## Comandos verificados

```bash
# Preparación desde la raíz
python3.14 -m venv .venv
.venv/bin/python -m pip install -r backend/requirements.txt
(cd frontend/sispoa && npm ci)

# Backend desde la raíz; la suite completa requiere PostgreSQL + PostGIS
make migrate
make test-backend
make lint
(cd backend && ../.venv/bin/python manage.py makemigrations --check --dry-run)

# Test backend enfocado y determinista
(cd backend && ../.venv/bin/python -m pytest -n 0 <ruta_o_nodo>)

# Frontend desde la raíz
make test-frontend      # TMPDIR dedicado + ChromeHeadlessNoSandbox
make build-frontend    # build production con baseHref=/pip/
```

CI ejecuta, en este orden por job: backend `python -m pytest -q` y `python -m ruff check .`; frontend `npm ci` y `npm run build`. No hay deploy automático.

Una entrega solo se cierra con tests relevantes, lint disponible, build/type-check, migraciones válidas y contratos coherentes. El informe final debe indicar archivos, migraciones, endpoints, pruebas ejecutadas, riesgos, deuda y pendientes.

## Reanudación activa: `acceso-modular-poau-por-unidad`

**Estado verificado: 2026-08-26.** Autoridad: `openspec/changes/acceso-modular-poau-por-unidad/tasks.md` para secuencia/estado, `specs/*/spec.md` para comportamiento y Git+código actual para realidad. `proposal.md` y partes de `design.md` conservan un split antiguo de dos PR: no sustituyen las seis unidades stacked-to-main de `tasks.md` (presupuesto de 400 líneas, ask-on-risk). Todo el directorio `openspec/` está actualmente sin seguimiento.

- `tasks.md` marca 1.1–4.2 y deja 5.1–6.3 pendientes, pero WU1–WU4 **no están aceptadas como seguras**: sus hunks siguen mezclados en un árbol ampliamente sucio y existen bloqueos confirmados.
- WU2: `/api/v1/asignaciones-usuario-unidad/` conserva CRUD autenticado sin capacidad administrativa explícita; sus mutaciones sincronizan `AlcanceOrganizacional`, por lo que permiten cambiar el scope canónico desde la ruta legacy.
- WU1: `fiscal_year` pasó a obligatorio globalmente, pero clientes CORE/SIS-PE versionados aún envían `null`; aprobación tampoco valida que UO y gestión coincidan. Definir el contrato por dominio antes de migrar esos clientes.
- WU3: `gestion_id` llega a `ScopeResolver`, pero los querysets V2 no filtran explícitamente el año real del registro; el test actual solo prueba propagación al resolver y no aislamiento con datos de dos gestiones.
- Seeds: las capacidades atómicas y roles base nuevos dependen de `seed_roles_permisos`, no de una migración versionada. La DB local las contiene, pero `FORMULADOR_POAU` carece de `sis_poa.formulate`; no asumir paridad de despliegue.
- Migración `accounts.0013_poau_scope_backfill`: está aplicada en la DB local y su archivo sigue sin seguimiento. Es `atomic = False`; no existe prueba de interrupción/reinicio entre normalización, `AlterField` y constraint.
- Hay seis commits frontend recientes hasta HEAD `243c656`. Ese último commit toca `admin-usuarios.module.ts` y `usuario-edicion-dialog.component.{ts,html,spec.ts}`; reconciliar esos cuatro archivos con WU6 antes de reemplazar el flujo role-first.

**Próxima acción segura:** no iniciar WU5/WU6. Primero resolver los bloqueos anteriores con pruebas RED enfocadas, separar WU1–WU4 de cambios ajenos bajo el presupuesto de revisión y volver a auditar migración/seed en un estado reproducible.

```bash
cd backend
../.venv/bin/python -m pytest -n 0 apps/accounts/tests/test_migration_0013_poau_scope.py apps/accounts/tests/test_scope_resolver.py
../.venv/bin/python -m pytest -n 0 apps/organizacion/tests.py apps/accounts/tests/test_user_assignments_v2.py
../.venv/bin/python -m pytest -n 0 apps/poau/tests/test_scope_integration.py
../.venv/bin/python -m pytest -n 0 apps/accounts/tests/test_access_preview_v2.py apps/accounts/tests/test_seed_roles_permisos.py
```

Después de aceptar backend, continuar WU5/WU6 con los comandos focales registrados en `tasks.md`; no duplicar aquí su checklist.

<!-- gitnexus:start -->
# GitNexus — Code Intelligence

This project is indexed by GitNexus as **sispad-pei-poa** (16383 symbols, 32864 relationships, 300 execution flows). Use the GitNexus MCP tools to understand code, assess impact, and navigate safely.

> Index stale? Run `node .gitnexus/run.cjs analyze` from the project root — it auto-selects an available runner. No `.gitnexus/run.cjs` yet? `npx gitnexus analyze` (npm 11 crash → `npm i -g gitnexus`; #1939).

## Always Do

- **MUST run impact analysis before editing any symbol.** Before modifying a function, class, or method, run `impact({target: "symbolName", direction: "upstream"})` and report the blast radius (direct callers, affected processes, risk level) to the user.
- **MUST run `detect_changes()` before committing** to verify your changes only affect expected symbols and execution flows. For regression review, compare against the default branch: `detect_changes({scope: "compare", base_ref: "main"})`.
- **MUST warn the user** if impact analysis returns HIGH or CRITICAL risk before proceeding with edits.
- When exploring unfamiliar code, use `query({search_query: "concept"})` to find execution flows instead of grepping. It returns process-grouped results ranked by relevance.
- When you need full context on a specific symbol — callers, callees, which execution flows it participates in — use `context({name: "symbolName"})`.
- For security review, `explain({target: "fileOrSymbol"})` lists taint findings (source→sink flows; needs `analyze --pdg`).

## Never Do

- NEVER edit a function, class, or method without first running `impact` on it.
- NEVER ignore HIGH or CRITICAL risk warnings from impact analysis.
- NEVER rename symbols with find-and-replace — use `rename` which understands the call graph.
- NEVER commit changes without running `detect_changes()` to check affected scope.

## Resources

| Resource | Use for |
|----------|---------|
| `gitnexus://repo/sispad-pei-poa/context` | Codebase overview, check index freshness |
| `gitnexus://repo/sispad-pei-poa/clusters` | All functional areas |
| `gitnexus://repo/sispad-pei-poa/processes` | All execution flows |
| `gitnexus://repo/sispad-pei-poa/process/{name}` | Step-by-step execution trace |

## CLI

| Task | Read this skill file |
|------|---------------------|
| Understand architecture / "How does X work?" | `.claude/skills/gitnexus/gitnexus-exploring/SKILL.md` |
| Blast radius / "What breaks if I change X?" | `.claude/skills/gitnexus/gitnexus-impact-analysis/SKILL.md` |
| Trace bugs / "Why is X failing?" | `.claude/skills/gitnexus/gitnexus-debugging/SKILL.md` |
| Rename / extract / split / refactor | `.claude/skills/gitnexus/gitnexus-refactoring/SKILL.md` |
| Tools, resources, schema reference | `.claude/skills/gitnexus/gitnexus-guide/SKILL.md` |
| Index, status, clean, wiki CLI commands | `.claude/skills/gitnexus/gitnexus-cli/SKILL.md` |

<!-- gitnexus:end -->

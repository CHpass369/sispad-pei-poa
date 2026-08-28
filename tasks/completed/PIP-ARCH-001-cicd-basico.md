# TASK PIP-ARCH-001: Pipeline CI/CD básico

## DOMINIO

`core/infra`

## OBJECTIVE

Introducir un pipeline mínimo de CI/CD versionado en el repositorio que ejecute los gates de calidad existentes (tests backend, build frontend) en cada cambio, sin deploy automático.

## CONTEXT

Auditoría ETAPA A (2026-08-16): el repositorio no tiene CI/CD (`backend/`, `frontend/`, `infra/` están en el repo; no existe `.github/` ni otra config de CI). El repo sí tiene los gates definidos: pytest 1252 tests (`pytest.ini` con `-n auto --dist loadscope`, pytest-django, pytest-xdist), frontend Angular 21 con 252 tests Karma/Jasmine, ruff para lint. Sin pipeline, los gates dependen de la disciplina local de cada desarrollador/agente y las regresiones llegan a `main`.

## CURRENT BEHAVIOR

- No existe `.github/workflows/` ni config equivalente.
- Cada cambio se valida solo localmente (si acaso); `main` no tiene gate automático.

## EXPECTED BEHAVIOR

- Existe un workflow (por ejemplo, `.github/workflows/ci.yml`) que, en cada PR/push a ramas de integración:
  1. Instala el backend (Python + dependencias).
  2. Ejecuta el gate de tests: `cd backend; python -m pytest -q` (con xdist según pytest.ini).
  3. Ejecuta el gate de frontend: `cd frontend/sispoa; npm ci && npm run build` (build de producción).
  4. (Opcional) Ejecuta lint: `cd backend; ruff check .`
- El workflow falla y bloquea si cualquier gate falla.
- Se puede ejecutar manualmente (`workflow_dispatch`).

## IN SCOPE

- [ ] Crear `.github/workflows/ci.yml` (o equivalente) con los gates mínimos.
- [ ] Fijar versiones de Python/Node compatibles con el stack actual (Python 3.14, Django 6.0; verificar Node para Angular 21).
- [ ] Documentar en la tarea cómo se cachean dependencias (pip/npm) para mantener el tiempo razonable.

## OUT OF SCOPE

- Deploy automático a servidores (producción, staging, docker-compose).
- Migraciones automáticas en entornos reales.
- Análisis de cobertura, sonar u otros gates adicionales (se proponen como tareas futuras si aplica).
- Refactor de tests para hacerlos "CI-compatibles" salvo necesidad demostrable.

## INVARIANTS

- Los gates reflejan los comandos locales reales (misma config que pytest.ini y scripts del repo).
- No se cambia el flujo de desarrollo local (make dev, docker-compose) por el pipeline.

## DATABASE IMPACT

`ninguno` (el CI usa base de datos de prueba; PostgreSQL vía servicio de CI o sqlite según conveniencia de los tests — verificar `settings_test_sqlite.py` existente)

## API IMPACT

`ninguno`

## FRONTEND IMPACT

`ninguno`

## FILES EXPECTED

- `.github/workflows/ci.yml` — crear: pipeline mínimo
- Posible `docs/architecture/CI_CD.md` o nota en `tasks/` con el diseño del pipeline — solo si aporta valor; evitar docs huérfanas

## DEPENDENCIES

`ninguna`

## ACCEPTANCE CRITERIA

- [ ] Existe un workflow versionado en el repo que ejecuta: `cd backend; python -m pytest -q` y `cd frontend/sispoa; npm ci && npm run build` (y lint opcional).
- [ ] El workflow se dispara en PR y push a ramas de integración y es manualmente ejecutable.
- [ ] El workflow es ejecutable localmente con act (u otra herramienta) o la sintaxis se valida contra el schema de GitHub Actions; no se requiere merge para probarlo.
- [ ] No introduce código funcional ni cambia el flujo local.

## TESTS

```bash
# Verificación local de los mismos gates que el pipeline ejecutará:
cd backend; python -m pytest -q
cd frontend/sispoa; npm ci && npm run build
cd backend; ruff check .
# Sintaxis del workflow (si act disponible):
act -l
```

## RISKS

Medio. Riesgo principal: los tests locales asumen servicios (PostGIS, Redis, MinIO) que el runner de CI no tiene; mitigación: evaluar `settings_test_sqlite.py` (existe) o servicios de CI con Postgres+PostGIS antes de fijar el job. Riesgo: tiempos largos de build; mitigación: cacheo de dependencias.

## ROLLBACK

- Revert del/los commit(s): `git revert <commit>`.
- El workflow solo actúa sobre CI; revertir no afecta runtime ni datos.

## FINAL REPORT

Cerrada 2026-08-16.

**Archivos creados (1):** `.github/workflows/ci.yml` (93 líneas) — triggers `pull_request` + `push` (main, integrate/**) + `workflow_dispatch`; 2 jobs:
- `backend` (ubuntu-latest): servicio `postgis/postgis:17-3.4` (misma imagen que docker-compose), setup-python **3.13** (real del repo: `backend/.venv/pyvenv.cfg` → CPython 3.13.11, no 3.14 como asumía la tarea), cache pip, `pip install -r requirements.txt`, gate `python -m pytest -q`
- `frontend` (ubuntu-latest): setup-node **22** (Angular 21.2 sin .nvmrc/engines), cache npm, `npm ci`, gate `npm run build`
- Lint ruff **omitido** y documentado: ruff no está en requirements.txt ni instalado en el venv → gate lint requiere tarea futura (versionar ruff + config)

**Gates ejecutados localmente (mismos comandos del workflow):** `pytest -q` → 1252 passed (5m59s); `npm run build` → build producción OK (10.7s).

**Servicios requeridos en CI:** PostgreSQL+PostGIS vía service container (pytest.ini → `config.settings` → postgis, TEST.template=template_postgis). `settings_test_sqlite.py` NO se usó: su propio docstring lo restringe (apps geo requieren PostGIS). Credenciales del service = valores de ejemplo, nunca secrets.

**Validación:** YAML ok (`yaml.safe_load`); `act` no instalado localmente (no blocker; sintaxis estándar de GitHub Actions, key `on` entre comillas).

**Commits:** `26c134c`.

**Riesgos:** medio — la suite en CI creará N test DBs vía template PostGIS (mismo comportamiento que local); tiempos de build mitigados con cache pip/npm.

**Deuda detectada:** (1) ruff sin versionar → gate lint ausente (proponer tarea: agregar ruff + config y habilitar job); (2) sin deploy automático por diseño (OUT OF SCOPE); (3) revisar si se desean secrets reales para la DB de CI a futuro.

---

**Corrección posterior (2026-08-21).** El dato de Python de esta tarea era incorrecto. Se leyó `backend/.venv`, que era un venv huérfano: el `Makefile` y `.claude/launch.json` siempre usaron el de la raíz (`../.venv/bin/python`). El intérprete real del repo es **CPython 3.14.4** (`.venv/pyvenv.cfg`), así que la suposición original de 3.14 era la correcta y la "corrección" a 3.13 la invirtió. `ci.yml` quedó fijando `python-version: '3.13'` durante cinco días, testeando en una versión distinta a la de desarrollo. Corregido a `'3.14'`; `backend/.venv` fue eliminado.

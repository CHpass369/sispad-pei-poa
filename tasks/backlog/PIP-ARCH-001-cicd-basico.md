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

Completar al cerrar con `/task-close`: archivos creados, gates ejecutados en CI (si hubo merge), tiempo del pipeline, servicios requeridos, riesgos y deuda detectada.

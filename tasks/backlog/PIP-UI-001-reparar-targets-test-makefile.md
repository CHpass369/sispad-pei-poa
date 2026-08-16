# TASK PIP-UI-001: Reparar targets de testing del Makefile

## DOMINIO

`core/infra` (tooling) — impacto `ui`

## OBJECTIVE

Reparar los targets `test-backend` y `test-frontend` del Makefile raíz para que ejecuten los comandos reales de testing, sin depender de contenedores que no tienen las herramientas (frontend = nginx sin npm) y sin contradecir la configuración de pytest.ini.

## CONTEXT

Auditoría ETAPA A (2026-08-16). `Makefile` (raíz):

- Línea 56, `test-backend`: `docker compose exec backend python -m pytest apps/ -v` — ejecuta SOLO `apps/` y sin `-n auto --dist loadscope` que fija `pytest.ini` (pytest-xdist); además omite config/tests fuera de apps.
- Línea 59, `test-frontend`: `docker compose exec frontend npm test -- --watch=false` — el contenedor `frontend` sirve el build (nginx) y NO tiene npm instalado → el target está roto de forma permanente.

Los comandos locales reales y verificados:

- Backend: `cd backend; python -m pytest` (respeta `pytest.ini` con `-n auto --dist loadscope`).
- Frontend: `cd frontend/sispoa; npm test -- --watch=false`.

## CURRENT BEHAVIOR

- `make test-backend` corre pytest solo sobre `apps/` sin xdist (ignora `pytest.ini` para addopts en la parte de `-n`) → más lento y no cubre la config completa.
- `make test-frontend` falla: `docker compose exec frontend npm ...` → npm no existe en el contenedor frontend (nginx).

## EXPECTED BEHAVIOR

- `make test-backend` ejecuta el gate backend real: `cd backend; python -m pytest` (usa pytest.ini con xdist).
- `make test-frontend` ejecuta el gate frontend real: `cd frontend/sispoa; npm test -- --watch=false`.
- Opcionalmente `make lint` sigue usando ruff (`cd backend; ruff check .`).

## IN SCOPE

- [ ] Corregir el target `test-backend` para ejecutar `cd backend; python -m pytest` (heredando pytest.ini).
- [ ] Corregir el target `test-frontend` para ejecutar `cd frontend/sispoa; npm test -- --watch=false`.
- [ ] Verificar que ambos targets corren OK en el entorno local.

## OUT OF SCOPE

- Cambiar docker-compose (agregar npm al contenedor frontend) — alineado con NO tocar infra fuera de necesidad; la solución es local-first.
- Cambiar pytest.ini o los tests.
- Migrar la suite frontend a otro runner (Jest, etc.).

## INVARIANTS

- `pytest.ini` (addopts `-n auto --dist loadscope`) se mantiene como fuente de verdad para la ejecución de tests backend.
- Los targets siguen siendo invocables con `make test-backend` / `make test-frontend` desde la raíz.

## DATABASE IMPACT

`ninguno`

## API IMPACT

`ninguno`

## FRONTEND IMPACT

`ninguno` (solo tooling del Makefile)

## FILES EXPECTED

- `Makefile` — modificar: targets `test-backend` (línea 56) y `test-frontend` (línea 59)

## DEPENDENCIES

`ninguna`

## ACCEPTANCE CRITERIA

- [ ] `make test-backend` ejecuta `cd backend; python -m pytest` y termina en verde (suite completa).
- [ ] `make test-frontend` ejecuta `cd frontend/sispoa; npm test -- --watch=false` y termina en verde.
- [ ] `make lint` (opcional) sigue funcionando o queda documentado su estado.
- [ ] Ningún otro target del Makefile se modifica.

## TESTS

```bash
make test-backend    # desde la raíz; debe correr la suite completa (xdist vía pytest.ini)
make test-frontend   # desde la raíz; debe correr Karma/Jasmine sin watch
```

## RISKS

Bajo. Riesgo: dependencias locales (Python, npm) con versiones distintas al contenedor; mitigación: documentar prerequisitos en el propio Makefile si hace falta. Riesgo de desviación de entorno de desarrollo si el equipo usaba docker para testear; mitigación: los comandos son los mismos que corren en el pipeline local documentado.

## ROLLBACK

- Revert del/los commit(s): `git revert <commit>`.
- El cambio solo afecta targets del Makefile; sin impacto en runtime ni datos.

## FINAL REPORT

Completar al cerrar con `/task-close`: targets corregidos, comandos finales, resultados de `make test-backend` y `make test-frontend`, deuda detectada (p.ej. si el contenedor frontend debería tener herramientas de test a futuro).

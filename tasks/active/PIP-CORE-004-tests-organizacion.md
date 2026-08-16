# TASK PIP-CORE-004: Tests de backend para apps/organizacion

## DOMINIO

`core` (organizacion)

## OBJECTIVE

Cubrir con tests de backend los endpoints V1 de organizacion (`unidades-ejecutoras`, `direcciones-administrativas`, `unidades/arbol/`) que hoy no tienen ninguna cobertura, para fijar el contrato corregido en PIP-CORE-001.

## CONTEXT

Deuda registrada en PIP-CORE-001 (cerrada 2026-08-16): `backend/apps/organizacion/tests.py` es un stub vacío (`# Create your tests here.`) — la app no tiene tests. Los endpoints V1 existen y son usados por el frontend: `unidades-ejecutoras` (urls.py:12), `direcciones-administrativas` (urls.py:11), action `arbol` (views.py:24-25).

## CURRENT BEHAVIOR

- Cero tests backend en organizacion; el contrato V1 (corregido en el frontend) no tiene red de seguridad.

## EXPECTED BEHAVIOR

- Tests que verifican: listado de unidades-ejecutoras, direcciones-administrativas, árbol de unidades (200 + shape), y CRUD básico de los viewset según el router V1.

## IN SCOPE

- [ ] Crear tests en `backend/apps/organizacion/tests.py` (o carpeta tests/) con el patrón del repo (pytest-django, client/APIClient, fixtures existentes si las hay).
- [ ] Verificar el patrón de tests de otras apps del repo (accounts, gestion) para reutilizar convenciones.

## OUT OF SCOPE

- Cambios a views/serializers/urls de organizacion.
- Migrar organizacion a V2.

## INVARIANTS

- No se modifica código productivo (solo tests).
- Suite completa sigue en verde.

## DATABASE IMPACT

`ninguno`

## API IMPACT

`ninguno`

## FRONTEND IMPACT

`ninguno`

## FILES EXPECTED

- `backend/apps/organizacion/tests.py` — modificar (o tests/ con conftest si el repo lo usa)

## DEPENDENCIES

- PIP-CORE-001 (contrato corregido)

## ACCEPTANCE CRITERIA

- [ ] Tests nuevos pasan (`pytest apps/organizacion` ya no dice "no tests ran").
- [ ] Suite completa en verde (1252 + nuevos).

## TESTS

```bash
cd backend; .venv\Scripts\python -m pytest apps/organizacion -q
cd backend; .venv\Scripts\python -m pytest -q
```

## RISKS

Bajo. Riesgo: fixtures/models dependan de datos de seed; mitigación: crear objetos en los propios tests.

## ROLLBACK

`git revert <commit>`.

## FINAL REPORT

Completar al cerrar: tests creados, cobertura de endpoints, totales de suite.

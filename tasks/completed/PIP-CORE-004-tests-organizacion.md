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

Cerrada 2026-08-16.

**Tests creados (29) en `backend/apps/organizacion/tests.py`:** `TestContratoURLsV1` (4, verifica que reverse() resuelve a `/api/v1/...` sin doble prefijo), `TestAutenticacion` (3, 401 sin auth), `TestUnidadEjecutoraAPI` (8, listado+shape+filtro gestion+CRUD), `TestDireccionAdministrativaAPI` (5), `TestArbolUnidadesAPI` (5, árbol anidado, excluye inactivas), `TestUnidadOrganizacionalAPI` (2), `TestTiposUnidadAPI`/`TestAsignacionUsuarioUnidadAPI` (2).

**Patrón:** pytest-django (config.settings), `APIClient.force_authenticate` con superadmin, fixtures locales espejo + factories que crean objetos en-test (sin depender de seeds).

**Totales de suite:** `pytest apps/organizacion` → **29 passed**; suite completa → **1281 passed** (1252 base + 29).

**Commit:** `8944107`.

**Deuda detectada:** (1) `apps/catalogos/test_t4_clasificadores.py:363` flaky por seed exacto dependiente del scheduling de xdist (falla intermitente pre-existente, ajeno a organizacion); (2) `AsignacionUsuarioUnidad` sin `Meta.ordering` → UnorderedObjectListWarning; (3) serializers con `fields='__all__'` exponen `created_by/updated_by` escribibles (inconsistencia menor).

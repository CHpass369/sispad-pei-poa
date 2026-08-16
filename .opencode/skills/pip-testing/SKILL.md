---
name: pip-testing
description: "Use when: tests, pytest, xdist, Karma, Jasmine, specs, fixtures, conftest, settings_test_sqlite, ejecutar pruebas, verificar tests, cobertura, suite de tests, make test."
---

# PIP — Testing

## Backend (pytest)

- Ejecutar: `cd backend; python -m pytest` (suite completa: 1252 tests, xdist).
- Tests relevantes antes de DONE: `cd backend; python -m pytest <ruta>` (app, módulo o test específico).
- Estructura: `tests/` + tests por app; fixtures en `conftest.py` (api_client, auth_client, gestion, etc.).
- Config para tests con SQLite: `settings_test_sqlite` — usar para tests unitarios rápidos; mantener compatibilidad con PostgreSQL para tests de integración que dependan de PostGIS.
- Fixtures reutilizables: gestion fiscal (GestionFiscal), usuarios con capacidades, clientes autenticados JWT.

## Frontend (Karma + Jasmine)

- Ejecutar: `cd frontend/sispoa; npm test -- --watch=false`.
- `make test-frontend` está ROTO: no usarlo; el comando npm directo es el canónico.
- Escribir specs (describe/it) para features nuevas: componentes y servicios tocados.
- Verificar que los specs no queden en falso positivo (asserts reales sobre estado, llamadas HTTP con HttpTestingController).

## Reglas

- Correr los tests RELEVANTES antes de declarar DONE una tarea; nunca entregar rompiendo la suite completa.
- Test de backend: nombre descriptivo en español o inglés según convención del archivo; cubrir casos de error (403/404/validación), no solo el happy path.
- Si una feature nueva no tiene spec, la tarea no está completa (ACCEPTANCE CRITERIA obliga testing).
- Al tocar contratos (serializers/rutas), verificar los tests de contrato existentes y actualizarlos si el cambio es intencional.

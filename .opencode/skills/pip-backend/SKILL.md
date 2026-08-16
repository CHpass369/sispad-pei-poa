---
name: pip-backend
description: "Use when: backend, Django, DRF, REST, serializers, viewsets, endpoints, urls, JWT, SimpleJWT, capacidades, permisos, paginación, drf-spectacular, swagger, Celery, tareas asíncronas, models.py, services.py, urls_v2, namespaces."
---

# PIP — Backend (Django 6 + DRF)

Backend en `backend/` con apps en `backend/apps/` (27 apps). PostgreSQL 17 + PostGIS, ORM Django.

## Estructura por app

`models.py`, `serializers.py`, `views.py`, `urls.py`, `services.py`. Para V2: `urls_v2.py` con namespaces `/api/v2/{platform,core,catalogos,geo,integracion,auditoria,sis-pe,sis-poa,budget,sis-pro,me}/`. Seguir el patrón de la app que se toca.

## Reglas

- Código nuevo → API V2. API V1 es legacy (Sunset 2027-01-01): solo mantenimiento, y NO registrar rutas V2 en urls v1 ni al revés.
- SEARCH BEFORE CREATE: modelo/serializer/viewset/endpoint/catálogo nuevo → buscar equivalente primero (grep, codegraph, docs/architecture/DUPLICATION_ANALYSIS.md). REUSE → EXTEND → LOCAL REFACTOR.
- No crear apps nuevas sin task aprobada. No duplicar modelos existentes.
- Auth: AUTH_USER_MODEL=accounts.Usuario, JWT con SimpleJWT, permisos por capacidades (endpoint de capacidades en /api/v2/me/capabilities/).
- Paginación dual (página + offset/limit según el endpoint existente) y documentación con drf-spectacular.
- Tareas asíncronas (notificaciones, procesos pesados): Celery; no bloquear el request.
- Convenciones de idioma: modelos legacy en español (Techos, Presupuesto, etc.); budget V2 en inglés (DirectiveCeiling, ProgrammaticCategory...) — deuda conocida, continuar la convención de cada app y señalarla, no mezclarla.
- Scope: no modificar apps ajenas a la tarea (SCOPE CONTROL). Deuda detectada → documentar en tasks/technical-debt/, no refactor oportunista.

## Verificación

- Tests relevantes: `cd backend; python -m pytest <ruta>` (suite: 1252 tests con xdist).
- `make migrate` válido; migraciones nuevas deterministas.
- Contratos frontend↔backend coherentes (campos, tipos, errores) — no inventar rutas.

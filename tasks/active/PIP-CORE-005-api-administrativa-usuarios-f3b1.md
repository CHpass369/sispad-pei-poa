# TASK PIP-CORE-005: API administrativa de usuarios F3b1

## DOMINIO

`core`

## OBJECTIVE

Exponer en API V2 el listado, detalle, edición de datos personales y activación/inactivación administrativa de usuarios, respetando capacidades y límites SIS-PE/SIS-POA.

## CONTEXT

F3a incorporó el ciclo `PENDIENTE/ACTIVO/INACTIVO`, registro público y aprobación en `apps/accounts/views_register.py`. Las capacidades administrativas ya existen y la derivación de sistemas por rol debe reutilizarse entre F3a y F3b1.

## CURRENT BEHAVIOR

`apps/accounts/urls_v2.py` solo expone registro, solicitudes y aprobación. `views_register.py` contiene una regla local para limitar JEFE_PE/JEFE_POA al aprobar, pero no existe API administrativa de lectura o actualización.

## EXPECTED BEHAVIOR

La API V2 permite consultar y actualizar únicamente usuarios dentro del sistema administrable del actor; los detalles fuera de dominio responden 404. Solo se editan datos personales y las transiciones de estado usan endpoints dedicados.

## IN SCOPE

- [x] Listado y detalle paginados/serializados con filtros administrativos.
- [x] PATCH limitado a `first_name`, `last_name`, `cargo` y `telefono`.
- [x] Activación e inactivación coherentes entre `estado`, `activo` e `is_active`.
- [x] Regla compartida de sistemas para F3a y F3b1.
- [x] Tests de filtros, contrato, permisos, límites de sistema y transiciones.

## OUT OF SCOPE

- Asignación o revocación de roles, capacidades y alcances (F3b2).
- Cambios de modelos, migraciones o frontend.
- Refactorizaciones ajenas a `accounts`.

## INVARIANTS

- No modificar `ScopeResolver`, `TieneCapacidad` ni `CapacidadConScope`.
- Preservar los endpoints y tests de F3a.
- No exponer usuarios `SUPER_ADMIN` a JEFE_PE/JEFE_POA.
- No permitir que un usuario se inactive a sí mismo.

## DATABASE IMPACT

Ninguno. Se reutilizan `Usuario`, `Rol`, `Capacidad` y `AlcanceOrganizacional`; no hay migraciones.

## API IMPACT

- `GET /api/v2/admin/users/`
- `GET /api/v2/admin/users/{id}/`
- `PATCH /api/v2/admin/users/{id}/`
- `POST /api/v2/admin/users/{id}/activate/`
- `POST /api/v2/admin/users/{id}/deactivate/`

## FRONTEND IMPACT

Ninguno en esta tarea.

## FILES EXPECTED

- `backend/apps/accounts/services.py` — reglas compartidas de sistemas.
- `backend/apps/accounts/serializers.py` — contratos de salida y PATCH.
- `backend/apps/accounts/views_admin.py` — endpoints administrativos.
- `backend/apps/accounts/views_register.py` — reutilización de reglas compartidas.
- `backend/apps/accounts/urls_v2.py` — rutas F3b1.
- `backend/apps/accounts/tests/test_user_admin_v2.py` — cobertura F3b1.

## DEPENDENCIES

F3a, commit `1eaf906`.

## ACCEPTANCE CRITERIA

- [x] Capacidades `view`, `edit` y `activate` protegen cada operación.
- [x] Los cinco filtros devuelven usuarios correctos y `system/state` validan valores.
- [x] JEFE_PE y JEFE_POA solo acceden a usuarios exclusivamente de su sistema.
- [x] El contrato expone roles, alcances y sistemas efectivos sin duplicados.
- [x] PATCH rechaza cualquier campo fuera de los cuatro permitidos.
- [x] Activación/inactivación sincroniza los tres campos y prohíbe auto-inactivación.
- [x] Los comandos obligatorios de pytest, Ruff y `git diff --check` pasan.

## TESTS

```bash
cd backend; /home/chpass369/proyectos/poa/.venv/bin/python -m pytest apps/accounts/tests/test_user_admin_v2.py apps/accounts/tests/test_register.py --tb=short -q -o "addopts="
cd backend; /home/chpass369/proyectos/poa/.venv/bin/python -m pytest apps/accounts/ --tb=short -q -o "addopts="
cd backend; /home/chpass369/proyectos/poa/.venv/bin/python -m ruff check apps/accounts/ config/urls_v2.py
git diff --check
```

## RISKS

La derivación de sistema depende de capacidades activas con prefijo `sis_pe.`/`sis_poa.`; se usa el código como fuente porque el campo legacy `sistema` conserva variantes con guion. Se mitiga con tests de roles mixtos y límites cruzados.

## ROLLBACK

Revertir únicamente los archivos F3b1 listados; no hay migraciones ni cambios de datos que deshacer.

## FINAL REPORT

- Se agregaron los cinco endpoints F3b1 y una consulta administrativa paginada con filtros validados.
- Las reglas JEFE_PE/JEFE_POA/SUPER_ADMIN se centralizaron en `accounts.services` y F3a reutiliza la misma autoridad.
- PATCH no acepta roles, scopes, permisos, correo ni estado; las transiciones usan endpoints atómicos con bloqueo de fila.
- Se agregaron 22 tests y 11 subtests F3b1; la suite completa de `accounts` pasa con 98 tests y 11 subtests.
- No hay modelos, migraciones, endpoints frontend ni archivos ajenos modificados por la tarea.
- Riesgo residual: F3b2 debe reutilizar la misma derivación de sistemas al asignar roles y alcances para evitar divergencia de autorización.

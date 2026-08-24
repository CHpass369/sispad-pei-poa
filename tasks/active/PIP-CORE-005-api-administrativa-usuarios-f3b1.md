# TASK PIP-CORE-005: API administrativa IAM F3b1/F3b2a

## DOMINIO

`core`

## OBJECTIVE

Exponer en API V2 la administración de usuarios (F3b1) y de roles personalizados/capacidades (F3b2a), respetando capacidades, roles base inmutables y límites SIS-PE/SIS-POA.

## CONTEXT

F3a incorporó el ciclo `PENDIENTE/ACTIVO/INACTIVO`, registro público y aprobación. F3b1 completó la administración de datos personales y estado. F3b2a reutiliza `Rol`, `Capacidad`, la autorización administrativa y la derivación efectiva por prefijo para administrar roles personalizados sin habilitar edición del catálogo de capacidades.

## CURRENT BEHAVIOR

F3b1 ya expone usuarios y centraliza límites por sistema en `accounts.services`. La API V2 todavía no expone roles/capacidades; el `RolViewSet` V1 existente es genérico, no aplica las restricciones F3b2a y no debe reutilizarse como contrato administrativo V2.

## EXPECTED BEHAVIOR

La API V2 permite consultar y actualizar usuarios dentro del dominio del actor y administrar exclusivamente roles personalizados. Los seis roles base permanecen visibles e inmutables. El catálogo de capacidades es de solo lectura, excluye SIS-PRO y deriva el sistema efectivo desde el prefijo del código.

## IN SCOPE

- [x] Listado y detalle paginados/serializados con filtros administrativos.
- [x] PATCH limitado a `first_name`, `last_name`, `cargo` y `telefono`.
- [x] Activación e inactivación coherentes entre `estado`, `activo` e `is_active`.
- [x] Regla compartida de sistemas para F3a y F3b1.
- [x] Tests de filtros, contrato, permisos, límites de sistema y transiciones.
- [x] Listado, creación, detalle y PATCH de roles con filtros administrativos.
- [x] Reemplazo atómico de capacidades de roles personalizados.
- [x] Catálogo paginado de capacidades de solo lectura sin SIS-PRO.
- [x] Límites JEFE_PE/JEFE_POA para visibilidad, creación y asignación.
- [x] Tests F3b2a de autorización, contrato, validación, inmutabilidad y atomicidad.

## OUT OF SCOPE

- Asignación de roles o alcances a usuarios (F3b2b).
- Creación, edición o desactivación de capacidades.
- Cambios de modelos, migraciones o frontend.
- Refactorizaciones ajenas a `accounts`.

## INVARIANTS

- No modificar `ScopeResolver`, `TieneCapacidad` ni `CapacidadConScope`.
- Preservar los endpoints y tests de F3a.
- No exponer usuarios `SUPER_ADMIN` a JEFE_PE/JEFE_POA.
- No permitir que un usuario se inactive a sí mismo.
- Los seis roles base `es_sistema=True`, `deprecated=False` son inmutables, incluso para superusuarios.
- Los roles personalizados siempre se crean con `es_sistema=False` y `deprecated=False`.
- Solo `is_superuser=True` puede crear roles personalizados; `accounts.rol.create` no habilita POST por sí sola.
- Ningún contrato F3b2a expone o acepta capacidades `sis_pro.*`.
- La autorización por sistema se deriva del prefijo del código, no del campo legacy `Capacidad.sistema`.

## DATABASE IMPACT

Ninguno. Se reutilizan `Usuario`, `Rol`, `Capacidad`, sus M2M existentes y `AlcanceOrganizacional`; no hay migraciones esperadas.

## API IMPACT

- `GET /api/v2/admin/users/`
- `GET /api/v2/admin/users/{id}/`
- `PATCH /api/v2/admin/users/{id}/`
- `POST /api/v2/admin/users/{id}/activate/`
- `POST /api/v2/admin/users/{id}/deactivate/`
- `GET|POST /api/v2/admin/roles/`
- `GET|PATCH /api/v2/admin/roles/{id}/`
- `PUT /api/v2/admin/roles/{id}/capabilities/`
- `GET /api/v2/admin/capabilities/`

## FRONTEND IMPACT

Ninguno en esta tarea.

## FILES EXPECTED

- `backend/apps/accounts/services.py` — reglas compartidas de sistemas.
- `backend/apps/accounts/serializers.py` — contratos de salida y PATCH.
- `backend/apps/accounts/views_admin.py` — endpoints administrativos.
- `backend/apps/accounts/views_register.py` — reutilización de reglas compartidas.
- `backend/apps/accounts/urls_v2.py` — rutas F3b1.
- `backend/apps/accounts/tests/test_user_admin_v2.py` — cobertura F3b1.
- `backend/apps/accounts/services.py` — prefijos efectivos y límites reutilizables F3b2a.
- `backend/apps/accounts/serializers.py` — contratos y validaciones de roles/capacidades.
- `backend/apps/accounts/views_admin.py` — endpoints F3b2a y reemplazo transaccional.
- `backend/apps/accounts/urls_v2.py` — rutas F3b2a.
- `backend/apps/accounts/tests/test_role_admin_v2.py` — cobertura F3b2a.

## DEPENDENCIES

F3a, commit `1eaf906`, y F3b1 implementado en esta tarea.

## ACCEPTANCE CRITERIA

- [x] Capacidades `view`, `edit` y `activate` protegen cada operación.
- [x] Los cinco filtros devuelven usuarios correctos y `system/state` validan valores.
- [x] JEFE_PE y JEFE_POA solo acceden a usuarios exclusivamente de su sistema.
- [x] El contrato expone roles, alcances y sistemas efectivos sin duplicados.
- [x] PATCH rechaza cualquier campo fuera de los cuatro permitidos.
- [x] Activación/inactivación sincroniza los tres campos y prohíbe auto-inactivación.
- [x] Los comandos obligatorios de pytest, Ruff y `git diff --check` pasan.
- [x] List/detail/PATCH/asignación exigen su capacidad administrativa específica o superusuario.
- [x] POST de roles exige `is_superuser=True`, incluso si el actor posee `accounts.rol.create`.
- [x] Los roles base se listan/detallan, pero PATCH y asignación responden 403.
- [x] Códigos personalizados cumplen `^[A-Z][A-Z0-9_]{2,49}$` y no reutilizan códigos reservados, base o deprecated.
- [x] JEFE_PE/JEFE_POA solo ven y administran roles exclusivos de su dominio; fuera de dominio responde 404.
- [x] Las jefaturas solo asignan capacidades de su sistema y capacidades `accounts.*` que poseen, sin mezclar PE/POA.
- [x] El superusuario puede crear roles PE, POA, accounts o mixtos PE/POA, nunca SIS-PRO.
- [x] La asignación valida todos los códigos activos antes de reemplazar el M2M y es atómica.
- [x] El catálogo de capacidades filtra por `search`, `system`, `active`, deriva sistema por prefijo y es de solo lectura.
- [x] Las verificaciones focalizada, regresión de `accounts`, Ruff, migraciones y diff pasan.

## TESTS

```bash
cd backend; /home/chpass369/proyectos/poa/.venv/bin/python -m pytest apps/accounts/tests/test_user_admin_v2.py apps/accounts/tests/test_register.py --tb=short -q -o "addopts="
cd backend; /home/chpass369/proyectos/poa/.venv/bin/python -m pytest apps/accounts/tests/test_role_admin_v2.py apps/accounts/tests/test_user_admin_v2.py apps/accounts/tests/test_register.py --tb=short -q -o "addopts="
cd backend; /home/chpass369/proyectos/poa/.venv/bin/python -m pytest apps/accounts/ --tb=short -q -o "addopts="
cd backend; /home/chpass369/proyectos/poa/.venv/bin/python -m ruff check apps/accounts/ config/urls_v2.py
cd backend; /home/chpass369/proyectos/poa/.venv/bin/python manage.py makemigrations accounts --check --dry-run
git diff --check
```

## RISKS

La derivación de sistema depende de prefijos `sis_pe.`/`sis_poa.`/`accounts.`; el campo legacy `sistema` conserva datos históricos y no es autoridad. Sin un campo de propietario o sistema en `Rol`, un rol personalizado vacío o solo `accounts.*` no pertenece a PE ni POA y queda visible para ambas jefaturas; la asignación impide que incorporen capacidades fuera de su autoridad. Resolver propiedad explícita requeriría un cambio de modelo fuera de F3b2a.

## ROLLBACK

Revertir únicamente los bloques F3b2a en los archivos listados y eliminar su test nuevo; no hay migraciones ni cambios estructurales que deshacer.

## FINAL REPORT

- Se agregaron los cinco endpoints F3b1 y una consulta administrativa paginada con filtros validados.
- Las reglas JEFE_PE/JEFE_POA/SUPER_ADMIN se centralizaron en `accounts.services` y F3a reutiliza la misma autoridad.
- PATCH no acepta roles, scopes, permisos, correo ni estado; las transiciones usan endpoints atómicos con bloqueo de fila.
- Se agregaron 22 tests y 11 subtests F3b1; la suite completa de `accounts` pasa con 98 tests y 11 subtests.
- F3b2a agregó seis operaciones sobre cuatro rutas: roles list/create/detail/patch, reemplazo de capacidades y catálogo de capacidades de solo lectura.
- Decisión posterior F3b2a: solo usuarios con `is_superuser=True` pueden crear roles personalizados; JEFE_PE/JEFE_POA reciben 403 aunque posean `accounts.rol.create`.
- Los roles base son visibles e inmutables; los personalizados validan código reservado/duplicado y no permiten modificar `codigo`, `es_sistema` o `deprecated`.
- Se agregaron 20 tests y 21 subtests F3b2a. La verificación focalizada pasó con 80 tests y 32 subtests; la suite completa de `accounts` pasó con 118 tests y 32 subtests.
- Ruff pasó, `makemigrations accounts --check --dry-run` no detectó cambios y `git diff --check` pasó.
- No hay modelos, migraciones, frontend, commit ni stage. Los cambios ajenos preexistentes del working tree se preservaron.
- Siguiente recomendado: F3b2b para asignar roles y alcances a usuarios reutilizando estos límites y la derivación efectiva por prefijo.

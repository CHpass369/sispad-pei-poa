# TASK PIP-CORE-005: IAM F3b1/F3b2a/F3b2b/F4a

## DOMINIO

`core`

## OBJECTIVE

Exponer en API V2 la administración de usuarios (F3b1), roles personalizados/capacidades (F3b2a), asignaciones atómicas de roles/alcances organizacionales (F3b2b) y el registro público Angular (F4a), respetando capacidades, roles base inmutables y límites SIS-PE/SIS-POA.

## CONTEXT

F3a incorporó el ciclo `PENDIENTE/ACTIVO/INACTIVO`, registro público y aprobación. F3b1 completó la administración de datos personales y estado. F3b2a reutiliza `Rol`, `Capacidad`, la autorización administrativa y la derivación efectiva por prefijo para administrar roles personalizados sin habilitar edición del catálogo de capacidades. F3b2b reutiliza esos contratos para reemplazar, en una sola transacción, roles y alcances del dominio administrable del actor. F4a lleva el contrato público al frontend y necesita un catálogo anónimo mínimo de UO, porque `/api/v2/core/unidades/` exige autenticación y expone más campos de los necesarios.

## CURRENT BEHAVIOR

F3b1, F3b2a y F3b2b exponen usuarios, roles, capacidades y asignaciones, con límites por sistema centralizados en `accounts.services`. El contrato F3b2b mantiene sincronizados `Usuario.roles` y los `AlcanceOrganizacional` activos, sin permitir reemplazos parciales ni elevación de privilegios por jefaturas. El login Angular no ofrece todavía acceso al registro y no existe un selector público seguro de UO.

## EXPECTED BEHAVIOR

La API V2 permite consultar y actualizar usuarios dentro del dominio del actor, administrar exclusivamente roles personalizados y reemplazar atómicamente las asignaciones de roles/alcances que el actor puede administrar. Los seis roles base permanecen visibles e inmutables. El catálogo de capacidades es de solo lectura, excluye SIS-PRO y deriva el sistema efectivo desde el prefijo del código. Además, una persona anónima puede elegir una UO activa y vigente, enviar exclusivamente sus datos personales y recibir confirmación sin inicio de sesión ni token.

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
- [x] GET de asignaciones reutilizando la serialización administrativa F3b1.
- [x] PUT atómico que sincroniza roles y alcances del dominio administrable.
- [x] Preservación de asignaciones ajenas al sistema de JEFE_PE/JEFE_POA.
- [x] Scopes fijos de roles base, normalización GLOBAL a raíz y scopes libres para roles personalizados.
- [x] Tests F3b2b de autorización, dominio, validación, preservación y rollback.
- [x] Contratos Angular V2 tipados para registro y catálogo público de UO.
- [x] Ruta pública lazy `/auth/register` y formulario Material responsive.
- [x] Enlace desde login hacia el registro público.
- [x] Endpoint anónimo mínimo de UO activas y vigentes, con búsqueda opcional.
- [x] Tests focalizados frontend y backend de F4a.

## OUT OF SCOPE

- Creación, edición o desactivación de capacidades.
- Cambios de modelos o migraciones.
- Sidebar y gestor administrativo Angular (F4b/F5).
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
- F3b2b no modifica `estado`, `activo` ni `is_active`; rechaza usuarios `PENDIENTE`.
- Cada asignación F3b2b produce un rol directo y un alcance activo ligado al mismo rol.
- JEFE_PE/JEFE_POA nunca modifican asignaciones del otro sistema, usuarios SUPER_ADMIN ni sus propias asignaciones.
- Se valida el payload completo antes de mutar y se bloquea el usuario con `select_for_update`.

## F3B2B IMPLEMENTATION PLAN

1. **Dominio:** CORE/accounts; sin cambios de esquema ni dependencias nuevas.
2. **Servicios:** extender reglas de autoridad por sistema para clasificar roles asignables y limitar objetivos de asignaciones sin ocultar sus asignaciones preservadas del otro sistema.
3. **Contrato:** agregar serializers estrictos para la lista `assignments`, resolver roles/UO/gestiones en bloque, rechazar duplicados y normalizar GLOBAL a la raíz organizacional.
4. **Aplicación:** agregar GET/PUT sobre una vista transaccional; bloquear el usuario, validar antes de borrar/crear y reemplazar solo el subconjunto administrable.
5. **Persistencia:** reutilizar M2M `Usuario.roles` y `AlcanceOrganizacional`; no crear tablas ni migraciones. Los roles directos se recalculan desde todos los alcances activos preservados y nuevos.
6. **Pruebas:** crear `test_user_assignments_v2.py`; ejecutar regresión de register/user_admin/role_admin, suite completa accounts, Ruff, `makemigrations --check --dry-run` y `git diff --check`.
7. **Impacto frontend:** ninguno; F4 consumirá el contrato posteriormente.

## F4A IMPLEMENTATION PLAN

1. **Dominio:** CORE/accounts y feature Angular `auth`; sin cambios de esquema ni dependencias nuevas.
2. **Reutilización:** extender `AuthService`, `AuthModule`, la ruta lazy existente y la identidad visual del login; usar `HttpClient` con `environment.apiUrlV2`, no `ApiService` V1.
3. **API pública:** agregar en `accounts` un listado `AllowAny` de UO activas y vigentes con `id`, `codigo`, `nombre`, `sigla` y `padre`; aceptar únicamente `search` y no exponer responsables, usuarios ni metadatos internos.
4. **Contrato:** tipar payload, respuesta de registro y UO pública; devolver la colección breve sin paginación y validar también en backend que la UO enviada siga activa y vigente.
5. **Interfaz:** crear un formulario Material de dos columnas que colapsa a una, con búsqueda de UO, validación cruzada de contraseñas, estado de carga y confirmación sin auto-login.
6. **Pruebas:** cubrir URL/payload del servicio, seguridad del payload, mismatch, éxito sin token, errores API y navegación login→registro; verificar endpoint anónimo, vigencia y campos mínimos.
7. **Verificación:** ejecutar Karma focalizado con `ChromeHeadlessNoSandbox`, build production, lint disponible, pytest focalizado, Ruff, `makemigrations --check --dry-run` y `git diff --check`.

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
- `GET|PUT /api/v2/admin/users/{id}/assignments/`
- `GET /api/v2/auth/organizational-units/?search=...`
- `POST /api/v2/auth/register/` (reutilizado por F4a)

## FRONTEND IMPACT

F4a agrega la ruta pública `/auth/register`, extiende `AuthService` con contratos V2 y enlaza el login existente. F4b/F5 permanecen fuera de alcance.

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
- `backend/apps/accounts/services.py` — autoridad y clasificación F3b2b.
- `backend/apps/accounts/serializers.py` — payload estricto y validación F3b2b.
- `backend/apps/accounts/views_admin.py` — lectura y reemplazo transaccional F3b2b.
- `backend/apps/accounts/urls_v2.py` — ruta F3b2b.
- `backend/apps/accounts/tests/test_user_assignments_v2.py` — cobertura F3b2b.
- `backend/apps/accounts/serializers.py` — contrato público mínimo de UO y validación de vigencia.
- `backend/apps/accounts/views_register.py` — listado público seguro de UO.
- `backend/apps/accounts/urls_v2.py` — ruta pública F4a.
- `backend/apps/accounts/tests/test_register.py` — cobertura backend F4a.
- `frontend/sispoa/src/app/core/models/usuario.model.ts` — contratos públicos de registro.
- `frontend/sispoa/src/app/core/services/auth.service.ts` — métodos V2.
- `frontend/sispoa/src/app/core/services/auth.service.spec.ts` — contratos HTTP F4a.
- `frontend/sispoa/src/app/features/auth/auth.module.ts` — ruta y módulos Material.
- `frontend/sispoa/src/app/features/auth/register.component.ts` — formulario público.
- `frontend/sispoa/src/app/features/auth/register.component.spec.ts` — comportamiento del registro.
- `frontend/sispoa/src/app/features/auth/login.component.ts` — enlace a registro.
- `frontend/sispoa/src/app/features/auth/login.component.spec.ts` — navegación pública.

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
- [x] GET/PUT exigen respectivamente `accounts.alcance.view` y `accounts.alcance.assign`, con 404 fuera del dominio.
- [x] SUPER_ADMIN reemplaza PE/POA/accounts; cada jefatura reemplaza solo su sistema y preserva el resto.
- [x] Ninguna jefatura modifica usuarios SUPER_ADMIN, se autoasigna ni asigna roles/capacidades fuera de su autoridad.
- [x] Los roles base respetan su scope fijo; GLOBAL se normaliza a la raíz y los roles personalizados aceptan los tres scopes.
- [x] Roles inactivos/deprecated, SIS-PRO, UO/gestión inexistentes, duplicados y usuarios PENDIENTE se rechazan sin mutaciones parciales.
- [x] PUT no cambia `estado`, `activo` ni `is_active`.
- [x] El listado público de UO no requiere autenticación y devuelve solo registros activos/vigentes y campos mínimos.
- [x] `AuthService.register` y `listPublicOrganizationalUnits` usan `environment.apiUrlV2` sin doble prefijo V1.
- [x] `/auth/register` es pública y no presenta ni envía rol, sistema, permisos o scope.
- [x] El formulario bloquea mismatch, deshabilita submit durante la petición y muestra errores API claros.
- [x] El éxito muestra el mensaje normativo, no almacena token y permite volver al login.
- [x] Login muestra “¿No tienes una cuenta?” y “Crear cuenta”, que navega a `/auth/register`.
- [x] Tests focalizados, build production, Ruff, migraciones y diff check pasan; lint fue ejecutado y reportado como no configurado.

## TESTS

```bash
cd backend; /home/chpass369/proyectos/poa/.venv/bin/python -m pytest apps/accounts/tests/test_user_admin_v2.py apps/accounts/tests/test_register.py --tb=short -q -o "addopts="
cd backend; /home/chpass369/proyectos/poa/.venv/bin/python -m pytest apps/accounts/tests/test_role_admin_v2.py apps/accounts/tests/test_user_admin_v2.py apps/accounts/tests/test_register.py --tb=short -q -o "addopts="
cd backend; /home/chpass369/proyectos/poa/.venv/bin/python -m pytest apps/accounts/ --tb=short -q -o "addopts="
cd backend; /home/chpass369/proyectos/poa/.venv/bin/python -m pytest apps/accounts/tests/test_user_assignments_v2.py apps/accounts/tests/test_register.py apps/accounts/tests/test_user_admin_v2.py apps/accounts/tests/test_role_admin_v2.py --tb=short -q -o "addopts="
cd backend; /home/chpass369/proyectos/poa/.venv/bin/python -m ruff check apps/accounts/ config/urls_v2.py
cd backend; /home/chpass369/proyectos/poa/.venv/bin/python manage.py makemigrations accounts --check --dry-run
cd frontend/sispoa; CHROME_BIN=/snap/bin/chromium npm test -- --watch=false --browsers=ChromeHeadlessNoSandbox --include='src/app/core/services/auth.service.spec.ts' --include='src/app/features/auth/register.component.spec.ts' --include='src/app/features/auth/login.component.spec.ts'
cd frontend/sispoa; npm run build -- --configuration production
cd frontend/sispoa; npm run lint
git diff --check
```

## RISKS

La derivación de sistema depende de prefijos `sis_pe.`/`sis_poa.`/`accounts.`; el campo legacy `sistema` conserva datos históricos y no es autoridad. Sin un campo de propietario o sistema en `Rol`, un rol personalizado vacío o solo `accounts.*` no pertenece a PE ni POA; F3b2b permite asignarlo únicamente a SUPER_ADMIN. Los solapamientos se validan en API y la fila de usuario serializa escrituras concurrentes, pero no existe todavía un constraint de base de datos que impida duplicados creados fuera de este endpoint. Resolver ambas deudas requiere cambios de modelo fuera del alcance sin migraciones de F3b2b. En F4a, el catálogo público permite enumerar nombres institucionales y devuelve la colección completa; el riesgo se limita a campos no sensibles y al throttling anónimo global, pero convendrá paginar si el catálogo crece significativamente.

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
- F3b2b agregó `GET|PUT /api/v2/admin/users/{id}/assignments/`, con validación completa previa, transacción y bloqueo `select_for_update` del usuario.
- Las jefaturas reemplazan únicamente roles de su sistema que están dentro de su autoridad; las asignaciones del otro sistema y roles no administrables permanecen intactos. Usuarios mixtos son accesibles en F3b2b si pertenecen al sistema de la jefatura, sin relajar la visibilidad F3b1.
- Los seis roles base exigen su scope fijo, GLOBAL almacena la UO raíz, los roles personalizados aceptan SELF/DESCENDANTS/GLOBAL y se rechazan asignaciones duplicadas o con cobertura solapada.
- Se agregaron 19 tests y 29 subtests F3b2b. La regresión focalizada pasó con 99 tests y 61 subtests; la suite completa de `accounts` pasó con 137 tests y 61 subtests.
- Ruff pasó sobre `apps/accounts/` y `config/urls_v2.py`; `makemigrations accounts --check --dry-run` no detectó cambios y `git diff --check` pasó.
- Una corrida focalizada lanzada en paralelo con la suite completa produjo errores internos de fixtures de pytest; ambas verificaciones canónicas se repitieron secuencialmente y pasaron.
- Siguiente recomendado: F4b para el gestor unificado de usuarios, consumiendo F3b1/F3b2b sin duplicar reglas de autoridad en Angular.
- F4a agregó `GET /api/v2/auth/organizational-units/`, público, buscable y limitado a UO activas/vigentes con cinco campos públicos; el POST de registro rechaza ahora una UO no disponible aunque se fuerce el payload.
- Angular agregó contratos V2 en `AuthService`, la ruta lazy `/auth/register`, un formulario Material responsive con selector buscable y el enlace desde login; no existe auto-login ni persistencia de token.
- Verificación F4a: 30 tests Karma focalizados pasaron; build production pasó; 43 tests backend focalizados pasaron con SQLite; Ruff y `makemigrations --check --dry-run` pasaron; `git diff --check` pasó.
- `npm run lint` se ejecutó, pero Angular reportó `Cannot find "lint" target for the specified project`; no hay lint configurado. PostgreSQL local en `/tmp/opencode:5433` no respondió, por lo que la corrida focalizada canónica se validó con `config.settings_test_sqlite`.
- La suite completa `apps/accounts/` con settings SQLite obtuvo 129 tests y 51 subtests aprobados, con 23 fallos preexistentes porque esos settings reemplazan `REST_FRAMEWORK` y eliminan la paginación esperada por F3b1/F3b2a; no se modificaron esos tests fuera de alcance.
- No hubo migraciones, stage ni commit. F4b queda como siguiente fase para consumir los contratos administrativos existentes sin tocar todavía sidebar/F5.

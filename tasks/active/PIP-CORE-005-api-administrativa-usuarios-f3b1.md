# TASK PIP-CORE-005: IAM F3b1/F3b2a/F3b2b/F4a/F4b1/F4b2

## DOMINIO

`core`

## OBJECTIVE

Exponer en API V2 la administración de usuarios (F3b1), roles personalizados/capacidades (F3b2a), asignaciones atómicas de roles/alcances organizacionales (F3b2b), el registro público Angular (F4a), el listado administrativo Angular (F4b1) y la edición de datos/asignaciones (F4b2), respetando capacidades, roles base inmutables y límites SIS-PE/SIS-POA.

## CONTEXT

F3a incorporó el ciclo `PENDIENTE/ACTIVO/INACTIVO`, registro público y aprobación. F3b1 completó la administración de datos personales y estado. F3b2a reutiliza `Rol`, `Capacidad`, la autorización administrativa y la derivación efectiva por prefijo para administrar roles personalizados sin habilitar edición del catálogo de capacidades. F3b2b reutiliza esos contratos para reemplazar, en una sola transacción, roles y alcances del dominio administrable del actor. F4a lleva el contrato público al frontend y necesita un catálogo anónimo mínimo de UO, porque `/api/v2/core/unidades/` exige autenticación y expone más campos de los necesarios.

## CURRENT BEHAVIOR

F3b1, F3b2a y F3b2b exponen usuarios, roles, capacidades y asignaciones, con límites por sistema centralizados en `accounts.services`. El contrato F3b2b mantiene sincronizados `Usuario.roles` y los `AlcanceOrganizacional` activos, sin permitir reemplazos parciales ni elevación de privilegios por jefaturas. F4a ofrece registro público y catálogo mínimo de UO. F4b1 ya reemplazó el interior legacy de `admin-usuarios` por el shell Material único, listado V2, filtros, paginación, detalle y cambios de estado; todavía no permite editar datos personales ni asignaciones.

## EXPECTED BEHAVIOR

La API V2 permite consultar y actualizar usuarios dentro del dominio del actor, administrar exclusivamente roles personalizados y reemplazar atómicamente las asignaciones de roles/alcances que el actor puede administrar. Los seis roles base permanecen visibles e inmutables. El catálogo de capacidades es de solo lectura, excluye SIS-PRO y deriva el sistema efectivo desde el prefijo del código. Además, una persona anónima puede elegir una UO activa y vigente, enviar exclusivamente sus datos personales y recibir confirmación sin inicio de sesión ni token. En F4b1/F4b2, la única entrada Angular `admin-usuarios` presenta el shell “Usuarios y permisos”, aplica visibilidad por capacidades y permite listar, consultar, actualizar datos personales y reemplazar atómicamente asignaciones administrables.

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
- [x] Shell único “Usuarios y permisos” sobre el feature Angular existente.
- [x] Tabs Usuarios, Roles, Permisos y Solicitudes visibles según capacidades.
- [x] Listado Material de usuarios con filtros y paginación real de backend.
- [x] Estados de carga, error accionable, vacío y detalle de usuario.
- [x] Activación e inactivación visibles únicamente con capacidad administrativa.
- [x] Servicio administrativo V2 y DTOs estrictamente tipados sin `any`.
- [x] Guard de ruta con acceso por cualquiera de las cuatro capacidades administrativas.
- [x] Tests focalizados de servicio, tabla, filtros, estados, acciones, tabs y ruta.
- [x] Dialog Material accesible para edición de usuario desde el listado.
- [x] PATCH estricto de nombres, apellidos, cargo y teléfono.
- [x] Lectura y reemplazo atómico de asignaciones mediante GET/PUT V2.
- [x] Filas dinámicas tipadas con rol, UO, scope, gestión opcional y sistema derivado.
- [x] Scopes normativos fijos para roles base y seleccionables para roles personalizados.
- [x] Preservación visual de asignaciones ajenas que el actor no puede reenviar.
- [x] Bloqueo de asignaciones para usuarios pendientes con navegación a Solicitudes.
- [x] Cierre seguro, estados de carga/error/éxito y refresco inmediato del listado/detalle.
- [x] Tests F4b2 de contratos, scopes, filas, capacidades, pendiente, rollback visual y éxito.

## OUT OF SCOPE

- Creación, edición o desactivación de capacidades.
- Cambios de modelos o migraciones.
- Implementación funcional de Roles, Permisos y Solicitudes (F4c).
- Sidebar nuevo o rediseño de navegación (F5).
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

## F4B1 IMPLEMENTATION PLAN

1. **Dominio:** CORE/accounts en frontend; sin cambios de backend, esquema ni migraciones.
2. **Reutilización:** extender el feature lazy `admin-usuarios`, mantener su única ruta, reutilizar `CapabilitiesService`, `CapabilityGuard`, `AuthService.listPublicOrganizationalUnits`, Angular Material y tokens `--pip-*`.
3. **Contrato:** reemplazar el servicio V1 del feature por `HttpClient` sobre `environment.apiUrlV2`; definir DTOs de usuarios y una interfaz paginada canónica compartida sin `any`.
4. **Ruta:** proteger la entrada con OR de `accounts.usuario.view`, `accounts.rol.view`, `accounts.capacidad.view` y `accounts.solicitud.view`; retirar temporalmente las rutas legacy de creación/edición hasta F4b2.
5. **Interfaz:** convertir el listado existente en shell Material; cargar Usuarios solo con su capacidad, ocultar tabs no autorizadas y dejar placeholders honestos para F4c.
6. **Listado:** enviar `search`, `organizational_unit`, `role`, `system`, `state` y `page`; reiniciar la página al aplicar o limpiar filtros y representar datos reales, carga, error, vacío y paginador.
7. **Acciones:** consultar detalle por API V2 y activar/desactivar solo con `accounts.usuario.activate`; no ofrecer creación, edición, eliminación ni asignaciones.
8. **Pruebas:** cubrir URLs/query params/paginación, renderizado de columnas y filas, filtros, estados, capacidades, tabs y configuración de ruta.
9. **Verificación:** ejecutar Karma focalizado con `ChromeHeadlessNoSandbox`, build production, type-check, lint únicamente si existe target funcional y `git diff --check`.

## F4B2 IMPLEMENTATION PLAN

1. **Dominio:** CORE/accounts en frontend; sin cambios de backend, modelos ni migraciones.
2. **Reutilización:** extender `AdminUsuariosService`, el listado F4b1, `AuthService.listPublicOrganizationalUnits`, `GestionHabilitadaService`, `CapabilitiesService`, Material Dialog y tokens `--pip-*`.
3. **Contrato personal:** agregar `patchUser` con un payload que solo puede contener `first_name`, `last_name`, `cargo` y `telefono`; no enviar correo, estado, roles ni scopes.
4. **Contrato de asignaciones:** agregar `getAssignments`, `putAssignments` y `listRoles`; tipar roles, capacidades, scopes y payload atómico sin `any` ni API V1.
5. **Dialog:** crear un componente focalizado con dos secciones y guardados independientes, foco inicial/restaurado, cierre con confirmación si hay cambios y diseño responsive.
6. **Autoridad:** ocultar la acción si faltan capacidades; habilitar datos con `accounts.usuario.edit`, lectura con `accounts.alcance.view` y mutación con `accounts.alcance.assign`.
7. **Scopes:** mantener únicamente el mapa normativo de seis roles base; derivar sistema desde `role.sistemas` y permitir los tres scopes en roles personalizados.
8. **Preservación:** construir filas editables solo con roles devueltos por backend; mostrar aparte alcances ajenos y excluirlos del PUT para que la jefatura no intente reemplazar otro sistema.
9. **Gestión fiscal:** reutilizar el candado V2 `GestionHabilitadaService`; ofrecer únicamente la gestión activa, omitir el selector si no existe, conservar IDs existentes y usar `null` en filas nuevas.
10. **Pendientes:** no consultar ni editar asignaciones y ofrecer navegación al tab Solicitudes cuando sea visible.
11. **Pruebas:** cubrir contratos HTTP, payloads, scope fijo/custom, filas, sistema derivado, pendiente, capacidades, error sin cierre/pérdida y refresco tras éxito.
12. **Verificación:** ejecutar Karma focalizado con `ChromeHeadlessNoSandbox`, build production, typecheck app/specs y `git diff --check`; no ejecutar lint porque el proyecto no define target.

## F4B2 PHONE CONTRACT CORRECTION PLAN

1. **Backend/API:** extender únicamente `UsuarioAdminReadSerializer` para devolver `telefono` en listado, detalle y respuestas de mutación; mantener sin cambios el PATCH estricto de cuatro campos personales.
2. **Frontend:** hacer obligatorio `AdminUser.telefono`, inicializar el formulario con el valor real del contrato y eliminar fallbacks creados para una respuesta incompleta.
3. **Pruebas:** afirmar el teléfono en el contrato backend, el DTO/HTTP frontend y el dialog; comprobar que editar otro campo no envía ni reemplaza el teléfono.
4. **Impacto:** sin modelos, migraciones, endpoints nuevos ni cambios fuera de CORE/accounts y `admin-usuarios`.
5. **Verificación:** pytest focalizado, Karma F4b2, Ruff, build, typecheck app/specs, `makemigrations --check --dry-run` y `git diff --check`.

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

F4a agrega la ruta pública `/auth/register`, extiende `AuthService` con contratos V2 y enlaza el login existente. F4b1 reemplaza el interior legacy de `/admin-usuarios` por el shell único “Usuarios y permisos”. F4b2 agrega edición personal y gestión de asignaciones en un dialog Material, consume exclusivamente contratos V2 y conserva Roles/Permisos/Solicitudes como placeholders de F4c. F5 permanece fuera de alcance.

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
- `frontend/sispoa/src/app/core/models/paginado.model.ts` — contrato paginado canónico.
- `frontend/sispoa/src/app/features/admin-usuarios/admin-usuarios.service.ts` — contrato HTTP V2 tipado F4b1.
- `frontend/sispoa/src/app/features/admin-usuarios/admin-usuarios.service.spec.ts` — pruebas de URLs, parámetros y paginación.
- `frontend/sispoa/src/app/features/admin-usuarios/usuarios-lista.component.{ts,html,scss}` — shell, tabs y listado Material.
- `frontend/sispoa/src/app/features/admin-usuarios/usuarios-lista.component.spec.ts` — pruebas de interacción y capacidades.
- `frontend/sispoa/src/app/features/admin-usuarios/admin-usuarios-routing.module.ts` — ruta única protegida.
- `frontend/sispoa/src/app/features/admin-usuarios/admin-usuarios-routing.module.spec.ts` — contrato de guard y capacidades.
- `frontend/sispoa/src/app/features/admin-usuarios/usuario-form.component.ts` — eliminado por depender de V1 y exponer operaciones fuera de F4b1.
- `frontend/sispoa/src/app/features/admin-usuarios/usuario-edicion-dialog.component.{ts,html,scss}` — edición personal y asignaciones F4b2.
- `frontend/sispoa/src/app/features/admin-usuarios/usuario-edicion-dialog.component.spec.ts` — comportamiento, capacidades y rollback visual F4b2.

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
- [x] `/admin-usuarios` conserva una sola entrada y exige al menos una capacidad administrativa mediante `CapabilityGuard`.
- [x] Cada tab y la acción de estado se ocultan si falta su capacidad; el backend conserva la autoridad final.
- [x] Usuarios usa tabla y paginador Material con las ocho columnas requeridas y filtros enviados a backend.
- [x] Aplicar o limpiar filtros reinicia la página; navegar el paginador solicita la página real de API V2.
- [x] La interfaz representa carga, error con reintento, vacío, detalle y error de transición de estado.
- [x] El servicio usa `environment.apiUrlV2`, no `ApiService` V1, y no contiene doble prefijo.
- [x] No se ofrecen creación, edición, eliminación ni asignaciones antes de F4b2.
- [x] Karma focalizado pasa con 14 tests; build production, typecheck de app/specs y `git diff --check` pasan.
- [x] Editar solo aparece con capacidad personal o lectura de alcances; la mutación exige además `accounts.alcance.assign` para evitar reemplazos atómicos sin lectura previa.
- [x] PATCH envía únicamente campos personales modificados y nunca correo, estado, roles ni asignaciones.
- [x] GET/PUT de asignaciones y listado completo paginado de roles usan rutas V2 tipadas.
- [x] Los seis roles base fijan su scope normativo; un rol personalizado mantiene selector SELF/DESCENDANTS/GLOBAL.
- [x] El sistema visible se deriva de `role.sistemas`; no existen opciones ni datos simulados de SIS-PRO.
- [x] Agregar/quitar filas es local y un error de PUT mantiene dialog y filas sin alterar.
- [x] Alcances de roles no devueltos por el catálogo administrable se muestran como conservados y no se envían en PUT.
- [x] Un usuario PENDIENTE no dispara GET de asignaciones y puede ir al tab Solicitudes si tiene capacidad.
- [x] Cada éxito actualiza inmediatamente la fila y el detalle abierto mediante el resultado real del backend.
- [x] Karma focalizado pasa con 26 tests; build production, typecheck app/specs y `git diff --check` pasan.
- [x] El contrato administrativo devuelve `telefono` en listado, detalle y respuestas de mutación; `AdminUser.telefono` es obligatorio.
- [x] El dialog inicializa el teléfono real y solo lo incluye en PATCH cuando cambia, sin fallback ni sobrescritura a ciegas.
- [x] Corrección de contrato verificada con 24 tests backend y 27 tests Karma F4b2.

## TESTS

```bash
cd backend; /home/chpass369/proyectos/poa/.venv/bin/python -m pytest apps/accounts/tests/test_user_admin_v2.py apps/accounts/tests/test_register.py --tb=short -q -o "addopts="
cd backend; /home/chpass369/proyectos/poa/.venv/bin/python -m pytest -n 0 apps/accounts/tests/test_user_admin_v2.py
cd backend; /home/chpass369/proyectos/poa/.venv/bin/python -m pytest apps/accounts/tests/test_role_admin_v2.py apps/accounts/tests/test_user_admin_v2.py apps/accounts/tests/test_register.py --tb=short -q -o "addopts="
cd backend; /home/chpass369/proyectos/poa/.venv/bin/python -m pytest apps/accounts/ --tb=short -q -o "addopts="
cd backend; /home/chpass369/proyectos/poa/.venv/bin/python -m pytest apps/accounts/tests/test_user_assignments_v2.py apps/accounts/tests/test_register.py apps/accounts/tests/test_user_admin_v2.py apps/accounts/tests/test_role_admin_v2.py --tb=short -q -o "addopts="
cd backend; /home/chpass369/proyectos/poa/.venv/bin/python -m ruff check apps/accounts/ config/urls_v2.py
cd backend; /home/chpass369/proyectos/poa/.venv/bin/python manage.py makemigrations accounts --check --dry-run
cd frontend/sispoa; CHROME_BIN=/snap/bin/chromium npm test -- --watch=false --browsers=ChromeHeadlessNoSandbox --include='src/app/core/services/auth.service.spec.ts' --include='src/app/features/auth/register.component.spec.ts' --include='src/app/features/auth/login.component.spec.ts'
cd frontend/sispoa; npm run build -- --configuration production
cd frontend/sispoa; CHROME_BIN=/snap/bin/chromium npm test -- --watch=false --browsers=ChromeHeadlessNoSandbox --include='src/app/features/admin-usuarios/admin-usuarios.service.spec.ts' --include='src/app/features/admin-usuarios/usuarios-lista.component.spec.ts' --include='src/app/features/admin-usuarios/usuario-edicion-dialog.component.spec.ts' --include='src/app/features/admin-usuarios/admin-usuarios-routing.module.spec.ts'
cd frontend/sispoa; npm run lint
git diff --check
cd frontend/sispoa; CHROME_BIN=/snap/bin/chromium npm test -- --watch=false --browsers=ChromeHeadlessNoSandbox --include='src/app/features/admin-usuarios/admin-usuarios.service.spec.ts' --include='src/app/features/admin-usuarios/usuarios-lista.component.spec.ts' --include='src/app/features/admin-usuarios/admin-usuarios-routing.module.spec.ts'
cd frontend/sispoa; npx tsc -p tsconfig.app.json --noEmit
cd frontend/sispoa; npx tsc -p tsconfig.spec.json --noEmit
cd frontend/sispoa; npm run build -- --configuration production
```

## RISKS

La derivación de sistema depende de prefijos `sis_pe.`/`sis_poa.`/`accounts.`; el campo legacy `sistema` conserva datos históricos y no es autoridad. Sin un campo de propietario o sistema en `Rol`, un rol personalizado vacío o solo `accounts.*` no pertenece a PE ni POA; F3b2b permite asignarlo únicamente a SUPER_ADMIN. Los solapamientos se validan en API y la fila de usuario serializa escrituras concurrentes, pero no existe todavía un constraint de base de datos que impida duplicados creados fuera de este endpoint. Resolver ambas deudas requiere cambios de modelo fuera del alcance sin migraciones de F3b2b. En F4a/F4b1, el catálogo público permite enumerar nombres institucionales y devuelve la colección completa; F4b1/F4b2 lo reutilizan porque no exige una capacidad organizacional adicional. El contrato administrativo ya expone `telefono` como string en listado, detalle y mutaciones; PATCH conserva el valor cuando se omite. `listRoles` exige autoridad backend propia; si el actor tiene capacidades de alcance pero no puede listar roles, el dialog muestra error y no intenta inventar opciones. Las asignaciones no devueltas por ese catálogo se excluyen del payload; el backend preserva únicamente las que están fuera de la autoridad del actor y mantiene la decisión final. La gestión fiscal usa exclusivamente el candado activo ADR-007; si no existe, omite el selector y usa `null` en filas nuevas.

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
- F4b1 convirtió el feature legacy `admin-usuarios` en el shell único “Usuarios y permisos”, sin crear otra entrada ni modificar el sidebar.
- El tab Usuarios consume paginación y cinco filtros reales de `/api/v2/admin/users/`, muestra detalle y permite activar/desactivar solo con capacidad.
- Roles, Permisos y Solicitudes muestran placeholders sin datos falsos y solo existen en el DOM cuando su capacidad está presente.
- Se eliminó el formulario legacy no enrutable porque dependía de API V1 y ofrecía creación, edición y eliminación fuera del alcance.
- Se agregó un contrato `Paginado<T>` canónico y se evitó `any` en todos los artefactos activos F4b1.
- Verificación F4b1: 14 tests Karma focalizados pasaron en Chrome Headless 151; build production y typecheck app/specs pasaron sin errores; `git diff --check` pasó. Lint no se ejecutó porque `angular.json` no define target `lint`.
- No hubo cambios de backend, migraciones, endpoints, stage ni commit. Siguiente: F4b2 para edición de datos personales y asignaciones atómicas.
- F4b2 agregó un dialog Material con guardados independientes para datos personales y asignaciones; no simula atomicidad entre dos endpoints distintos.
- `AdminUsuariosService` incorporó PATCH personal, GET/PUT de asignaciones y carga de todas las páginas de roles activos.
- Las filas de asignación derivan sistema desde backend, fijan scopes de los seis roles base y permiten scopes libres en roles personalizados.
- Las asignaciones ajenas al catálogo administrable se muestran en un bloque preservado y se excluyen del PUT de una jefatura.
- Un error de PUT conserva las filas y el dialog abierto; cada éxito actualiza inmediatamente la tabla y el detalle mediante `userSaved`.
- La gestión fiscal reutiliza `GestionHabilitadaService`; no agrega endpoint, selector histórico ni mock.
- Verificación F4b2: 26 tests Karma focalizados pasaron en Chrome Headless 151; build production pasó con hash `bb7e79c044a6b9b1` y chunk lazy de administración de `259.92 kB`; typecheck app/specs y `git diff --check` pasaron.
- Lint no se ejecutó porque `angular.json` no define target `lint`. No hubo cambios de backend, migraciones, sidebar, stage ni commit. Siguiente: F4c.
- Corrección final F4b2: `UsuarioAdminReadSerializer` expone `telefono`; Angular lo tipa como obligatorio y el dialog compara contra el valor real antes de construir PATCH.
- Verificación de la corrección: 24 tests backend pasaron en 292.89 s; 27 tests Karma pasaron en Chrome Headless 151; Ruff pasó; `makemigrations accounts --check --dry-run` no detectó cambios; typecheck app/specs pasó; build production pasó con hash `e49ec32a1fc316b1` y chunk lazy admin de `259.49 kB`.

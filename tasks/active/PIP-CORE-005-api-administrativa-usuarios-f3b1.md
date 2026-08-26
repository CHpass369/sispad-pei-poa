# TASK PIP-CORE-005: IAM F3b1/F3b2a/F3b2b/F4a/F4b1/F4b2/F4c1/F4c2/F5

## DOMINIO

`core`

## OBJECTIVE

Exponer en API V2 la administración de usuarios (F3b1), roles personalizados/capacidades (F3b2a), asignaciones atómicas de roles/alcances organizacionales (F3b2b), completar el gestor Angular hasta la aprobación de Solicitudes F4c2 y cerrar F5 con navegación derivada exclusivamente de capacidades, respetando roles base inmutables y límites SIS-PE/SIS-POA.

## CONTEXT

F3a incorporó el ciclo `PENDIENTE/ACTIVO/INACTIVO`, registro público y aprobación. F3b1 completó la administración de datos personales y estado. F3b2a reutiliza `Rol`, `Capacidad`, la autorización administrativa y la derivación efectiva por prefijo para administrar roles personalizados sin habilitar edición del catálogo de capacidades. F3b2b reutiliza esos contratos para reemplazar, en una sola transacción, roles y alcances del dominio administrable del actor. F4a lleva el contrato público al frontend y necesita un catálogo anónimo mínimo de UO, porque `/api/v2/core/unidades/` exige autenticación y expone más campos de los necesarios.

### Plan de corrección visual F4a — 2026-08-25

- Dominio: CORE, exclusivamente el registro público Angular.
- Archivos: plantilla/estilos/spec de `RegisterComponent`, más la regla global acotada al overlay de autocomplete.
- Dependencias: reutilizar la API `classList` de `MatAutocomplete` y los tokens `--pip-*`; no crear componentes ni estilos genéricos.
- Impacto: solo presentación y prueba del overlay/campos; sin cambios de base de datos, API, contratos o routing.
- Verificación: Karma focalizado, typecheck de aplicación y specs, build production y `git diff --check`.

## CURRENT BEHAVIOR

F3b1, F3b2a y F3b2b exponen usuarios, roles, capacidades y asignaciones con límites centralizados en `accounts.services`. F4a ofrece registro público; F4b1/F4b2 implementan listado, detalle, edición personal y asignaciones. F4c1 activa Roles y Permisos. F4c2 completa Solicitudes con bandeja PENDIENTE, aprobación controlada y refresco coordinado del listado de usuarios. F5 elimina las decisiones por rol del sidebar, limita TRANSVERSAL al gestor IAM y retira la ruta y el chunk lazy de SIS-PRO sin borrar su código fuente.

## EXPECTED BEHAVIOR

La API V2 permite consultar y actualizar usuarios, administrar exclusivamente roles personalizados y reemplazar atómicamente asignaciones/capacidades dentro de la autoridad del actor. Los seis roles base permanecen visibles e inmutables. El catálogo de capacidades es read-only y excluye SIS-PRO. La única entrada Angular `admin-usuarios` ofrece Usuarios, Roles, Permisos y Solicitudes funcionales con visibilidad por capacidad y autoridad final en backend. El sidebar muestra módulos SIS-PE/SIS-POA autorizados por capacidades efectivas; TRANSVERSAL contiene solo “Usuarios y permisos” y SIS-PRO deja de formar parte del routing y grafo lazy de la aplicación actual.

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
- [x] Tab Roles F4c1 con filtros/paginación backend, estados y acciones por capacidad.
- [x] Alta y edición de roles personalizados; roles base visibles e inmutables.
- [x] Reemplazo atómico de capacidades de roles personalizados con catálogo real agrupado.
- [x] Tab Permisos F4c1 read-only con filtros/paginación backend y exclusión SIS-PRO.
- [x] Tests F4c1 de servicio, tablas, filtros, estados, autoridad y diálogos.
- [x] Tab Solicitudes F4c2 con tabla PENDIENTE, paginación y estados completos.
- [x] Dialog de aprobación con UO/rol reales, sistema derivado, scope normativo y gestión opcional.
- [x] POST de aprobación estricto desde Angular y refresco coordinado de Solicitudes/Usuarios.
- [x] Autoridad visual por `accounts.solicitud.view/approve` y error 400/403 sin pérdida de selección.
- [x] Tests F4c2 de contratos, tabla, capacidades, derivación y aprobación.
- [x] Sidebar sin campos, filtros ni nombres de rol hardcodeados.
- [x] SIS-PE y SIS-POA visibles por capacidades efectivas y con módulos filtrados por capacidad.
- [x] TRANSVERSAL limitado a la única entrada “Usuarios y permisos”.
- [x] Matriz de sidebar cubierta para FORMULADOR_POAU, JEFE_PE, JEFE_POA y SUPER_ADMIN.
- [x] Ruta/import lazy y navegación de SIS-PRO retirados sin borrar su código fuente.
- [x] Breadcrumb de `admin-usuarios` actualizado a “Usuarios y permisos”.
- [x] Tests focalizados F5, typechecks, build sin chunk SIS-PRO y checks de whitespace.

## OUT OF SCOPE

- Creación, edición o desactivación de capacidades.
- Cambios de modelos o migraciones.
- Creación de un sidebar alternativo o rediseño visual de navegación.
- Eliminación física del código fuente de SIS-PRO.
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

## F4C1 IMPLEMENTATION PLAN

1. **Dominio y alcance:** CORE/accounts; activar únicamente Roles y Permisos dentro del shell existente. Solicitudes, sidebar y F5 permanecen fuera de alcance.
2. **Reutilización:** extender `AdminUsuariosService`, `Paginado<T>`, `CapabilitiesService`, Material Table/Paginator/Dialog y tokens `--pip-*`; no existe un componente equivalente de roles/permisos en frontend.
3. **Contrato backend mínimo:** conservar endpoints F3b2a y ampliar solo el filtro `system` a `accounts` para que la paginación backend cubra todo sistema efectivo permitido; SIS-PRO sigue inválido y excluido.
4. **Servicio/DTOs:** tipar filtros, payloads create/edit y reemplazo de capacidades; mantener `listRoles()` completo para F4b2 y agregar consultas paginadas independientes para F4c1.
5. **Roles:** crear un componente de tab focalizado con tabla, filtros `search/system/active`, paginación, loading/error/empty y resumen de capacidades.
6. **Autoridad:** mostrar alta con `accounts.rol.create` sin inferir superusuario; mostrar edición con `accounts.rol.edit` y asignación con `accounts.capacidad.assign`; el backend resuelve 403/404 y roles base permanecen readonly.
7. **Diálogos:** usar un formulario create/edit con payloads estrictos y otro selector de capacidades real, filtrable y agrupado por SIS-PE/SIS-POA/accounts; errores no cierran ni pierden selección.
8. **Permisos:** crear un componente read-only con tabla, filtros `search/system/active`, paginación y defensa visual contra SIS-PRO; sin acciones create/edit.
9. **Diseño:** mantener la identidad municipal verde/dorada del shell y usar códigos monoespaciados y bandas de sistema como firma de “registro de autoridad”; responsive, foco restaurado y reduced motion.
10. **Pruebas:** cubrir URLs/query params/paginación, estados de tablas, tabs, roles base, payloads, 403 visible, PUT atómico, rollback de selección y ausencia de mutaciones/SIS-PRO en Permisos.
11. **Verificación:** pytest/ruff/migraciones por el ajuste backend, Karma focalizado F4c1+regresión F4b, build production, typecheck app/specs y `git diff --check`; lint solo si existe target.

## F4C2 IMPLEMENTATION PLAN

1. **Dominio y alcance:** CORE/accounts; activar únicamente Solicitudes dentro del shell existente. Sidebar y F5 permanecen fuera de alcance; no hay modelos, migraciones ni endpoints nuevos.
2. **Reutilización:** extender `AdminUsuariosService`, `Paginado<T>`, `AuthService.listPublicOrganizationalUnits`, `GestionHabilitadaService`, `CapabilitiesService`, Material Table/Paginator/Dialog, `adminApiErrorMessage` y el mapa normativo de scopes F4b2.
3. **Contrato:** tipar la fila real de `GET /api/v2/admin/solicitudes/`, el payload exacto de aprobación y su respuesta mínima; enviar solo `page` al listado y los seis campos permitidos al POST.
4. **Tabla:** crear un componente focalizado para solicitudes PENDIENTE con usuario, cargo, UO solicitada, fecha, estado, acciones, paginación y estados loading/error/empty con refresh explícito.
5. **Diálogo:** cargar roles activos administrables y UO públicas reales; preseleccionar la UO solicitada, incorporar al catálogo la UO histórica si ya no está vigente y conservar selección ante 400/403.
6. **Autoridad derivada:** ofrecer únicamente roles con sistema SIS-PE/SIS-POA; autoseleccionar sistema si es único o permitir elegir entre ambos si el rol es multi; reutilizar scope fijo para los seis roles base y selector SELF/DESCENDANTS/GLOBAL para custom.
7. **Gestión fiscal:** usar el candado `GestionHabilitadaService` solo para SIS-POA; enviar su UUID cuando existe y `null` para SIS-PE o cuando no hay gestión. No crear selector histórico, mock ni endpoint.
8. **Backend authority:** reemplazar la regla parcial por `SCOPES_FIJOS_ROLES_SISTEMA` y validar el rol con `puede_administrar_asignacion_rol`, ambos canónicos en `accounts.services`; los scopes base y la autoridad quedan protegidos aun fuera de Angular, con regresión focalizada.
9. **Integración:** al aprobar, quitar la fila local, recargar la página de Solicitudes y emitir un evento al shell; el shell recarga Usuarios si el actor puede verlo.
10. **Pruebas:** cubrir URLs/paginación, solo PENDIENTE, UO preseleccionada, sistema único/multi, scope fijo/custom, payload exacto, 400/403 sin pérdida, éxito y capacidades de tab/acción.
11. **Verificación:** pytest/ruff/migraciones por la corrección backend, Karma focalizado F4c2+regresión admin, build production, typecheck app/specs y whitespace check tracked/untracked; lint solo si existe target.

## F5 IMPLEMENTATION PLAN

1. **Dominio y alcance:** CORE/frontend para navegación transversal, con lectura de capacidades SIS-PE/SIS-POA; sin backend, modelos, migraciones, endpoints ni cambios de datos.
2. **Reutilización:** usar `CapabilitiesService`, `CapabilityGuard` y el sidebar existentes; declarar en el propio sidebar los grupos de capacidades necesarios para no ampliar el alcance de archivos del F5 cancelado.
3. **Sidebar:** eliminar `NavItem.roles`, `PermissionsService`, constantes de roles y `hasAnyRole`; cada entrada de sistema y `admin-usuarios` se filtra por al menos una capacidad declarada.
4. **Perfiles esperados:** `FORMULADOR_POAU` ve únicamente herramientas POAU dentro de SIS-POA; JEFE_PE ve únicamente SIS-PE más “Usuarios y permisos” cuando posee capacidad accounts; JEFE_POA ve SIS-POA completo; capacidades completas ven SIS-PE, SIS-POA y Usuarios, nunca SIS-PRO.
5. **TRANSVERSAL:** conservar exactamente una entrada a `/admin-usuarios`, visible por cualquiera de `accounts.usuario.view`, `accounts.rol.view`, `accounts.capacidad.view` o `accounts.solicitud.view`.
6. **Routing:** retirar SIS-PRO del contexto del sidebar y de `MainModule`; no modificar ni borrar `features/sis-pro/` y no convertir ocultamiento de menú en autorización.
7. **Código retirado:** no borrar `features/sis-pro/`; comprobar mediante build production que ya no se emite el chunk `features-sis-pro-sis-pro-module`.
8. **Presentación:** cambiar el breadcrumb de `admin-usuarios` a “Usuarios y permisos”; no modificar estilos ni identidad visual.
9. **Pruebas:** reemplazar specs por rol/SIS-PRO con escenarios de capacidades, cubrir la matriz de cuatro perfiles, contrato de routing sin SIS-PRO y regresión de administración/autenticación.
10. **Verificación:** Karma focalizado sidebar/routing/sistemas/admin/auth, typecheck app/specs, build production, búsqueda del chunk SIS-PRO y whitespace check tracked/untracked; lint se reporta no configurado porque `angular.json` no define target.

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

F4a agrega registro público; F4b1/F4b2 completan listado y edición de usuarios; F4c1 activa Roles y Permisos. F4c2 reemplaza el último placeholder por la bandeja de Solicitudes y aprobación sobre contratos V2 existentes. F5 integra esa entrada única en una navegación por capacidades y retira la ruta y carga lazy de SIS-PRO.

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
- `frontend/sispoa/src/app/features/admin-usuarios/roles-admin-tab.component.{ts,html,scss,spec.ts}` — tabla y acciones de roles F4c1.
- `frontend/sispoa/src/app/features/admin-usuarios/permissions-admin-tab.component.{ts,html,scss,spec.ts}` — catálogo read-only de permisos F4c1.
- `frontend/sispoa/src/app/features/admin-usuarios/role-form-dialog.component.{ts,html,scss,spec.ts}` — alta/edición custom.
- `frontend/sispoa/src/app/features/admin-usuarios/role-capabilities-dialog.component.{ts,html,scss,spec.ts}` — reemplazo atómico de capacidades.
- `frontend/sispoa/src/app/features/admin-usuarios/admin-api-error.ts` — extracción local de errores DRF para diálogos.
- `backend/apps/accounts/views_register.py` — autoridad canónica de rol/scope durante aprobación F4c2.
- `backend/apps/accounts/tests/test_register.py` — regresión de scopes base y bloqueo de elevación de rol.
- `frontend/sispoa/src/app/features/admin-usuarios/admin-role-scope.ts` — mapa compartido de scopes normativos.
- `frontend/sispoa/src/app/features/admin-usuarios/requests-admin-tab.component.{ts,html,scss,spec.ts}` — bandeja PENDIENTE F4c2.
- `frontend/sispoa/src/app/features/admin-usuarios/request-approval-dialog.component.{ts,html,scss,spec.ts}` — aprobación con catálogos reales.
- `frontend/sispoa/src/app/layout/sidebar/sidebar.component.{ts,spec.ts}` — menú exclusivamente por capacidades.
- `frontend/sispoa/src/app/main/main.module.{ts,spec.ts}` — grafo lazy sin SIS-PRO.
- `frontend/sispoa/src/app/core/components/breadcrumbs/breadcrumbs.component.{ts,spec.ts}` — etiqueta unificada del gestor IAM.

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
- [x] Roles usa las siete columnas requeridas, filtros/paginación backend y estados loading/error/empty.
- [x] Alta se muestra por `accounts.rol.create`; un 403 backend permanece visible sin inferir superusuario por rol o nombre.
- [x] Roles base no muestran edición/asignación; custom respeta `accounts.rol.edit` y `accounts.capacidad.assign`.
- [x] PUT de capacidades envía la selección completa, conserva selección ante error y agrupa SIS-PE/SIS-POA/accounts sin SIS-PRO.
- [x] Permisos es read-only, paginado, filtrable y no presenta acciones create/edit.
- [x] El filtro backend `system` acepta `accounts` y continúa rechazando SIS-PRO.
- [x] Verificación F4c1: 21 tests backend y 47 tests Karma pasan; Ruff, migraciones, typecheck app/specs, build y whitespace check pasan.
- [x] Solicitudes muestra únicamente filas PENDIENTE con UO/fecha real, paginación backend y estados loading/error/empty.
- [x] La UO solicitada queda preseleccionada y puede cambiarse por otra UO pública real.
- [x] Roles sin SIS-PE/SIS-POA no se ofrecen; sistema único se deriva y rol multi limita el selector a ambos sistemas válidos.
- [x] Los seis roles base usan scope normativo fijo y los custom permiten SELF/DESCENDANTS/GLOBAL.
- [x] El payload de aprobación contiene exclusivamente UO, rol, scope, sistema y gestión opcional; nunca password, `is_staff` ni privilegios extra.
- [x] Un 400/403 mantiene dialog y selecciones; éxito elimina/refresca Solicitudes y emite el UUID para refrescar Usuarios/detalle.
- [x] Backend bloquea roles fuera de autoridad con 403 y aplica `SCOPES_FIJOS_ROLES_SISTEMA` incluso ante POST directo.
- [x] Tab y acción respetan respectivamente `accounts.solicitud.view` y `accounts.solicitud.approve`.
- [x] Verificación F4c2: 45 tests backend y 64 tests Karma pasan; Ruff, migraciones, typecheck app/specs, build y whitespace check pasan.
- [x] El sidebar no contiene `roles`, `hasAnyRole` ni `PermissionsService`; cada módulo contextual se decide con `CapabilitiesService.tieneAlguna`.
- [x] TRANSVERSAL desaparece sin capacidades administrativas y contiene exactamente “Usuarios y permisos” con cualquiera de sus cuatro capacidades `view`.
- [x] `FORMULADOR_POAU` ve únicamente la entrada canónica POAU; JEFE_PE y JEFE_POA reciben sus módulos por capacidades de dominio.
- [x] La matriz focalizada demuestra FORMULADOR_POAU solo con POAU, JEFE_PE solo con SIS-PE más Usuarios, JEFE_POA con SIS-POA completo más Usuarios y SUPER_ADMIN con PE/POA/Usuarios, nunca SIS-PRO.
- [x] `MainModule` no registra `sis-pro` ni `inversion`; el build production no contiene chunk, módulo ni archivo SIS-PRO.
- [x] El breadcrumb de `/admin-usuarios` usa “Usuarios y permisos”.
- [x] Verificación F5: 43 tests Karma focalizados pasan; typecheck app/specs, build production y whitespace checks pasan.

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
cd backend; /home/chpass369/proyectos/poa/.venv/bin/python -m pytest -n 0 apps/accounts/tests/test_role_admin_v2.py
cd frontend/sispoa; CHROME_BIN=/snap/bin/chromium npm test -- --watch=false --browsers=ChromeHeadlessNoSandbox --include='src/app/features/admin-usuarios/admin-usuarios.service.spec.ts' --include='src/app/features/admin-usuarios/usuarios-lista.component.spec.ts' --include='src/app/features/admin-usuarios/usuario-edicion-dialog.component.spec.ts' --include='src/app/features/admin-usuarios/admin-usuarios-routing.module.spec.ts' --include='src/app/features/admin-usuarios/roles-admin-tab.component.spec.ts' --include='src/app/features/admin-usuarios/role-form-dialog.component.spec.ts' --include='src/app/features/admin-usuarios/role-capabilities-dialog.component.spec.ts' --include='src/app/features/admin-usuarios/permissions-admin-tab.component.spec.ts'
cd backend; /home/chpass369/proyectos/poa/.venv/bin/python -m pytest -n 0 apps/accounts/tests/test_register.py
cd frontend/sispoa; CHROME_BIN=/snap/bin/chromium npm test -- --watch=false --browsers=ChromeHeadlessNoSandbox --include='src/app/features/admin-usuarios/admin-usuarios.service.spec.ts' --include='src/app/features/admin-usuarios/usuarios-lista.component.spec.ts' --include='src/app/features/admin-usuarios/usuario-edicion-dialog.component.spec.ts' --include='src/app/features/admin-usuarios/admin-usuarios-routing.module.spec.ts' --include='src/app/features/admin-usuarios/roles-admin-tab.component.spec.ts' --include='src/app/features/admin-usuarios/role-form-dialog.component.spec.ts' --include='src/app/features/admin-usuarios/role-capabilities-dialog.component.spec.ts' --include='src/app/features/admin-usuarios/permissions-admin-tab.component.spec.ts' --include='src/app/features/admin-usuarios/requests-admin-tab.component.spec.ts' --include='src/app/features/admin-usuarios/request-approval-dialog.component.spec.ts'
cd frontend/sispoa; CHROME_BIN=/snap/bin/chromium npm test -- --watch=false --browsers=ChromeHeadlessNoSandbox --include='src/app/layout/sidebar/sidebar.component.spec.ts' --include='src/app/main/main.module.spec.ts' --include='src/app/core/components/breadcrumbs/breadcrumbs.component.spec.ts' --include='src/app/features/admin-usuarios/admin-usuarios-routing.module.spec.ts' --include='src/app/core/guards/capability.guard.spec.ts' --include='src/app/core/services/auth.service.spec.ts'
cd frontend/sispoa; npx tsc -p tsconfig.app.json --noEmit
cd frontend/sispoa; npx tsc -p tsconfig.spec.json --noEmit
cd frontend/sispoa; npm run build -- --configuration production
cd frontend/sispoa; npm run lint  # target no configurado; se reporta N/A
```

## RISKS

La derivación de sistema depende de prefijos `sis_pe.`/`sis_poa.`/`accounts.`; el campo legacy `sistema` conserva datos históricos y no es autoridad. Sin un campo de propietario o sistema en `Rol`, un rol personalizado vacío o solo `accounts.*` no pertenece a PE ni POA; F3b2b permite asignarlo únicamente a SUPER_ADMIN. Los solapamientos se validan en API y la fila de usuario serializa escrituras concurrentes, pero no existe todavía un constraint de base de datos que impida duplicados creados fuera de este endpoint. Resolver ambas deudas requiere cambios de modelo fuera del alcance. El catálogo público de UO permite enumerar nombres institucionales y devuelve la colección completa. `listRoles` exige `accounts.rol.view`; un actor con `accounts.solicitud.approve` sin esa capacidad verá un error de catálogo, porque F4c2 no inventa una fuente paralela de roles. En F4c1, la visibilidad del alta depende de `accounts.rol.create`, pero solo `is_superuser=True` puede completar el POST. En F4c2, la autoridad de aprobación se endureció para reutilizar la regla cerrada F3b2b: actores que no sean SUPER_ADMIN/JEFE_PE/JEFE_POA pueden recibir 403 aun si una asignación manual les otorgó `accounts.solicitud.approve`; esta restricción evita elevación de rol. La gestión fiscal usa el candado ADR-007 solo para SIS-POA y envía `null` para SIS-PE o cuando no hay gestión habilitada. El chunk lazy de administración quedó en 362.72 kB. F5 no convierte el sidebar en autoridad: los módulos conservan sus contratos de routing y el backend sigue siendo el límite final.

## ROLLBACK

Para revertir F4c2, restaurar el placeholder de Solicitudes, retirar sus dos componentes y el helper compartido de scope, devolver el mapa a `usuario-edicion-dialog`, revertir DTOs/métodos F4c2 y retirar del endpoint de aprobación los dos guards canónicos agregados. Para revertir F5, restaurar la configuración anterior de sidebar/MainModule, retirar los specs F5 y devolver la etiqueta del breadcrumb; no hay migraciones, endpoints ni código fuente SIS-PRO eliminado que deshacer.

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
- F4c1 reemplazó los placeholders de Roles y Permisos por tablas Material reales con filtros y paginación backend; Solicitudes permanece explícitamente reservado para F4c2.
- Roles permite alta/edición custom y reemplazo atómico de capacidades según capacidades del actor; los seis roles base son visibles e inmutables y el backend conserva la autoridad final.
- Permisos expone un catálogo estrictamente read-only y excluye defensivamente SIS-PRO; el filtro backend `system` ahora incluye el sistema efectivo `accounts` en roles y capacidades.
- Verificación backend F4c1: 21 tests pasaron secuencialmente en 262.35 s; Ruff pasó y `makemigrations accounts --check --dry-run` no detectó cambios.
- Verificación frontend F4c1: 47 tests Karma pasaron en Chrome Headless 151; typecheck app/specs pasó; build production pasó con hash `62a5bcd69633786a` y chunk lazy admin de `339.30 kB`.
- `git diff --check` y el check equivalente de todos los archivos untracked pasaron. Lint no se ejecutó porque `angular.json` no define target `lint`.
- No hubo migraciones, endpoints nuevos, sidebar, stage ni commit. Siguiente: F4c2 para la bandeja de Solicitudes.
- F4c2 reemplazó el último placeholder por una bandeja paginada de solicitudes PENDIENTE con fecha, UO solicitada, refresh y estados completos.
- El diálogo usa UO/roles reales, deriva SIS-PE/SIS-POA desde capacidades, fija scopes base, permite scopes custom y aplica gestión ADR-007 solo a SIS-POA.
- El payload POST es exacto y los errores 400/403 conservan selección; un éxito retira/refresca la solicitud y refresca el listado/detalle de Usuarios mediante evento tipado.
- La autoridad backend de aprobación ahora reutiliza `puede_administrar_asignacion_rol` y `SCOPES_FIJOS_ROLES_SISTEMA`, cerrando una elevación posible por POST directo y el drift de scopes de cuatro roles base.
- Auditoría posterior F4c2: se bloqueó todo cierre del dialog durante el POST para evitar una aprobación exitosa en backend sin callback de refresco en la bandeja; cancelar/cerrar vuelve a habilitarse al terminar el error.
- Verificación backend F4c2: 45 tests pasaron secuencialmente en 247.73 s; Ruff pasó y `makemigrations accounts --check --dry-run` no detectó cambios.
- Verificación frontend F4c2: 64 tests Karma pasaron en Chrome Headless 151; typecheck app/specs pasó; build production pasó con hash `545ef7940f17be47` y chunk lazy admin de `362.72 kB`.
- Whitespace check tracked/untracked pasó. Lint no se ejecutó porque `angular.json` no define target `lint`.
- No hubo migraciones, endpoints nuevos, sidebar/F5, stage ni commit. Siguiente: F5 con control explícito del tamaño del módulo admin.
- F5 agrupó capacidades SIS-PE, SIS-POA y accounts dentro del sidebar; ya no depende de roles visibles ni de `PermissionsService`.
- TRANSVERSAL contiene una sola entrada “Usuarios y permisos” y la matriz focalizada cubre FORMULADOR_POAU, JEFE_PE, JEFE_POA y SUPER_ADMIN.
- SIS-PRO fue retirado del contexto del sidebar y de `MainModule`; su código fuente permanece intacto y el build hash `3f295caf83d80041` no emite el chunk `features-sis-pro-sis-pro-module`.
- Verificación F5: 43 tests Karma focalizados pasan; typecheck app/specs y build production pasan; lint continúa N/A porque no existe target; whitespace tracked/untracked pasa.
- No hubo backend, migraciones, endpoints, stage, commit ni borrado del feature SIS-PRO. Los cambios ajenos preexistentes se preservaron.

## EVIDENCIA BUGFIX POST-LOGIN — 2026-08-25

- Flujo verificado antes de modificar código: `AuthService.login()` persiste el token, obtiene el usuario y navega a `/sistemas`; `AppComponent` solo carga capacidades y gestión fiscal durante su `ngOnInit()` cuando el token ya existía al arrancar la aplicación. Un login realizado después de ese arranque no inicializa ninguno de esos dos estados, mientras `CapabilityGuard` y `GestionHabilitadaGuard` esperan sus respectivos latches. La recarga funciona porque reinicia `AppComponent` con el token persistido.
- Alcance del plan: frontend CORE/autenticación y selector; sin backend, contratos, modelos, migraciones ni cambios visuales. Se reutilizarán `CapabilitiesService.cargar()`, `GestionHabilitadaService.cargar()` y los guards existentes, componiendo las cargas con RxJS antes de navegar, sin subscripciones anidadas ni permisos por defecto.
- Regresión a escribir antes de la corrección: login exitoso debe iniciar ambas cargas y no navegar a `/sistemas` hasta que terminen; el selector debe conservar únicamente SIS-PE/SIS-POA y nunca ofrecer SIS-PRO.
- Verificación prevista: Karma focalizado de login, selector, capacidades y guard; typecheck app/spec; build production; `git diff --check`; revisión de diff y runtime harness solo con credenciales seguras disponibles.
- La regresión se ejecutó antes del código productivo y falló como se esperaba: 2 fallos y 5 éxitos; `LoginComponent` no invocaba ninguna carga y navegaba inmediatamente, y el selector todavía presentaba SIS-PRO.
- Corrección aplicada: el login compone en paralelo las cargas existentes de capacidades y gestión fiscal y navega solo al completarse ambas; cada error de estado se degrada de forma cerrada mediante los latches existentes. El selector quedó alineado con F5 y expone únicamente SIS-PE/SIS-POA.
- Verificación final: 40/40 tests Karma focalizados pasaron; `tsc` de aplicación y specs pasó sin salida; build production pasó con hash `7f6b7dd35cd63e7d`; no se emitió archivo SIS-PRO; `git diff --check` pasó.
- Runtime harness: N/A; no se proporcionaron credenciales seguras y no se inspeccionaron secretos. Rollback exacto: revertir únicamente los cambios post-login en `login.component.ts`/spec y la retirada residual de SIS-PRO en los tres archivos de `features/sistemas`; no revertir el resto de esta tarea ni los cambios ajenos del working tree.

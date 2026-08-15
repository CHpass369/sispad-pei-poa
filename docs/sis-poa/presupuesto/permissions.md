# SIS-POA — Permisos y Capacidades IAM del Ciclo

## 1. Capacidades del ciclo

Sembradas por data migrations de `apps.accounts` (idempotentes,
`get_or_create`, preservan mapeos manuales):

| Capacidad | Nombre | Sistema | Orden | Migración |
|---|---|---|---|---|
| `sis_poa.budget.manage` | Gestionar presupuesto | sis-poa | — | `0002` (WP-03) |
| `sis_poa.budget.validate` | Validar presupuesto | sis-poa | — | `0002` (WP-03) |
| `sis_poa.budget.approve` | Aprobar presupuesto | sis-poa | 26 | `0004` (Fase 2) |
| `sis_poa.budget.import` | Importar presupuesto | sis-poa | 27 | `0004` (Fase 2) |
| `sis_poa.budget.reform` | Reformular presupuesto | sis-poa | 28 | `0004` (Fase 2) |
| `sis_poa.budget.audit_read` | Consultar auditoría del presupuesto | sis-poa | 29 | `0005` (Fase 11) |

## 2. Mapeo a roles

| Rol | Capacidades del ciclo |
|---|---|
| `superadmin` | todas (maneja/valida/aprueba/importa/reforma/audita) |
| `admin_presupuesto` | `manage`, `validate`, `approve`, `import`, `reform`, `audit_read` |
| `revisor_presupuesto` | `validate`, `approve` (aprueba, no gestiona) |
| `tecnico_admin` | `audit_read` (solo consulta de auditoría; rol V1 si existe) |
| `auditor` | `audit_read` |
| `admin_poa` | — (sin capacidades budget en el seed) |
| `responsable_unidad` / `revisor_planificacion` / otros | — |

Enforcement: `TieneCapacidad('sis_poa.budget.X')` en `permission_classes`
de cada acción (default global `IsAuthenticated` para lectura).

## 3. Mapeo por endpoint (de `views.py`)

### `sis_poa.budget.manage` — gestionar
- `POST /fiscal-years/{id}/enable/`, `POST /fiscal-years/{id}/close/`
- CRUD `directive-ceilings` (create/update/partial_update/destroy)
- CRUD `resources`, `mandatory-expenses`, `documents` (create/destroy)
- CRUD `programmatic-categories` (create/update/delete; `http_method_names`)
- `distributions`: create/update/destroy + `ajuste`
- `allocations`: create/update/destroy + `cerrar`
- `reserves`: create/update/destroy + `liberar`
- `expense-objects`: create/update/destroy
- `territorial-distributions`: create/update/destroy + `calcular`/`aplicar`/`liberar`

### `sis_poa.budget.approve` — aprobar (flujo de estados)
- `directive-ceilings`: `submit`, `observe`, `approve`, `freeze`
- `distributions`: `submit`, `observe`, `approve`, `freeze`
- `reforms`: `observe`, `approve`, `reject`, `apply`

### `sis_poa.budget.import` — importar planillas
- `imports`: `create` (upload), `map`, `validate`, `apply`

### `sis_poa.budget.reform` — reformular
- `reforms`: create/update/destroy + `submit`

### `sis_poa.budget.audit_read` — auditar
- `GET /budget/audit/` (`TieneCapacidadAuditoria`, paginado)

### Lectura (solo autenticado, default global)
- listados/detalles de todos los routers, `composition`, `catalogs`,
  `dashboard`, `control/summary`, `control/validate`, `hojas`, `errors`,
  `versions`, `validate` de distribuciones.

## 4. Notas

- `sis_poa.budget.validate` se siembra pero **no se usa en `budget/views.py`**
  (las validaciones las ejecutan servicios y las escrituras piden manage/
  approve); se mantiene para compatibilidad WP-03 (`techos/views_v2.py` la
  usa junto a `sis_poa.budget.manage` y `sis_poa.formulate`).
- Las migraciones solo **agregan** capacidades a roles existentes (no
  revocan ni crean roles).
- El frontend construye el menú por capacidades; las rutas del módulo
  `features/sis-poa/budget/` usan `CapabilityGuard` con estas capacidades.

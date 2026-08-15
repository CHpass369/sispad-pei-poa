# SIS-POA — Arquitectura del Módulo Presupuesto (`apps.budget`)

**Ciclo presupuestario SIS-POA** (Fases 1-12, commits `0500fbe`…`4f449d9`).

## 1. Visión general

`backend/apps/budget/` es la app Django del ciclo presupuestario: gestión fiscal,
techo directivo, categorías programáticas, distribución presupuestaria, reparto
territorial, importador Excel, fijación inmutable, control financiero central,
objetos del gasto, reformulaciones y auditoría. Se registra en `INSTALLED_APPS`
y se monta en `config/urls_v2.py`:

```python
path('sis-poa/budget/', include('apps.budget.urls')),
```

### Estructura del paquete

| Archivo | Rol |
|---|---|
| `models.py` (1497 líneas) | 17 entidades del ciclo + máquinas de estado (constantes `Estados*`, `Tipo*`) |
| `services.py` (2212 líneas) | Servicios de dominio: gestión fiscal, techo, distribución, fijación, objetos del gasto, reformulaciones, auditoría |
| `control.py` | `BudgetControlService`: núcleo financiero transaccional (Fase 8) |
| `territorial.py` | Reparto por distrito con ajuste de redondeo exacto (Fase 6) |
| `importer.py` | Importador Excel en staging: parseo, validación por severidad, aplicación (Fase 5) |
| `views.py` | API V2: 13 viewsets + 6 APIView (Composition, CatalogOptions, Dashboard, Control, Audit) |
| `serializers.py` | Serializers V2 con montos `Decimal → str` (convención `COERCE_DECIMAL_TO_STRING`) |
| `urls.py` | Router `budget_router` + paths sueltos bajo `/api/v2/sis-poa/budget/` |
| `migrations/0001…0007` | 7 migraciones (una por fase de modelos) |
| `tests.py` | **191 tests** (contratos, flujos, inmutabilidad, concurrencia, E2E) |

## 2. Patrones del módulo

1. **`TimeStampedModel`** (`apps.core.models`): `created_at/updated_at/created_by/updated_by` en todas las entidades; mixin del proyecto.
2. **Versionado inmutable con checksum SHA-256** (patrón `VersionInstrumento` de `apps.planificacion`): `DirectiveCeilingVersion` y `DistributionVersion` calculan el hash sobre datos semánticos ordenados (recursos/gastos, o asignaciones/reservas), `fijar()` congela (estado `FIJADO`, `inmutable=True`, hash, fecha, autor) y `save()` rechaza cualquier modificación posterior con `ValidationError`. Los serializers/viewsets devuelven **409** ante escrituras sobre versiones fijadas.
3. **Dinero `NUMERIC(18,2)`/`Decimal`**: nunca float; `CheckConstraint` de no negatividad en 7 tablas; tolerancia de redondeo `0.01` en la fijación (`UMBRAL_DIFERENCIA`).
4. **API V2 por namespace** (ADR-002): `/api/v2/sis-poa/budget/` con routers por dominio, paginación DRF y Swagger vía drf-spectacular.
5. **Capacidades IAM** (ADR-003): `sis_poa.budget.manage/approve/import/reform/audit_read` (+ `validate` de WP-03) mapeadas a roles por data migrations (`accounts.0002/0004/0005`); enforcement con `TieneCapacidad` en cada viewset.
6. **`EventoAuditoria` transversal** (`apps.auditoria`): cada operación registra eventos; `services.registrar_auditoria` mapea acciones semánticas del ciclo (CREATE/SUBMIT/FREEZE/REFORM/RELEASE…) al catálogo fijo `EventoAuditoria.Accion` (FREEZE→aprobar, REFORM→aprobar, RELEASE→modificar; se distinguen por el `resumen`).
7. **Control central sin estado**: `BudgetControlService` es un namespace de métodos estáticos; las escrituras corren en `transaction.atomic` con `select_for_update` sobre las filas del techo FIJADO (punto único de serialización de consumos).
8. **Nunca filas de total en BD**: todos los totales son agregaciones SQL (`models.Sum`).

## 3. Dependencias (apps reutilizadas, sin duplicar)

| App | Uso |
|---|---|
| `gestion` | `GestionFiscal` (estados del ciclo extendidos), `CicloFormulacion`/`EtapaFormulacion` (herencia de configuración) |
| `catalogos` | `RubroRecurso`, `FuenteFinanciamiento`, `OrganismoFinanciador`, `EntidadTransferencia`, `ObjetoGasto` (versionados) |
| `organizacion` | `DireccionAdministrativa`, `UnidadEjecutora`, `UnidadOrganizacional` |
| `territorio` | `Distrito` |
| `auditoria` | `EventoAuditoria` + `registrar_evento` |
| `accounts` | `TieneCapacidad`, `Usuario` |
| `core` | `TimeStampedModel` |

## 4. Capas de la solución

- **Backend**: Django 6.0.7 + DRF 3.17 + PostgreSQL 16 (PostGIS), drf-spectacular, openpyxl (importador), JWT/OIDC.
- **Frontend**: módulo lazy `features/sis-poa/budget/` con `BudgetService` tipado (patrón `SisPoaService`), pipe `moneda` (`Bs 1.234.567,89`), rutas con `CapabilityGuard` y 8 componentes con specs: `fiscal-year`, `directive-ceiling`, `programmatic-categories`, `distribution`, `imports`, `territorial`, `reforms`, `audit`. (75 specs en `features/sis-poa`; 225 specs frontend totales.)

## 5. Fases y commits

| Fase | Entregable | Commit |
|---|---|---|
| 1 | Gestión fiscal (estados, API, UI) | `0500fbe` |
| 2 | Techo directivo (recursos, SIGEP, obligatorios, fijación) | `a5f364b` |
| 3 | Categorías programáticas + catálogos | `efe2777` |
| 4 | Distribución (aperturas, fuentes, reservas) | `44b90f7` |
| 5 | Importador Excel | `58fa5d4` |
| 6 | Distribución territorial | `2a74a9b` |
| 7 | Fijación de distribución | `f37d525` |
| 8 | Control presupuestario central | `fb44e91` |
| 9 | Objetos del gasto (409 BUDGET_EXCEEDED) | `81d148a` |
| 10 | Reformulaciones | `da64eb8` |
| 11 | Auditoría de trazabilidad | `9f8f958` |
| 12 | Testing E2E del flujo completo | `4f449d9` |

## 6. Documentación por dominio

Ver `docs/sis-poa/presupuesto/`: `fiscal-year.md`, `directive-ceiling.md`,
`sigep-import.md`, `budget-distribution.md`, `programmatic-categories.md`,
`excel-importer.md`, `budget-control.md`, `reforms.md`, `permissions.md`,
`api.md`, `testing.md`, `database.md`.

# Reporte de Auditoría PIP-GAMS (2026-08-16)

Auditoría técnica del estado AS-IS del PIP-GAMS Sacaba, verificada contra el código fuente. Fuente única de hallazgos: verificación en código (marcas CONFIRMADO/INFERIDO) más los reportes de `docs/refactor-pip/`.

## Executive Summary

El PIP-GAMS es un monolito modular (27 apps Django, 32 features Angular, ~213 tablas en 9 esquemas) con un refactor V2 en curso y una deuda estructural importante: duplicaciones de entidades en múltiples apps, un ciclo de dependencias latente sobre core, API V1 con Sunset 2027-01-01 pero con el frontend íntegro en V1, y 5 hallazgos críticos que deben resolverse antes de cualquier cutover. El refactor de 2026 (1252 tests/7m03s, 5 frentes) estabilizó budget V2, kernel V2 de planificación y el motor de articulación; el siguiente paso es gobernanza (este bootstrap) y estabilización por bounded context.

## Architecture AS-IS

- Modular monolith (ADR-009), 27 apps, 32 features lazy. [CONFIRMADO]
- 9 esquemas PostgreSQL; renombrado 2026-08-15 rompió queries externas. [CONFIRMADO]
- API V1 (~118 rutas) + V2 (~102 rutas, 11 namespaces). [CONFIRMADO]
- Dual V1/V2 en planificacion, poau, inversion, workflow, indicadores; legacy autodeclarado en techos, presupuesto, modificaciones, seguimiento, recursos. [CONFIRMADO]
- Sin CI/CD; docker compose dev/full/prod. [CONFIRMADO]

## Architecture TO-BE

PIP{CORE, SIS-PE, SIS-POA, SIS-PRO, SHARED, PIP-INTEGRACION} con regla CORE←dominios, contratos explícitos, ownership único. Ver `PIP_SYSTEM_MAP.md`, `DOMAIN_BOUNDARIES.md`, `DATA_OWNERSHIP.md`.

## Critical Findings

| ID | Hallazgo | Evidencia | Impacto |
|---|---|---|---|
| F-1 | Bug doble prefijo `/api/v1/api/v1` en frontend organizacion | organizacion-ue.component.ts:35,79; organizacion-da.component.ts:35,79; organizacion-tree.component.ts:25 — ApiService antepone environment.apiUrl='/api/v1' y los paths ya lo llevan; sin interceptor corrector → 404 | Funcionalidad organizacion rota |
| F-2 | `core/validators.py:119` importa `apps.pad.models.PlanAnual` inexistente | validators.py:119; 4 validadores sin uso | ImportError si se invoca |
| F-3 | Techo duplicado expuesto en V2 | techos_* (apps.techos) en `/api/v2/sis-poa/techos/` y presupuesto_techo_* (budget) en `/api/v2/sis-poa/budget/directive-ceilings/` | Dos fuentes de verdad en contrato público |
| F-4 | Triple cadena operativa acción/operación/actividad/tarea | articulacion_*, indicadores_* (REMOVE_LATER), planificacion_accioncortoplazo, poau_* V2 | Ambigüedad de dominio |
| F-5 | GestionFiscal sin FK en ~12 apps | gestion_gestionfiscal canónica vs gestion PositiveIntegerField suelto en techos, presupuesto, recursos, organizacion, pad, poau, seguimiento, modificaciones, articulacion, evaluacion, workflow, indicadores | Sin integridad referencial de gestión |

## High Priority Findings

| ID | Hallazgo | Evidencia |
|---|---|---|
| F-6 | Renombrado 2026-08-15 sin retiro: queries externas con nombres viejos rotas | budget_*→presupuesto_*, workflow_*→flujo_*, catalogos_*→catalogo_*, accounts_*→cuentas_*, core_*→nucleo_* |
| F-7 | V1 Sunset 2027-01-01 pero frontend íntegro en V1 | DeprecationV1Middleware + ApiService apiUrl='/api/v1'; LEGACY_MENU_VISIBLE=true (cutover.config.ts) |
| F-8 | FKs genéricas entidad/entidad_id sin constraints en 9 apps | territorio_localizacionterritorial, documentos_documentoadjunto, auditoria_eventoauditoria, notificaciones_notificacion, flujo_instancia, flujo_observacion, modificaciones_solicitudmodificacion, pad_articulacionlog, codificacion_secuenciacodigo/homologacioncodigo |
| F-9 | Cero CI/CD: build/deploy manuales | make targets rotos (test-frontend, test-backend contradictorio con pytest.ini) |
| F-10 | Strings duplican catálogos en 4 apps | pad_articulacionsipeb, articulacion_seguimientopresupuesto, articulacion_asignacionobjetogasto, inversion_fuentefinanciamientoedtp |
| F-11 | Core dependiente de 14 apps de negocio (ciclo latente) | DEPENDENCY_MAP §4 |

## Medium Priority Findings

| ID | Hallazgo | Evidencia |
|---|---|---|
| F-12 | Monolitos budget/inversion | budget/models.py 1512 líneas, views 1532, services ~2100; budget.service.ts 1081 líneas ~60 interfaces |
| F-13 | Frontend strict:false + strictTemplates:false | tsconfig |
| F-14 | 28/32 features sin specs (32 specs Karma total) | frontend features |
| F-15 | environment.prod.ts hardcodea localhost:9999 | environment.prod.ts |
| F-16 | PermissionsService accede a authService['userSubject']; getRefreshToken() muerto | core/services/permissions.service.ts, auth.service.ts |
| F-17 | Paginado<T> ×5; presupuesto triplicado; techos cuádruple; PdeSa duplicado; TablaGenericaComponent muerto; deps muertas (echarts, ngx-echarts, ol, @angular/material) | features |
| F-18 | Rutas legacy sin CapabilityGuard | app.routes |
| F-19 | celery CMD -B hardcodeado; healthcheck celery inválido; serve.py solo GET/POST/PATCH | Makefile/docker |

## Duplications

Matriz completa en `DUPLICATION_ANALYSIS.md` (D1-D18). Pares principales: techo, categoría programática, lineamiento PAD triple, cadena operativa ×4, proyecto, workflow V1/V2, plan vs instrumento, modificación, sector ×4, gestión fiscal, más 7 duplicaciones frontend.

## Database Risks

1. Renombrado sin retiro: peso muerto y queries rotas. [CONFIRMADO]
2. FKs genéricas sin constraints: integridad imposible de validar. [CONFIRMADO]
3. Cero DeleteModel en 127 migraciones: nada se retira físicamente. [CONFIRMADO]
4. Strings donde hay catálogos: inconsistencia de valores. [CONFIRMADO]

## Integration Risks

1. Articulacion escribe/lee strings y modelos ajenos sin contrato formal (C-3/C-11/C-12). [CONFIRMADO]
2. SIS-PRO sin contrato de presupuesto aprobado (C-10). [CONFIRMADO]
3. Reportes: hub de lectura directa de casi todos los modelos. [CONFIRMADO]
4. Ciclo latente core↔dominios dificulta extracción. [CONFIRMADO]

## Frontend Risks

1. Todo el frontend consume V1 con Sunset en 2027-01-01. [CONFIRMADO]
2. Bug F-1 rompe organizacion. [CONFIRMADO]
3. Sin type safety (strict:false), specs ausentes, rutas sin guards. [CONFIRMADO]
4. environment.prod.ts con localhost:9999 — despliegue prod incorrecto. [CONFIRMADO]

## Backend Risks

1. Validators rotos (F-2). [CONFIRMADO]
2. Monolitos budget (F-12) dificultan evolución. [CONFIRMADO]
3. Workflow acoplado a 11 apps. [CONFIRMADO]
4. codificacion sin API: articulacion la consume vía import directo. [CONFIRMADO]

## Testing Risks

1. 1252 tests backend sólidos pero centrados en los 5 frentes del refactor; cobertura del legacy desconocida. [INFERIDO]
2. Frontend: 32 specs para 32 features. [CONFIRMADO]
3. make test-frontend roto; make test-backend contradice pytest.ini. [CONFIRMADO]

## Technical Debt

- Duplicaciones D1-D18; monolitos de código; strict:false; código muerto (getRefreshToken, TablaGenericaComponent, validadores sin uso, deps frontend); V1 como contrato real del frontend; outbox solo en preinversión; gestión fiscal suelta.

## Recommended Refactoring Order

1. **Fase 0 — Gobernanza** (este bootstrap): documentos AS-IS/TO-BE, ownership, contratos.
2. **Fase 1 — CORE**: resolver F-1, F-2, F-8 (FKs genéricas), F-16, F-18; quitar dependencia de negocio de core.
3. **Fase 2 — SIS-PE**: canónicos V2 instrumentos; unificar cadena operativa (F-4) hacia poau V2; resolver lineamiento PAD triple (D3) y strings de catálogo.
4. **Fase 3 — SIS-POA**: techo único (F-3), categoría única (D2), reformas únicas (D8), FK gestión (F-5), congelar escrituras legacy (techos/presupuesto/modificaciones V1).
5. **Fase 4 — SIS-PRO**: proyecto V2 único (D5), contrato C-10/C-11, extender outbox.
6. **Fase 5 — Integración transversal**: contratos formales (INTEGRATION_CONTRACTS.md), reportes vía servicios, V1→V2 (F-7) y cutover frontend.
7. **Fase 6 — Endurecimiento**: CI/CD (F-9), strict:true, specs frontend, deps muertas.
8. **Fase 7 — Producción**: environment prod, observabilidad, retiro físico post-cutover.

Detalle con tareas y criterios de salida: `REFACTORING_ROADMAP.md`.

## Suggested First Tasks

1. Fix doble prefijo organizacion (F-1) — bug de 404 inmediato.
2. Eliminar imports de PlanAnual en core/validators.py (F-2).
3. Designar techo canónico y congelar escrituras en techos V1 (F-3) — requiere tarea de contrato.
4. FK de gestión fiscal (F-5) — tarea de datos con migración.
5. Corregir make targets y alinear test-backend con pytest.ini (F-9).

## Referencias

- `docs/refactor-pip/FINAL_REPORT.md` — balance del refactor ejecutado (5 frentes).
- `docs/refactor-pip/LEGACY_DEPRECATION.md`, `docs/refactor-pip/ARQUITECTURA_ACTUAL.md`, `docs/refactor-pip/ARQUITECTURA_OBJETIVO.md`.
- `docs/refactor-pip/ADR/ADR-001..ADR-010`.
- `docs/pip_gams/WP00_baseline.md`, `docs/pip_gams/WP14_retiro_legacy.md`.
- `docs/sis-poa/presupuesto/implementation-plan.md`.
- Complementos: `docs/architecture/` completo (11 documentos ETAPA B).

Documento de gobernanza — creado en bootstrap ETAPA B (2026-08-16). No reemplaza a docs/refactor-pip/*; los complementa.

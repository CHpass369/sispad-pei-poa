# Contratos de Integración entre Dominios

Contratos necesarios entre dominios del PIP-GAMS. Estado: **EXISTE** (implementado), **EXISTE PARCIAL** (implementado de forma incompleta/acoplada), **NO EXISTE** (pendiente de diseño). No se implementa nada aquí: este documento fija el contrato futuro. Mecanismo de integración objetivo: `Dominio A → Application service → Contrato → Application service → Dominio B` (ver `PIP_SYSTEM_MAP.md`).

## 1. Contratos futuros necesarios

### 1.1 SIS-PE → SIS-POA

| # | Concepto | Entidades | Dirección | Estado |
|---|---|---|---|---|
| C-1 | PEI habilitado (instrumento publicado) | planificacion_versioninstrumento (V2) | SIS-PE → SIS-POA (lectura) | EXISTE PARCIAL: poau vínculos V2 leen versioninstrumento |
| C-2 | Resultado institucional | articulacion_resultadopei, planificacion_nodoestrategico | SIS-PE → SIS-POA | EXISTE PARCIAL: vía articulacion |
| C-3 | Acción institucional | planificacion_accioncortoplazo, poau_accioncortoplazo (V2) | SIS-PE → SIS-POA | EXISTE PARCIAL: duplicación de cadena (D4) |
| C-4 | Indicador y meta | indicadores_indicador, indicadores_metaprogramada, articulacion_indicadorcadena | SIS-PE → SIS-POA | EXISTE PARCIAL: vía articulacion |
| C-5 | Articulación PAD-PEI-POA | articulacion_articulacionpadpei, matrices A/B | SIS-PE → SIS-POA | EXISTE: motor de articulación activo |
| C-6 | Presupuesto base (insumo a techos) | resultadopad, productopad, metas | SIS-PE → SIS-POA | NO EXISTE: hoy no hay contrato formal |

### 1.2 SIS-POA → SIS-PRO

| # | Concepto | Entidades | Dirección | Estado |
|---|---|---|---|---|
| C-7 | Operación presupuestada | poau_operacion (V2), presupuesto_apertura | SIS-POA → SIS-PRO | EXISTE PARCIAL: inversion_vinculoproyectoactividad→poau_actividad |
| C-8 | Proyecto vinculado a actividad | inversion_vinculoproyectoactividad | SIS-PRO → SIS-POA (FK) | EXISTE: vínculo V2 |
| C-9 | Unidad ejecutora | organizacion_unidadejecutora | CORE → ambos | EXISTE (lectura directa, no contractual) |
| C-10 | Presupuesto aprobado por proyecto | presupuesto_apertura, presupuesto_asignacion_territorial | SIS-POA → SIS-PRO | NO EXISTE |
| C-11 | Fuente y categoría programática | catalogo_fuentefinanciamiento, presupuesto_categoria_programatica | SIS-POA/SHARED → SIS-PRO | EXISTE PARCIAL: fuentefinanciamientoedtp en inversion sin FK (string) |
| C-12 | Ejecución financiera de proyectos | presupuesto_gasto_obligatorio, inversion_proyecto | SIS-POA ↔ SIS-PRO | NO EXISTE |

## 2. Mecanismos de integración YA EXISTENTES

| Mecanismo | Ubicación | Rol | Estado |
|---|---|---|---|
| Motor de articulación | apps/articulacion (services/motor.py, materializacion_matriz.py) | Cadena PAD-PEI-POA con matrices A/B, 19+4 M2M | EXISTE, activo |
| Vínculos V2 poau→planificacion | poau V2 (accioncortoplazo→versioninstrumento) | PEI habilitado en POA | EXISTE |
| Vínculo proyecto→actividad | inversion_vinculoproyectoactividad → poau_actividad | SIS-PRO anclado a POA | EXISTE |
| Workflow motor genérico | apps/workflow V2 (flujo_definicion, flujo_instancia, flujo_tarea) | Aprobaciones de cualquier dominio | EXISTE |
| EventoOutbox | inversion_eventooutbox, inversion_mensajeentrante (preinversión) | Mensajería asíncrona de preinversión | EXISTE (solo preinversión) |
| Importación presupuesto | presupuesto_importacion(+detalle+error) | Carga SIGEP/Excel a budget | EXISTE |
| API V2 namespaces | /api/v2/{platform,core,catalogos,geo,integracion,auditoria,sis-pe,sis-poa,sis-poa/budget,sis-pro,me} | Superficie de contratos | EXISTE |
| DeprecationV1Middleware | middleware core | RFC 8594 Sunset V1 2027-01-01 | EXISTE |

## 3. Formato de contrato (registro)

| Campo | Valor |
|---|---|
| dominio origen / dominio destino | C-xx como arriba |
| concepto | nombre corto |
| entidades | tablas y campos intercambiados |
| dirección de lectura/escritura | quién lee / quién escribe |
| mecanismo | API V2, service de dominio, outbox, vínculo FK vía contrato |
| estado | EXISTE / EXISTE PARCIAL / NO EXISTE |

## 4. Brechas de integración priorizadas

1. **C-10/C-12 (SIS-POA→SIS-PRO)**: sin contrato formal de presupuesto aprobado a proyectos; SIS-PRO lee hoy vía imports directos.
2. **C-6 (SIS-PE→SIS-POA)**: el insumo de resultados/metas al presupuesto no está contractualizado (articulacion lo cubre parcialmente).
3. **C-11**: fuentefinanciamientoedtp sin FK al catálogo — debe pasar a catalogo_fuentefinanciamiento.
4. **Strings en articulacion** (seguimientopresupuesto, asignacionobjetogasto): deben volverse contrato a presupuesto_* y catalogo_objetogasto.

## 5. Contrato de cutover — techos legacy V2 → DirectiveCeiling

Cutover de la ruta `/api/v2/sis-poa/techos/` (`techos.TechoPresupuestario`) hacia
`/api/v2/sis-poa/budget/directive-ceilings/` (`budget.DirectiveCeiling`, ADR-005).
Registro completo del mapeo de campos y endpoints en
`docs/refactor-pip/LEGACY_DEPRECATION.md` §6.5.

| Aspecto | Valor |
|---|---|
| Contrato | `directive-ceilings` (canónico) reemplaza `techos` (legacy V2) |
| Deprecación | Blanda RFC 8594: `Deprecation: true`, `Sunset: Sun, 01 Jan 2027 00:00:00 GMT`, `Link: <...LEGACY_DEPRECATION.md>; rel="deprecation"` en `TechoViewSetV2.finalize_response` |
| Gestión | `gestion` legacy = año; `gestion` canónico = FK GestionFiscal (`gestion_anio` read-only) |
| Montos | `monto_total` → `composicion.techo_bruto`; los montos viven en `version.recursos[]` por origen |
| Estado | `activo` (bool) → `estado` (BORRADOR…FIJADO) + `version_actual`/`version.numero` |
| Frontend migrado | `features/techos` (2 vistas) y `features/sis-poa/sis-poa-techos.component.ts` → `BudgetService` |
| Datos | Sin sync legacy→canónico en esta fase (data migration = tarea separada) |

## Referencias

- `docs/refactor-pip/INTEGRATION_CONTRACTS.md` (refactor-pip) — nomenclatura previa.
- `docs/refactor-pip/ADR/ADR-004-articulation-model.md`, `ADR-005-budget-inside-sis-poa.md`, `ADR-008-instrument-versioning.md`.
- `docs/refactor-pip/SIS_PE_BOUNDED_CONTEXT.md`, `SIS_POA_BOUNDED_CONTEXT.md`, `SIS_PRO_BOUNDED_CONTEXT.md`, `PIP_INTEGRACION_BOUNDED_CONTEXT.md`.
- `docs/pip_gams/WP14_retiro_legacy.md`.
- `docs/sis-poa/presupuesto/implementation-plan.md`, `docs/sis-poa/presupuesto/sigep-import.md`.
- Complementos: `docs/architecture/DOMAIN_BOUNDARIES.md`, `DATA_OWNERSHIP.md`, `PIP_SYSTEM_MAP.md`.

Documento de gobernanza — creado en bootstrap ETAPA B (2026-08-16). No reemplaza a docs/refactor-pip/*; los complementa.

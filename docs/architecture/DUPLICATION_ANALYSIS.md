# Análisis de Duplicaciones

Matriz de duplicaciones estructurales detectadas en la auditoría (2026-08-16). Grado: CONFIRMADO (verificado en código/auditoría), PROBABLE (evidencia indirecta), POSIBLE (sospecha). Estado de deprecación oficial según `docs/refactor-pip/LEGACY_DEPRECATION.md`.

## 1. Tabla resumen

| # | Concepto | Lado A | Lado B | Lado C | Grado | Deprecación oficial |
|---|---|---|---|---|---|---|
| D1 | Techo presupuestario | techos_techopresupuestario/distribuciontecho/movimientotecho (apps.techos, V1 LEGACY autodeclarado) | presupuesto_techo_directivo/techo_version/distribucion_version (apps.budget, V2 canónico) | — | CONFIRMADO | techos→legacy; ambos expuestos en V2: `/api/v2/sis-poa/techos/` y `/api/v2/sis-poa/budget/directive-ceilings/` |
| D2 | Categoría programática | presupuesto_categoriaprogramatica (apps.presupuesto V1) | presupuesto_categoria_programatica (apps.budget V2) | — | CONFIRMADO | presupuesto→legacy |
| D3 | Lineamiento PAD | pad_lineamientoestrategico | articulacion_lineamientopad | codificacion_lineamientopad (canónico; docstring: "reemplaza a ambos") | CONFIRMADO | codificacion canónico |
| D4 | Cadena acción/operación/actividad/tarea | articulacion_* (accionpoa/operacionpoau/actividadpoau/tareapoau) | indicadores_* (operacion/tarea/producto, REMOVE_LATER) | planificacion_accioncortoplazo; poau_* (V2 canónica: operacion/actividad/tarea) | CONFIRMADO | poau V2 canónica; indicadores REMOVE_LATER |
| D5 | Proyecto | inversion_proyectoinversion (V1) | inversion_proyecto (V2) | — | CONFIRMADO | V2 canónico |
| D6 | Workflow | flujo_* (V1: envio_formulacion/revision/observacion/aprobacion) | flujo_*_motor (V2 motor: definicion/instancia/tarea/observacion_motor/aprobacion_motor/delegacion) | — | CONFIRMADO | V2 motor |
| D7 | Plan estratégico | planificacion_plan/planversion (V1) | instrumentoplanificacion/versioninstrumento (V2) | — | CONFIRMADO | V2 instrumentos |
| D8 | Modificación presupuestaria | modificaciones_solicitudmodificacion/cambiomodificacion/impactomodificacion (V1) | presupuesto_reforma/reforma_movimiento (V2) | — | CONFIRMADO | V2 reformas |
| D9 | Sector | pad_sectorpad | planificacion_sector | codificacion_sectoreconomico + catalogo_sectoreconomicopresupuestario | CONFIRMADO | ×4 variantes |
| D10 | Gestión fiscal | gestion_gestionfiscal (canónica) | ~12 apps guardan gestion como PositiveIntegerField suelto (techos, presupuesto, recursos, organizacion, pad, poau, seguimiento, modificaciones, articulacion, evaluacion, workflow, indicadores) | — | CONFIRMADO | canónica en gestion, sin FK en el resto |
| D11 | Unidad ejecutora | organizacion_unidadejecutora | SIS-PRO referencia unidades | PROBABLE | — |
| D12 | Presupuesto frontend | features/presupuesto (v1) | features/sis-poa/presupuesto (v2) | features/sis-poa/budget | CONFIRMADO | triplicado |
| D13 | Techos frontend | 4 vistas de techos | — | — | CONFIRMADO | cuádruple |
| D14 | Paginado<T> frontend | sis-pe, sis-poa, sis-pro, workflow-v2, budget | — | — | CONFIRMADO | ×5 duplicado |
| D15 | PdeSa | features/consolidacion | features/portal-publico | — | CONFIRMADO | duplicado |
| D16 | TablaGenericaComponent | muerto (sin uso) | — | — | CONFIRMADO | muerto |
| D17 | Módulos cargados | @angular/material (parcial), echarts, ngx-echarts, ol (sin uso) | — | — | CONFIRMADO | dependencias muertas |
| D18 | JWT/refresh | getRefreshToken() en auth.service | — | — | CONFIRMADO | código muerto |

## 2. Detalle por duplicación

### D1 — Techo presupuestario (impacto alto)
Dos modelos de techos conviven y AMBOS se exponen en V2. Riesgo de divergencia de datos y confusión de contratos. Deprecación de techos_* es prerrequisito para cutover de budget.

### D3 — Lineamiento PAD triple (impacto alto)
`codificacion_lineamientopad` se autodeclara canónico ("reemplaza a ambos"). pad y articulacion deben leer de codificacion vía contrato.

### D4 — Cadena operativa ×4 (impacto alto)
La cadena acción→operación→actividad→tarea existe en 4 apps con nombres distintos; `poau_*` V2 es canónica; `indicadores_*` operacion/tarea/producto tienen REMOVE_LATER según LEGACY_DEPRECATION.

### D10 — Gestión fiscal sin FK (impacto alto)
La entidad canónica existe en `gestion` pero la mayoría de apps guarda el año como entero suelto: sin integridad referencial ni trazabilidad.

### D12-D14 — Frontend (impacto medio)
Triplicado de presupuesto, cuádruple de techos, Paginado<T> ×5, PdeSa ×2: dispersión de UI que amplifica el costo de cada cambio de contrato.

## 3. Estado de deprecación oficial

| App/entidad | Estado | Fuente |
|---|---|---|
| techos, presupuesto, modificaciones, seguimiento, recursos (V1) | LEGACY autodeclarado | docstrings/LEGACY_DEPRECATION.md |
| indicadores operacion/tarea/producto | REMOVE_LATER | LEGACY_DEPRECATION.md |
| API V1 | Sunset 2027-01-01 (RFC 8594) | DeprecationV1Middleware |
| flujo V1, plan V1, poau V1, proyecto V1 | dual; V2 canónico | auditoría |

## 4. Recomendaciones (sin ejecutar — solo registro)

1. Elegir un único lado canónico por duplicación y documentarlo en DATA_OWNERSHIP.md.
2. Prohibir nuevos escritores al lado legacy; migrar lectores con contrato (INTEGRATION_CONTRACTS.md).
3. Eliminar el frontend legacy (v1) una vez el V2 cubra la feature (REFACTORING_ROADMAP.md, fases 3 y 4).

## Referencias

- `docs/refactor-pip/LEGACY_DEPRECATION.md` — estados de deprecación oficiales.
- `docs/refactor-pip/SCHEMA_MAPPING.md` — tablas de ambos lados de cada par.
- `docs/refactor-pip/ADR/ADR-002-sis-poa-bounded-context.md`, `ADR-005-budget-inside-sis-poa.md`.
- `docs/pip_gams/WP14_retiro_legacy.md` — plan de retiro de legacy.
- `docs/architecture/DUPLICATION_ANALYSIS.md` — este documento (referencia propia).
- `docs/refactor-pip/FINAL_REPORT.md` — balance del refactor ejecutado.

Documento de gobernanza — creado en bootstrap ETAPA B (2026-08-16). No reemplaza a docs/refactor-pip/*; los complementa.

# TASK PIP-CORE-003: Eliminar 12 validadores muertos restantes en core/validators.py

## DOMINIO

`core`

## OBJECTIVE

Aplicar el mismo patrón validado en PIP-CORE-002 a las 12 funciones validadoras restantes sin llamadores en `backend/apps/core/validators.py`, documentando la decisión de dominio por función.

## CONTEXT

Deuda registrada en el FINAL REPORT de PIP-CORE-002 (cerrada 2026-08-16). El censo de llamadores de esa tarea detectó 12 funciones adicionales con 0 referencias en `backend/*.py`: `validar_ponderaciones_suma_100`, `validar_fechas_consistentes`, `validar_codigo_unico`, `validar_sin_circulares`, `validar_duplicidad_codigo`, `validar_proyecto_sisin_obligatorio`, `validar_ejecucion_sin_evidencia_obligatoria`, `validar_modificacion_sin_justificacion`, `validar_modificacion_sin_documento`, `validar_categoria_programatica_distinta`, `validar_archivo_tipo_permitido`, `validar_geometria_valida`.

## CURRENT BEHAVIOR

- 12 funciones sin llamadores en el módulo, con acoplamientos de negocio latentes (proyectos SISIN, modificaciones, categorías programáticas, geometría).

## EXPECTED BEHAVIOR

- Cada función clasificada MUERTA (eliminar) o CONSERVADA con motivo documentado.
- El módulo queda sin funciones sin llamadores ni acoplamiento de negocio en core (regla CORE: DOMAIN_BOUNDARIES).

## IN SCOPE

- [ ] Re-auditar llamadores de las 12 funciones (grep amplio incl. getattr/registry/strings).
- [ ] Eliminar o conservar según decisión de dominio documentada.
- [ ] Suite core + suite completa en verde.

## OUT OF SCOPE

- Validadores con llamadores vivos.
- Cambiar lógica de validación de negocio; si una regla es requerida por el dominio, crear tarea propia en ese dominio.

## INVARIANTS

- `python -m pytest` global pasa (1252 baseline).
- No se cambian firmas de funciones vivas.

## DATABASE IMPACT

`ninguno`

## API IMPACT

`ninguno`

## FRONTEND IMPACT

`ninguno`

## FILES EXPECTED

- `backend/apps/core/validators.py` — modificar

## DEPENDENCIES

- PIP-CORE-002 (patrón de análisis ya validado)

## ACCEPTANCE CRITERIA

- [ ] Censo por función documentado (0 llamadores verificado).
- [ ] Módulo importa sin error; suite completa en verde.
- [ ] Decisión de dominio por función en FINAL REPORT.

## TESTS

```bash
cd backend; .venv\Scripts\python -m pytest apps/core -q
cd backend; .venv\Scripts\python -m pytest -q
```

## RISKS

Bajo (mismo patrón que PIP-CORE-002, ya validado). Mitigación: censo amplio antes de eliminar.

## ROLLBACK

`git revert <commit>`.

## FINAL REPORT

**Archivos modificados (1):** `backend/apps/core/validators.py` — 316 → 112 líneas.

**Decisión por función (10 ELIMINADAS, 2 CONSERVADAS):**

| Función | Decisión | Motivo (censo + dueño de dominio) |
|---|---|---|
| `validar_ponderaciones_suma_100` | CONSERVADA | Regla de negocio real sin dueño: ponderaciones de vínculos son SIS-PE (planificacion/models_v2.py:467-470 valida rango 0-100 y requerida; articulacion/models.py:346 campo ponderacion) pero la regla suma=100 NO está implementada en ningún dominio. → requiere tarea de traslado a SIS-PE. |
| `validar_fechas_consistentes` | ELIMINADA | Util genérica inicio<fin; concepto con dueño en SIS-POA: gestion/services.py:49 `validar_fechas_gestion` (cierre>apertura, plurianual). 0 llamadores, 0 tests. |
| `validar_codigo_unico` | ELIMINADA | Util genérica de unicidad codigo+gestion; unicidad resuelta por constraints en dominios (ej. budget/models.py:821-826 UniqueConstraint gestion+codigo). 0 llamadores, 0 tests. |
| `validar_sin_circulares` | ELIMINADA | 0 llamadores y disfuncional para modelos actuales: usa convención `model._padre_field` que NO existe en ningún modelo del repo (0 matches). Jerarquías reales (ProgrammaticCategory.parent, ObjetoGasto.padre) sin validación de ciclos → deuda registrada. |
| `validar_duplicidad_codigo` | ELIMINADA | Duplica `validar_codigo_unico` (misma lógica sin exclude_id). 0 llamadores, 0 tests; unicidad en dominios vía constraints. |
| `validar_proyecto_sisin_obligatorio` | ELIMINADA | Regla con dueño en SIS-PRO: workflow/consolidacion.py:540-556 (alerta `proyecto_sin_sisin` en consolidación); campo codigo_sisin en inversion/models.py:25. Core no debe tener reglas SIS-PRO (DOMAIN_BOUNDARIES). |
| `validar_ejecucion_sin_evidencia_obligatoria` | ELIMINADA | Regla con dueño en SIS-POA: seguimiento/services.py:237-245 (alerta `sin_evidencia`: avance_fisico>0 sin evidencia; modelo seguimiento/models.py:131). |
| `validar_modificacion_sin_justificacion` | ELIMINADA | Regla esencial con dueño en el modelo modificaciones: SolicitudModificacion.motivo obligatorio (models.py:47, sin blank). 0 llamadores, 0 tests. |
| `validar_modificacion_sin_documento` | ELIMINADA | Regla NO exigida por el dominio actual: CambioModificacion 1:N opcional y informe_tecnico/documento_legal blank=True por diseño (estados borrador→en_revision). Contiene además código muerto interno (2º bloque de error inalcanzable). Si la normativa exige documento para aprobación → tarea SIS-POA. |
| `validar_categoria_programatica_distinta` | ELIMINADA | Regla con dueño en budget V2: UniqueConstraint(gestion,codigo) models.py:821-826 + clean() ProgrammaticCategory (misma gestión). 0 llamadores, 0 tests. |
| `validar_archivo_tipo_permitido` | ELIMINADA | Concepto con dueño en CORE documentos: documentos/services.py:38 `validar_tipo_archivo`. 0 llamadores, 0 tests. |
| `validar_geometria_valida` | CONSERVADA | Regla de dominio sin dueño: territorio (models.py) define MultiPolygonField/GeometryField null/blank sin clean/validate; 0 validación GEOS fuera de core. Validación topológica es requisito real de datos espaciales (LocalizacionTerritorial). → requiere tarea de traslado a territorio. |

**Evidencia de censo:**
- Nombre exacto de las 12 en `backend/*.py`: 12 matches, todos en `validators.py` (definiciones). 0 en views/serializers/services/tasks/admin/signals/commands/tests.
- Imports desde `apps.core.validators`: solo las 5 vivas (`validar_meta_no_negativa`, `validar_nombre_corto`, `validar_lineas_igual_total`, `validar_ejecucion_no_negativa`, `validar_valor_no_negativo`). 0 star imports, 0 imports de las 12.
- Patrones dinámicos: 0 `getattr`/`globals`/strings `"validar_"` apuntando a las 12.
- Fuera de backend: solo `docs/ARQUITECTURA.md:484-489` menciona 4 (deuda de docs ya registrada, ver abajo).
- Conceptos de negocio auditados en apps/inversion, modificaciones, budget, territorio, seguimiento, workflow, articulacion, planificacion, documentos, gestion.

**Tests ejecutados:**
- `python -c "from apps.core.validators import *"` → ok
- `pytest apps/core -q` → **26 passed** (baseline 26, delta 0)
- `pytest -q` completo → **1252 passed** (baseline 1252, delta 0)

**Deuda detectada (registrada, no ejecutada):**
1. `validar_ponderaciones_suma_100` y `validar_geometria_valida` conservadas: reglas de dominio sin dueño → crear tareas de traslado a SIS-PE (suma=100 de ponderaciones) y territorio (validación GEOS en serializers de Distrito/UnidadTerritorial/LocalizacionTerritorial).
2. `validar_sin_circulares` eliminada: si se requiere validación de ciclos en jerarquías (ProgrammaticCategory.parent, ObjetoGasto.padre) → tarea en SIS-POA/SHARED.
3. `validar_modificacion_sin_documento` eliminada: si la normativa exige documento para aprobación de modificaciones → tarea en SIS-POA (validación por estado).
4. `docs/ARQUITECTURA.md:484-495` sigue listando validaciones eliminadas (incluye 3 de estas 12: fechas_consistentes, codigo_unico, sin_circulares) → cubrir en PIP-ARCH-003 (backlog).

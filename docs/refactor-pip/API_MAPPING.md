# FASE 8 — MAPA DE API POR BOUNDED CONTEXT (SISPOA → PIP)

> Mapeo de las rutas de API entre V1 (legacy), V2 (ADR-002) y los bounded contexts objetivo de PIP (ARQUITECTURA_OBJETIVO.md §5).
> Esta fase registra los namespaces V2 de los dominios transversales que faltaban: **core, catalogos, geo, integracion, auditoria** (todas en `backend/config/urls_v2.py`).
> Complemento de `LEGACY_DEPRECATION.md` (política) y `ARQUITECTURA_OBJETIVO.md` (destino).

---

## 1. Mapa V1 → V2 → destino PIP

Estado: **V2** = existe equivalente en `/api/v2/`; **solo v1** = sin equivalente V2 todavía; **solo v2** = no existió en V1 (creado directamente en V2); **por migrar** = será reemplazado en fases posteriores.

| App V1 | Ruta V1 (`/api/v1/…`) | Equivalente V2 | Destino PIP | Estado |
|---|---|---|---|---|
| accounts | `auth/usuarios/`, `auth/roles/` | — (identidad en `/api/v2/me/`) | PIP CORE (cuentas) | solo v1 |
| accounts | `auth/login|refresh|logout|password-reset*` | `me/` | PIP CORE (IAM) | V2 |
| core | `dashboard/` | — | PIP CORE | solo v1 |
| gestion | `gestiones/` | `sis-poa/budget/fiscal-years/` (FiscalYearViewSet) | SIS-POA (gestión fiscal) | V2 — no duplicado (ver §4) |
| gestion | `ciclos/`, `etapas/` | — | SIS-POA (formulación) | solo v1 |
| organizacion | `tipos-unidad/`, `unidades/`, `direcciones-administrativas/`, `unidades-ejecutoras/`, `asignaciones-usuario-unidad/` | `core/tipos-unidad/`, `core/unidades/`, `core/direcciones-administrativas/`, `core/unidades-ejecutoras/`, `core/asignaciones-usuario-unidad/` | PIP CORE (organización) | **V2 (FASE 8)** |
| catalogos | `clasificadores-institucionales/`, `rubros/`, `objetos-gasto/`, `fuentes/`, `organismos/`, `entidades-transferencia/`, `finalidades-funciones/`, `unidades-medida/`, `tipos-operacion/`, `tipos-producto/`, `tipos-proyecto/`, `tipos-financiamiento/`, `versiones-catalogo/` | `catalogos/…` (mismos slugs) | PIP CATÁLOGOS | **V2 (FASE 8)** |
| normativa | `versiones-normativa/`, `reglas-presupuestarias/` | — | PIP CATÁLOGOS (normativa) | solo v1 |
| planificacion | `planes/`, `versiones-plan/`, `nodos-planificacion/` | `sis-pe/instrumentos/`, `sis-pe/versiones/`, `sis-pe/nodos/` | SIS-PE (PAD/PEI) | V2 (FASE 3) |
| planificacion | `acciones-mediano-plazo/`, `acciones-corto-plazo/`, `articulaciones/`, `formulacion/`, `articular/`, `matriz-completa/` | — (vinculable vía `sis-pe/vinculos/`) | SIS-PE | solo v1 / por migrar |
| indicadores | `indicadores/`, `metas-programadas/`, `medios-verificacion/`, `supuestos/` | `sis-pe/evaluaciones/`, `sis-pe/lecciones/`, `sis-pe/recomendaciones/` | SIS-PE | V2 (FASE 3) parcial |
| indicadores | `operaciones/`, `tareas/`, `productos/` (jerarquía legacy) | `sis-poa/operaciones/`, `sis-poa/actividades/`, `sis-poa/tareas/` (canónica) | SIS-POA | V2 — legacy REMOVE_LATER (LEGACY_DEPRECATION #17) |
| recursos | `estimaciones/`, `estimaciones-plurianuales/` | — | SIS-POA (recursos) | solo v1 |
| techos | `techos/…` (3 tablas legacy) | `sis-poa/techos/` (TechoViewSetV2), `sis-poa/budget/directive-ceilings/` | SIS-POA | V2 (FASE 4) |
| presupuesto | `programas/`, `proyectos-presupuestarios/`, `actividades-presupuestarias/`, `lineas-presupuestarias/` | `sis-poa/budget/programmatic-categories/`, `allocations/`, `expense-objects/` | SIS-POA | V2 — legacy DEPRECATE (LEGACY_DEPRECATION #3) |
| inversion | `proyectos-inversion/`, `programacion-plurianual/`, `programacion-fisica-financiera/` | `sis-pro/proyectos/` | SIS-PRO | V2 (FASE 6) |
| inversion (preinv.) | — (no existió en V1) | `sis-pro/itcps/`, `tdrs/`, `edtps/`, `revisiones/`, `observaciones/`, `aprobaciones/`, `documentos-preinv/`… | SIS-PRO (preinversión) | solo v2 (FASE 6) |
| territorio | `distritos/`, `unidades-territoriales/`, `localizaciones/` | `geo/distritos/`, `geo/unidades-territoriales/`, `geo/localizaciones/` | PIP GEO | **V2 (FASE 8)** |
| pad | `pad/sectores-pad/`, `pad/politicas-pad/`, `pad/lineamientos/`, `pad/resultados-territoriales/`, `pad/productos-territoriales/`, `pad/articulaciones-sipeb/`, `pad/programaciones-anuales/` | `integracion/resultados-pad/`, `integracion/productos-pad/`, `integracion/lineamientos-pad/` | SIS-PE (PAD) + PIP INTEGRACIÓN | V2 (FASE 8) parcial |
| workflow | `envios/`, `revisiones/`, `observaciones/`, `aprobaciones/`, `consolidacion/` | `platform/workflow-definiciones/`, `workflow-instancias/`, `workflow-tareas/`; preinversión en `sis-pro/revisiones/`… | PIP CORE (workflow) | V2 (FASE 3/6) parcial |
| documentos | `documentos/` | `sis-pro/documentos/` (documentos de proyecto) | PIP CORE (documentos) | V2 parcial |
| reportes | `reportes/` (+actions `poa_unidad`, `consolidado`, `proyectos`, …) | — | REPORTES | solo v1 / por migrar |
| auditoria | `eventos/` | `auditoria/eventos/` (EventoAuditoriaViewSet) + `sis-poa/budget/audit/` (AuditLogView) | PIP AUDITORÍA | **V2 (FASE 8)** |
| poau | `poau/poaus/`, `poau/actividades/`, `poau/ejecucion-fisica/`, `poau/ejecucion-financiera/` | `sis-poa/poas/`, `acciones/`, `operaciones/`, `actividades/`, `tareas/`, `programaciones/` | SIS-POA | V2 (FASE 4) |
| evaluacion | `evaluaciones/`, `criterios-evaluacion/`, `resultados-evaluacion/`, `lecciones-aprendidas/`, `recomendaciones/` | `sis-pe/evaluaciones/`, `lecciones/`, `recomendaciones/` | SIS-PE | V2 (FASE 3) parcial |
| modificaciones | `solicitudes-modificacion/`, `cambios-modificacion/`, `impactos-modificacion/` | `sis-poa/budget/reforms/` | SIS-POA | V2 (FASE 4) |
| notificaciones | `tipos/`, `notificaciones/`, `preferencias/` | — | PIP CORE (notificaciones) | solo v1 |
| seguimiento | `reportes-seguimiento/`, `entradas/`, `alertas/`, `umbrales/` | — | SIS-POA (seguimiento) | solo v1 |
| articulacion | `articulacion/resultados-pad/`, `productos-pad/`, `resultados-pei/`, `productos-pei/`, `articulaciones-pad-pei/`, `indicadores/`, `acuerdos/`, `normativas/`, `codigos-nivel/`, `lineamientos-pad/`, `matrices/*` | `integracion/…` (mismos slugs + `matrices/m1_pad_pei…m5_objetos_gasto`) | PIP INTEGRACIÓN (cadena PAD-PEI) | **V2 (FASE 8)** |
| articulacion | `articulacion/acciones-poa/`, `operaciones/`, `actividades/`, `normativas-actividad/`, `tareas/`, `normativas-tarea/`, `seguimientos/`, `asignaciones-gasto/` | `sis-poa/poas|acciones|operaciones|actividades|tareas|programaciones/` (canónico) | SIS-POA | V2 (FASE 4) — legacy articulación operativa |
| acciones_correctivas | `acciones-correctivas/`, `compromisos-accion-correctiva/` | — | PIP CORE (acciones correctivas) | solo v1 |

## 2. Arquitectura objetivo vs. V2 (cumplimiento por dominio)

| Bounded context objetivo (§5) | Namespace V2 | Estado |
|---|---|---|
| PIP CORE (cuentas, organización, workflow, documentos, notificaciones) | `platform/` (workflow + me) y `core/` (organización) | Parcial: workflow V2 listo; organización V2 en **FASE 8**; cuentas/dashboard/documentos/notificaciones/acciones correctivas quedan como alias V1 |
| PIP CATÁLOGOS | `catalogos/` | **FASE 8**: 13 viewsets registrados; normativa aún solo V1 |
| SIS-PE (pe/pad/pei) | `sis-pe/` | Cumplido (FASE 3); la estructura PAD legacy (app `pad`) queda parcialmente en V1 hasta su cutover |
| SIS-POA (gestiones, techos, distribuciones, asignaciones, poas, poaus, programación-presupuestaria) | `sis-poa/` + `sis-poa/budget/` | Cumplido (FASE 4): fiscal-years (budget), techos, distribuciones, asignaciones, poas, programaciones |
| SIS-PRO (proyectos, preinversión) | `sis-pro/` | Cumplido (FASE 6) |
| PIP INTEGRACIÓN (articulaciones) | `integracion/` | **FASE 8**: cadena PAD-PEI + matrices; outbox/mensajes/referencias externas aún sin API V2 |
| PIP AUDITORÍA | `auditoria/` | **FASE 8**: eventos de auditoría |
| PIP GEO | `geo/` | **FASE 8**: distritos, unidades territoriales, localizaciones |
| REPORTES | — | Pendiente (solo V1, `reportes/`) |

## 3. Política de compatibilidad (resumen de `LEGACY_DEPRECATION.md`)

- **V1 se mantiene intacto** hasta que el cutover V2 cubra todos los consumidores de cada dominio (palanca `LEGACY_MENU_VISIBLE`, `cutover.config.ts`). Ninguna ruta V1 se elimina ni se altera en esta fase.
- **Deprecación escalonada** (nunca en silencio): (1) marcar con header `Deprecation` (RFC 8594) + `Warning: 299` y log de uso por consumidor; (2) ventana de observación mínima de 1 ciclo de gestión (30 días para infraestructura); (3) retiro con 404 solo tras la ventana, con backup `-Fc` verificado y registro en `pip_core.mapa_migraciones_legacy`.
- **Estrategias por referencia**: Deprecated API (V1), Compat view (presupuesto/techos legacy), Adapter (`TechoViewSetV2`, importador SIGEP), Alias (infraestructura), KEEP con coexistencia (perfiles `SISPOA_GASTOS_*`, `sistema_origen='SISPOA'`). Detalle por referencia en `LEGACY_DEPRECATION.md` §2-4.
- **Frontend**: los consumidores V2 (BudgetService, SisPoaService, SisPeService, WorkflowV2Service) usan `environment.apiUrlV2`; los nuevos namespaces de esta fase **no tienen consumidor frontend aún** — se exponen para el cutover por dominio y para que las integraciones dejen de apuntar a V1.

## 4. Endpoints V2 nuevos en la FASE 8

Todos registrados en `backend/config/urls_v2.py` (solo viewsets ya existentes, sin views nuevos; imports con alias por dominio).

| Namespace | Endpoints |
|---|---|
| `/api/v2/core/` (PIP CORE) | `tipos-unidad/`, `unidades/` (+ `unidades/arbol/`), `direcciones-administrativas/`, `unidades-ejecutoras/`, `asignaciones-usuario-unidad/` |
| `/api/v2/catalogos/` (PIP CATÁLOGOS) | `clasificadores-institucionales/`, `rubros/`, `objetos-gasto/`, `fuentes/`, `organismos/`, `entidades-transferencia/`, `finalidades-funciones/`, `unidades-medida/`, `tipos-operacion/`, `tipos-producto/`, `tipos-proyecto/`, `tipos-financiamiento/`, `versiones-catalogo/` (todos con action `importar/` heredada de `CatalogoImportMixin`) |
| `/api/v2/geo/` (PIP GEO) | `distritos/`, `unidades-territoriales/`, `localizaciones/` |
| `/api/v2/integracion/` (PIP INTEGRACIÓN) | `resultados-pad/`, `productos-pad/`, `resultados-pei/`, `productos-pei/`, `articulaciones-pad-pei/`, `indicadores/`, `lineamientos-pad/`, `acuerdos/`, `normativas/`, `codigos-nivel/`, `matrices/m1_pad_pei/`, `m2_pei_poa/`, `m3_poa_poau/`, `m4_presupuesto/`, `m5_objetos_gasto/` |
| `/api/v2/auditoria/` (PIP AUDITORÍA) | `eventos/` |

Decisión: **no** se registró `gestiones/` en `core/` — la gestión fiscal ya vive en `/api/v2/sis-poa/budget/fiscal-years/` (FiscalYearViewSet, apps.budget) desde la FASE 4; duplicar `GestionFiscalViewSet` crearía dos fuentes para el mismo concepto (principio "una sola fuente de verdad", ARQUITECTURA_OBJETIVO §2.8).

## 5. Hallazgos y desvíos de la FASE 8

- **Nombres reales de viewsets verificados**: `apps/organizacion/views.py` → `TipoUnidadViewSet`, `UnidadOrganizacionalViewSet` (con action `arbol`), `DireccionAdministrativaViewSet`, `UnidadEjecutoraViewSet`, `AsignacionUsuarioUnidadViewSet`; `apps/catalogos/views.py` → 13 viewsets (todos con `CatalogoImportMixin`); `apps/territorio/views.py` → 3 viewsets; `apps/auditoria/views.py` → `EventoAuditoriaViewSet`; `apps/articulacion/views.py` → 18 viewsets + `apps/articulacion/views_matrices.py` → `MatrizViewSet`. No hubo ningún viewset inexistente respecto a lo esperado.
- **Se registraron 3 viewsets extra** que la tarea no enumeraba pero existen en las apps y completan el dominio: `TipoUnidadViewSet`, `AsignacionUsuarioUnidadViewSet` (core) y `UnidadTerritorialViewSet`, `LocalizacionTerritorialViewSet` (geo) — todos cubiertos por V1, todos por el mismo viewset.
- **Integración registra la cadena estratégica** (resultados/productos PAD-PEI, articulaciones, indicadores, lineamientos, acuerdos, normativas, códigos de nivel) y las 5 matrices; los viewsets **operativos** de `articulacion` (acciones-poa, operaciones, actividades, tareas, seguimientos, asignaciones-gasto, normativas-*) NO se registran en V2 porque su dominio es SIS-POA y ya existe el canónico en `/api/v2/sis-poa/` (SPLIT documentado en ARQUITECTURA_OBJETIVO §5).
- **`MatrizViewSet` no tiene `list`/`retrieve`** (es `viewsets.ViewSet` con solo 5 actions): `/api/v2/integracion/matrices/` responde 404 por diseño, idéntico a V1; las rutas reales son `/api/v2/integracion/matrices/m{1..5}_*/`.
- **Colisión latente preexistente (no tocada)**: `urls_v2.py` importa `VinculoViewSet` dos veces sin alias (apps.inversion.views_v2 y apps.planificacion.views_v2); el último import gana, por lo que tanto `sis-pe/vinculos/` como `sis-pro/vinculos/` apuntan al de planificación. No se modificó por no estar en alcance (FASE 8), pero debe corregirse en una fase futura con alias.
- **Los nombres de URL DRF** son `v2-core-unidades-list/-detail`, `v2-catalogos-fuentes-list`, `v2-geo-distritos-list`, `v2-integracion-matrices-m1-pad-pei`, etc. (basename + sufijo del router), verificados por `reverse()`.

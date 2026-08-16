# Inventario de Módulos — Backend (27 apps) y Frontend (32 features)

Inventario completo de módulos con responsabilidad aparente, dominio probable, dependencias, entidades, endpoints y estado. Estado: `activo` (núcleo actual), `legacy` (autodeclarado V1 en deprecación), `dual` (conviven V1 y V2). Dominios: CORE, SIS-PE, SIS-POA, SIS-PRO, SHARED, INFRAESTRUCTURA, UNKNOWN.

## 1. Backend (27 apps, `backend/apps/`)

| # | App | Responsabilidad aparente | Dominio | Dependencias principales | Entidades | Endpoints | Estado | Problemas |
|---|---|---|---|---|---|---|---|---|
| 1 | core | Mixins base, middleware deprecación, dashboard, validadores, permisos | CORE | planificacion, presupuesto, techos, workflow, organizacion, normativa, poau, pad, indicadores, articulacion, catalogos, codificacion, gestion, seguimiento | nucleo_* | V1/V2 | dual | Ciclo latente: core depende de dominios de negocio; validators.py:119 importa PlanAnual inexistente |
| 2 | accounts | Usuario, Rol, Capacidad, AlcanceOrganizacional, JWT | CORE | auditoria | cuentas_* | V1/V2 | activo | — |
| 3 | organizacion | TipoUnidad, UnidadOrganizacional, DireccionAdministrativa, UnidadEjecutora, AsignacionUsuarioUnidad | CORE | core | organizacion_* | V1/V2 | activo | Frontend organizacion con bug doble prefijo; UnidadEjecutora duplicada en SIS-PRO [INFERIDO] |
| 4 | territorio | Distrito, UnidadTerritorial, LocalizacionTerritorial (PostGIS) | CORE | core | territorio_* | V1/V2 | activo | FK genérica en localizacion_territorial |
| 5 | workflow | V1 flujo_* formulación/revisión/observación/aprobación; V2 motor flujo_*_motor | CORE | poau, indicadores, inversion, organizacion, planificacion, presupuesto, techos, modificaciones, seguimiento, acciones_correctivas, accounts | flujo_* + flujo_*_motor | V1/V2 | dual | V1 vs V2 duplicados; FKs genéricas en instancia/observacion |
| 6 | documentos | DocumentoAdjunto | CORE | core | documentos_* | V1/V2 | activo | FK genérica |
| 7 | notificaciones | Notificaciones (3 tablas) | CORE | core | notificaciones_* | V1/V2 | activo | FK genérica |
| 8 | auditoria | EventoAuditoria append-only | CORE | core | auditoria_* | V1/V2 | activo | — |
| 9 | reportes | ReporteGenerado + tarea Celery diaria | CORE | casi todas (hub de lectura) | reportes_* | V1/V2 | activo | Hub de lectura con acoplamiento amplio |
| 10 | acciones_correctivas | Acciones correctivas (2 tablas) | CORE | core | acciones_correctivas_* | V1/V2 | activo | — |
| 11 | normativa | VersionNormativa, ReglaPresupuestariaLegal | CORE | core | normativa_* | V1/V2 | activo | — |
| 12 | catalogos | 16-17 catálogos versionados catalogo_* | SHARED | core | catalogo_* (fuente_financiamiento, objeto_gasto, rubro_recurso, organismo_financiador, ubicacion_geografica_presupuestaria, sector_economico_presupuestario, finalidad_funcion, unidad_medida, tipo_*) | V1/V2 | activo | Strings duplican catálogos en otras apps |
| 13 | codificacion | Codificación normativa (12 tablas codificacion_*): EjePGDESA, ComponentePDESA, SectorEconomico, ResultadoSectorial, EntidadTerritorialCGEO, LineamientoPAD, SecuenciaCodigo, HomologacionCodigo, EjecucionMigracionSIM | SHARED | core, planificacion | codificacion_* | SIN API | activo | LineamientoPAD canónico aquí; FKs genéricas en secuencia/homologacion |
| 14 | planificacion | V1 plan/sector/nodoplanificacion/accionmedianoplazo/accioncortoplazo/articulacionplanificacion/planversion; V2 tipoinstrumento/versionmetodologia/instrumentoplanificacion/versioninstrumento/tiponodoestrategico/nodoestrategico/tipovinculoestrategico/vinculoestrategico; kernel V2 checksum SHA-256 | SIS-PE | articulacion, indicadores, accounts, core | planificacion_* | V1/V2 | dual | plan vs instrumento duplicados; cadena acción/operación/actividad/tarea compartida ×4 |
| 15 | pad | V1 sectorpad/politicapad/lineamientoestrategico/resultadoterritorial/productoterritorial/programacionanualpad/articulacionlog/articulacionsipeb | SIS-PE | core, gestion | pad_* | V1/V2 | dual | Lineamiento PAD triple; articulacionlog FK genérica; gestion suelta |
| 16 | articulacion | Motor de articulación (19+4 M2M articulacion_*): acuerdos ODS/NDC/NDT/30x30, lineamientopad, resultadopad, productopad, resultadopei, productopei, articulacionpadpei, indicadorcadena, accionpoa, operacionpoau, actividadpoau, tareapoau, seguimientopresupuesto, asignacionobjetogasto, borradormatrizpad; services/motor.py y materializacion_matriz.py | SIS-PE | codificacion, presupuesto, catalogos, planificacion | articulacion_* | V1/V2 | activo | Strings duplican catálogos (seguimientopresupuesto, asignacionobjetogasto); cadena operativa ×4 |
| 17 | evaluacion | 5 tablas: evaluacion/criterio/resultado/leccion/recomendacion | SIS-PE | organizacion, pad, planificacion, poau | evaluacion_* | V1/V2 | activo | gestion suelta |
| 18 | indicadores | V1 indicador/metaprogramada/operacion/tarea/producto/medioverificacion/supuesto; operacion/tarea/producto marcados REMOVE_LATER | SIS-PE | poau, core | indicadores_* | V1/V2 | dual | Cadena operativa duplicada; REMOVE_LATER |
| 19 | gestion | GestionFiscal, CicloFormulacion, EtapaFormulacion; estados legacy lowercase + UPPERCASE | SIS-POA | core | gestion_* | V1/V2 | activo | Gestión canónica aquí pero ~12 apps guardan el año suelto |
| 20 | budget | V2 canónico presupuesto (18 tablas presupuesto_*): techo_directivo, techo_version, recurso_techo, gasto_obligatorio, documento, distribucion_version, apertura, apertura_fuente, reserva, categoria_programatica, importacion(+detalle+error), distribucion_territorial, asignacion_territorial, asignacion_objeto_gasto, reforma, reforma_movimiento | SIS-POA | gestion, catalogos, auditoria, organizacion, territorio, accounts, core | presupuesto_* | V2 (`/api/v2/sis-poa/budget/`) | activo | Monolitos: models 1512 líneas, views 1532, services ~2100; modelos en inglés; techo/categoría duplicados con techos/presupuesto V1 |
| 21 | poau | V1 poau/poauactividad/ejecucionfisica/ejecucionfinanciera; V2 poainstitucional/accioncortoplazo/operacion/actividad/tarea/programacionactividad; migration_v2.py puente | SIS-POA | articulacion, techos, indicadores, planificacion, organizacion, presupuesto | poau_* | V1/V2 | dual | Cadena V2 canónica; V1 en deprecación |
| 22 | recursos | V1 estimacionrecurso/estimacionplurianual | SIS-POA | catalogos, presupuesto, techos, core | recursos_* | V1/V2 | legacy | gestion suelta |
| 23 | techos | V1 LEGACY autodeclarado: techopresupuestario/distribuciontecho/movimientotecho | SIS-POA | catalogos, organizacion, presupuesto, core | techos_* | V2 también (`/api/v2/sis-poa/techos/`) | legacy | Duplicado con presupuesto_techo_* de budget |
| 24 | presupuesto | V1 LEGACY autodeclarado: programapresupuestario/proyectopresupuestario/actividadpresupuestaria/categoriaprogramatica/asignacionpresupuestariaunidad/lineapresupuestaria | SIS-POA | organizacion, catalogos, core, techos | presupuesto_* (V1) | V1/V2 | legacy | Categoría programática duplicada (categoriaprogramatica vs budget categoria_programatica) |
| 25 | modificaciones | V1 solicitudmodificacion/cambiomodificacion/impactomodificacion | SIS-POA | core | modificaciones_* | V1/V2 | legacy | Duplicado con presupuesto_reforma*; FK genérica |
| 26 | seguimiento | V1 reporteseguimiento/entradaseguimiento/alerta/umbralconfiguracion | SIS-POA | core | seguimiento_* | V1/V2 | legacy | gestion suelta |
| 27 | inversion | 37 tablas: V1 proyectoinversion/programacionplurianualproyecto/programacionfisicafinanciera; V2 proyecto/condicionprevia/documentotecnico/costoproyecto/vinculoproyectoactividad/proyectoterritorio; preinversión SISPRE/RM115 28 tablas: itcp/tdr/edtp/alternativaproyecto/documentopreinversion/versiondocumentopreinversion/fuentefinanciamientoedtp/referenciaexterna/eventooutbox/mensajeentrante | SIS-PRO | organizacion, catalogos, presupuesto, accounts, core | inversion_* | V1/V2 | dual | proyecto duplicado (proyectoinversion vs proyecto); fuentefinanciamientoedtp sin FK; EventoOutbox solo en preinversión |

## 2. Frontend (32 features, `frontend/sispoa/src/app/features/`)

| # | Feature | Responsabilidad aparente | Dominio | Dependencias/notas | Estado | Problemas |
|---|---|---|---|---|---|---|
| 1 | auth | Login, token JWT | CORE | ApiService, AuthService | activo | PermissionsService accede a authService['userSubject']; getRefreshToken() muerto |
| 2 | admin-usuarios | Gestión de usuarios y roles | CORE | accounts | activo | — |
| 3 | auditoria | Visualización de eventos | CORE | auditoria | activo | — |
| 4 | catalogos | CRUD catálogos | SHARED | catalogos | activo | — |
| 5 | documentos | Adjuntos | CORE | documentos | activo | — |
| 6 | gestion | Gestiones fiscales y ciclos | SIS-POA | gestion | activo | — |
| 7 | normativa | Versiones normativas | CORE | normativa | activo | — |
| 8 | notificaciones | Bandeja de notificaciones | CORE | notificaciones | activo | — |
| 9 | organizacion | Unidad organizacional, direcciones, UE, árbol | CORE | organizacion | activo | Bug doble prefijo /api/v1/api/v1 en 3 componentes |
| 10 | reportes | Reportes generados | CORE | reportes | activo | — |
| 11 | sistemas | Administración del sistema | CORE | core | activo | — |
| 12 | workflow | Flujos de aprobación | CORE | workflow | dual | Paginado<T> duplicado ×5 |
| 13 | dashboard | Tablero | CORE | reportes | activo | — |
| 14 | portal-publico | Portal ciudadano | SIS-PE | planificacion/pad | activo | PdeSa duplicado vs consolidacion |
| 15 | sis-pe | Planificación estratégica V2 | SIS-PE | planificacion | activo | Paginado<T> duplicado ×5 |
| 16 | articulacion | Matrices de articulación | SIS-PE | articulacion | activo | — |
| 17 | matrices-pad | Matrices PAD | SIS-PE | pad, articulacion | activo | — |
| 18 | pad | PAD V1 | SIS-PE | pad | legacy | — |
| 19 | indicadores | Indicadores | SIS-PE | indicadores | legacy | — |
| 20 | territorio | Distritos/territorio | CORE | territorio | activo | — |
| 21 | evaluacion | Evaluación | SIS-PE | evaluacion | activo | — |
| 22 | sis-poa | POA V2 (planificacion POA) | SIS-POA | planificacion/poau | activo | Paginado<T> duplicado ×5 |
| 23 | planificacion | Planificación POA | SIS-POA | poau | legacy | — |
| 24 | poau | POAU V1 | SIS-POA | poau | legacy | — |
| 25 | presupuesto | Presupuesto V1 | SIS-POA | presupuesto | legacy | Triplicado: features/presupuesto (v1), features/sis-poa/presupuesto (v2), features/sis-poa/budget |
| 26 | techos | Techos | SIS-POA | techos | legacy | Cuádruple: 4 vistas |
| 27 | recursos | Recursos V1 | SIS-POA | recursos | legacy | — |
| 28 | seguimiento | Seguimiento V1 | SIS-POA | seguimiento | legacy | — |
| 29 | modificaciones | Modificaciones V1 | SIS-POA | modificaciones | legacy | — |
| 30 | consolidacion | Consolidación (PdeSa) | SIS-POA | presupuesto | activo | PdeSa duplicado vs portal-publico |
| 31 | inversion | Inversión V1/V2 | SIS-PRO | inversion | dual | Paginado<T> duplicado ×5 |
| 32 | sis-pro | Proyectos SIS-PRO | SIS-PRO | inversion | activo | — |

Notas transversales [CONFIRMADO]:

- `Paginado<T>` duplicado ×5: sis-pe, sis-poa, sis-pro, workflow-v2, budget.
- `budget.service.ts`: 1081 líneas, ~60 interfaces.
- Presupuesto triplicado: `features/presupuesto` (v1), `features/sis-poa/presupuesto` (v2), `features/sis-poa/budget`.
- Techos cuádruple: 4 vistas de techos.
- TablaGenericaComponent muerto; dependencias muertas (@angular/material parcial, echarts, ngx-echarts, ol).
- tsconfig `strict:false` + `strictTemplates:false`; rutas legacy sin CapabilityGuard; 28/32 features sin specs.

## Referencias

- `docs/refactor-pip/ARQUITECTURA_ACTUAL.md` — detalle por aplicación y flujos.
- `docs/refactor-pip/SCHEMA_MAPPING.md` — tablas por app.
- `docs/refactor-pip/LEGACY_DEPRECATION.md` — apps V1 en deprecación y REMOVE_LATER.
- `docs/refactor-pip/DOMAIN_MAP.md`, `docs/refactor-pip/API_MAPPING.md`.
- `docs/sis-poa/presupuesto/architecture.md`, `docs/sis-poa/presupuesto/budget-control.md`.
- `docs/pip_gams/domain_map.md`, `docs/pip_gams/WP14_retiro_legacy.md`.

Documento de gobernanza — creado en bootstrap ETAPA B (2026-08-16). No reemplaza a docs/refactor-pip/*; los complementa.

# Propiedad de Datos (Data Ownership)

Quién es dueño de cada concepto de datos en el PIP-GAMS. Clasificación: **OWNER** = único escritor legítimo; **READER** = lee vía contrato; **CONSUMER** = consume agregados; **UNKNOWN** = no definido. Nombres de tablas reales ([CONFIRMADO] por auditoría) cuando existen.

## 1. Matriz de ownership

| Concepto | Tabla(s) real(es) | Owner | Lectores | Estado |
|---|---|---|---|---|
| Usuarios | cuentas_usuario | accounts (CORE) | todos | OK |
| Roles y capacidades | cuentas_rol, cuentas_capacidad | accounts (CORE) | frontend vía permisos | OK |
| Alcance organizacional | cuentas_alcanceorganizacional | accounts (CORE) | core | OK |
| Unidades organizacionales | organizacion_tipounidad, organizacion_unidadorganizacional | organizacion (CORE) | SIS-PE/SIS-POA/SIS-PRO (lectura) | OK; lectura no contractualizada |
| Direcciones administrativas | organizacion_direccionadministrativa | organizacion (CORE) | presupuesto, budget | OK |
| Unidades ejecutoras | organizacion_unidadejecutora | organizacion (CORE) | budget, inversion | Duplicación probable con SIS-PRO (D11) |
| Asignación usuario-unidad | organizacion_asignacionusuariounidad | organizacion (CORE) | accounts | OK |
| Territorio | territorio_distrito, territorio_unidadterritorial, territorio_localizacionterritorial | territorio (CORE) | budget, geo | FK genérica en localización |
| Gestiones fiscales | gestion_gestionfiscal | gestion (SIS-POA) | todos | **CONFLICTO**: ~12 apps guardan `gestion` como entero suelto (techos, presupuesto, recursos, organizacion, pad, poau, seguimiento, modificaciones, articulacion, evaluacion, workflow, indicadores) sin FK |
| Ciclo/etapa de formulación | gestion_cicloformulacion, gestion_etapaformulacion | gestion (SIS-POA) | budget, workflow | OK |
| Catálogos (16-17) | catalogo_* (fuente_financiamiento, objeto_gasto, rubro_recurso, organismo_financiador, ubicacion_geografica_presupuestaria, sector_economico_presupuestario, finalidad_funcion, unidad_medida, tipo_*) | catalogos (SHARED) | todos | **CONFLICTO**: strings duplican catálogos en pad_articulacionsipeb, articulacion_seguimientopresupuesto, articulacion_asignacionobjetogasto, inversion_fuentefinanciamientoedtp |
| Codificación normativa | codificacion_* (EjePGDESA, ComponentePDESA, SectorEconomico, ResultadoSectorial, EntidadTerritorialCGEO, LineamientoPAD, SecuenciaCodigo, HomologacionCodigo, EjecucionMigracionSIM) | codificacion (SHARED) | articulacion | OK (sin API) |
| Plan estratégico V1 | planificacion_plan, planificacion_planversion | planificacion (SIS-PE) | pad | Legacy |
| Instrumentos V2 | planificacion_instrumentoplanificacion, planificacion_versioninstrumento, planificacion_versionmetodologia, planificacion_tipoinstrumento | planificacion (SIS-PE) | poau (vínculos V2), articulacion | Canónico V2 |
| Nodos estratégicos | planificacion_nodoestrategico, tiponodoestrategico, tipovinculoestrategico, vinculoestrategico | planificacion (SIS-PE) | articulacion | Canónico V2 |
| PAD | pad_sectorpad, pad_politicapad, pad_lineamientoestrategico, pad_resultadoterritorial, pad_productoterritorial, pad_programacionanualpad | pad (SIS-PE) | articulacion, planificacion | Lineamiento PAD triple (D3) |
| Articulación PAD-PEI-POA | articulacion_* (matrices, indicadorcadena, acuerdos) | articulacion (SIS-PE/INTEGRACION) | poau, planificacion | Motor activo |
| Evaluación | evaluacion_* (5 tablas) | evaluacion (SIS-PE) | planificacion, poau | OK |
| Indicadores | indicadores_indicador, indicadores_metaprogramada, indicadores_medioverificacion, indicadores_supuesto | indicadores (SIS-PE) | planificacion, evaluacion | Operacion/tarea/producto REMOVE_LATER |
| POA/POAU V1 | poau_poau, poau_poauactividad, poau_ejecucionfisica, poau_ejecucionfinanciera | poau (SIS-POA) | seguimiento, workflow | Legacy |
| POA/POAU V2 | poau_poainstitucional, poau_accioncortoplazo, poau_operacion, poau_actividad, poau_tarea, poau_programacionactividad | poau (SIS-POA) | articulacion, indicadores, inversion | Canónico V2 |
| Techos (V1) | techos_techopresupuestario, techos_distribuciontecho, techos_movimientotecho | techos (SIS-POA) | presupuesto, recursos, poau | **CONFLICTO**: duplicado con budget (D1) |
| Techos (V2) | presupuesto_techo_directivo, presupuesto_techo_version, presupuesto_recurso_techo | budget (SIS-POA) | distribucion_version | Canónico |
| Distribuciones | presupuesto_distribucion_version, presupuesto_distribucion_territorial | budget (SIS-POA) | asignaciones | Canónico |
| Asignaciones | presupuesto_asignacion_territorial, presupuesto_asignacion_objeto_gasto | budget (SIS-POA) | ejecución | Canónico |
| Aperturas y reservas | presupuesto_apertura, presupuesto_apertura_fuente, presupuesto_reserva | budget (SIS-POA) | ejecución | Canónico |
| Gastos obligatorios | presupuesto_gasto_obligatorio | budget (SIS-POA) | seguimiento | Canónico |
| Categorías programáticas | presupuesto_categoria_programatica (budget) vs presupuesto_categoriaprogramatica (V1) | budget (SIS-POA) | poau, inversion | **CONFLICTO** (D2) |
| Importaciones | presupuesto_importacion(+detalle+error) | budget (SIS-POA) | reportes | Canónico |
| Reformas | presupuesto_reforma, presupuesto_reforma_movimiento | budget (SIS-POA) | modificaciones (V1) | **CONFLICTO** con modificaciones_* (D8) |
| Presupuesto V1 | presupuesto_programapresupuestario, proyectopresupuestario, actividadpresupuestaria, asignacionpresupuestariaunidad, lineapresupuestaria | presupuesto (SIS-POA) | techos, seguimiento | Legacy |
| Recursos estimados | recursos_estimacionrecurso, recursos_estimacionplurianual | recursos (SIS-POA) | techos | Legacy |
| Seguimiento V1 | seguimiento_reporteseguimiento, entradaseguimiento, alerta, umbralconfiguracion | seguimiento (SIS-POA) | reportes | Legacy |
| Proyectos V1 | inversion_proyectoinversion, inversion_programacionplurianualproyecto, inversion_programacionfisicafinanciera | inversion (SIS-PRO) | ejecución | Legacy (D5) |
| Proyectos V2 | inversion_proyecto, inversion_condicionprevia, inversion_documentotecnico, inversion_costoproyecto, inversion_vinculoproyectoactividad, inversion_proyectoterritorio | inversion (SIS-PRO) | poau (vínculo), presupuesto | Canónico |
| Preinversión | inversion_itcp, inversion_tdr, inversion_edtp, inversion_alternativaproyecto, inversion_documentopreinversion, inversion_versiondocumentopreinversion, inversion_eventooutbox, inversion_mensajeentrante, ... | inversion (SIS-PRO) | core (workflow), reportes | Outbox solo aquí |
| Flujos V1 | flujo_* (envio_formulacion, revision, observacion, aprobacion) | workflow (CORE) | dominios | Legacy |
| Flujo motor V2 | flujo_definicion, flujo_instancia, flujo_tarea, flujo_observacion_motor, flujo_aprobacion_motor, flujo_delegacion | workflow (CORE) | todos | Canónico |
| Documentos | documentos_documentoadjunto | documentos (CORE) | todos | FK genérica |
| Notificaciones | notificaciones_* | notificaciones (CORE) | todos | FK genérica |
| Auditoría | auditoria_eventoauditoria | auditoria (CORE) | todos (append-only) | OK |
| Reportes generados | reportes_reportegenerado | reportes (CORE) | usuarios | OK |
| Acciones correctivas | acciones_correctivas_* | acciones_correctivas (CORE) | workflow | OK |
| Normativa | normativa_versionnormativa, normativa_reglapresupuestarialegal | normativa (CORE) | presupuesto, budget | OK |

## 2. Conflictos de ownership actuales

| # | Conflicto | Detalle | Resolución sugerida |
|---|---|---|---|
| O-1 | GestionFiscal suelta | gestion es dueña, pero 12 apps guardan el año como entero sin FK | Introducir FK vía contrato en fase 3; lectura vía /api/v2/sis-poa |
| O-2 | Lineamiento PAD triple | pad_lineamientoestrategico, articulacion_lineamientopad, codificacion_lineamientopad (canónico) | Solo codificacion escribe; pad/articulacion leen contrato |
| O-3 | Strings vs catálogos | 4 apps guardan strings donde existe catálogo (fuente, objeto de gasto, sector) | Migrar a FK de catalogo_* en fase 2/4 |
| O-4 | Techo doble | techos_* (V1) y presupuesto_techo_* (budget) ambos en V2 | Budget es owner; techos V1 congela escrituras |
| O-5 | Categoría programática doble | presupuesto_categoriaprogramatica vs presupuesto_categoria_programatica | Budget es owner |
| O-6 | Cadena operativa ×4 | articulacion_*, indicadores_*, planificacion_accioncortoplazo, poau_* V2 | poau V2 es owner; los demás leen |
| O-7 | Unidad ejecutora | organizacion_unidadejecutora vs consumo en SIS-PRO | organizacion es owner |

## 3. Reglas de ownership (TO-BE)

1. Todo concepto tiene UN solo owner escritor. [TO-BE]
2. UNKNOWN = no hay dueño declarado; debe resolverse antes de tocar el concepto. [TO-BE]
3. El owner puede reestructurar sus tablas sin coordinar más que contratos; los lectores no cambian esquema ajeno. [TO-BE]
4. Catálogos y codificación: solo SHARED escribe; toda entidad que hoy guarda strings debe migrar a FK en su fase. [TO-BE]

## Referencias

- `docs/refactor-pip/ARQUITECTURA_OBJETIVO.md`, `docs/refactor-pip/SCHEMA_MAPPING.md`.
- `docs/refactor-pip/ADR/ADR-005-budget-inside-sis-poa.md`, `ADR-006-shared-organizational-structure.md`, `ADR-007-multiyear-model.md`.
- `docs/pip_gams/domain_map.md`, `docs/modelo_datos.md`.
- Complementos: `docs/architecture/DOMAIN_BOUNDARIES.md`, `DUPLICATION_ANALYSIS.md`, `INTEGRATION_CONTRACTS.md`.

Documento de gobernanza — creado en bootstrap ETAPA B (2026-08-16). No reemplaza a docs/refactor-pip/*; los complementa.

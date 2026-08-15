# FASE 1 — MAPEO DE ESQUEMAS: tablas actuales → esquemas destino PIP

> Mapeo de las **217 tablas** reales del esquema `public` (BD `gams_sis_poa`, PostgreSQL 16 + PostGIS 3.4.0) hacia los esquemas destino de la arquitectura PIP.
> Nombres verificados contra los modelos Django (`manage.py shell` + `information_schema`), fecha 2026-08-15.
> Recordatorio: el commit **9961550** ya renombró a español los prefijos `budget_→presupuesto_`, `catalogos_→catalogo_`, `accounts_→cuentas_`, `core_→nucleo_`, `workflow_→flujo_`. Este mapeo usa los nombres ACTUALES.

## Leyenda de acciones

| Acción | Significado |
|---|---|
| KEEP | Se conserva tal cual (ya correcta o de sistema) |
| RENAME | Cambiar nombre de tabla (prefijo/identidad) |
| MOVE | Cambiar de esquema (a `pip_*` / `sis_*`) |
| MERGE | Fusionar con la tabla canónica del destino |
| SPLIT | Separar filas entre dos destinos |
| DEPRECATE | Marcar legacy; retirar tras el cutover del dominio V2 |
| REMOVE_LATER | Eliminar tras cutover (duplicados de jerarquía V2) |
| KEEP_SYSTEM | Tablas del framework/PostGIS: no tocar |

Las filas marcadas con `*` requieren decisión explícita (dominio compartido o split).

## 1. Destino: PIP CORE (núcleo transversal de plataforma)

### `accounts` → pip_core (IAM)

| Objeto actual (tabla) | Schema actual | Dominio real | Schema destino | Objeto destino | Acción |
|---|---|---|---|---|---|
| `cuentas_usuario` | public | IAM | pip_core | `pip_core.cuentas_usuario` | KEEP |
| `cuentas_rol` | public | IAM | pip_core | `pip_core.cuentas_rol` | KEEP |
| `cuentas_capacidad` | public | IAM | pip_core | `pip_core.cuentas_capacidad` | KEEP |
| `cuentas_alcance_organizacional` | public | IAM | pip_core | `pip_core.cuentas_alcance_organizacional` | KEEP |
| `cuentas_rol_capacidades` | public | IAM (M2M) | pip_core | `pip_core.cuentas_rol_capacidades` | KEEP |
| `cuentas_usuario_roles` | public | IAM (M2M) | pip_core | `pip_core.cuentas_usuario_roles` | KEEP |
| `cuentas_usuario_grupos` | public | IAM (M2M auth) | pip_core | `pip_core.cuentas_usuario_grupos` | KEEP |
| `cuentas_usuario_permisos` | public | IAM (M2M auth) | pip_core | `pip_core.cuentas_usuario_permisos` | KEEP |

### `organizacion` → pip_core (estructura institucional)

| Objeto actual (tabla) | Schema actual | Dominio real | Schema destino | Objeto destino | Acción |
|---|---|---|---|---|---|
| `organizacion_tipounidad` | public | Estructura | pip_core | `pip_core.tipounidad` | MOVE |
| `organizacion_unidadorganizacional` | public | Estructura | pip_core | `pip_core.unidadorganizacional` | MOVE |
| `organizacion_direccionadministrativa` | public | Estructura | pip_core | `pip_core.direccionadministrativa` | MOVE |
| `organizacion_unidadejecutora` | public | Estructura | pip_core | `pip_core.unidadejecutora` | MOVE |
| `organizacion_asignacionusuariounidad` | public | Estructura | pip_core | `pip_core.asignacionusuariounidad` | MOVE |

### `core` → pip_core (núcleo técnico)

| Objeto actual (tabla) | Schema actual | Dominio real | Schema destino | Objeto destino | Acción |
|---|---|---|---|---|---|
| `nucleo_manifesto_dataset_demo` | public | Infraestructura | pip_core | `pip_core.manifesto_dataset_demo` | KEEP |
| `nucleo_mapa_migraciones_legacy` | public | Infraestructura | pip_core | `pip_core.mapa_migraciones_legacy` | KEEP |

### `workflow` → pip_core (motor V2) + DEPRECATE legacy

| Objeto actual (tabla) | Schema actual | Dominio real | Schema destino | Objeto destino | Acción |
|---|---|---|---|---|---|
| `flujo_definicion` | public | Motor workflow V2 | pip_core | `pip_core.definicion_workflow` | KEEP |
| `flujo_paso_definicion` | public | Motor workflow V2 | pip_core | `pip_core.paso_definicion` | KEEP |
| `flujo_transicion` | public | Motor workflow V2 | pip_core | `pip_core.transicion_workflow` | KEEP |
| `flujo_instancia` | public | Motor workflow V2 | pip_core | `pip_core.instancia_workflow` | KEEP |
| `flujo_tarea` | public | Motor workflow V2 | pip_core | `pip_core.tarea_workflow` | KEEP |
| `flujo_observacion_motor` | public | Motor workflow V2 | pip_core | `pip_core.observacion_workflow` | KEEP |
| `flujo_aprobacion_motor` | public | Motor workflow V2 | pip_core | `pip_core.aprobacion_workflow` | KEEP |
| `flujo_delegacion` | public | Motor workflow V2 | pip_core | `pip_core.delegacion_workflow` | KEEP |
| `flujo_envio_formulacion` | public | Flujo POA legacy | — | — | DEPRECATE |
| `flujo_revision` | public | Flujo POA legacy | — | — | DEPRECATE |
| `flujo_observacion` | public | Flujo POA legacy | — | — | DEPRECATE |
| `flujo_aprobacion` | public | Flujo POA legacy | — | — | DEPRECATE |

### Otras apps → pip_core

| Objeto actual (tabla) | Schema actual | Dominio real | Schema destino | Objeto destino | Acción |
|---|---|---|---|---|---|
| `documentos_documentoadjunto` | public | Repositorio | pip_core | `pip_core.documento_adjunto` | MOVE |
| `notificaciones_tiponotificacion` | public | Transversal | pip_core | `pip_core.tipo_notificacion` | MOVE |
| `notificaciones_notificacion` | public | Transversal | pip_core | `pip_core.notificacion` | MOVE |
| `notificaciones_preferencianotificacion` | public | Transversal | pip_core | `pip_core.preferencia_notificacion` | MOVE |
| `acciones_correctivas_accioncorrectiva` | public | Mejora continua | pip_core | `pip_core.accion_correctiva` | MOVE |
| `acciones_correctivas_compromisoaccioncorrectiva` | public | Mejora continua | pip_core | `pip_core.compromiso_accion_correctiva` | MOVE |

## 2. Destino: PIP AUDITORÍA

| Objeto actual (tabla) | Schema actual | Dominio real | Schema destino | Objeto destino | Acción |
|---|---|---|---|---|---|
| `auditoria_eventoauditoria` | public | Trazabilidad | pip_auditoria | `pip_auditoria.evento_auditoria` | MOVE |

## 3. Destino: PIP CATÁLOGOS

### `catalogos` (prefijo ya en español: `catalogo_*`)

| Objeto actual (tabla) | Schema actual | Dominio real | Schema destino | Objeto destino | Acción |
|---|---|---|---|---|---|
| `catalogo_version_clasificador` | public | Catálogos normativos | pip_catalogo | `pip_catalogo.version_clasificador` | KEEP |
| `catalogo_clasificador_institucional` | public | Catálogos normativos | pip_catalogo | `pip_catalogo.clasificador_institucional` | KEEP |
| `catalogo_rubro_recurso` | public | Catálogos normativos | pip_catalogo | `pip_catalogo.rubro_recurso` | KEEP |
| `catalogo_objeto_gasto` | public | Catálogos normativos | pip_catalogo | `pip_catalogo.objeto_gasto` | KEEP |
| `catalogo_fuente_financiamiento` | public | Catálogos normativos | pip_catalogo | `pip_catalogo.fuente_financiamiento` | KEEP |
| `catalogo_organismo_financiador` | public | Catálogos normativos | pip_catalogo | `pip_catalogo.organismo_financiador` | KEEP |
| `catalogo_ubicacion_geografica_presupuestaria` | public | Catálogos normativos | pip_catalogo | `pip_catalogo.ubicacion_geografica_presupuestaria` | KEEP |
| `catalogo_entidad_transferencia` | public | Catálogos normativos | pip_catalogo | `pip_catalogo.entidad_transferencia` | KEEP |
| `catalogo_finalidad_funcion` | public | Catálogos normativos | pip_catalogo | `pip_catalogo.finalidad_funcion` | KEEP |
| `catalogo_unidad_medida` | public | Catálogos normativos | pip_catalogo | `pip_catalogo.unidad_medida` | KEEP |
| `catalogo_tipo_operacion` | public | Catálogos normativos | pip_catalogo | `pip_catalogo.tipo_operacion` | KEEP |
| `catalogo_tipo_producto` | public | Catálogos normativos | pip_catalogo | `pip_catalogo.tipo_producto` | KEEP |
| `catalogo_tipo_proyecto` | public | Catálogos normativos | pip_catalogo | `pip_catalogo.tipo_proyecto` | KEEP |
| `catalogo_tipo_financiamiento` | public | Catálogos normativos | pip_catalogo | `pip_catalogo.tipo_financiamiento` | KEEP |
| `catalogo_version_catalogo` | public | Catálogos normativos | pip_catalogo | `pip_catalogo.version_catalogo` | KEEP |

### `normativa` → pip_catalogo

| Objeto actual (tabla) | Schema actual | Dominio real | Schema destino | Objeto destino | Acción |
|---|---|---|---|---|---|
| `normativa_versionnormativa` | public | Marco legal | pip_catalogo | `pip_catalogo.version_normativa` | MOVE |
| `normativa_reglapresupuestarialegal` | public | Marco legal | pip_catalogo | `pip_catalogo.regla_presupuestaria_legal` | MOVE |

### `codificacion` → pip_catalogo / SIS-PE *

| Objeto actual (tabla) | Schema actual | Dominio real | Schema destino | Objeto destino | Acción |
|---|---|---|---|---|---|
| `codificacion_versioncatalogoplan` | public | Codificación PGDESA/PDESA | pip_catalogo | `pip_catalogo.version_catalogo_plan` | MOVE |
| `codificacion_ejepgdesa` | public | Codificación PGDESA | sis_pe | `sis_pe.eje_pgdesa` | MOVE |
| `codificacion_componentepdesa` | public | Codificación PDESA | sis_pe | `sis_pe.componente_pdesa` | MOVE |
| `codificacion_sectoreconomico` | public | Codificación PDESA | sis_pe | `sis_pe.sector_economico` | MOVE |
| `codificacion_resultadosectorial` | public | Codificación PDESA | sis_pe | `sis_pe.resultado_sectorial` | MOVE |
| `codificacion_entidadterritorialcgeo` | public | Codificación CGEO | pip_geo | `pip_geo.entidad_territorial_cgeo` | MOVE |
| `codificacion_entidadcodificadora` | public | Codificación | pip_catalogo | `pip_catalogo.entidad_codificadora` | MOVE |
| `codificacion_lineamientopad` | public | Codificación PAD | sis_pe | `sis_pe.lineamiento_pad` | MOVE |
| `codificacion_secuenciacodigo` | public | Codificación | pip_catalogo | `pip_catalogo.secuencia_codigo` | MOVE |
| `codificacion_homologacioncodigo` | public | Codificación | pip_catalogo | `pip_catalogo.homologacion_codigo` | MOVE |

## 4. Destino: SIS-PE (planificación estratégica)

### `planificacion` (salvo `accioncortoplazo` → SIS-POA)

| Objeto actual (tabla) | Schema actual | Dominio real | Schema destino | Objeto destino | Acción |
|---|---|---|---|---|---|
| `planificacion_plan` | public | Estratégico | sis_pe | `sis_pe.plan` | MOVE |
| `planificacion_sector` | public | Estratégico | sis_pe | `sis_pe.sector` | MOVE |
| `planificacion_nodoplanificacion` | public | Estratégico | sis_pe | `sis_pe.nodo_planificacion` | MOVE |
| `planificacion_accionmedianoplazo` | public | Estratégico | sis_pe | `sis_pe.accion_mediano_plazo` | MOVE |
| `planificacion_accioncortoplazo` | public | Operativo (plan maestro: `AccionCortoPlazo` → SIS-POA `AccionPOA`) | sis_poa | `sis_poa.accion_poa` | MOVE * |
| `planificacion_articulacionplanificacion` | public | Estratégico | sis_pe | `sis_pe.articulacion_planificacion` | MOVE |
| `planificacion_planversion` | public | Estratégico | sis_pe | `sis_pe.plan_version` | MOVE |
| `planificacion_tipoinstrumento` | public | Estratégico | sis_pe | `sis_pe.tipo_instrumento` | MOVE |
| `planificacion_versionmetodologia` | public | Estratégico | sis_pe | `sis_pe.version_metodologia` | MOVE |
| `planificacion_instrumentoplanificacion` | public | Estratégico | sis_pe | `sis_pe.instrumento_planificacion` | MOVE |
| `planificacion_versioninstrumento` | public | Estratégico (inmutable, checksum) | sis_pe | `sis_pe.version_instrumento` | MOVE |
| `planificacion_tiponodoestrategico` | public | Estratégico | sis_pe | `sis_pe.tipo_nodo_estrategico` | MOVE |
| `planificacion_nodoestrategico` | public | Estratégico | sis_pe | `sis_pe.nodo_estrategico` | MOVE |
| `planificacion_tipovinculoestrategico` | public | Estratégico | sis_pe | `sis_pe.tipo_vinculo_estrategico` | MOVE |
| `planificacion_vinculoestrategico` | public | Estratégico | sis_pe | `sis_pe.vinculo_estrategico` | MOVE |

### `pad` → sis_pe

| Objeto actual (tabla) | Schema actual | Dominio real | Schema destino | Objeto destino | Acción |
|---|---|---|---|---|---|
| `pad_sectorpad` | public | PAD | sis_pe | `sis_pe.sector_pad` | MOVE |
| `pad_politicapad` | public | PAD | sis_pe | `sis_pe.politica_pad` | MOVE |
| `pad_lineamientoestrategico` | public | PAD | sis_pe | `sis_pe.lineamiento_estrategico` | MOVE |
| `pad_resultadoterritorial` | public | PAD | sis_pe | `sis_pe.resultado_territorial` | MOVE |
| `pad_articulacionlog` | public | PAD | sis_pe | `sis_pe.articulacion_log` | MOVE |
| `pad_productoterritorial` | public | PAD | sis_pe | `sis_pe.producto_territorial` | MOVE |
| `pad_programacionanualpad` | public | PAD | sis_pe | `sis_pe.programacion_anual_pad` | MOVE |
| `pad_articulacionsipeb` | public | PAD | sis_pe | `sis_pe.articulacion_sipeb` | MOVE |

### `articulacion` estratégico → sis_pe / pip_integracion (SPLIT *)

| Objeto actual (tabla) | Schema actual | Dominio real | Schema destino | Objeto destino | Acción |
|---|---|---|---|---|---|
| `articulacion_codigonivel` | public | Cadena estratégica | sis_pe | `sis_pe.codigo_nivel` | MOVE * |
| `articulacion_acuerdointernacional` | public | Cadena estratégica | sis_pe | `sis_pe.acuerdo_internacional` | MOVE * |
| `articulacion_normativa` | public | Cadena estratégica | sis_pe | `sis_pe.normativa` | MOVE * |
| `articulacion_lineamientopad` | public | Cadena estratégica | sis_pe | `sis_pe.lineamiento_pad` | MERGE con `pad_*` * |
| `articulacion_resultadopad` | public | Cadena estratégica | sis_pe | `sis_pe.resultado_pad` | MERGE con `pad_*` * |
| `articulacion_productopad` | public | Cadena estratégica | sis_pe | `sis_pe.producto_pad` | MERGE con `pad_*` * |
| `articulacion_resultadopei` | public | Cadena estratégica | sis_pe | `sis_pe.resultado_pei` | MOVE |
| `articulacion_productopei` | public | Cadena estratégica | sis_pe | `sis_pe.producto_pei` | MOVE |
| `articulacion_articulacionpadpei` | public | Articulación PAD-PEI | pip_integracion | `pip_integracion.articulacion_pad_pei` | MOVE |
| `articulacion_indicadorcadena` | public | Cadena estratégica | sis_pe | `sis_pe.indicador_cadena` | MOVE |
| `articulacion_actividadnormativa` | public | Cadena estratégica | sis_pe | `sis_pe.actividad_normativa` | MOVE |
| `articulacion_tareanormativa` | public | Cadena estratégica | sis_pe | `sis_pe.tarea_normativa` | MOVE |

### `indicadores` → sis_pe / sis_poa (SPLIT *)

| Objeto actual (tabla) | Schema actual | Dominio real | Schema destino | Objeto destino | Acción |
|---|---|---|---|---|---|
| `indicadores_indicador` | public | Indicadores | sis_pe / sis_poa | compartido * | KEEP * |
| `indicadores_metaprogramada` | public | Indicadores | sis_pe / sis_poa | compartido * | KEEP * |
| `indicadores_medioverificacion` | public | Indicadores | sis_pe | `sis_pe.medio_verificacion` | MOVE * |
| `indicadores_supuesto` | public | Indicadores | sis_pe | `sis_pe.supuesto` | MOVE * |
| `indicadores_operacion` | public | Jerarquía operativa legacy (duplicada en poau V2) | sis_poa | — | REMOVE_LATER * |
| `indicadores_tarea` | public | Jerarquía operativa legacy (duplicada en poau V2) | sis_poa | — | REMOVE_LATER * |
| `indicadores_producto` | public | Jerarquía operativa legacy (duplicada en poau V2) | sis_poa | — | REMOVE_LATER * |

### `evaluacion` → sis_pe / sis_pro *

| Objeto actual (tabla) | Schema actual | Dominio real | Schema destino | Objeto destino | Acción |
|---|---|---|---|---|---|
| `evaluacion_evaluacion` | public | Evaluación | sis_pe / sis_pro | compartido * | KEEP * |
| `evaluacion_criterioevaluacion` | public | Evaluación | sis_pe / sis_pro | compartido * | KEEP * |
| `evaluacion_resultadoevaluacion` | public | Evaluación | sis_pe / sis_pro | compartido * | KEEP * |
| `evaluacion_leccionaprendida` | public | Evaluación | sis_pe / sis_pro | compartido * | KEEP * |
| `evaluacion_recomendacion` | public | Evaluación | sis_pe / sis_pro | compartido * | KEEP * |

## 5. Destino: SIS-POA (operativo)

### `gestion` → sis_poa (gestion_fiscal)

| Objeto actual (tabla) | Schema actual | Dominio real | Schema destino | Objeto destino | Acción |
|---|---|---|---|---|---|
| `gestion_gestionfiscal` | public | Ciclo presupuestario | sis_poa | `sis_poa.gestion_fiscal` | MERGE con `budget.FiscalYear` |
| `gestion_cicloformulacion` | public | Ciclo presupuestario | sis_poa | `sis_poa.ciclo_formulacion` | MOVE |
| `gestion_etapaformulacion` | public | Ciclo presupuestario | sis_poa | `sis_poa.etapa_formulacion` | MOVE |

### `budget` (prefijo renombrado a `presupuesto_*` en 9961550) → sis_poa

| Objeto actual (tabla) | Schema actual | Dominio real | Schema destino | Objeto destino | Acción |
|---|---|---|---|---|---|
| `presupuesto_techo_directivo` | public | Ciclo SIS-POA | sis_poa | `sis_poa.techo_directivo` | KEEP |
| `presupuesto_techo_version` | public | Ciclo SIS-POA | sis_poa | `sis_poa.techo_version` | KEEP |
| `presupuesto_recurso_techo` | public | Ciclo SIS-POA | sis_poa | `sis_poa.recurso_techo` | KEEP |
| `presupuesto_gasto_obligatorio` | public | Ciclo SIS-POA | sis_poa | `sis_poa.gasto_obligatorio` | KEEP |
| `presupuesto_documento` | public | Ciclo SIS-POA | sis_poa | `sis_poa.documento` | KEEP |
| `presupuesto_distribucion_version` | public | Ciclo SIS-POA | sis_poa | `sis_poa.distribucion_version` | KEEP |
| `presupuesto_apertura` | public | Ciclo SIS-POA | sis_poa | `sis_poa.apertura` | KEEP |
| `presupuesto_apertura_fuente` | public | Ciclo SIS-POA | sis_poa | `sis_poa.apertura_fuente` | KEEP |
| `presupuesto_reserva` | public | Ciclo SIS-POA | sis_poa | `sis_poa.reserva` | KEEP |
| `presupuesto_categoria_programatica` | public | Ciclo SIS-POA | sis_poa | `sis_poa.categoria_programatica` | KEEP |
| `presupuesto_importacion` | public | Ciclo SIS-POA | sis_poa | `sis_poa.importacion` | KEEP |
| `presupuesto_importacion_detalle` | public | Ciclo SIS-POA | sis_poa | `sis_poa.importacion_detalle` | KEEP |
| `presupuesto_importacion_error` | public | Ciclo SIS-POA | sis_poa | `sis_poa.importacion_error` | KEEP |
| `presupuesto_distribucion_territorial` | public | Ciclo SIS-POA | sis_poa | `sis_poa.distribucion_territorial` | KEEP |
| `presupuesto_asignacion_territorial` | public | Ciclo SIS-POA | sis_poa | `sis_poa.asignacion_territorial` | KEEP |
| `presupuesto_asignacion_objeto_gasto` | public | Ciclo SIS-POA | sis_poa | `sis_poa.asignacion_objeto_gasto` | KEEP |
| `presupuesto_reforma` | public | Ciclo SIS-POA | sis_poa | `sis_poa.reforma` | KEEP |
| `presupuesto_reforma_movimiento` | public | Ciclo SIS-POA | sis_poa | `sis_poa.reforma_movimiento` | KEEP |

### `presupuesto` legacy → sis_poa (DEPRECATE)

| Objeto actual (tabla) | Schema actual | Dominio real | Schema destino | Objeto destino | Acción |
|---|---|---|---|---|---|
| `presupuesto_programapresupuestario` | public | Presupuesto legacy | — | — | DEPRECATE |
| `presupuesto_proyectopresupuestario` | public | Presupuesto legacy | — | — | DEPRECATE |
| `presupuesto_actividadpresupuestaria` | public | Presupuesto legacy | — | — | DEPRECATE |
| `presupuesto_categoriaprogramatica` | public | Presupuesto legacy | — | — | DEPRECATE |
| `presupuesto_asignacionpresupuestariaunidad` | public | Presupuesto legacy | — | — | DEPRECATE |
| `presupuesto_lineapresupuestaria` | public | Presupuesto legacy | — | — | DEPRECATE |

### `techos` legacy → sis_poa (DEPRECATE)

| Objeto actual (tabla) | Schema actual | Dominio real | Schema destino | Objeto destino | Acción |
|---|---|---|---|---|---|
| `techos_techopresupuestario` | public | Techos legacy | — | — | DEPRECATE (TechoDirectivo V2) |
| `techos_distribuciontecho` | public | Techos legacy | — | — | DEPRECATE |
| `techos_movimientotecho` | public | Techos legacy | — | — | DEPRECATE |

### `recursos` → sis_poa

| Objeto actual (tabla) | Schema actual | Dominio real | Schema destino | Objeto destino | Acción |
|---|---|---|---|---|---|
| `recursos_estimacionrecurso` | public | Recursos SIS-POA | sis_poa | `sis_poa.estimacion_recurso` | MOVE |
| `recursos_estimacionplurianual` | public | Recursos SIS-POA | sis_poa | `sis_poa.estimacion_plurianual` | MOVE |

### `poau` → sis_poa

| Objeto actual (tabla) | Schema actual | Dominio real | Schema destino | Objeto destino | Acción |
|---|---|---|---|---|---|
| `poau_poau` | public | POAU legacy | sis_poa | — | MERGE con jerarquía V2 * |
| `poau_poauactividad` | public | POAU legacy | sis_poa | — | MERGE con jerarquía V2 * |
| `poau_ejecucionfisica` | public | Ejecución | sis_poa | `sis_poa.ejecucion_fisica` | MOVE |
| `poau_ejecucionfinanciera` | public | Ejecución | sis_poa | `sis_poa.ejecucion_financiera` | MOVE |
| `poau_poainstitucional` | public | POA consolidado | sis_poa | `sis_poa.poa_institucional` | MOVE |
| `poau_accioncortoplazo` | public | POA legacy | sis_poa | `sis_poa.accion_poa` | MERGE con V2 * |
| `poau_operacion` | public | Jerarquía canónica V2 | sis_poa | `sis_poa.operacion` | KEEP |
| `poau_actividad` | public | Jerarquía canónica V2 | sis_poa | `sis_poa.actividad` | KEEP |
| `poau_tarea` | public | Jerarquía canónica V2 | sis_poa | `sis_poa.tarea` | KEEP |
| `poau_programacionactividad` | public | Programación V2 | sis_poa | `sis_poa.programacion_actividad` | KEEP |

### `articulacion` operativo → sis_poa (MOVE/MERGE)

| Objeto actual (tabla) | Schema actual | Dominio real | Schema destino | Objeto destino | Acción |
|---|---|---|---|---|---|
| `articulacion_accionpoa` | public | POA legacy | sis_poa | `sis_poa.accion_poa` | MERGE (con V2) |
| `articulacion_operacionpoau` | public | POAU legacy | sis_poa | `sis_poa.operacion` | MERGE (con V2) |
| `articulacion_actividadpoau` | public | POAU legacy | sis_poa | `sis_poa.actividad` | MERGE (con V2) |
| `articulacion_tareapoau` | public | POAU legacy | sis_poa | `sis_poa.tarea` | MERGE (con V2) |
| `articulacion_seguimientopresupuesto` | public | Seguimiento presupuestal | sis_poa | `sis_poa.seguimiento_presupuesto` | MOVE |
| `articulacion_asignacionobjetogasto` | public | Presupuesto | sis_poa | `sis_poa.asignacion_objeto_gasto` | MERGE (con budget) |

### `seguimiento` → sis_poa / sis_pro *

| Objeto actual (tabla) | Schema actual | Dominio real | Schema destino | Objeto destino | Acción |
|---|---|---|---|---|---|
| `seguimiento_reporteseguimiento` | public | Seguimiento operativo | sis_poa | `sis_poa.reporte_seguimiento` | MOVE * |
| `seguimiento_entradaseguimiento` | public | Seguimiento operativo | sis_poa | `sis_poa.entrada_seguimiento` | MOVE * |
| `seguimiento_alerta` | public | Seguimiento operativo | sis_poa | `sis_poa.alerta` | MOVE * |
| `seguimiento_umbralconfiguracion` | public | Seguimiento operativo | sis_poa | `sis_poa.umbral_configuracion` | MOVE * |

### `modificaciones` → sis_poa

| Objeto actual (tabla) | Schema actual | Dominio real | Schema destino | Objeto destino | Acción |
|---|---|---|---|---|---|
| `modificaciones_solicitudmodificacion` | public | Reformulaciones POA | sis_poa | `sis_poa.solicitud_modificacion` | MOVE |
| `modificaciones_cambiomodificacion` | public | Reformulaciones POA | sis_poa | `sis_poa.cambio_modificacion` | MOVE |
| `modificaciones_impactomodificacion` | public | Reformulaciones POA | sis_poa | `sis_poa.impacto_modificacion` | MOVE |

## 6. Destino: SIS-PRO (proyectos)

### `inversion` → sis_pro (+ 3 tablas a pip_integracion)

| Objeto actual (tabla) | Schema actual | Dominio real | Schema destino | Objeto destino | Acción |
|---|---|---|---|---|---|
| `inversion_proyectoinversion` | public | Cartera | sis_pro | `sis_pro.proyecto_inversion` | MOVE |
| `inversion_programacionplurianualproyecto` | public | Programación | sis_pro | `sis_pro.programacion_plurianual_proyecto` | MOVE |
| `inversion_programacionfisicafinanciera` | public | Programación | sis_pro | `sis_pro.programacion_fisica_financiera` | MOVE |
| `inversion_proyecto` | public | Ciclo del proyecto | sis_pro | `sis_pro.proyecto` | MOVE |
| `inversion_condicionprevia` | public | Condiciones previas | sis_pro | `sis_pro.condicion_previa` | MOVE |
| `inversion_documentotecnico` | public | Documentos | sis_pro | `sis_pro.documento_tecnico` | MOVE |
| `inversion_costoproyecto` | public | Costos | sis_pro | `sis_pro.costo_proyecto` | MOVE |
| `inversion_vinculoproyectoactividad` | public | Vínculo con SIS-POA | sis_pro | `sis_pro.vinculo_proyecto_actividad` | KEEP (contrato explícito con SIS-POA) |
| `inversion_proyectoterritorio` | public | Territorio | sis_pro | `sis_pro.proyecto_territorio` | MOVE |
| `inversion_componenteproyecto` | public | Componentes | sis_pro | `sis_pro.componente_proyecto` | MOVE |
| `inversion_grupobeneficiario` | public | Beneficiarios | sis_pro | `sis_pro.grupo_beneficiario` | MOVE |
| `inversion_alternativaproyecto` | public | Alternativas | sis_pro | `sis_pro.alternativa_proyecto` | MOVE |
| `inversion_solicitudreformulacion` | public | Reformulación (origen SIS-POA) | sis_pro | `sis_pro.solicitud_reformulacion` | KEEP (revisar `sistema_origen`) |
| `inversion_itcp` | public | Preinversión | sis_pro | `sis_pro.itcp` | MOVE |
| `inversion_condicionitcp` | public | Preinversión | sis_pro | `sis_pro.condicion_itcp` | MOVE |
| `inversion_tdr` | public | Preinversión | sis_pro | `sis_pro.tdr` | MOVE |
| `inversion_actividadtdr` | public | Preinversión | sis_pro | `sis_pro.actividad_tdr` | MOVE |
| `inversion_productotdr` | public | Preinversión | sis_pro | `sis_pro.producto_tdr` | MOVE |
| `inversion_personaltdr` | public | Preinversión | sis_pro | `sis_pro.personal_tdr` | MOVE |
| `inversion_itempresupuestotdr` | public | Preinversión | sis_pro | `sis_pro.item_presupuesto_tdr` | MOVE |
| `inversion_edtp` | public | Preinversión | sis_pro | `sis_pro.edtp` | MOVE |
| `inversion_seccionedtp` | public | Preinversión | sis_pro | `sis_pro.seccion_edtp` | MOVE |
| `inversion_estudiotecnico` | public | Preinversión | sis_pro | `sis_pro.estudio_tecnico` | MOVE |
| `inversion_itemcostoedtp` | public | Preinversión | sis_pro | `sis_pro.item_costo_edtp` | MOVE |
| `inversion_fuentefinanciamientoedtp` | public | Preinversión | sis_pro | `sis_pro.fuente_financiamiento_edtp` | MOVE |
| `inversion_itemcronograma` | public | Preinversión | sis_pro | `sis_pro.item_cronograma` | MOVE |
| `inversion_planoperacionmantenimiento` | public | Preinversión | sis_pro | `sis_pro.plan_operacion_mantenimiento` | MOVE |
| `inversion_indicadorevaluacionedtp` | public | Preinversión | sis_pro | `sis_pro.indicador_evaluacion_edtp` | MOVE |
| `inversion_documentopreinversion` | public | Preinversión | sis_pro | `sis_pro.documento_preinversion` | MOVE |
| `inversion_versiondocumentopreinversion` | public | Preinversión | sis_pro | `sis_pro.version_documento_preinversion` | MOVE |
| `inversion_documentogenerado` | public | Preinversión | sis_pro | `sis_pro.documento_generado` | MOVE |
| `inversion_revisionpreinversion` | public | Preinversión | sis_pro | `sis_pro.revision_preinversion` | MOVE |
| `inversion_observacionpreinversion` | public | Preinversión | sis_pro | `sis_pro.observacion_preinversion` | MOVE |
| `inversion_aprobacionpreinversion` | public | Preinversión | sis_pro | `sis_pro.aprobacion_preinversion` | MOVE |
| `inversion_referenciaexterna` | public | Integración | pip_integracion | `pip_integracion.referencia_externa` | MOVE |
| `inversion_eventooutbox` | public | Integración (outbox) | pip_integracion | `pip_integracion.evento_outbox` | MOVE |
| `inversion_mensajeentrante` | public | Integración | pip_integracion | `pip_integracion.mensaje_entrante` | MOVE |

## 7. Destino: PIP GEO

| Objeto actual (tabla) | Schema actual | Dominio real | Schema destino | Objeto destino | Acción |
|---|---|---|---|---|---|
| `territorio_distrito` | public | Base geográfica | pip_geo | `pip_geo.distrito` | MOVE |
| `territorio_unidadterritorial` | public | Base geográfica | pip_geo | `pip_geo.unidad_territorial` | MOVE |
| `territorio_localizacionterritorial` | public | Base geográfica | pip_geo | `pip_geo.localizacion_territorial` | MOVE |

## 8. Destino: REPORTES

| Objeto actual (tabla) | Schema actual | Dominio real | Schema destino | Objeto destino | Acción |
|---|---|---|---|---|---|
| `reportes_reportegenerado` | public | Reportes | reportes | `reportes.reporte_generado` | MOVE |

## 9. Tablas de sistema / framework (KEEP)

| Objeto actual (tabla) | Schema actual | Dominio real | Schema destino | Objeto destino | Acción |
|---|---|---|---|---|---|
| `auth_group` | public | Framework Django | public | — | KEEP_SYSTEM |
| `auth_permission` | public | Framework Django | public | — | KEEP_SYSTEM |
| `django_admin_log` | public | Framework Django | public | — | KEEP_SYSTEM |
| `django_content_type` | public | Framework Django | public | — | KEEP_SYSTEM |
| `django_session` | public | Framework Django | public | — | KEEP_SYSTEM |
| `geometry_columns` | public | PostGIS | public | — | KEEP_SYSTEM |
| `spatial_ref_sys` | public | PostGIS | public | — | KEEP_SYSTEM |

## 10. Notas y riesgos

1. **Colisión de prefijos post-9961550**: `presupuesto_categoria_programatica` (budget V2) y `presupuesto_categoriaprogramatica` (legacy) coexisten en `public`. Cualquier cambio futuro de esquema debe resolver esta ambigüedad (por eso el destino propuesto usa `sis_poa.*` para budget y DEPRECATE para el legacy).
2. **Renombrado 9961550 ya aplicado**: no rehacer `budget_→presupuesto_`, `catalogos_→catalogo_`, `accounts_→cuentas_`, `core_→nucleo_`, `workflow_→flujo_`; el mapeo aquí parte de los nombres actuales.
3. **Valores de datos protegidos**: `Importacion.perfil` (`SISPOA_GASTOS_*`), `SolicitudReformulacion.sistema_origen` (`'SISPOA'`) y `Capacidad.sistema` (`'sis-poa'`, `'sis-pe'`) son datos persistidos; renombrarlos requiere backfill con plan (ver `AUDITORIA_SISPOA.md` secciones 3.3 y 3.6).
4. **Fase de ejecución**: los MOVE/MERGE/DEPRECATE se ejecutan por dominio en las fases 2-8, no en bloque; cada dominio conserva sus datos hasta completar su cutover V2 (palanca `LEGACY_MENU_VISIBLE` en el frontend).
5. **Conteos**: 217 tablas listadas (200 modelos de dominio + 10 tablas M2M + 7 de framework/PostGIS).

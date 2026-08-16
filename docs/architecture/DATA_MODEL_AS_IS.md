# Modelo de Datos AS-IS

Inventario de alto nivel del modelo de datos del PIP-GAMS: ~213 tablas en 9 esquemas PostgreSQL. El inventario fino por tabla (217 mapeadas) vive en `docs/refactor-pip/SCHEMA_MAPPING.md`; este documento agrega por dominio y destaca riesgos estructurales.

## 1. Esquemas PostgreSQL (search_path en settings.py:116-124)

| Esquema | Contenido | Confiabilidad |
|---|---|---|
| public | Tablas legado/migración y PostGIS | [CONFIRMADO] |
| pip_core | núcleo: identidad, organización, territorio, workflow, documentos, normativa | [CONFIRMADO] |
| pip_catalogo | catálogos versionados | [CONFIRMADO] |
| sis_pe | planificación estratégica, PAD, articulación, indicadores | [CONFIRMADO] |
| sis_poa | gestión, budget V2, POA/POAU, recursos, techos, presupuesto, seguimiento | [CONFIRMADO] |
| sis_pro | inversión y preinversión | [CONFIRMADO] |
| pip_integracion | articulación (matrices) | [CONFIRMADO] |
| pip_auditoria | auditoría append-only | [CONFIRMADO] |
| pip_geo | geoespacial PostGIS | [CONFIRMADO] |
| reportes | reportes generados | [CONFIRMADO] |

## 2. Tablas por dominio

### 2.1 CORE (pip_core, cuentas, organizacion, territorio, workflow, documentos, auditoria)

| Tabla/entidad | PK | FKs principales | Responsabilidad | Riesgo |
|---|---|---|---|---|
| nucleo_* (core) | id | — | mixins, dashboard, permisos | [INFERIDO] detalle en SCHEMA_MAPPING |
| cuentas_usuario/rol/capacidad/alcanceorganizacional | id | cadenas de roles | identidad y permisos | — |
| organizacion_tipounidad/unidadorganizacional/direccionadministrativa/unidadejecutora/asignacionusuariounidad | id | organización jerárquica | estructura institucional | unidad ejecutora también consumida por SIS-PRO |
| territorio_distrito/unidadterritorial/localizacionterritorial | id | geometry PostGIS | división territorial | FK genérica en localizacion_territorial |
| flujo_* (V1) y flujo_*_motor (V2) | id | múltiples a dominios | workflow aprobación | FKs genéricas instancia/observacion; V1/V2 duplicados |
| documentos_documentoadjunto | id | — | adjuntos | FK genérica entidad/entidad_id |
| notificaciones_* (3 tablas) | id | — | notificaciones | FK genérica |
| auditoria_eventoauditoria | id | — | auditoría append-only | — |
| reportes_reportegenerado | id | — | reportes | — |
| acciones_correctivas_* (2 tablas) | id | — | acciones correctivas | — |
| normativa_versionnormativa/reglapresupuestarialegal | id | — | normativa | — |

### 2.2 SHARED — catálogos (pip_catalogo, catalogo_*)

| Tabla | Notas | Riesgo |
|---|---|---|
| catalogo_fuentefinanciamiento | versionado | strings lo duplican en articulacion/inversion |
| catalogo_objetogasto | versionado | asignacion_objeto_gasto en budget |
| catalogo_rubrorecurso, organismo_financiador, ubicacion_geografica_presupuestaria, sector_economico_presupuestario, finalidad_funcion, unidad_medida, tipo_* (16-17 tablas) | versionado | — |

### 2.3 SHARED — codificación (codificacion_*)

EjePGDESA, ComponentePDESA, SectorEconomico, ResultadoSectorial, EntidadTerritorialCGEO, LineamientoPAD (canónico), SecuenciaCodigo, HomologacionCodigo, EjecucionMigracionSIM. Sin API; consumida por articulacion. [CONFIRMADO] Riesgo: FKs genéricas en secuencia/homologacion.

### 2.4 SIS-PE

| Grupo | Tablas | Riesgo |
|---|---|---|
| planificacion V1 | plan, sector, nodoplanificacion, accionmedianoplazo, accioncortoplazo, articulacionplanificacion, planversion | plan vs instrumento duplicado |
| planificacion V2 | tipoinstrumento, versionmetodologia, instrumentoplanificacion, versioninstrumento, tiponodoestrategico, nodoestrategico, tipovinculoestrategico, vinculoestrategico (kernel checksum SHA-256) | canónico V2 |
| pad V1 | sectorpad, politicapad, lineamientoestrategico, resultadoterritorial, productoterritorial, programacionanualpad, articulacionlog, articulacionsipeb | lineamiento PAD triple; articulacionlog FK genérica; articulacionsipeb strings |
| articulacion | 19+4 M2M: acuerdos (ODS/NDC/NDT/30x30), lineamientopad, resultadopad, productopad, resultadopei, productopei, articulacionpadpei, indicadorcadena, accionpoa, operacionpoau, actividadpoau, tareapoau, seguimientopresupuesto, asignacionobjetogasto, borradormatrizpad | strings duplican catálogos; triple cadena operativa |
| evaluacion | evaluacion, criterio, resultado, leccion, recomendacion | — |
| indicadores V1 | indicador, metaprogramada, operacion, tarea, producto, medioverificacion, supuesto | operacion/tarea/producto REMOVE_LATER |

### 2.5 SIS-POA

| Grupo | Tablas | Riesgo |
|---|---|---|
| gestion | gestionfiscal, cicloformulacion, etapaformulacion | canónica, pero ~12 apps guardan gestion como PositiveIntegerField suelto |
| budget V2 (18) | techo_directivo, techo_version, recurso_techo, gasto_obligatorio, documento, distribucion_version, apertura, apertura_fuente, reserva, categoria_programatica, importacion(+detalle+error), distribucion_territorial, asignacion_territorial, asignacion_objeto_gasto, reforma, reforma_movimiento | techo/categoría duplicados con V1; modelos en inglés |
| poau V1/V2 | poau, poauactividad, ejecucionfisica, ejecucionfinanciera; poainstitucional, accioncortoplazo, operacion, actividad, tarea, programacionactividad | cadena V2 canónica; V1 legacy |
| recursos V1 | estimacionrecurso, estimacionplurianual | legacy |
| techos V1 | techopresupuestario, distribuciontecho, movimientotecho | duplicado con budget techo_directivo |
| presupuesto V1 | programapresupuestario, proyectopresupuestario, actividadpresupuestaria, categoriaprogramatica, asignacionpresupuestariaunidad, lineapresupuestaria | categoría programática duplicada con budget |
| modificaciones V1 | solicitudmodificacion, cambiomodificacion, impactomodificacion | duplicado con reforma*; FK genérica |
| seguimiento V1 | reporteseguimiento, entradaseguimiento, alerta, umbralconfiguracion | legacy |

### 2.6 SIS-PRO (inversion, 37 tablas)

| Grupo | Tablas | Riesgo |
|---|---|---|
| V1 | proyectoinversion, programacionplurianualproyecto, programacionfisicafinanciera | duplicado con V2 proyecto |
| V2 | proyecto, condicionprevia, documentotecnico, costoproyecto, vinculoproyectoactividad, proyectoterritorio | canónico |
| preinversión SISPRE/RM115 (28) | itcp, tdr, edtp, alternativaproyecto, documentopreinversion, versiondocumentopreinversion, fuentefinanciamientoedtp, referenciaexterna, eventooutbox, mensajeentrante, ... | fuentefinanciamientoedtp sin FK al catálogo; outbox solo aquí |

## 3. Riesgos estructurales del modelo (todos [CONFIRMADO] por auditoría)

1. **Renombrado 2026-08-15**: budget_*→presupuesto_*, workflow_*→flujo_*, catalogos_*→catalogo_*, accounts_*→cuentas_*, core_*→nucleo_*; queries externas con nombres viejos rotas.
2. **GestionFiscal canónica vs suelta**: ~12 apps guardan `gestion` como PositiveIntegerField (techos, presupuesto, recursos, organizacion, pad, poau, seguimiento, modificaciones, articulacion, evaluacion, workflow, indicadores) sin FK.
3. **FKs genéricas sin constraints** en 9 apps: territorio_localizacionterritorial, documentos_documentoadjunto, auditoria_eventoauditoria, notificaciones_notificacion, flujo_instancia, flujo_observacion, modificaciones_solicitudmodificacion, pad_articulacionlog, codificacion_secuenciacodigo/homologacioncodigo.
4. **Strings que duplican catálogos**: pad_articulacionsipeb, articulacion_seguimientopresupuesto, articulacion_asignacionobjetogasto, inversion_fuentefinanciamientoedtp.
5. **Triple cadena operativa**: acción/operación/actividad/tarea en articulacion_*, indicadores_*, planificacion_accioncortoplazo y poau_* (V2 canónica).
6. **Zero DeleteModel** en 127 migraciones: nada se retira físicamente.
7. **Duplicaciones pares**: techo (techos_* vs presupuesto_techo_*), categoría programática (presupuesto_categoriaprogramatica vs presupuesto_categoria_programatica), lineamiento PAD triple, proyecto (inversion_proyectoinversion vs inversion_proyecto), workflow V1/V2, plan vs instrumento, modificación (modificaciones_* vs presupuesto_reforma*), sector ×4.

## Referencias

- `docs/refactor-pip/SCHEMA_MAPPING.md` — inventario fino: 217 tablas mapeadas.
- `docs/refactor-pip/DATA_MIGRATION_PLAN.md`, `docs/refactor-pip/LEGACY_DEPRECATION.md`.
- `docs/modelo_datos.md`, `docs/diagrama_entidad_relacion.md`, `docs/diagrama_bd_completo.*`.
- `docs/diagramas_bd/01_presupuesto.* .. 05_legacy.*`.
- `docs/sis-poa/presupuesto/database.md`, `docs/sis-poa/presupuesto/sigep-import.md`.
- `docs/pip_gams/ADR-004-migracion.md`, `docs/refactor-pip/ADR/ADR-003-postgresql-schemas.md`.

Documento de gobernanza — creado en bootstrap ETAPA B (2026-08-16). No reemplaza a docs/refactor-pip/*; los complementa.

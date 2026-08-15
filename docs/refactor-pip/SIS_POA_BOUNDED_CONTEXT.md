# SIS-POA — Frontera del bounded context operativo

- **Fecha:** 2026-08-15
- **Fase:** 4 del refactor SISPOA→PIP (aislar SIS-POA)
- **Relacionado con:** ADR-002, ADR-005, ADR-008; `DOMAIN_MAP.md` §1, §3; `SCHEMA_MAPPING.md` §5; `SIS_PE_BOUNDED_CONTEXT.md` (FASE 3)

## 1. Propósito

Definir QUÉ pertenece al contexto **SIS-POA** (planificación operativa anual:
gestión fiscal, techos, distribución, asignación, POA/POAU, programación,
modificaciones, seguimiento, recursos propios), QUÉ NO, qué dependencias entre
apps son legítimas, y el flujo maestro que la FASE 4 declara como frontera de
aislamiento. Es la frontera de la FASE 4: el código acoplado NO se mueve, solo
se fija la identidad del contexto.

## 2. Frontera del contexto

### 2.1 Qué pertenece a SIS-POA

| Pieza | Ubicación actual (tablas reales) | Rol en SIS-POA |
|---|---|---|
| Gestión fiscal y habilitación de gestión | `gestion` (`gestion_gestionfiscal`, `gestion_cicloformulacion`, `gestion_etapaformulacion`); V2: `budget.FiscalYear` | Ciclo presupuestario (MERGE pendiente `gestion_gestionfiscal` → `sis_poa.gestion_fiscal`) |
| Techos presupuestarios V2 | `budget` (`presupuesto_techo_directivo`, `presupuesto_techo_version`, `presupuesto_recurso_techo`, `presupuesto_gasto_obligatorio`) | `TechoDirectivo` V2, fuente de verdad para distribución/asignación |
| Techos legacy V1 | `techos` (`techos_techopresupuestario`, `techos_distribuciontecho`, `techos_movimientotecho`) | DEPRECATE a favor de budget V2 (ADR-002 §4) |
| Distribución presupuestaria | `budget` (`presupuesto_distribucion_version`, `presupuesto_distribucion_territorial`) | Distribución de techos (bolsa, territorial) |
| Asignación presupuestaria | `budget` (`presupuesto_apertura`, `presupuesto_apertura_fuente`, `presupuesto_asignacion_territorial`, `presupuesto_asignacion_objeto_gasto`, `presupuesto_categoria_programatica`, `presupuesto_reserva`) | Apertura programática y asignación por objeto de gasto |
| Presupuesto legacy V1 | `presupuesto` (`presupuesto_programapresupuestario`, `presupuesto_proyectopresupuestario`, `presupuesto_actividadpresupuestaria`, `presupuesto_categoriaprogramatica`, `presupuesto_asignacionpresupuestariaunidad`, `presupuesto_lineapresupuestaria`) | Modelo v1 que será deprecado por budget V2; NO es un subsistema independiente (ADR-005) |
| POA institucional | `poau` (`poau_poainstitucional`, `poau_accioncortoplazo` legacy) + `articulacion` (`articulacion_accionpoa` legacy) | POA consolidado y acciones (V1 legacy, MERGE con V2) |
| POAU | `poau` (`poau_poau`, `poau_poauactividad` legacy; jerarquía canónica V2 `poau_operacion`, `poau_actividad`, `poau_tarea`) | POA por unidad; jerarquía canónica única operación → actividad → tarea (ADR-002 §5) |
| Programación físico-financiera | `poau` (`poau_programacionactividad`); `budget` (`presupuesto_asignacion_objeto_gasto`); `articulacion` (`articulacion_seguimientopresupuesto` legacy) | Programación con validación de techo; objetos de gasto aplicados |
| Modificaciones / reformulaciones | `modificaciones` (`modificaciones_solicitudmodificacion`, `modificaciones_cambiomodificacion`, `modificaciones_impactomodificacion`); `budget` (`presupuesto_reforma`, `presupuesto_reforma_movimiento`) | Reformulaciones del POA (modificaciones) y reformas presupuestarias (budget) |
| Seguimiento operativo | `seguimiento` (`seguimiento_reporteseguimiento`, `seguimiento_entradaseguimiento`, `seguimiento_alerta`, `seguimiento_umbralconfiguracion`) | Reportes/entradas/alertas del POA (contrato compartido con SIS-PRO por IDs) |
| Recursos propios | `recursos` (`recursos_estimacionrecurso`, `recursos_estimacionplurianual`) | Estimación de ingresos propios que alimenta la programación |
| Indicadores operativos | `indicadores` (`indicadores_indicador`, `indicadores_metaprogramada`; jerarquía legacy `indicadores_operacion/tarea/producto`) | Metas del ciclo operativo; la jerarquía duplicada se retira tras cutover (REMOVE_LATER) |
| Importación de planillas presupuestarias | `budget` (`presupuesto_importacion`, `presupuesto_importacion_detalle`, `presupuesto_importacion_error`) | Carga de datos del presupuesto aprobado |

### 2.2 Qué NO pertenece a SIS-POA

| Pieza | Destino real |
|---|---|
| Catálogos maestros (`catalogo_version_clasificador`, `catalogo_objeto_gasto`, `catalogo_fuente_financiamiento`, `catalogo_rubro_recurso`, `catalogo_organismo_financiador`, `catalogo_ubicacion_geografica_presupuestaria`, `catalogo_finalidad_funcion`, `catalogo_unidad_medida`, `catalogo_tipo_operacion`, `catalogo_tipo_producto`, `catalogo_tipo_proyecto`, `catalogo_tipo_financiamiento`, `catalogo_version_catalogo`) y normativa (`normativa_versionnormativa`, `normativa_reglapresupuestarialegal`) | **PIP CATÁLOGOS** (ADR-005 §3): compartidos por los tres SIS, con versión y checksum |
| Planificación estratégica (`planificacion.*`, kernel V2 `models_v2.py`) y PAD/PEI (`pad.*`) | **SIS-PE** (FASE 3; kernel inmutable leído por SIS-POA, ADR-008) |
| Articulación estratégica PAD-PEI (`articulacion_resultadopad/productopad/resultadopei/productopei/articulacionpadpei/indicadorcadena`) | **SIS-PE** (cadena estratégica; SPLIT de `articulacion` es la fase 5) |
| Vínculos de integración (outbox/eventos, `inversion_referenciaexterna`, `inversion_eventooutbox`, `inversion_mensajeentrante`) | **PIP INTEGRACIÓN** |
| Proyectos de inversión (`inversion.*`, incl. `inversion_vinculoproyectoactividad` y `inversion_solicitudreformulacion`) | **SIS-PRO** (consume SIS-POA por contrato, nunca tablas internas) |
| Codificación oficial (`codificacion.CodigoSegmentadoModel` + `CodificadorService`, 16 segmentos) | **Infraestructura compartida PIP** — NO se mueve, es el pegamento de la cadena (FASE 3 §2.2) |

## 3. Aclaración ADR-005: presupuesto NO es un cuarto subsistema

`apps/presupuesto` y `apps/techos` NO son contextos independientes: son el
modelo **v1 legacy** del ciclo presupuestario, que convive temporalmente con
`apps/budget` (**V2**, dueño del dominio, ADR-005 §2). La transición la gestiona
el cutover V2 del frontend (`frontend/sispoa/src/app/core/config/cutover.config.ts`,
palanca `LEGACY_MENU_VISIBLE`): las rutas `/presupuesto` y `/techos` legacy
permanecen visibles hasta que budget V2 cubra el dominio, y luego se ocultan
del menú (sin romper URLs). Nunca se crea SIS-PRESUPUESTO ni esquema
`pip_presupuesto`: techos → distribución → asignación → programación son
momentos de UN solo flujo transaccional dentro de SIS-POA.

## 4. Dependencias permitidas y prohibidas

### 4.1 Permitidas (existentes, se conservan)

| Dependencia | Evidencia | Nota |
|---|---|---|
| SIS-POA → PIP CATÁLOGOS | FKs a `catalogo_*` (`objeto_gasto`, `fuente_financiamiento`, `rubro_recurso`, etc.) en budget/presupuesto | Catálogos maestros compartidos; NO mover |
| SIS-POA → PIP CORE | `organizacion_unidadorganizacional` (poau/seguimiento), `cuentas_usuario`, motor `flujo_*` (aprobaciones) | Estructura institucional + IAM + workflow compartidos |
| SIS-POA → SIS-PE (kernel) | Trazabilidad PEI → POA por versiones inmutables (`VersionInstrumento`, checksum) | Lee SOLO versiones aprobadas (ADR-008) |
| SIS-PRO → SIS-POA | `inversion_vinculoproyectoactividad` (vínculo explícito), `inversion_solicitudreformulacion.sistema_origen = 'SISPOA'` | Contrato por servicios/IDs; NUNCA tablas internas de SIS-POA |
| `budget` ↔ `modificaciones` | Reformas (`presupuesto_reforma`) vs solicitudes (`modificaciones_solicitudmodificacion`) | Ambos lados del ciclo de reformulación, mismo contexto |

### 4.2 Prohibidas (objetivo, fases 5+)

| Dependencia | Motivo |
|---|---|
| SIS-POA → tablas de borrador del kernel SIS-PE | SIS-POA lee solo versiones aprobadas e inmutables (ADR-008) |
| `articulacion` operativo → `pad` legacy | La cadena operativa se resuelve por IDs/versiones del kernel V2 |
| Nuevos imports desde SIS-PE / SIS-PRO hacia tablas operativas de `articulacion` (`AccionPOA`…) | Perfora la frontera; el SPLIT de `articulacion` (estratégico/operativo/cadena) es la fase 5 |
| SIS-POA → `inversion.*` (tablas internas de proyectos) | El vínculo es solo por contrato explícito (`vinculo_proyecto_actividad`) |

## 5. Flujo maestro SIS-POA (12 pasos)

Flujo anual con las tablas reales de cada paso (nombres actuales post-9961550,
`SCHEMA_MAPPING.md` §5):

| # | Paso | Tablas reales |
|---|---|---|
| 1 | Habilitar gestión fiscal | `gestion_gestionfiscal`, `gestion_cicloformulacion`, `gestion_etapaformulacion` (V1); `budget.FiscalYear` (V2) |
| 2 | Definir y aprobar techo | `presupuesto_techo_directivo`, `presupuesto_techo_version`, `presupuesto_recurso_techo`, `presupuesto_gasto_obligatorio`; legacy `techos_*` |
| 3 | Aprobar techo (documento) | `presupuesto_documento` + motor `flujo_*` (workflow V2) |
| 4 | Distribuir | `presupuesto_distribucion_version`, `presupuesto_distribucion_territorial` |
| 5 | Asignar | `presupuesto_apertura`, `presupuesto_apertura_fuente`, `presupuesto_asignacion_territorial`, `presupuesto_asignacion_objeto_gasto`, `presupuesto_categoria_programatica`, `presupuesto_reserva` |
| 6 | Formular POA | `poau_poainstitucional`, `poau_accioncortoplazo` (V1); `articulacion_accionpoa` (V1); V2: jerarquía canónica `poau_operacion/actividad/tarea` |
| 7 | Asignar POAU | `poau_poau`, `poau_poauactividad` (V1) |
| 8 | Formular POAU | `poau_poau`, `poau_poauactividad` + jerarquía canónica V2 (`poau_operacion`, `poau_actividad`, `poau_tarea`) |
| 9 | Programar | `poau_programacionactividad` (V2), `presupuesto_asignacion_objeto_gasto`, `recursos_estimacionrecurso`, `recursos_estimacionplurianual`, `indicadores_metaprogramada` |
| 10 | Consolidar | `poau_poainstitucional` (consolidación institucional) |
| 11 | Aprobar POA | Motor `flujo_*` (workflow V2) + `presupuesto_documento` |
| 12 | Seguimiento y modificaciones | `seguimiento_reporteseguimiento`, `seguimiento_entradaseguimiento`, `seguimiento_alerta`, `seguimiento_umbralconfiguracion`; `modificaciones_solicitudmodificacion`, `modificaciones_cambiomodificacion`, `modificaciones_impactomodificacion`; `presupuesto_reforma`, `presupuesto_reforma_movimiento` |

## 6. Identidad del contexto (FASE 4)

Las nueve apps operativas exponen ahora `verbose_name` con prefijo SIS-POA,
registradas sus AppConfig en `config/settings.py` y `config/settings_test_sqlite.py`
(FASE 4): `gestion` = "SIS-POA - Gestión Fiscal", `indicadores` =
"SIS-POA - Indicadores", `recursos` = "SIS-POA - Recursos", `techos` =
"SIS-POA - Techos (legacy)", `presupuesto` = "SIS-POA - Presupuesto (legacy)",
`poau` = "SIS-POA - POAU", `modificaciones` = "SIS-POA - Modificaciones",
`seguimiento` = "SIS-POA - Seguimiento", `budget` = "SIS-POA - Presupuesto".
Los labels de app NO cambian (`gestion`, `indicadores`, …): eso preserva
contenttypes y permisos.

## 7. Deuda técnica registrada

1. **Legacy presupuesto/techos**: `apps/presupuesto` (6 tablas) y `apps/techos`
   (3 tablas) son V1 que conviven con budget V2 (18 tablas); DEPRECATE tras
   cutover por dominio (ADR-002 §4, ADR-005 §2), datos conservados en
   `public_legacy`, nunca DROP.
2. **Colisión de prefijos**: `presupuesto_categoria_programatica` (budget V2)
   vs `presupuesto_categoriaprogramatica` (legacy) coexisten en `public`
   (`SCHEMA_MAPPING.md` §10.1); se resuelve con la separación de esquemas
   (ADR-003) — no con renombrado ad-hoc.
3. **Datos persistidos SISPOA**: `Importacion.perfil` (`SISPOA_GASTOS_*`),
   `SolicitudReformulacion.sistema_origen` (`'SISPOA'`) y `Capacidad.sistema`
   (`'sis-poa'`) son datos, no código: renombrarlos requiere backfill con plan
   (`AUDITORIA_SISPOA.md` §3.3, §3.6).
4. **Duplicación de jerarquía operativa**: `indicadores_operacion/tarea/producto`
   y `articulacion_*POAU` duplican la jerarquía canónica V2 de `poau`
   (REMOVE_LATER tras reconciliación, ADR-002 §5).
5. **Importación de planillas** (`presupuesto_importacion*`): perfil
   `SISPOA_GASTOS_*` atado al formato legacy; validar compatibilidad con el
   formato V2 antes del cutover.

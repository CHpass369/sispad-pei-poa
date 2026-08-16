# Límites de Dominio (Domain Boundaries)

Reglas por dominio para el PIP-GAMS. Cada dominio define: RESPONSABILIDAD, ENTIDADES PROPIAS, DATOS QUE PUEDE LEER, DATOS QUE PUEDE MODIFICAR, CONTRATOS EXPUESTOS, DEPENDENCIAS PERMITIDAS, DEPENDENCIAS PROHIBIDAS. Estado marcado: **[AS-IS]** = comportamiento actual verificado; **[TO-BE]** = regla objetivo de gobernanza.

## Reglas globales

1. Un dominio solo modifica tablas propias. [TO-BE]
2. Lectura de datos ajenos solo vía contrato de integración (ver `INTEGRATION_CONTRACTS.md`). [TO-BE]
3. `CORE ← SIS-PE`, `CORE ← SIS-POA`, `CORE ← SIS-PRO`; CORE no depende de lógica de negocio de los sistemas. [TO-BE; AS-IS incumplido — ver DEPENDENCY_MAP §4]
4. SHARED es transversal: solo SHARED escribe catálogos/codificación. [TO-BE; AS-IS incumplido — strings duplican catálogos]
5. Un bounded context se estabiliza a la vez; nunca big-bang. [TO-BE]

## 1. CORE

| Aspecto | Contenido |
|---|---|
| RESPONSABILIDAD | Identidad, organización, territorio, workflow, documentos, notificaciones, auditoría, reportes, acciones correctivas, normativa |
| ENTIDADES PROPIAS | cuentas_* (usuario, rol, capacidad, alcance), organizacion_*, territorio_*, flujo_*_motor, documentos_*, notificaciones_*, auditoria_eventoauditoria, reportes_*, acciones_correctivas_*, normativa_* |
| DATOS QUE PUEDE LEER | Los propios; nada de negocio. [TO-BE] — AS-IS: lee planificacion/presupuesto/poau/pad/indicadores/articulacion/codificacion (ciclo latente) [AS-IS] |
| DATOS QUE PUEDE MODIFICAR | Solo tablas propias |
| CONTRATOS EXPUESTOS | /api/v2/platform/, /api/v2/core/, /api/v2/geo/, /api/v2/auditoria/; workflow motor |
| DEPENDENCIAS PERMITIDAS | Ninguna de negocio. [TO-BE] — AS-IS: 14 apps de negocio dependidas [AS-IS] |
| DEPENDENCIAS PROHIBIDAS | planificacion, presupuesto, poau, pad, indicadores, articulacion, techos, seguimiento, inversion, evaluacion [TO-BE] |

## 2. SIS-PE

| Aspecto | Contenido |
|---|---|
| RESPONSABILIDAD | Planificación estratégica: PGDES/PDESA, PAD, PEI, instrumentos, articulación, evaluación, indicadores |
| ENTIDADES PROPIAS | planificacion_* (V1 y V2 instrumentos), pad_*, articulacion_*, evaluacion_*, indicadores_* |
| DATOS QUE PUEDE LEER | CORE (identidad, organización), SHARED (catálogos, codificación) |
| DATOS QUE PUEDE MODIFICAR | Tablas propias |
| CONTRATOS EXPUESTOS | /api/v2/sis-pe/; articulación PAD-PEI-POA (matrices A/B) hacia SIS-POA |
| DEPENDENCIAS PERMITIDAS | core, accounts, catalogos, codificacion |
| DEPENDENCIAS PROHIBIDAS | Modificar tablas de SIS-POA/SIS-PRO directamente (hoy escribe via articulacion_* — se conserva como capa de integración). [TO-BE] |

## 3. SIS-POA

| Aspecto | Contenido |
|---|---|
| RESPONSABILIDAD | Planificación operativa: POA/POAU, presupuesto, techos, distribuciones, asignaciones, reformas, seguimiento |
| ENTIDADES PROPIAS | gestion_*, presupuesto_* (budget V2), poau_* V2, recursos_*, techos_*, presupuesto_* V1 (legacy), modificaciones_*, seguimiento_* |
| DATOS QUE PUEDE LEER | CORE, SHARED, SIS-PE (resultados institucionales, metas, articulación) |
| DATOS QUE PUEDE MODIFICAR | Tablas propias |
| CONTRATOS EXPUESTOS | /api/v2/sis-poa/, /api/v2/sis-poa/budget/ |
| DEPENDENCIAS PERMITIDAS | gestion, catalogos, auditoria, organizacion, territorio, accounts, core, articulacion (matrices), planificacion (vínculos V2) |
| DEPENDENCIAS PROHIBIDAS | Escribir en tablas de SIS-PE/SIS-PRO; escribir en techos/presupuesto legacy al estabilizar budget. [TO-BE] |

## 4. SIS-PRO

| Aspecto | Contenido |
|---|---|
| RESPONSABILIDAD | Ciclo del proyecto: cartera, preinversión ITCP/EDTP, ejecución |
| ENTIDADES PROPIAS | inversion_* (V1 y V2), preinversión SISPRE/RM115 (itcp, tdr, edtp, ...) |
| DATOS QUE PUEDE LEER | CORE, SHARED, SIS-POA (operación, presupuesto aprobado, fuente, categoría programática) |
| DATOS QUE PUEDE MODIFICAR | Tablas propias |
| CONTRATOS EXPUESTOS | /api/v2/sis-pro/ |
| DEPENDENCIAS PERMITIDAS | organizacion, catalogos, presupuesto, accounts, core |
| DEPENDENCIAS PROHIBIDAS | Escribir en tablas ajenas. [TO-BE] |

## 5. SHARED

| Aspecto | Contenido |
|---|---|
| RESPONSABILIDAD | Catálogos versionados y codificación normativa |
| ENTIDADES PROPIAS | catalogo_* (16-17 tablas), codificacion_* (12 tablas, sin API) |
| DATOS QUE PUEDE LEER | core |
| DATOS QUE PUEDE MODIFICAR | Tablas propias (único escritor de catálogos/codificación) [TO-BE] |
| CONTRATOS EXPUESTOS | /api/v2/catalogos/; codificacion consumida por articulacion (sin API pública) |
| DEPENDENCIAS PERMITIDAS | core |
| DEPENDENCIAS PROHIBIDAS | Depender de dominios de negocio [TO-BE; AS-IS: codificacion → planificacion] |

## 6. PIP-INTEGRACION (articulación)

| Aspecto | Contenido |
|---|---|
| RESPONSABILIDAD | Motor de articulación PAD-PEI-POA: acuerdos internacionales (ODS/NDC/NDT/30x30), matrices A/B, cadena de indicadores |
| ENTIDADES PROPIAS | articulacion_* (19+4 M2M) — hoy bajo SIS-PE |
| DATOS QUE PUEDE LEER | codificacion, presupuesto, catalogos, planificacion |
| DATOS QUE PUEDE MODIFICAR | Tablas propias de articulación |
| CONTRATOS EXPUESTOS | /api/v2/integracion/ |
| DEPENDENCIAS PERMITIDAS | codificacion, presupuesto, catalogos, planificacion |
| DEPENDENCIAS PROHIBIDAS | Escribir en tablas de otros dominios (hoy escribe matrices propias; el seguimientopresupuesto/asignacionobjetogasto deben pasar a contrato). [TO-BE] |

## Resumen de reglas

| Dominio | Lee | Modifica | Depende de |
|---|---|---|---|
| CORE | propio | propio | nada de negocio [TO-BE] |
| SIS-PE | CORE, SHARED | propio | core, accounts, catalogos, codificacion |
| SIS-POA | CORE, SHARED, SIS-PE | propio | gestion, catalogos, auditoria, organizacion, territorio, accounts, core |
| SIS-PRO | CORE, SHARED, SIS-POA | propio | organizacion, catalogos, presupuesto, accounts, core |
| SHARED | core | propio | core |
| PIP-INTEGRACION | codificacion, presupuesto, catalogos, planificacion | propio | codificacion, presupuesto, catalogos, planificacion |

## Referencias

- `docs/refactor-pip/DOMAIN_MAP.md`, `docs/refactor-pip/ARQUITECTURA_OBJETIVO.md`.
- `docs/refactor-pip/ADR/ADR-002-sis-poa-bounded-context.md`, `ADR-004-articulation-model.md`, `ADR-006-shared-organizational-structure.md`.
- `docs/refactor-pip/SIS_PE_BOUNDED_CONTEXT.md`, `SIS_POA_BOUNDED_CONTEXT.md`, `SIS_PRO_BOUNDED_CONTEXT.md`, `PIP_INTEGRACION_BOUNDED_CONTEXT.md`.
- `docs/pip_gams/domain_map.md`.
- Complementos: `docs/architecture/PIP_SYSTEM_MAP.md`, `DATA_OWNERSHIP.md`, `INTEGRATION_CONTRACTS.md`.

Documento de gobernanza — creado en bootstrap ETAPA B (2026-08-16). No reemplaza a docs/refactor-pip/*; los complementa.

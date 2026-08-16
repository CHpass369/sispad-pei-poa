---
name: sis-pe
description: "Use when: SIS-PE, planificación estratégica, PGDES, PDES, PAD, PEI, instrumento de planificación, nodo estratégico, articulación estratégica, matrices, ODS, NDC, NDT, 30x30, evaluación, indicadores, cheksum de versiones, vinculación estratégica."
---

# SIS-PE — Planificación Estratégica

## Propósito

Planificación estratégica del municipio: instrumentos nacionales/sectoriales (PGDES/PDES), PAD, PEI y su articulación, seguimiento y evaluación.

## ESTADO ACTUAL

### Subdominios y apps

- **planificacion** (V1+V2): kernel de planificación. V1: Plan, NodoPlanificacion. V2: InstrumentoPlanificacion, VersionInstrumento, NodoEstrategico, VinculoEstrategico — el kernel V2 es CANÓNICO y usa checksum de versiones.
- **pad** (V1): Plan Anual de Desarrollo — legado.
- **articulacion**: motor de articulación PAD-PEI-POA: matrices, acuerdos ODS/NDC/NDT/30x30.
- **evaluacion**: evaluación estratégica.
- **indicadores** (V1): indicadores; operacion/tarea/producto marcados REMOVE_LATER.

### Reglas encontradas

- Kernel V2 de planificacion (InstrumentoPlanificacion/VersionInstrumento/NodoEstrategico/VinculoEstrategico) es la fuente canónica para nuevos desarrollos; V1 es legado.
- Codificación oficial PAD/PEI vive en `codificacion` (catálogo canónico, sin API).
- El "lineamiento" PAD está duplicado en pad / articulacion / codificacion: el canónico es `codificacion`. No crear nuevas referencias a las copias.
- La cadena acción→operación→actividad→tarea aparece duplicada entre articulacion, indicadores y poau: consultar DUPLICATION_ANALYSIS.md antes de tocarla.

## Invariantes

- Checksum de VersionInstrumento: cualquier cambio en el instrumento debe invalidar/actualizar el checksum.
- Cadena de articulación PAD → PEI → POA: los vínculos entre instrumentos deben respetar la dirección del motor articulacion.

## ARQUITECTURA OBJETIVO

- Consolidar en planificacion V2 + articulacion como motor único; pad V1 y piezas REMOVE_LATER de indicadores se retiran por tarea aprobada.
- Depende de CORE (identidad, organización, periodo, catálogos, normativa, workflow); nunca al revés.
- Articulación con SIS-POA vía contratos (motor articulacion), no acceso directo a tablas de sis_poa.

## Riesgos

- Triplicación del lineamiento (pad/articulacion/codificacion) si se reutiliza la copia equivocada.
- Duplicación de la cadena estratégica entre apps al modelar nuevas entidades.
- Confundir V1 (Plan/NodoPlanificacion) con V2 (InstrumentoPlanificacion/NodoEstrategico) al extender modelos.

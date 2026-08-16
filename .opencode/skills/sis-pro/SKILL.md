---
name: sis-pro
description: "Use when: SIS-PRO, ciclo del proyecto, cartera de proyectos, preinversión, ITCP, TDR, EDTP, SISPRE, RM 115, condiciones previas, costos, programación de proyectos, ejecución, Proyecto, ProyectoInversion, vinculación con POA."
---

# SIS-PRO — Ciclo del Proyecto

## Propósito

Ciclo de vida del proyecto de inversión municipal: cartera, preinversión, condiciones previas, costos, programación y ejecución.

## ESTADO ACTUAL

### App y entidades

- **inversion**: única app del dominio (backend/apps/inversion).
  - V1: ProyectoInversion (legacy).
  - V2: Proyecto (canónico para nuevos desarrollos).
  - Preinversión: models_preinversion con 28 tablas (ITCP, TDR, EDTP, SISPRE/RM 115).

### Reglas

- NO inventar módulos: si el concepto no existe en el dominio, revisar SIS-POA (poau) y CORE antes de modelar; puede pertenecer a otro bounded context.
- Preinversión usa EVENTOS asíncronos: EventoOutbox (event sourcing/outbox). Nuevos flujos de preinversión deben seguir este patrón, no sincronismo directo.
- Vínculo con SIS-POA: vinculoproyectoactividad → poau_actividad. La relación proyecto↔actividad operativa se expresa por ese vínculo, nunca saltando a tablas de sis_poa directamente.
- Proyecto duplicado V1 vs V2: usar Proyecto (V2); ProyectoInversion es legacy.
- Depende de CORE (organización, territorio, normativa, workflow, documentos). No debe depender de la lógica interna de SIS-POA: la conexión es por contrato/vínculo.

## ARQUITECTURA OBJETIVO

- Proyecto V2 + preinversión por eventos (EventoOutbox) como núcleo canónico; ProyectoInversion se retira por tarea aprobada.
- Integración con SIS-POA por contratos (vínculo actividad ↔ proyecto), con SIS-PE por la cadena estratégica cuando corresponda.

## Riesgos

- Modelar conceptos de preinversión como CRUD síncrono en vez del patrón EventoOutbox.
- Crear relaciones directas hacia tablas sis_poa (poau_*) en vez de usar vinculoproyectoactividad.
- Duplicar ProyectoInversion al extender modelos V2.

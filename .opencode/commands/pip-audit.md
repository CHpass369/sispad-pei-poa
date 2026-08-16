---
description: Auditar un módulo, app o feature de PIP: arquitectura, duplicaciones, dependencias, deuda, errores potenciales, testing y recomendaciones. Uso: pip-audit <dominio|app|path>.
agent: pip-architect
---

Audita el módulo indicado SIN MODIFICAR NINGÚN ARCHIVO. $ARGUMENTS

Pasos:

1. Localiza el objetivo: dominio (core, sis-pe, sis-poa, sis-pro), app backend (backend/apps/<app>) o feature frontend (frontend/sispoa/src/app/features/<feature>).
2. Analiza con codegraph/grep (cita ruta:línea en todo hallazgo):
   - Arquitectura: bounded context, dependencias entrantes/salientes, ownership (DATA_OWNERSHIP.md), cumplimiento de DOMAIN_BOUNDARIES.md.
   - Duplicaciones conocidas: contrasta con docs/architecture/DUPLICATION_ANALYSIS.md (techos V1 vs budget V2, categoría programática, lineamiento PAD, cadena acción/operación/actividad/tarea, proyecto V1/V2, workflow V1/V2).
   - Deuda: código legacy, V1 sin migrar, columnas/FKs sueltas, patrón doble prefijo, Paginado<T> duplicado.
   - Errores potenciales: consultas a tablas renombradas (15-08-2026), contratos rotos V1/V2.
   - Testing: cobertura existente (pytest backend, Karma frontend) y huecos.
3. Clasifica hallazgos BLOCKER/HIGH/MEDIUM/LOW/INFO y propón recomendaciones accionables (tareas, no refactor inmediato).

NO MODIFICAR. Salida: informe de auditoría estructurado con evidencia y recomendaciones.

---
description: Analizar una TASK sin modificar código. Plan de trabajo mínimo con dominio, archivos afectados, dependencias e impactos. Uso: pip-plan <ID o ruta de task>.
agent: pip-architect
---

Analiza la TASK indicada SIN MODIFICAR NINGÚN ARCHIVO. $ARGUMENTS

Pasos:

1. Lee tasks/TASK_TEMPLATE.md para conocer el formato canónico de tareas.
2. Lee la task completa (ruta en $ARGUMENTS; si es solo un ID, localízala en tasks/ — backlog/, active/ o completed/).
3. Analiza y reporta:
   - Dominio afectado (CORE, SIS-PE, SIS-POA, SIS-PRO, SHARED) y apps/features involucradas.
   - Estado actual relevante del código (verificado con codegraph/grep, citando ruta:línea).
   - Archivos a tocar (backend, frontend, docs, tests).
   - Dependencias y entidades relacionadas (consultar docs/architecture/DUPLICATION_ANALYSIS.md para duplicados conocidos).
   - Impacto en base de datos (migraciones), API (V1/V2, contratos) y frontend.
   - Riesgos y supuestos.
   - Plan mínimo ordenado (pasos accionables con orden de ejecución).
4. Valida que el plan respete IN SCOPE / OUT OF SCOPE de la task.

DO NOT MODIFY CODE. Salida: informe de análisis con el plan propuesto.

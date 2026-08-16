---
description: Revisar los cambios actuales del repositorio (git diff) con criterios PIP: scope, arquitectura, regresiones, duplicación, contratos, seguridad, tests. Uso: pip-review [path/scope opcional].
agent: code-reviewer
---

Revisa los cambios actuales del repositorio. $ARGUMENTS

Pasos:

1. Determina el alcance: `git diff --stat` y `git diff` (usa $ARGUMENTS como path o scope si se indicó).
2. Valida contra la tarea asociada si existe (tasks/): ¿respeta IN SCOPE / OUT OF SCOPE?
3. Revisa cada archivo con criterio PIP:
   - Correctness y regresiones.
   - Arquitectura: dependencias entre dominios (CORE base, sistemas dependientes), integración por contratos, V1 vs V2 (código nuevo no debe ir a V1).
   - Duplicación: Paginado<T> en frontend, modelos/tablas duplicadas en backend (DUPLICATION_ANALYSIS.md).
   - Contratos: rutas V2 namespaces correctos, sin doble prefijo /api/v1/api/v1, DTOs frontend↔backend coherentes.
   - Seguridad: secrets, permisos por capacidades, JWT.
   - Testing: ¿hay tests relevantes? ¿los cubre la suite (1252 backend / Karma frontend)?
4. Clasifica hallazgos: BLOCKER / HIGH / MEDIUM / LOW / INFO con ruta:línea.

NO MODIFICAR código salvo solicitud explícita del usuario. Salida: informe con hallazgos clasificados y veredicto (APROBADO / APROBADO CON OBSERVACIONES / RECHAZADO).

---
description: Cerrar una TASK: verificar acceptance criteria, tests, build, review, scope y documentación; mover de tasks/active/ a tasks/completed/ solo si cumple. Uso: task-close <ID o ruta de task>.
agent: code-reviewer
---

Cierra la TASK indicada verificando que esté realmente completa. $ARGUMENTS

Pasos:

1. Localiza la task (ruta o ID en $ARGUMENTS; normalmente en tasks/active/).
2. Verifica, sin dar por hecho nada:
   - ACCEPTANCE CRITERIA: cada criterio cumplido con evidencia (código, tests, capturas si aplica).
   - Tests: suite relevante pasa (backend pytest, frontend Karma+Jasmine vía npm test -- --watch=false); sin regresiones introducidas.
   - Build/lint/typecheck: sin errores (make lint, make test, type-check frontend).
   - Review: cambios revisados (git diff) sin hallazgos BLOCKER/HIGH pendientes.
   - Scope: no se implementó trabajo fuera de IN SCOPE.
   - Documentación: migraciones aplicadas, endpoints documentados, deuda detectada registrada en la task.
3. Si cumple TODO: mueve el archivo de tasks/active/ a tasks/completed/ y reporta el cierre. Si NO cumple: NO lo muevas; devuelve la task con los motivos y los hallazgos pendientes (BLOCKER/HIGH) para corrección.

Salida: veredicto de cierre (CERRADA / NO CIERRA) con evidencia por cada criterio y acciones pendientes en caso de rechazo.

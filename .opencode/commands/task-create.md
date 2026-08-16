---
description: Crear una nueva TASK formal siguiendo tasks/TASK_TEMPLATE.md con nomenclatura PIP-XXX-### y guardarla en tasks/backlog/. Uso: task-create <dominio> <objetivo> <scope> <criterios de aceptación> [contexto].
agent: pip-architect
---

Crea una nueva TASK formal del repositorio SIN MODIFICAR CÓDIGO. $ARGUMENTS

Pasos:

1. Parsea los argumentos: dominio (CORE, SIS-PE, SIS-POA, SIS-PRO, SHARED), objetivo, scope (IN/OUT), criterios de aceptación y contexto opcional.
2. Lee tasks/TASK_TEMPLATE.md y respeta su estructura al pie de la letra.
3. Asigna ID con nomenclatura PIP-XXX-### (XXX = dominio o área, ### = secuencial). Verifica los IDs existentes en tasks/ (backlog/, active/, completed/) para no colisionar.
4. Valida el dominio contra docs/architecture/DOMAIN_BOUNDARIES.md y menciona duplicados conocidos relevantes (docs/architecture/DUPLICATION_ANALYSIS.md) si aplican.
5. Escribe la task en tasks/backlog/ como archivo Markdown.

Salida: ruta del archivo creado, resumen de la task (ID, dominio, objetivo, scope) y advertencias de duplicación detectadas. NO implementar la task.

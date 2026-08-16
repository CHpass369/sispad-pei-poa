---
description: Implementar una TASK del repositorio respetando scope, invariantes y criterios de aceptación. Uso: pip-build <ID o ruta de task>.
agent: backend-developer
---

Implementa la TASK indicada. $ARGUMENTS

Pasos:

1. Lee la task completa (ruta o ID en $ARGUMENTS): IN SCOPE, OUT OF SCOPE, INVARIANTS y ACCEPTANCE CRITERIA. Si la task involucra frontend, delega la parte frontend al agente frontend-developer (puedes continuar tú la parte backend).
2. Carga los skills de dominio correspondientes (.opencode/skills/): pip-backend, pip-frontend, pip-database y el skill del dominio (sis-pe, sis-poa o sis-pro) según aplique.
3. Ejecuta SEARCH BEFORE CREATE: verifica en grep/codegraph y docs/architecture/DUPLICATION_ANALYSIS.md que no exista equivalente antes de crear.
4. Implementa SOLO lo que la task pide: no trabajo adicional, no refactor oportunista. Código nuevo en V2 salvo que la task indique lo contrario.
5. Verifica: tests relevantes (cd backend; python -m pytest <ruta> y/o cd frontend/sispoa; npm test -- --watch=false), lint y migraciones válidas (make migrate).
6. Documenta deuda detectada en la task, no la arregles fuera de scope.

Salida: archivos modificados/creados, migraciones, endpoints, tests ejecutados con resultados, riesgos y trabajo pendiente.

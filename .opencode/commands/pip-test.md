---
description: Detectar y ejecutar las verificaciones apropiadas para los cambios actuales (tests backend/frontend, lint, typecheck). Uso: pip-test [path opcional].
agent: backend-developer
---

Detecta qué verificaciones corresponden a los cambios actuales y ejecútalas. $ARGUMENTS

Pasos:

1. Inspecciona los cambios (git status / git diff --stat) y determina qué capa tocaron.
2. Backend (backend/): `cd backend; python -m pytest <ruta>` — acota a la app o módulo modificado si $ARGUMENTS lo indica; suite completa: 1252 tests con xdist.
3. Frontend (frontend/sispoa/): `cd frontend/sispoa; npm test -- --watch=false` (Karma + Jasmine). NO uses make test-frontend: está roto.
4. Lint/typecheck: usa los targets que defina el Makefile (make lint, make test, etc.). No inventes comandos ni flags.
5. Migraciones: si hay cambios de modelos, verifica `make migrate` (makemigrations --check --dry-run si aplica).

Reporta: comandos ejecutados, resultados (pasados/fallidos), y qué queda pendiente de verificar. No corras toda la suite si solo basta el subset relevante.

# TASK PIP-ARCH-002: Versionar ruff y habilitar gate lint en CI

## DOMINIO

`core/infra`

## OBJECTIVE

Versionar ruff como dependencia de desarrollo backend, agregar configuración mínima y habilitar el job lint en `.github/workflows/ci.yml` para que el gate de calidad existente en el Makefile (`ruff check .`) sea reproducible y bloqueante.

## CONTEXT

Deuda registrada en PIP-ARCH-001 (cerrada 2026-08-16): ruff NO está en `backend/requirements.txt` ni instalado en el venv (`No module named ruff`); el Makefile tiene `lint: docker compose exec backend ruff check . || echo "ruff no instalado"` (degradación silenciosa); el workflow de CI omitió el job lint por esta razón.

## CURRENT BEHAVIOR

- `make lint` no verifica nada (ruf no existe en el contenedor o degrada con echo).
- CI no tiene gate lint.

## EXPECTED BEHAVIOR

- ruff versionado (requirements o requirements-dev) y configurado (pyproject/ruff.toml).
- `ruff check backend` corre en CI como job o step, fallando el workflow si hay errores.
- El Makefile lint pasa a usar el comando local real.

## IN SCOPE

- [x] Agregar ruff a requirements (verificar si existe requirements-dev.txt; si no, requirements.txt).
- [x] Configuración mínima de ruff (line-length, select E/F básicos o default).
- [x] Job/step lint en ci.yml + actualizar Makefile lint si corresponde.
- [x] Correr `ruff check .` y resolver solo errores triviales del propio cambio; los errores pre-existentes se registran como deuda (NO refactor masivo).

## OUT OF SCOPE

- Corregir todos los lint errors pre-existentes del repo (se registran como deuda).
- Cambiar pytest.ini, docker-compose o flujo local.

## INVARIANTS

- Los gates de CI siguen reflejando comandos locales reales.
- Sin cambios de código funcional.

## DATABASE IMPACT

`ninguno`

## API IMPACT

`ninguno`

## FRONTEND IMPACT

`ninguno`

## FILES EXPECTED

- `backend/requirements.txt` (o requirements-dev.txt) — modificar
- `backend/pyproject.toml` o `ruff.toml` — crear (si no existe pyproject)
- `.github/workflows/ci.yml` — modificar (job lint)
- `Makefile` — modificar target lint si aplica

## DEPENDENCIES

- PIP-ARCH-001 (workflow CI ya existe)

## ACCEPTANCE CRITERIA

- [x] `ruff check .` corre localmente con la config versionada.
- [x] CI ejecuta ruff y falla ante errores.
- [x] Makefile lint invoca el comando real.
- [x] Suite backend sigue en verde.

## TESTS

```bash
cd backend; .venv\Scripts\python -m pip install ruff; ruff check .
cd backend; .venv\Scripts\python -m pytest -q
```

## RISKS

Bajo. Riesgo: aparezcan cientos de lint errors pre-existentes al primer run; mitigación: se registran como deuda, no se corrigen en masa (NO OPPORTUNISTIC REFACTORING).

## ROLLBACK

`git revert <commit>`.

## FINAL REPORT

Pendiente de cierre vía `/task-close`.

**Versión de ruff:** `0.16.3` (instalada en el venv del repo, `backend/.venv`, y versionada en `backend/requirements.txt` como `ruff==0.16.3`).

**Errores pre-existentes contabilizados (ruff 0.16.3, sin config versionada):**
- Default completo de ruff 0.16 (incluye reglas de preview/RUF/FURB/BLE/DTZ…): **2375 errores en 403 archivos**.
- Set clásico `E4,E7,E9,F`: **284 errores en 132 archivos** (0 en migraciones, 0 en `.venv`).

**Decisión de config (`backend/pyproject.toml`, creado):**
- `[tool.ruff] line-length = 88`, `target-version = "py313"` (Python real del venv y de CI).
  - Longitud de línea: el repo respeta ≤88 en el 96.6% de las líneas (80,170/82,972); ~1,097 líneas superan 120. Se usa 88 (default de ruff/Django); E501 queda fuera del select, así que el gate no abre una bomba de line-length.
- `[tool.ruff.lint] select = ["E4", "E7", "E9", "F"]` (default clásico de ruff = "E/F básicos" que pide la tarea), con `ignore` de las 9 reglas que la deuda pre-existente viola: `E401` (5), `E402` (4), `E731` (2), `E741` (5), `F401` (223), `F541` (9), `F811` (8), `F821` (2), `F841` (26).
  - Justificación: el repo NO pasa el default completo (2375) ni el clásico (284) → config mínima + deuda documentada, según procedimiento de la tarea. Ignorar estas 9 reglas deja `ruff check .` en cero; el gate queda verde hoy y bloquea regresiones en el resto de las reglas E/F. Ampliar select/recortar ignores es la tarea futura de pago de deuda.
  - `select` explícito además fija el comportamiento frente al default amplio de ruff 0.16 (que incluye RUF/I/FURB… y daría 2375 errores).

**Archivos modificados:**
- `backend/requirements.txt` — agrega `ruff==0.16.3` (junto a pytest/pytest-xdist; no existe requirements-dev.txt y CI instala todo desde requirements.txt).
- `Makefile` — target `lint` pasa de `docker compose exec backend ruff check . || echo "ruff no instalado"` (degradación silenciosa) a `cd backend && python -m ruff check .` (gate local real, mismo patrón que `test-backend`).
- `.github/workflows/ci.yml` — agrega el step `Lint backend (ruff)` en el job `backend` (después de Tests), con `python -m ruff check .` y `working-directory: backend`. Se eligió step en vez de job separado para NO duplicar el `pip install -r requirements.txt` (instrucción de la tarea); reusa Python 3.13 y deps ya instaladas y no requiere el servicio Postgres. Header del workflow actualizado (backend ahora lista 2 gates).

**Archivos creados:**
- `backend/pyproject.toml` — config de ruff (ver decisión arriba).

**Resultado de gates (comandos locales reales, idénticos a CI):**
- `cd backend && .venv\Scripts\python -m ruff check .` → **All checks passed!** (limpio con la config versionada).
- `cd backend && .venv\Scripts\python -m pytest -q` → **1281 passed, 409 warnings, 239 subtests passed** (5m43s). (1281 > 1252 del skill: la suite creció con los 29 tests de contrato de PIP-CORE-001.)
- `ci.yml` validado con `yaml.safe_load`: OK, jobs `backend`/`frontend`, 5 steps en backend (checkout, setup-python, install, Tests backend, Lint backend).

**Migraciones:** ninguna. **Endpoints/API/Frontend/DB:** sin impacto (solo tooling/CI).

**Riesgos:** bajo. El step de lint en el job `backend` queda detrás del service Postgres (si falla la infra de Postgres no corre lint); aceptado para no duplicar instalación. `make lint` local depende de que `python` resuelva al venv (mismo supuesto que `make test-backend`).

**Deuda detectada (solo registrada, no corregida — NO OPPORTUNISTIC REFACTORING):**
1. **2375/284 errores de lint pre-existentes** (detalle: 223 F401 unused-import en 132 archivos; más E402 en settings/management commands, F841, F811, F821…). Corregir = tarea futura de pago de deuda (propuesta: ampliar `select`/recortar `ignore` por oleadas, empezando por las reglas con fixes seguros tipo F401/F541).
2. `make format` sigue degradado (`docker compose exec backend ruff format . || echo "ruff no instalado"`); fuera de scope de esta tarea, replicar el mismo tratamiento en tarea futura.
3. Ruff no está en la imagen Docker del backend (solo en requirements.txt); `docker compose exec backend ruff ...` no funcionará hasta rebuild/install — el target lint ya no lo usa, pero `format` sí.

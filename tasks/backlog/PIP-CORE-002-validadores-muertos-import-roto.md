# TASK PIP-CORE-002: Resolver import roto y validadores muertos en core/validators.py

## DOMINIO

`core`

## OBJECTIVE

Eliminar el import roto `from apps.pad.models import PlanAnual` (clase inexistente) en `core/validators.py:119` y aislar/eliminar las funciones validadoras sin llamadores, documentando si la validación es requerida por el dominio.

## CONTEXT

Auditoría ETAPA A (2026-08-16). `backend/apps/core/validators.py:115` define `validar_accion_pei_sin_pad`; en la línea 119 hace `from apps.pad.models import PlanAnual`, pero la clase `PlanAnual` NO existe en `backend/apps/pad/models.py` (clases reales: `SectorPAD`, `PoliticaPAD`, `LineamientoEstrategico`, `ResultadoTerritorial`, `ArticulacionLog`, `ProductoTerritorial`, `ProgramacionAnualPAD`, `ArticulacionSIPEB`). El import se ejecuta solo en tiempo de llamada (import local), por lo que el módulo importa sin error pero la función explota con `ImportError` si alguien la invoca. La auditoría también detectó funciones validadoras sin ningún llamador en el repositorio (grep en `backend/`): `validar_accion_poa_sin_pei` (:104), `validar_accion_pei_sin_pad` (:115), `validar_meta_sin_indicador` (:131), `validar_indicador_sin_unidad` (:142), `validar_actividad_fuera_periodo` (:151), `validar_presupuesto_mayor_techo` (:177).

## CURRENT BEHAVIOR

- `core/validators.py:119` — import de `apps.pad.models.PlanAnual` que no existe → `ImportError` en tiempo de llamada de `validar_accion_pei_sin_pad`.
- 6 funciones validadoras sin llamadores en todo el repo (ver CONTEXT).

## EXPECTED BEHAVIOR

- El módulo `core/validators.py` no contiene imports a símbolos inexistentes.
- Cada función validadora muerta está: (a) eliminada, (b) aislada con import defensivo, o (c) con llamador real — según la decisión documentada para el dominio.
- La decisión sobre si la validación es requerida por el dominio queda documentada en la tarea (FINAL REPORT o `tasks/technical-debt/`).

## IN SCOPE

- [ ] Eliminar o aislar con import defensivo `from apps.pad.models import PlanAnual` en `validar_accion_pei_sin_pad`.
- [ ] Auditar los llamadores de las 6 funciones (grep en `backend/`), eliminar las que sean muertas o registrarlas como deuda documentada.
- [ ] Correr la suite de core y de la app que corresponda a cada validador.

## OUT OF SCOPE

- Cambiar la lógica de validación SIS-PE (reglas de negocio) si la validación resulta requerida; en ese caso se crea su propia tarea.
- Refactor de otros validadores con llamadores vivos.
- Toques a modelos PAD.

## INVARIANTS

- `python -m pytest` global sigue pasando (1252 tests antes).
- No se cambian firmas ni comportamientos de validadores con llamadores vivos.

## DATABASE IMPACT

`ninguno`

## API IMPACT

`ninguno`

## FRONTEND IMPACT

`ninguno`

## FILES EXPECTED

- `backend/apps/core/validators.py` — modificar: import defensivo o eliminación de `validar_accion_pei_sin_pad` y otros muertos
- Posible `backend/apps/core/tests/` — nuevo test si se decide conservar alguna función

## DEPENDENCIES

`ninguna`

## ACCEPTANCE CRITERIA

- [ ] `grep -n "PlanAnual" backend/` no devuelve imports en código ejecutable (solo referencias documentadas).
- [ ] El módulo `core.validators` importa sin error y las funciones conservadas pasan sus tests.
- [ ] `cd backend; python -m pytest -q` sigue en verde (1252/1252 o menos solo si se eliminó un test roto por causa directa, con justificación).
- [ ] Decisión de dominio documentada: cada función eliminada queda registrada con motivo (sin llamador + sin referencias de dominio).

## TESTS

```bash
cd backend; python -m pytest apps/core -q
cd backend; python -m pytest -q   # suite completa: sin regresiones
python -c "import sys; sys.path.insert(0, 'backend'); from apps.core.validators import *; print('ok')"
```

## RISKS

Medio. Riesgo: alguna función "sin llamador" sea invocada dinámicamente (por nombre, serialización, comandos) — se descarta con grep amplio incluyendo `getattr`/registry. Riesgo: eliminar una validación requerida por el dominio SIS-PE sin saberlo; mitigación: documentar antes de eliminar y consultar la equivalencia semántica con las reglas de `docs/refactor-pip/` y SIS-PE.

## ROLLBACK

- Revert del/los commit(s): `git revert <commit>`
- Si se conservó la función con import defensivo, el rollback no es necesario: el comportamiento original (ImportError en llamada) es peor que el actual.

## FINAL REPORT

Completar al cerrar con `/task-close`: funciones eliminadas vs conservadas, evidencia de ausencia de llamadores, decisión de dominio, tests ejecutados.

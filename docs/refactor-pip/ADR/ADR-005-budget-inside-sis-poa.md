# ADR-005 — El presupuesto operativo vive DENTRO de SIS-POA (no existe SIS-PRESUPUESTO)

- **Fecha:** 2026-08-15
- **Estado:** Aceptado
- **Relacionado con:** ADR-002, ADR-003; plan maestro §13.3; `DOMAIN_MAP.md` §1, §3; `SCHEMA_MAPPING.md` §5

## Contexto

El ciclo presupuestario del SIS-POA está implementado en tres generaciones superpuestas: `techos` legacy (3 tablas), `presupuesto` legacy (6 tablas, `programa/proyecto/actividad/categoriaprogramatica/asignacionpresupuestariaunidad/lineapresupuestaria`) y `budget` V2 (18 tablas: `FiscalYear`, `DirectiveCeiling`, `DistribucionVersion`, `Apertura`, `Reforma`, `Importacion`, etc.). La tentación natural de la arquitectura es crear un cuarto contexto "SIS-PRESUPUESTO" o `pip_presupuesto` para el dominio financiero, separándolo del POA. Eso es un error de modelado: techos, distribución, asignación y programación no son un dominio independiente, son momentos del mismo flujo de planificación operativa anual, y su consistencia es transaccional (el techo valida la distribución, la distribución valida la asignación, la asignación valida la programación).

## Decisión

1. **OBLIGATORIO: techos, distribución, asignación, programación y modificaciones pertenecen al bounded context SIS-POA** (ADR-002). No se crea ningún contexto `SIS-PRESUPUESTO`, ni esquema `pip_presupuesto`, ni app separada.
2. **`budget` V2 es el dueño del dominio presupuestario operativo**; `presupuesto` legacy y `techos` legacy se DEPRECATE a favor suyo (datos conservados en `public_legacy`, nunca DROP).
3. **Solo los catálogos maestros presupuestarios viven en PIP CATÁLOGOS**: `version_clasificador`, `objeto_gasto`, `fuente_financiamiento`, `rubro_recurso`, `organismo_financiador`, `ubicacion_geografica_presupuestaria`, `finalidad_funcion`, `unidad_medida`, `tipo_operacion`, `tipo_producto`, `tipo_proyecto`, `tipo_financiamiento` y la normativa presupuestaria (`version_normativa`, `regla_presupuestaria_legal`) — todas con versión y checksum (`SCHEMA_MAPPING.md` §3).
4. **Los recursos estimados (`recursos_estimacionrecurso`, `recursos_estimacionplurianual`) permanecen técnicamente separados pero bajo el dominio funcional SIS-POA** (plan maestro §13.3): comparten esquema `sis_poa` y contratos explícitos con la programación.
5. **El flujo completo vive en `/api/v2/sis-poa/budget/`** (sub-router ya existente): fiscal-years → directive-ceilings → distribution → aperturas → importaciones → reformas.

## Consecuencias

Positivas:

- El encadenamiento techo → distribución → asignación → programación queda dentro de un solo contexto con consistencia transaccional: no hay sincronización entre sistemas para una sola gestión.
- Se elimina la duplicación de conceptos (tres generaciones de "presupuesto" se reducen a una) y la colisión de prefijos se resuelve con la separación de esquemas (ADR-003).
- La trazabilidad PEI → POA → gasto permanece en una sola base (plan maestro §16.1).

Negativas:

- La deprecación de `presupuesto` y `techos` legacy exige que el frontend legacy (features `presupuesto`, `techos`) migre por completo a budget V2 antes del retiro — cutover por dominio con palanca `LEGACY_MENU_VISIBLE`.
- Los reportes históricos que consultan tablas legacy (`presupuesto_categoriaprogramatica`, `techos_*`) requieren compat view read-only durante la ventana de deprecación.
- `budget` crece en responsabilidad: concentra el ciclo completo, y sus reglas de validación (techo, categoría, objeto de gasto) deben cubrirse con tests de contrato.

## Alternativas consideradas

1. **Crear SIS-PRESUPUESTO / `pip_presupuesto` como contexto separado**: descartado: rompería la transaccionalidad del flujo operativo, exigiría sincronización entre sistemas y duplicaría catálogos.
2. **Conservar `presupuesto` legacy como el sistema presupuestario oficial**: descartado: no soporta el ciclo V2 (distribución territorial, apertura por fuente, reformas) y su naming colisiona con `budget`.
3. **Mover los catálogos presupuestarios al esquema `sis_poa`**: descartado: son catálogos normativos compartidos por los tres SIS (ADR-002, ADR-006), deben vivir en `pip_catalogo`.

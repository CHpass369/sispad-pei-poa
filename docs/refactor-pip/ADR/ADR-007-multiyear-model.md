# ADR-007 — Modelo multigestión (GestionFiscal transversal, cero referencias hardcodeadas)

- **Fecha:** 2026-08-15
- **Estado:** Aceptado
- **Relacionado con:** ADR-002, ADR-005; plan maestro §15.2 (AlcanceTemporal); `DOMAIN_MAP.md` §1, §3; `ARQUITECTURA_ACTUAL.md` §4

## Contexto

El sistema maneja gestiones fiscales con dos representaciones: `gestion.GestionFiscal` (legacy, con `CicloFormulacion`/`EtapaFormulacion`) y `budget.FiscalYear` (V2, con habilitación/cierre vía `/api/v2/sis-poa/budget/fiscal-years/{id}/enable/`). Ambas conviven hoy y el V2 ya manda. El riesgo histórico de este tipo de sistemas es fijar la gestión en el código (constantes del año, comparaciones `== 2027`, filtros por año hardcodeados, seeds con fechas fijas), lo que convierte cada nuevo ejercicio fiscal en un cambio de código en lugar de una operación de datos. La auditoría y el baseline verifican que no hay referencias hardcodeadas a 2027 en el código actual, y esta decisión la convierte en regla permanente.

## Decisión

1. **La gestión fiscal es un concepto transversal de plataforma**: `GestionFiscal` (legacy) y `FiscalYear` (V2) convergen en una única entidad dentro de SIS-POA (`sis_poa.gestion_fiscal`, MERGE según `SCHEMA_MAPPING.md` §5), con habilitación por gestión y estados del ciclo (borrador → formulación → aprobado → ejecución → cierre).
2. **PROHIBIDO hardcodear gestiones**: ninguna consulta, serializer, vista, validación, seed o test referencia un año de gestión literal (`2027`, `datetime.now().year` como filtro de negocio, etc.). Toda entidad dependiente de gestión lleva FK a la gestión y opera sobre la gestión activa seleccionada por el usuario (alcance temporal, plan maestro §15.2).
3. **La gestión activa se propaga por request/contexto** (ruta o selector de gestión en el frontend + parámetro explícito en los servicios), nunca por inferencia de `now()` en el backend.
4. **Los datos dependientes de gestión se migran con su gestión de origen**: el MIGRATE por grupo conserva la FK a `gestion_fiscal`; los MERGE (`GestionFiscal` ↔ `FiscalYear`) se resuelven por homologación de IDs, no por año.

## Consecuencias

Positivas:

- Cada gestión nueva se habilita como dato (un `FiscalYear` nuevo), sin cambios de código ni despliegues.
- La comparación entre gestiones (techo, distribución, apertura, ejecución) es confiable: todo se filtra por la FK de gestión.
- La auditoría y la trazabilidad quedan contextualizadas por gestión (`EventoAuditoria` ya registra gestión, `ARQUITECTURA_ACTUAL.md` §9).

Negativas:

- Los reportes y consultas actuales que asumen una sola gestión deben parametrizarse por gestión antes del corte V2.
- Las entidades legacy sin FK de gestión (varias de `articulacion`, `poau`, `techos`) requieren backfill de la gestión de origen durante la migración de datos (riesgo documentado en `DATA_MIGRATION_PLAN.md` §8).
- El cierre de gestión debe ser explícito y transaccional: las escrituras fuera de la gestión activa se bloquean por validación de dominio, no por convención.

## Alternativas consideradas

1. **Una gestión global implícita (constante de configuración)**: descartado: la configuración global reemplaza el hardcode por otro punto fijo que exige despliegue cada gestión.
2. **Columnas `anio` sueltas sin FK en cada tabla**: descartado: no se puede garantizar coherencia ni auditar el ciclo por gestión.
3. **Migrar cada gestión a una BD o esquema propio (archivo de gestiones)**: descartado: rompe la transaccionalidad y la consulta transversal entre gestiones que el plan maestro §16.1 exige.

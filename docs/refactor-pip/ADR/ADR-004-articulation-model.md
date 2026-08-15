# ADR-004 — Modelo de articulación sin polimorfismo frágil (FK reales y vínculos tipados)

- **Fecha:** 2026-08-15
- **Estado:** Aceptado
- **Relacionado con:** ADR-001, ADR-008; plan maestro §3.8, §7.3, §12.2; `DOMAIN_MAP.md` §2

## Contexto

La cadena PGDESA → PDESA → PAD → PEI → POA → POAU → Proyecto se articula hoy mediante combinaciones de tablas dedicadas (`planificacion_articulacionplanificacion` con 18 usos, `articulacion_articulacionpadpei`, `pad_articulacionsipeb` con columnas fijas para PGDESA/PDESA/ODS/NDC/NDT, `vinculo_estrategico` en SIS-PE V2) y un patrón genérico `tipo + id` que aparece en varios puntos (entidad genérica de workflow `entidad_tipo` + `entidad_id`, `VinculoProyectoActividad`, `ReferenciaExterna`). El plan maestro §3.8 exige "relaciones de negocio con integridad referencial real; evitar `tipo + id` genérico para relaciones críticas", pero el código heredado usa ese patrón en relaciones de negocio, lo que permite vínculos huérfanos e inválidos sin que la base lo detecte.

## Decisión

1. **Las articulaciones de negocio críticas usan tablas de articulación específicas con FK reales**, no `source_type` + `source_id`:
   - la base canónica es `planificacion_articulacionplanificacion` (ya existente en SIS-PE V2), que se extiende hacia `vinculo_estrategico` (`tipo_vinculo_estrategico` con origen/destino permitidos, cardinalidad, ponderación y justificación);
   - la articulación PAD → PEI vive en `pip_integracion.articulacion_pad_pei` con FKs a nodos de ambos instrumentos (MOVE desde `articulacion_articulacionpadpei`, `SCHEMA_MAPPING.md` §6);
   - el vínculo proyecto → actividad POA es `sis_pro.vinculo_proyecto_actividad` con FK real a la actividad del SIS-POA (contrato explícito, KEEP en `SCHEMA_MAPPING.md` §6);
   - el patrón `articulacion_sipeb` con columnas fijas se migra a vínculos tipados (plan maestro §8.1: "varios vínculos estratégicos, no columnas fijas").
2. **Se introduce una tabla de vínculos tipados** (`tipo_vinculo_estrategico`/`vinculo_estrategico` V2) como mecanismo único de articulación estratégica; las matrices oficiales son proyecciones de estas relaciones, no tablas maestras paralelas (plan maestro §7.3).
3. **El patrón `tipo + id` genérico se reserva SOLO para usos transversales no críticos** (workflow `entidad_tipo`+`entidad_id`, auditoría, documentos), donde el costo de una tabla por tipo no se justifica; incluso allí se exige validación explícita del tipo contra un catálogo y verificación de existencia en el servicio.
4. **Decisión de integridad referencial**: las FKs entre esquemas son permitidas (PostgreSQL) y son la regla para articulaciones cross-context; la integridad se valida en cada MIGRATE con el VALIDATE de FKs del plan de datos.

## Consecuencias

Positivas:

- Los vínculos inválidos u huérfanos dejan de ser posibles en las relaciones de negocio: la base rechaza la escritura inconsistente.
- La trazabilidad PGDESA → proyecto se vuelve consultable por FK (requisito del plan maestro §14.2).
- El SIS-POA y el SIS-PRO no dependen de ids genéricos ni de internals del otro (regla R1 de la arquitectura objetivo).

Negativas:

- Los servicios de articulación deben migrar las filas existentes de los patrones genéricos heredados (backfill a las tablas tipadas) antes de retirar los vínculos viejos — trabajo de datos no trivial en `articulacion`.
- La articulación actual de `pad.ArticulacionSIPEB` (columnas fijas) pierde su forma al migrar: requiere homologación de códigos y validación con los usuarios del dominio.
- El motor de workflow conserva el patrón genérico: exige mantener y auditar la validación por tipo en el servicio para no reintroducir vínculos rotos.

## Alternativas consideradas

1. **Generalizar todo a `source_type` + `source_id`**: descartado por el plan maestro §3.8: sin integridad referencial real, la articulación se degrada silenciosamente.
2. **Una sola tabla universal de articulación con checks en SQL**: descartado: los checks no reemplazan FK reales y complican el reporting.
3. **Duplicar la articulación en cada SIS (matrices en tablas paralelas)**: descartado por el plan maestro §7.3: las matrices deben ser proyecciones, no fuentes.

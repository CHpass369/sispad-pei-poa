# ADR-008 — Versionado de instrumentos (PAD/PEI/POA/POAU): versiones inmutables y checksum

- **Fecha:** 2026-08-15
- **Estado:** Aceptado
- **Relacionado con:** ADR-004, ADR-007; plan maestro §3.4, §8.2, §19.2; `ARQUITECTURA_ACTUAL.md` §4 (patrón T4)

## Contexto

La plataforma ya implementa el patrón de versionado en dos puntos: `VersionClasificador` (catalogos, append-only con triggers y checksum `hash_fuente`) y `VersionInstrumento` (planificacion, checksum SHA-256 + inmutabilidad de versiones aprobadas), replicado en `budget` (`DirectiveCeilingVersion`, checksums en apertura). Sin embargo, el resto del ciclo (PAD legacy, POA/POAU legacy, modificaciones) sobrescribe sus registros: una reforma o corrección modifica el instrumento en sitio y la historia se pierde. El plan maestro §19.2 define los estados del ciclo (borrador → formulación → revisión → observado → corregido → validado → remitido → aprobado → ejecución → ajustado → evaluado → cerrado) y §3.4 exige "versiones aprobadas inmutables"; el SIS-POA lee del kernel estratégico solo versiones aprobadas.

## Decisión

1. **Todo instrumento (PAD, PEI, POA, POAU y sus versiones de clasificador/metodología) sigue el patrón `VersionInstrumento`/`VersionClasificador` existente**: una entidad de versión por instrumento, con número, estado del ciclo, vigencia, fecha y acto de aprobación, motivo del cambio, checksum de datos y bandera de inmutabilidad.
2. **Una versión aprobada es INMUTABLE**: ningún comando modifica, elimina o reabre filas de una versión aprobada; los ajustes crean una versión nueva (copiando el contenido aprobado como base) y pasan por el workflow de aprobación. El ajuste de versiones aprobadas es la única vía de evolución (plan maestro §8.2: expandir → backfill → reconciliar → cortar escritura legacy → observar → retirar).
3. **Checksum obligatorio**: cada versión aprueba con un hash (SHA-256) de su contenido; la integridad se verifica al leer y en los VALIDATE de migración; el SIS-POA puede verificar que la versión estratégica que consume no fue alterada.
4. **PK técnica UUID separada del código institucional**: los identificadores públicos son UUID; el código institucional (p. ej. código PAD/PEI, código de categoría programática) es un atributo de negocio, versionado y homologable, nunca la clave primaria (plan maestro §3.6).
5. **El motor de workflow V2 (`flujo_definicion`/`flujo_instancia`, `pip_core`) enlaza la aprobación con la acción de dominio** (`VersionInstrumento.aprobar`, `workflow/services_v2.py`): aprobar por workflow = sellar la versión (checksum + inmutable).

## Consecuencias

Positivas:

- La trazabilidad completa de un instrumento (quién, cuándo, por qué cambió) queda garantizada; la auditoría complementa con `pip_auditoria.evento_auditoria`.
- El SIS-POA y el SIS-PRO consumen versiones estables: los cambios de estrategia no corrompen la programación operativa en curso.
- La reforma del POA (`budget.Reforma`) y las modificaciones (`solicitud_modificacion`) operan sobre versiones: una reforma aplicada es una nueva versión, no una edición destructiva.

Negativas:

- El almacenamiento crece con cada versión (append-only): mitigado con contenido versionado y referencias a la versión previa, sin copiar estructuras completas innecesariamente.
- Los flujos legacy que editan en sitio (PAD legacy, POA legacy) requieren migración de datos: cada registro actual pasa a ser la versión 1 sellada (backfill con `LegacyMigrationMap`).
- La complejidad de escritura aumenta: todo comando de ajuste debe implementar copia de versión + workflow; los tests de contrato deben cubrir la inmutabilidad (prohibido escribir sobre versiones aprobadas).

## Alternativas consideradas

1. **Editar en sitio con historial en auditoría (patrón actual legacy)**: descartado: el historial por eventos no reconstruye el estado exacto del instrumento en cada momento y contradice el plan maestro §3.4.
2. **Versionado por tabla completa (copia de toda la estructura por versión)**: descartado por el costo de almacenamiento y la complejidad de joins; se versiona la versión del instrumento y sus datos con checksum, no la estructura física.
3. **Código institucional como PK**: descartado (plan maestro §3.6): los códigos cambian por homologación y rompen referencias históricas; se usa UUID técnico.

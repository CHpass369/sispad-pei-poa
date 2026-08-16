---
name: pip-database
description: "Use when: base de datos, modelo de datos, tablas, migraciones, modelos Django, constraints, índices, FKs, catálogos, duplicación de tablas, esquemas PostgreSQL, PostGIS, ownership de datos, nomenclatura de tablas."
---

# PIP — Reglas de Base de Datos

PostgreSQL 17 + PostGIS, 9 esquemas: public, pip_core, pip_catalogo, sis_pe, sis_poa, sis_pro, pip_integracion, pip_auditoria, pip_geo, reportes. ORM: Django 6. El esquema se resuelve por search_path de la conexión; PostgreSQL es la fuente estructural de verdad vía migraciones Django.

## Reglas

- SEARCH BEFORE CREATE: antes de crear cualquier tabla/modelo/catálogo, buscar equivalente (grep, codegraph, docs/architecture/DUPLICATION_ANALYSIS.md, DATA_MODEL_AS_IS.md). Preferir REUSE → EXTEND → LOCAL REFACTOR.
- Migraciones: SIEMPRE migraciones Django (makemigrations/migrate). Nunca SQL crudo fuera del sistema. Revisar migrations/ de la app antes de proponer cambios.
- No renombrar ni borrar tablas sin tarea aprobada (renombrado masivo 15-08-2026 ya rompió queries externas).
- Catálogos maestros: usar `catalogos` (catalogo_*) y `codificacion` (codificación oficial PAD/PEI). No duplicar catálogos.
- Auditoría: tablas de auditoría vía app `auditoria` (EventoAuditoria), no columnas sueltas ad hoc.
- Ownership: cada tabla pertenece al dominio de su app (docs/architecture/DATA_OWNERSHIP.md); no crear tablas de un dominio dentro de otro.
- Nomenclatura: respetar la convención de cada app — legacy en español con prefijo (techos_*, presupuesto_*, catalogo_*), budget V2 con db_table explícito presupuesto_* y modelos en inglés (deuda conocida, no mezclar).

## Modelado

- GestionFiscal (app gestion) es la fuente canónica del periodo: usar FK, nunca PositiveIntegerField suelto de año.
- FKs genéricas sin constraint real (content_type/object_id) son deuda conocida del repo: señalarlas, no replicarlas.
- Incluir constraints e índices acordes al acceso (FKs indexadas por defecto en Django, unique_together/UniqueConstraint donde el dominio lo exija, CheckConstraint cuando aplique).
- Normalización: sin columnas derivadas almacenadas cuando se pueden computar, sin duplicación semántica (consultar DUPLICATION_ANALYSIS.md).

## Verificación

- `cd backend; python -m pytest` para cambios que toquen modelos; `make migrate` para validar migraciones. Comprobar que la nueva migración sea determinista (sin RunPython dependiente de datos que no esté justificado).

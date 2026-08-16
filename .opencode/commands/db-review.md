---
description: Revisar entidades, tablas y migraciones de una app backend: relaciones, constraints, FKs, índices, duplicaciones, naming e integridad. Uso: db-review [app opcional].
agent: database-architect
---

Revisa el modelo de datos indicado SIN MODIFICAR NINGÚN ARCHIVO. $ARGUMENTS

Pasos:

1. Identifica la app (backend/apps/<app>); si $ARGUMENTS está vacío, analiza las apps del dominio que corresponda.
2. Revisa models.py, serializers y el historial de migrations/ de la app (el esquema real vive en las migraciones, no asumas que models.py refleja la BD).
3. Evalúa y reporta (con ruta:línea):
   - Relaciones y cardinalidad, FKs (incluye FKs genéricas sin constraint real: deuda conocida), constraints y unique.
   - Índices acordes a los accesos (búsquedas frecuentes por FK, filtros de gestión fiscal).
   - Duplicación semántica: contrasta cada tabla con docs/architecture/DUPLICATION_ANALYSIS.md y DATA_MODEL_AS_IS.md (techos_* vs presupuesto_techo_*, categoría programática V1 vs V2, catálogos).
   - Naming: convención de la app (español legacy / inglés budget V2, db_table explícito en budget, prefijos catalogo_*).
   - Ownership: tablas de otro dominio dentro de la app (DATA_OWNERSHIP.md).
   - Uso de GestionFiscal como FK vs año suelto (PositiveIntegerField).
4. Si hay propuesta de cambio: especifica la migración Django sugerida (nunca SQL crudo) y su justificación.

NO MODIFICAR. Salida: informe con hallazgos clasificados (BLOCKER/HIGH/MEDIUM/LOW/INFO) y propuestas de migración.

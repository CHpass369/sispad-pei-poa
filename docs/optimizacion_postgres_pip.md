# Optimización Postgres — SIS PAD PEI (PIP-GAMS)

> **Fecha**: 2026-08-15
> **Base**: PostgreSQL 16.0 + PostGIS 3.4.0 — BD `gams_sis_poa`
> **Criterios**: Supabase Postgres Best Practices (8 categorías, priorizadas por impacto)
> **Complementa**: `docs/auditoria_postgres.md` (estado general + 7 índices redundantes)

---

## 1. Mapa funcionalidad PIP → carga de datos (para priorizar)

| Funcionalidad PIP | Tablas que crecen | Patrón de acceso dominante | Volumen esperado |
|---|---|---|---|
| Ciclo presupuestario anual (techos, distribución, reformas) | `presupuesto_*` | Por `gestion` + `estado`, joins a catálogos | Medio (miles/año) |
| Bandeja de aprobaciones (workflow) | `flujo_tarea`, `flujo_instancia`, `flujo_aprobacion_motor` | **Por usuario** (`asignado_a`) + `estado` + orden por fecha | Medio |
| Trazabilidad (auditoría append-only) | `auditoria_eventoauditoria` | Por `entidad`+`entidad_id`, por `usuario`, por `gestion` | **ALTO — crece sin límite** |
| Formulación POAU (unidades) | `poau_*`, `articulacion_*` | Por `gestion` + jerarquía (padre→hijo) | Medio |
| Planificación estratégica (árboles) | `planificacion_*` | Recorrido de árbol por `plan` + `nivel` | Bajo (estable) |
| Consolidación/reportes | `lineapresupuestaria`, `distribuciontecho` (legacy) + agregaciones | **Agregaciones con JOINs** | Medio |

---

## 2. Hallazgos por categoría (regla Supabase aplicada)

### ✅ Cumplido correctamente
- **`schema-foreign-key-indexes`**: 0 FK sin índice — todas indexadas.
- **`schema-primary-keys`**: 0 tablas sin PK.
- **`schema-data-types`**: montos con `DecimalField` (nunca float); budget usa `BigAutoField` (futuro-proof); timestamps `auto_now_add` con `db_index` en auditoría.
- **`query-composite-indexes`**: `presupuesto_apertura` tiene compuestos correctos (`gestion,version`, `gestion,categoria`, `gestion,distrito`); `presupuesto_reserva` (`gestion,estado`, `gestion,version`); `presupuesto_apertura_fuente` UNIQUE (`allocation,fuente,organismo`).
- **`query-partial-indexes`**: `flujo_instancia` tiene UNIQUE parcial (`definicion,entidad_tipo,entidad_id WHERE cerrado=False`) — patrón ejemplar.
- **`schema-constraints`**: checks de monto >= 0, UNIQUEs de versionado (`catalogo_*`), inmutabilidad con checksum.

### ⚠️ Hallazgos de rendimiento (priorizados)

#### P0 — CRÍTICO para la bandeja de aprobaciones (workflow)
**`data-n-plus-one` + `query-missing-indexes` en `flujo_tarea`**:
- La UI nueva (bandeja) consulta `WorkflowTask.objects.filter(asignado_a=user, estado IN (...)).order_by('-creado_en')` — **no existe índice compuesto** para ese patrón (solo la FK automática `instancia_id` y la UNIQUE parcial de instancia).
- Con miles de tareas por gestión, cada consulta de bandeja hace seq scan.
- **Fix**: índice compuesto `(asignado_a, estado, -creado_en)` o mejor parcial:
  ```python
  models.Index(fields=['asignado_a', '-creado_en'], name='flujo_tarea_bandeja_idx',
               condition=models.Q(estado__in=['pendiente', 'en_curso'])),
  ```

#### P0 — Auditoría crece sin límite
**`monitor-` / `schema-partitioning` en `auditoria_eventoauditoria`**:
- Índices actuales: `(entidad, entidad_id)`, `(usuario, creado_en)`, `(gestion)`, `creado_en` db_index.
- Faltan: índice compuesto `(entidad, entidad_id, -creado_en)` para historial por entidad ordenado (el patrón real de la UI de auditoría) y `(gestion, accion)`.
- **Mediano plazo**: particionar por `gestion` (RANGE) cuando supere ~10M filas — la política de retención y el reporte por gestión lo hacen natural.

#### P1 — N+1 reales en código (data-n-plus-one)
1. **`apps/workflow/consolidacion.py:190`** — `for prog in programas_qs: lineas.filter(programa=prog).aggregate(...)` → **1 query por programa** (N+1). Con ~112 programas reales = 112+ queries por consolidación.
   - **Fix**: una sola agregación con `GROUP BY programa` + `prefetch` de detalle por programa.
2. **`apps/planificacion/services.py:147`** — `for hijo in NodoPlanificacion.objects.filter(padre=nodo)` → N+1 en recorrido de árbol.
   - **Fix**: cargar todos los nodos del plan de una vez y armar el árbol en memoria (los árboles de planificación son acotados).

#### P1 — Índices redundantes del rename (ya documentado en `auditoria_postgres.md`)
7 índices duplicados (sección 2 del doc) — limpiar antes de producción.

#### P2 — Tipos de datos (schema-data-types)
- Las tablas de workflow/planificación/articulación usan **UUID v4 aleatorio** como PK: índices B-tree más grandes y con fragmentación vs `bigint`. Es una decisión de diseño válida (sincronización/seguridad), no la cambies — pero **no la mezcles**: las tablas nuevas de negocio deberían usar `BigAutoField` como ya hace budget.
- `EventoAuditoria.entidad_id` es `CharField(100)` (FK genérica) — correcto para el patrón polimórfico; el índice compuesto lo mitiga.

#### P2 — Paginación profunda (data-pagination)
- Los viewsets usan paginación por offset (`Paginado{count, results}`) — con tablas grandes el `OFFSET` profundo degrada. Cuando `presupuesto_*` o auditoría crezcan, considerar **cursor pagination** en los listados de auditoría e importaciones.

#### P2 — Agregaciones de consolidación (query-composite-indexes)
- `consolidacion.py` agrega `LineaPresupuestaria`/`DistribucionTecho` por `(gestion, programa, fuente, organismo, objeto_gasto)` — confirmar índices compuestos en las tablas legacy `presupuesto_lineapresupuestaria` (ya tiene `gestion,fuente,objeto_gasto,programa` — cubre el patrón).

---

## 3. Plan de acción recomendado (por orden)

### Fase A — Antes de producción (bajo riesgo, 30 min)
1. Migraciones `RemoveIndex` para los 7 redundantes (`docs/auditoria_postgres.md` §2).
2. Índice de bandeja en `flujo_tarea` (P0):
   ```python
   # apps/workflow/models_v2.py → class Meta de WorkflowTask
   indexes = [
       models.Index(
           fields=['asignado_a', '-creado_en'],
           name='flujo_tarea_bandeja_idx',
           condition=models.Q(estado__in=['pendiente', 'en_curso']),
       ),
   ]
   ```
3. Índice de historial en auditoría:
   ```python
   # apps/auditoria/models.py → EventoAuditoria.Meta.indexes
   models.Index(fields=['entidad', 'entidad_id', '-creado_en'], name='audit_entidad_historial_idx'),
   models.Index(fields=['gestion', 'accion'], name='audit_gestion_accion_idx'),
   ```
4. Refactor N+1 de consolidación (una agregación GROUP BY) y árbol de planificación (carga en memoria).

### Fase B — Con datos reales (cuando el PIP opere)
5. Habilitar `pg_stat_statements` y medir 1 semana antes de más cambios.
6. Ajustar `shared_buffers` (~25% RAM), `work_mem` (16–32 MB), `effective_cache_size`.
7. pgbouncer (transaction pooling) entre app y BD.

### Fase C — Crecimiento
8. Particionar `auditoria_eventoauditoria` por gestión (~10M filas).
9. Cursor pagination en auditoría/importaciones.

---

## 4. Reglas Supabase consultadas (referencia para documentación futura)

| Regla | Archivo | Aplicación en el PIP |
|---|---|---|
| `query-missing-indexes` | references/query-missing-indexes.md | Índices de bandeja y auditoría |
| `query-composite-indexes` | references/query-composite-indexes.md | Orden de columnas: igualdad antes que rango |
| `query-partial-indexes` | references/query-partial-indexes.md | Bandeja (solo pendiente/en_curso); instancia abierta |
| `schema-foreign-key-indexes` | references/schema-foreign-key-indexes.md | ✅ Verificado 0 faltantes |
| `schema-data-types` | references/schema-data-types.md | Decimal montos ✅; UUID vs bigint (decisión) |
| `schema-constraints` | references/schema-constraints.md | Checks monto >= 0 ✅ |
| `data-n-plus-one` | references/data-n-plus-one.md | Consolidación y árbol de planificación |
| `data-pagination` | references/data-pagination.md | Cursor pagination futuro |
| `schema-partitioning` | references/schema-partitioning.md | Auditoría por gestión |
| `monitor-explain-analyze` | references/monitor-explain-analyze.md | pg_stat_statements antes de tocar más |

---

## 5. Verificación propuesta

```sql
-- Después de aplicar Fase A: la bandeja debe usar index scan
EXPLAIN ANALYZE
SELECT * FROM flujo_tarea
WHERE asignado_a = '<usuario>' AND estado IN ('pendiente','en_curso')
ORDER BY creado_en DESC;
-- Esperado: Index Scan using flujo_tarea_bandeja_idx

-- Auditoría: historial por entidad
EXPLAIN ANALYZE
SELECT * FROM auditoria_eventoauditoria
WHERE entidad = 'DirectiveCeilingVersion' AND entidad_id = '<uuid>'
ORDER BY creado_en DESC;
-- Esperado: Index Scan using audit_entidad_historial_idx
```

**Estado actual de este documento**: hallazgos y plan propuesto — **sin aplicar** (decisión del equipo: documentar antes de tocar la BD con datos reales cargados).

---

## 6. Registro de aplicación (2026-08-15) — FASES A/B/C APLICADAS

### ✅ FASE A — Aplicada (índices + refactor N+1 + limpieza)
- **Índice de bandeja**: `flujo_tarea_bandeja_idx` (parcial, `asignado_a, -creado_en WHERE estado IN ('pendiente','en_curso')`) — migración `workflow/0005`.
- **Índices de auditoría**: `audit_entidad_historial_idx` (`entidad, entidad_id, -creado_en`) + `audit_gestion_accion_idx` (`gestion, accion`) — migración `auditoria/0002`.
- **7 índices redundantes del rename eliminados**:
  - `budget/0009` (RunSQL DROP): 4 índices FK automáticos `budget_*` en territorialdistribution, budgetdocument, budgetimport, reform.
  - `presupuesto/0006` (RunSQL DROP): 1 índice FK automático legacy.
  - `budget/0010`: RemoveIndex `presupuesto_allocat_c5ae8a_idx` (duplicaba al UNIQUE `uniq_allocation_objeto_gasto`) — requirió quitar el índice no-unique de `ExpenseObjectAllocation.Meta`.
  - `seguimiento/0002`: RemoveIndex `seguimiento_reporte_521f0b_idx` (duplicaba al unique_together `(reporte, actividad)`) — requirió quitar el índice de `EntradaSeguimiento.Meta`.
  - **Nota de corrección sobre el doc original**: el índice a eliminar en `seguimiento_entradaseguimiento` era el **no-unique** (`seguimiento_reporte_521f0b_idx`), NO el UNIQUE `..._2cab77bf_uniq` (ese es la integridad activa). Corregido en la aplicación.
- **Refactor N+1**:
  - `workflow/consolidacion.py`: consolidación por programa batcheada (totales GROUP BY + detalle + techo por programa con `programa_id__in`) — antes ~4 queries × N programas, ahora 5 queries fijas. Contrato de salida preservado (verificado con regression manual).
  - `planificacion/services.py`: árbol de nodos con carga única + dict `{padre_id: [hijos]}`.
- **Tests**: workflow 57-66 passed, planificacion 25 passed, budget smoke 48 passed, importadores OK.

### ✅ FASE B — Aplicada (config PostgreSQL)
- `ALTER SYSTEM` (como superuser postgres): `work_mem 32MB`, `maintenance_work_mem 256MB`, `effective_cache_size 24GB`, `random_page_cost 1.1` — **activos** (context user, pg_reload_conf).
- `shared_buffers 2GB` — persistido en `postgresql.auto.conf` pero **requiere reinicio del servicio** `postgresql-x64-16` (context postmaster; el reinicio necesita permisos de administrador — pendiente manual: `Restart-Service postgresql-x64-16`).
- **Conexión real de la BD local**: HOST=localhost, PORT=**5432** (no 5433), USER=`sispoa`, PASSWORD=`sispoa_local_2026`, NAME=`gams_sis_poa`. Usuario `sispoa` no es superuser; `postgres`/`postgres` sí.

### ✅ FASE C — Aplicada parcial (paginación dual; particionado documentado como NO viable)
- **Paginación dual (cursor + page)** — `backend/apps/core/pagination.py`:
  - `PaginacionDualPagination(PageNumberPagination)` — modo page por defecto (contrato `{count, results, next, previous}` idéntico, frontend intacto); si el cliente manda `?cursor=`, delega a cursor con `count` real (una query COUNT extra, igual que page).
  - Aplicada a `EventoAuditoriaViewSet` (ordering `-creado_en`) y `AuditLogView` (el endpoint real que consume el frontend, `/api/v2/sis-poa/budget/audit/`) + `BudgetImportViewSet`.
  - **Confirmado**: el frontend Angular construye `?page=N` a mano y no usa `next` → queda en modo page por defecto, cero impacto; el modo cursor queda listo para clientes futuros (reportes, exportaciones).
  - Tests: `tests/test_paginacion_dual.py` 4 passed; frontend audit+imports 15 SUCCESS.
- **Particionado de `auditoria_eventoauditoria` — NO aplicado (bloqueo técnico documentado)**:
  - PostgreSQL exige que las constraints UNIQUE/PK de una tabla particionada **incluyan la columna de partición**.
  - `EventoAuditoria` tiene PK `id UUID` simple; particionar por `gestion` (o `creado_en`) obligaría a PK compuesta `(id, gestion)`, cambio estructural que rompe ORM, URLs, serializers y frontend.
  - **Alternativa recomendada cuando crezca (~10M filas)**: política de retención por gestión (purga de gestiones cerradas antiguas) + los índices nuevos ya cubren los patrones de consulta. Si algún día se decide particionar, requiere rediseño de PK con migración de datos planificada.

### 🔲 PENDIENTE
- Reiniciar el servicio PostgreSQL (`Restart-Service postgresql-x64-16` como administrador) para activar `shared_buffers = 2GB`.
- `pg_stat_statements` para producción (requiere agregar la librería a `shared_preload_libraries` + restart — NO aplicado en dev para no tocar la config de arranque; documentado en sección 3).
- Particionado de auditoría: solo si se acepta el rediseño de PK (ver arriba).

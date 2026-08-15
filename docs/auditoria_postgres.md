# Auditoría Postgres — SIS PAD PEI (gams_sis_poa)

> **Fecha**: 2026-08-15
> **Base**: PostgreSQL 16.0 + PostGIS 3.4.0
> **Criterios**: Supabase Postgres Best Practices (query-, schema-, data-, monitor-)

---

## 1. Estado general: OK

| Regla | Resultado |
|---|---|
| FK sin índice (`schema-foreign-key-indexes`) | **0 faltantes** — todas las FK indexadas |
| Tablas sin PK (`schema-primary-keys`) | **0** — las 219 tablas tienen PK |
| Índices `_like` (`varchar_pattern_ops`) | 31 pares `_key`/`_like` — **intencionales** (igualdad única + búsqueda LIKE), no son duplicados |
| Autovacuum | ON |
| Tablas de negocio > 1.000 filas | **Ninguna** (solo `spatial_ref_sys` de PostGIS, catálogo del sistema) |

## 2. Pendiente documentado: 7 índices redundantes

**Origen**: el rename de tablas a español (commit `9961550`, 2026-08-15) dejó los índices FK automáticos con prefijo viejo (`budget_*`) conviviendo con los nuevos (`presupuesto_*`). Misma columna, dos índices.

**Impacto actual**: despreciable (tablas casi vacías). **Obligatorio limpiar antes de producción.**

| Tabla | Índice redundante | Cubierto por |
|---|---|---|
| `presupuesto_distribucion_territorial` | `budget_territorialdistribution_gestion_id_8bcca733` | `presupuesto_gestion_b1b624_idx` |
| `presupuesto_documento` | `budget_budgetdocument_gestion_id_c28cf903` | `presupuesto_gestion_5e1323_idx` |
| `presupuesto_importacion` | `budget_budgetimport_gestion_id_36e918d5` | `presupuesto_gestion_7e3fbd_idx` |
| `presupuesto_reforma` | `budget_reform_gestion_id_e2cc3ea9` | `presupuesto_gestion_c81ad1_idx` |
| `presupuesto_asignacion_objeto_gasto` | `presupuesto_allocat_c5ae8a_idx` (no-unique) | `uniq_allocation_objeto_gasto` (UNIQUE) |
| `presupuesto_asignacionpresupuestariaunidad` (legacy) | `presupuesto_asignacionpres_categoria_programatica_id_e27958f4` | `presupuesto_categor_3e54f5_idx` |
| `seguimiento_entradaseguimiento` | `seguimiento_entradasegui_reporte_id_actividad_id_2cab77bf_uniq` (UNIQUE duplica al idx) | `seguimiento_reporte_521f0b_idx` |

### SQL de fix (migración Django, NO SQL suelto)

```python
# apps/budget/migrations/0009_limpiar_indices_redundantes.py (o la siguiente numeración)
from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ('budget', '0008_rename_budget_allo_gestion_6281d0_idx_...'),
    ]

    operations = [
        migrations.RemoveIndex(
            model_name='territorialdistribution',
            name='budget_territorialdistribution_gestion_id_8bcca733',
        ),
        migrations.RemoveIndex(
            model_name='budgetdocument',
            name='budget_budgetdocument_gestion_id_c28cf903',
        ),
        migrations.RemoveIndex(
            model_name='budgetimport',
            name='budget_budgetimport_gestion_id_36e918d5',
        ),
        migrations.RemoveIndex(
            model_name='reform',
            name='budget_reform_gestion_id_e2cc3ea9',
        ),
        migrations.RemoveIndex(
            model_name='expenseobjectallocation',
            name='presupuesto_allocat_c5ae8a_idx',
        ),
    ]
```

```python
# apps/presupuesto/migrations/0006_limpiar_indices_redundantes.py (o la siguiente numeración)
from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ('presupuesto', '0005_renombrar_catalogos_en_funciones_trigger'),
    ]

    operations = [
        migrations.RemoveIndex(
            model_name='asignacionpresupuestariaunidad',
            name='presupuesto_asignacionpres_categoria_programatica_id_e27958f4',
        ),
    ]
```

```python
# apps/seguimiento/migrations/000X_limpiar_indices_redundantes.py (o la siguiente numeración)
from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ('seguimiento', '<ultima migracion>'),
    ]

    operations = [
        migrations.RemoveIndex(
            model_name='entradaseguimiento',
            name='seguimiento_entradasegui_reporte_id_actividad_id_2cab77bf_uniq',
        ),
    ]
```

**Verificación post-fix**: `git grep "budget_" docs/ backend/` no debe encontrar índices; re-correr la query de duplicados debe dar 0.

## 3. Recomendaciones para producción (cuando el PIP esté operativo)

1. **Limpieza de índices** (sección 2) — antes de cargar datos reales.
2. **Config PostgreSQL** (hoy valores por defecto de PG16):
   - `shared_buffers` → ~25% de la RAM del servidor (hoy 128 MB)
   - `work_mem` → 16–32 MB (hoy 4 MB)
   - `effective_cache_size` → ~75% de la RAM (hoy 4 GB)
   - `max_connections` → ajustar según pgbouncer/pooler
3. **Connection pooling** (`conn-*`): pgbouncer en modo transaction entre app y BD.
4. **Particionado** (`schema-partitioning`): `auditoria_eventoauditoria` crece sin límite (append-only) — particionar por gestión cuando supere ~10M filas (riesgo R10 del backlog).
5. **Monitoreo** (`monitor-*`): habilitar `pg_stat_statements` en producción para detectar queries lentas reales con los datos reales.
6. **Backups**: verificar `pg_dump` programado + restore test (riesgo del backlog de infraestructura).

## 4. Notas

- Las queries del núcleo presupuestario ya están cubiertas por índices compuestos correctos (`gestion_id, version_id`, UNIQUE `allocation_id, objeto_gasto_id`, etc.).
- `catalogos_seed_t4_propiedad` es tabla temporal de data migration (no modelo) — se deja como está.
- La BD local de desarrollo tiene los datos reales 2027 cargados (catálogos + techo SIGEP) como base de trabajo.

# FASE 2 — PLAN DE MIGRACIÓN DE DATOS (public → esquemas PIP)

> Plan operativo para migrar las 217 tablas del esquema `public` (BD `gams_sis_poa`) hacia los esquemas objetivo de la arquitectura PIP.
> Fuente: `SCHEMA_MAPPING.md` (mapeo completo tabla por tabla), `ARQUITECTURA_ACTUAL.md` (baseline) y `ARQUITECTURA_OBJETIVO.md` (destino).
> Ciclo de vida de cada grupo: **AUDIT → MAP → BACKUP → CREATE TARGET → MIGRATE → VALIDATE → SWITCH → DEPRECATE → REMOVE LEGACY**.

---

## 1. Principios de la migración

| # | Principio |
|---|---|
| P1 | NUNCA ejecutar `DROP SCHEMA sispoa CASCADE;` (ni equivalentes) al inicio. El esquema `public` solo se renombra a `public_legacy` y se elimina al final, tras validación en producción. |
| P2 | Backup verificable antes de cada grupo (`pg_dump -Fc` + prueba de restauración `--list`), no solo antes de la fase 0. |
| P3 | Cada grupo se MIGRA y VALIDA completo (conteos, FKs, triggers, vistas, checksums) antes de migrar el siguiente. |
| P4 | La app Django se ajusta en el mismo paquete que el movimiento de tablas: `db_table` con esquema o `search_path` explícito + migración Django documentada. |
| P5 | Los nombres de tablas NO cambian al mover de esquema (KEEP); el renombrado semántico (`techo_directivo`, `documento_adjunto`, etc.) se hace SOLO si aporta valor y siempre con mapeo (`SCHEMA_MAPPING.md` columna "Objeto destino"). |
| P6 | Valores de datos protegidos (`Importacion.perfil = 'SISPOA_GASTOS_*'`, `SolicitudReformulacion.sistema_origen = 'SISPOA'`) se conservan intactos; el renombrado semántico es decisión de la fase de datos, con backfill y homologación. |
| P7 | Tablas de framework/PostGIS (`auth_*`, `django_*`, `geometry_columns`, `spatial_ref_sys`) quedan en `public` (KEEP_SYSTEM). |
| P8 | Rollback definido por grupo: los `ALTER TABLE ... SET SCHEMA` son reversibles con `SET SCHEMA` inverso mientras `public` siga existiendo. |

## 2. Fase 0 — AUDIT + MAP + BACKUP (línea base)

Ya ejecutado en la Fase 1 (auditoría y mapeo: `SCHEMA_MAPPING.md`, `DOMAIN_MAP.md`, `ARQUITECTURA_ACTUAL.md`). Lo que resta es el respaldo reproducible:

| Tarea | Comando / acción | Verificación |
|---|---|---|
| Snapshot Git del estado previo | `git tag refactor/pip-gams/pre-schema-migration` (después de commitear la Fase 1) | `git log --oneline` |
| Backup lógico completo | `pg_dump -Fc -h localhost -p 5433 -U sispoa -d gams_sis_poa -f gams_sis_poa_pre_migracion.dump` | El archivo existe y `pg_restore --list` no da error |
| Inventario de referencia | `SELECT table_name, pg_size_pretty(pg_total_relation_size(quote_ident(table_name))) FROM information_schema.tables WHERE table_schema='public' AND table_type='BASE TABLE' ORDER BY 1;` | 217 filas (baseline `ARQUITECTURA_ACTUAL.md` §4) |
| Conteos por tabla | `SELECT schemaname, tablename, n_live_tup FROM pg_stat_user_tables WHERE schemaname='public' ORDER BY 2;` | Guardar salida como `pre_migracion_conteos.csv` (referencia de validación) |
| Funciones y triggers existentes | `SELECT proname FROM pg_proc WHERE pronamespace = 'public'::regnamespace;` y `SELECT tgname, tgrelid::regclass FROM pg_trigger;` | Inventario para el riesgo R3 (funciones PL/pgSQL) |
| Vistas dependientes | `SELECT viewname FROM pg_views WHERE schemaname='public';` + `pg_depend` sobre tablas a mover | Lista de vistas a recalificar en cada SWITCH |

## 3. Fase 1 — CREATE TARGET (crear esquemas objetivo)

```sql
CREATE SCHEMA IF NOT EXISTS pip_core       AUTHORIZATION sispoa;
CREATE SCHEMA IF NOT EXISTS pip_catalogo   AUTHORIZATION sispoa;
CREATE SCHEMA IF NOT EXISTS sis_pe         AUTHORIZATION sispoa;
CREATE SCHEMA IF NOT EXISTS sis_poa        AUTHORIZATION sispoa;
CREATE SCHEMA IF NOT EXISTS sis_pro        AUTHORIZATION sispoa;
CREATE SCHEMA IF NOT EXISTS pip_integracion AUTHORIZATION sispoa;
CREATE SCHEMA IF NOT EXISTS pip_auditoria  AUTHORIZATION sispoa;
CREATE SCHEMA IF NOT EXISTS pip_geo        AUTHORIZATION sispoa;
CREATE SCHEMA IF NOT EXISTS reportes       AUTHORIZATION sispoa;
```

Reglas:

- Cada esquema se crea con el rol de aplicación como owner (`sispoa` hoy; `pip` tras el rename de infraestructura) para evitar problemas de ownership al mover tablas.
- Nada se mueve todavía; `public` permanece íntegro.
- PostGIS sigue en `public` (P7); los esquemas de negocio NO contienen extensiones.

## 4. Fase 2 — MIGRATE + VALIDATE por grupo

Orden de migración por grupos (independencia de dependencias: CORE → CATÁLOGOS → GEO → PE → POA → PRO → INTEGRACIÓN → AUDITORÍA → REPORTES). Para cada grupo se ejecuta el bloque: **BACKUP → MIGRATE → VALIDATE**.

### Bloque estándar por grupo

```sql
-- 1) Backup (conteos + dump selectivo del grupo, P2)
pg_dump -Fc -h localhost -p 5433 -U sispoa -d gams_sis_poa -t 'cuentas_*' -f backup_grupo_core.dump

-- 2) MIGRATE: mover tabla (KEEP de nombre; solo cambia el esquema)
ALTER TABLE public.cuentas_usuario SET SCHEMA pip_core;
ALTER TABLE public.cuentas_rol       SET SCHEMA pip_core;
-- ... resto del grupo

-- 3) VALIDATE (por tabla y total)
SELECT count(*) FROM pip_core.cuentas_usuario;
```

### 4.1 Grupos de migración (fuente: `SCHEMA_MAPPING.md`)

| Grupo | Esquema destino | Tablas (según sección del mapeo) | Acciones |
|---|---|---|---|
| A. CORE | `pip_core` | `cuentas_*` (8), `organizacion_*` (5), `nucleo_*` (2), `flujo_*` V2 (8) → `SCHEMA_MAPPING.md` §1; `documentos_documentoadjunto`, `notificaciones_*` (3), `acciones_correctivas_*` (2) → §1 "Otras apps" | KEEP + MOVE |
| B. AUDITORÍA | `pip_auditoria` | `auditoria_eventoauditoria` (1) → §2 | MOVE |
| C. CATÁLOGOS | `pip_catalogo` | `catalogo_*` (15), `normativa_*` (2), `codificacion_versioncatalogoplan`, `codificacion_entidadcodificadora`, `codificacion_secuenciacodigo`, `codificacion_homologacioncodigo` (4) → §3 | KEEP + MOVE |
| D. SIS-PE | `sis_pe` | `planificacion_*` (14; sin `accioncortoplazo`), `pad_*` (8), `articulacion_*` estratégico (11; sin `articulacionpadpei`), `codificacion_*` PGDESA/PDESA/PAD (5), `indicadores_medioverificacion`, `indicadores_supuesto` → §4 | MOVE + MERGE (*) |
| E. SIS-POA | `sis_poa` | `gestion_*` (3), `presupuesto_*` budget (18), `recursos_*` (2), `poau_*` (10), `articulacion_*` operativo (6), `planificacion_accioncortoplazo`, `seguimiento_*` (4), `modificaciones_*` (3) → §5 | MOVE + MERGE (*) |
| F. SIS-PRO | `sis_pro` | `inversion_*` (34; sin `eventooutbox`, `mensajeentrante`, `referenciaexterna`) → §6 | MOVE |
| G. INTEGRACIÓN | `pip_integracion` | `articulacion_articulacionpadpei`, `inversion_eventooutbox`, `inversion_mensajeentrante`, `inversion_referenciaexterna` (4) → §6 | MOVE |
| H. GEO | `pip_geo` | `territorio_*` (3), `codificacion_entidadterritorialcgeo` → §7 | MOVE |
| I. REPORTES | `reportes` | `reportes_reportegenerado` (1) → §8 | MOVE |
| L. LEGACY | `public` (se queda) | `presupuesto_*` legacy (6), `techos_*` (3), `flujo_*` legacy (4), `indicadores_operacion/tarea/producto` (3) → §5 y §4 | DEPRECATE / REMOVE_LATER |
| S. SISTEMA | `public` (se queda) | `auth_*`, `django_*` (5), `geometry_columns`, `spatial_ref_sys` (2) → §9 | KEEP_SYSTEM |

(*) Las filas MERGE (duplicados legacy vs V2: `poau_poau`, `poau_poauactividad`, `articulacion_accionpoa`/`operacionpoau`/`actividadpoau`/`tareapoau`, `articulacion_asignacionobjetogasto`, `gestion_gestionfiscal` vs `budget.FiscalYear`) NO se ejecutan en esta fase: primero se mueve el grupo completo con KEEP de esquema, y el MERGE de filas se hace en la fase de datos del dominio con `LegacyMigrationMap` (plan maestro §8.2: expandir → backfill → reconciliar → cortar escritura legacy → observar → retirar).

### 4.2 Ajuste de Django por grupo

Dos mecanismos, se elige UNO por grupo y se documenta:

1. **`search_path` por rol (recomendado para el SWITCH general)**: en `backend/config/settings.py`, `DATABASES['default']['OPTIONS'] = {'options': '-c search_path=pip_core,pip_catalogo,sis_pe,sis_poa,sis_pro,pip_integracion,pip_auditoria,pip_geo,reportes,public'}` (o `ALTER ROLE sispoa SET search_path = ...`). El primer esquema con la tabla la resuelve; `public` queda al final como fallback para framework/PostGIS.
2. **`db_table` por modelo**: `Meta.db_table = '"sis_poa"."techo_directivo"'` en los modelos del grupo + migración Django que altere `db_table`. Aplicar solo cuando se necesite renombrar además de mover.

Reglas:

- La migración Django acompaña SIEMPRE al movimiento físico (misma revisión), porque el ORM y las migraciones son el estado histórico de la BD (plan maestro §5.1).
- `urls_test_sqlite.py` (CI sin PostGIS) no distingue esquemas: el `search_path` default basta; validar que la suite pase antes y después de cada grupo.
- No se reescriben migraciones aplicadas (`budget/migrations/0004_*` con choices `SISPOA_GASTOS_*` se conserva tal cual, P6).

### 4.3 Validación por grupo (VALIDATE)

| Verificación | Query / acción | Criterio de aceptación |
|---|---|---|
| Conteos | `SELECT count(*) FROM <esquema>.<tabla>;` vs inventario `pre_migracion_conteos.csv` | Iguales (0 diferencias) |
| FKs | `SELECT conrelid::regclass, confrelid::regclass FROM pg_constraint WHERE contype='f' AND connamespace='<esquema>'::regnamespace;` | Todas las FK esperadas existen y apuntan al destino correcto (incluye FK cross-esquema, permitidas en PostgreSQL) |
| Triggers | `SELECT tgname, tgrelid::regclass FROM pg_trigger WHERE tgrelid::regclass::text LIKE '<esquema>.%';` | Mismos triggers que en `public` antes del movimiento |
| Vistas dependientes | `SELECT DISTINCT dependent_view FROM pg_depend JOIN pg_views ON ...` | Las vistas que referenciaban `public.<tabla>` fueron recalificadas a `<esquema>.<tabla>` o a la vista de compatibilidad |
| Checksums (catálogos) | `SELECT count(*), count(DISTINCT hash_fuente) FROM pip_catalogo.version_clasificador;` | Sin duplicados ni pérdida |
| Sumas presupuestarias (SIS-POA) | Comparar sumas de `techo_directivo`, `apertura`, `reforma_movimiento` por gestión antes/después | Diferencias = 0 |
| Perfiles de importación | `SELECT perfil, count(*) FROM sis_poa.importacion GROUP BY perfil;` | Perfiles `SISPOA_GASTOS_HISTORICO`/`ACTUAL` intactos (P6) |
| Escritura de prueba | Insert/update/delete en una fila de prueba por grupo (transacción con rollback) | Sin errores de permisos o search_path |

## 5. Fase 3 — SWITCH (apuntar Django al nuevo esquema)

| Paso | Acción |
|---|---|
| 1 | Aplicar `search_path` por rol o `db_table` (mecanismo elegido en §4.2) y desplegar el backend. |
| 2 | Mantener vistas de compatibilidad en `public` (p. ej. `CREATE VIEW public.cuentas_usuario AS SELECT * FROM pip_core.cuentas_usuario;`) SOLO si hay consumidores externos directos (reportes ad-hoc, BI, integraciones). Cada vista se registra en `LEGACY_DEPRECATION.md`. |
| 3 | Ejecutar suite de tests completa (`pytest` + contrato V2 en `backend/tests/`). |
| 4 | Período de observación con monitoreo de errores `UndefinedTable` en logs (indicador de search_path incompleto). |
| 5 | Rollback si falla: revertir `search_path`/`db_table` (los datos siguen en el esquema nuevo; no se pierde nada). |

## 6. Fase 4 — DEPRECATE `public` (renombrar, nunca dropear)

```sql
-- Solo cuando TODOS los grupos migraron y el SWITCH está estable
ALTER SCHEMA public RENAME TO public_legacy;
-- Ajustar search_path: eliminar 'public' del final o apuntar a public_legacy si hay vistas de compatibilidad
ALTER ROLE sispoa SET search_path = pip_core,pip_catalogo,sis_pe,sis_poa,sis_pro,pip_integracion,pip_auditoria,pip_geo,reportes,public_legacy;
```

- El esquema `public_legacy` conserva: tablas legacy DEPRECATE (`presupuesto_*`, `techos_*`, `flujo_*` legacy, `indicadores_operacion/tarea/producto`) y framework/PostGIS.
- Si alguna extensión (PostGIS) exige `public`, se crea el esquema `public` vacío SOLO para la extensión o se evalúa reubicar la extensión (requiere reinstalación, se documenta en el riesgo R4).
- Todo acceso en modo lectura a `public_legacy` se audita (quién lo consulta) para decidir el REMOVE.

## 7. Fase 5 — REMOVE LEGACY (con ventana de mantenimiento)

Condiciones previas (todas):

1. Cutover V2 completo (palanca `LEGACY_MENU_VISIBLE` del frontend apagada; `AUDITORIA_SISPOA.md` §7).
2. Cero escritura legacy en producción durante ≥ 1 ciclo de gestión (observación).
3. Reconciliación 100% de registros críticos (plan maestro FASE 14).
4. Backup `-Fc` verificado del estado previo + prueba de restauración documentada.
5. Ventana de mantenimiento comunicada.

Acciones:

```sql
-- Backup final del legacy
pg_dump -Fc -h localhost -p 5433 -U sispoa -d gams_sis_poa -n public_legacy -f public_legacy_final.dump
-- Luego de la ventana y la verificación de restauración ensayada:
DROP SCHEMA IF EXISTS public_legacy CASCADE;  -- SOLO aquí, con respaldo verificado y autorización escrita
```

- La tabla técnica `nucleo_mapa_migraciones_legacy` (en `pip_core.mapa_migraciones_legacy`) registra cada grupo migrado con fecha, lote y estado; se actualiza en cada fase.
- Eliminación ordenada: primero tablas REMOVE_LATER (`indicadores_operacion/tarea/producto`), luego DEPRECATE (`presupuesto_*`, `techos_*`, `flujo_*` legacy), al final el esquema completo.

## 8. Riesgos por grupo

| Riesgo | Grupo | Nivel | Mitigación |
|---|---|---|---|
| **Colisión de prefijos `presupuesto_categoria_programatica` (budget) vs `presupuesto_categoriaprogramatica` (legacy)** | E (SIS-POA) | Alto | Se resuelve por separación física: budget → `sis_poa`, legacy → `public_legacy`. Verificar en VALIDATE que ninguna query calificada `presupuesto_*` ambigua quede en el código (search_path puede resolver mal si ambos esquemas están en el path; por eso `public`/`public_legacy` va ÚLTIMO en el search_path). |
| **Funciones trigger PL/pgSQL con nombres viejos** | Todos (especialmente E) | Medio | Los triggers viajan con la tabla al mover esquema, pero las funciones que referencian pueden quedar en `public`. Recalificar (`ALTER FUNCTION ... SET SCHEMA`) o calificar con esquema en el cuerpo del trigger. Inventario previo en Fase 0. |
| **`search_path` de extensiones PostGIS** | H (GEO) y tablas con columnas geometry | Alto | `geometry_columns` y `spatial_ref_sys` viven en `public`; al renombrar a `public_legacy` o reubicar extensiones, verificar `Find_SRID`, `ST_*` y `populate_geometry_columns()` contra el search_path vigente. Probar una query espacial real en cada entorno tras el SWITCH. |
| **Permisos por esquema** | Todos | Medio | Otorgar `GRANT USAGE, CREATE ON SCHEMA <esquema> TO sispoa;` y `GRANT ALL ON ALL TABLES IN SCHEMA ...` + `ALTER DEFAULT PRIVILEGES`. Revisar secuencias (`nextval`) y ownership tras cada grupo. |
| **FK cross-esquema** | Todos (p. ej. `vinculo_proyecto_actividad` → actividad de SIS-POA) | Medio | PostgreSQL permite FKs entre esquemas; VALIDATE verifica que no se perdieron al mover (se mueven con la tabla). No usar `NOT VALID` sin plan de validación posterior. |
| **Vistas/materialized views sin recalificar** | Todos | Medio | Inventario de dependencias en Fase 0; recalificar o crear vistas de compatibilidad en cada SWITCH. |
| **M2M y tablas de through** | A, D, E | Bajo | Las tablas M2M se mueven con su grupo; verificar que ambas puntas estén en el mismo esquema o que la FK cross-esquema quede válida. |
| **Duplicados MERGE (`poau_*`, `articulacion_*`, `gestion_gestionfiscal`)** | E | Alto | NO fusionar filas en la migración de esquema; el MERGE se hace por dominio con `LegacyMigrationMap`, congelando escritura legacy antes (plan maestro §8.2 y §20). |
| **Valores de datos `SISPOA_GASTOS_*` y `sistema_origen='SISPOA'`** | E, G | Alto | KEEP en migración; renombrado solo con backfill y homologación documentada (`AUDITORIA_SISPOA.md` §3.6). |
| **`UndefinedTable` post-SWITCH por search_path incompleto** | Todos | Medio | Monitorear logs de errores 500 y `django.db.utils.ProgrammingError` en el período de observación (Fase 3, paso 4). |
| **CI/SQLite sin esquemas** | Todos | Bajo | `urls_test_sqlite.py` corre con search_path default; ejecutar la suite antes/después de cada grupo para detectar `db_table` rotos. |

## 9. Secuencia de ejecución resumida

| Fase | Acción | Salida |
|---|---|---|
| 0 | Backup `-Fc` + verificación + snapshot Git + inventarios | Baseline reproducible |
| 1 | `CREATE SCHEMA` × 9 | Esquemas objetivo vacíos |
| 2 | MIGRATE + VALIDATE por grupo (A → I) | 217 tablas ubicadas; conteos/FK/triggers/vistas OK |
| 3 | SWITCH (search_path o db_table + migraciones Django) | Backend leyendo de esquemas objetivo; vistas de compatibilidad |
| 4 | DEPRECATE `public` → `public_legacy` | Legacy aislado y solo lectura |
| 5 | REMOVE LEGACY (condiciones del §7) | `public_legacy` eliminado con respaldo verificado |

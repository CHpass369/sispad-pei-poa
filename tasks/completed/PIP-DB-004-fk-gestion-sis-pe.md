# TASK PIP-DB-004: FK gestión fiscal — SIS-PE (pad, indicadores, evaluacion)

## DOMINIO

`sis-pe`

## OBJECTIVE

Fase 2: convertir los campos de gestión de SIS-PE simple a FK sobre `GestionFiscal` con `ON DELETE PROTECT`. Sin data migration: `pad.*` con gestión 2027 válida; `indicadores.MetaProgramada` y `evaluacion.Evaluacion` vacías. Uniformar convención de nombre.

## SCOPE

- Apps: `pad` (PoliticaPAD, LineamientoEstrategico, ResultadoTerritorial, ProductoTerritorial, ArticulacionSIPEB, ProgramacionAnualPAD.anio), `indicadores` (MetaProgramada), `evaluacion` (Evaluacion.fiscal_year).
- Renombres de convención: `pad.ProgramacionAnualPAD.anio` → `gestion` (si aplica); `evaluacion.fiscal_year` → `gestion`.
- Migración por app: integer → FK `PROTECT`.

## OUT OF SCOPE

- `articulacion` y `planificacion` (complejas → PIP-DB-007).
- `pad.ProgramacionAnualPAD` si resulta ser programación plurianual (decidir con evidencia; ver §5 GESTION_FISCAL_AUDIT).

## INVARIANTS

- `GestionFiscal` canónica intacta.
- Contratos V1 (Sunset 2027-01-01) sincronizados en el renombre.

## DATABASE IMPACT

Migraciones Django por app. Posibles renombres de columna + data migration trivial si hay datos.

## API IMPACT

Serializers/servicios que consumen `fiscal_year`/`anio`: revisar `pad`, `indicadores`, `evaluacion` V1/V2.

## DEPENDENCIES

- `docs/architecture/GESTION_FISCAL_AUDIT.md` §5 (decisiones).

## ROLLBACK

FKR + reversa de renombres.

## FINAL REPORT

Cerrada 2026-08-16 — **SIS-PE simple con FK GestionFiscal PROTECT** (pad, indicadores, evaluacion).

**Tablas migradas (7 campos):** pad (PoliticaPAD, LineamientoEstrategico, ResultadoTerritorial, ProductoTerritorial, ArticulacionSIPEB — 1 fila cada una en 2027 válida; ProgramacionAnualPAD vacía), indicadores (MetaProgramada vacía), evaluacion (Evaluacion vacía).

**Renombres de convención aplicados:** `pad.ProgramacionAnualPAD.anio` → `gestion`; `evaluacion.Evaluacion.fiscal_year` → `gestion` (columnas renombradas; tabla vacía → sin data migration).

**Migraciones creadas (5):** pad 0005 (secuencia Add→RunPython→Remove→Rename→Alter con re-alineación de unique_together/ordering/index por paso — hallazgo: los Alter* con nombres de campo deben ir DESPUÉS del AddField y ANTES del RemoveField), pad 0006 + evaluacion 0005 (alineación generada por Django: indexes con nombres correctos), indicadores 0003, evaluacion 0004. `db_column='gestion'` conservada en FK; `makemigrations --check` limpio.

**Contratos:** serializers exponen `gestion` (uuid) + `gestion_anio` (año, ro); `?gestion__anio=<año>` como filtro V1/V2 de pad/evaluacion (django-filter dict; sin consumidores frontend de esos endpoints); validadores de pad/evaluacion normalizados a comparación por anio; kernel pad/migration_v2.py adaptado (`values_list('gestion__anio')`, filtros `gestion__anio`); MigracionSIMService (lineamientos) y reportes adaptados.

**Tests adaptados (7 archivos, ~90 sitios):** pad (comprehensive 40, models, serializers, views, migration — la data migration 0004 histórica no puede re-ejecutarse contra el esquema nuevo: test adaptado a comportamiento observable equivalente), evaluacion/test_api (27), test_migracion_pad_v2 (9), test_workflow_v2 (16), workflow/IndicadorCalculo, codificacion/test_migracion_sim.

**Suite:** **1282 passed** (baseline), ruff limpio, `makemigrations --check` sin drift.

**Lección de proceso registrada:** en Windows PowerShell, `Get-Content`/`Set-Content` corrompen UTF-8 en archivos con acentos (mojibake en asserts/strings) — usar `[System.IO.File]::ReadAllText/WriteAllText` con UTF-8 explícito o la herramienta edit; un script de replaces llegó a duplicar un helper y a auto-reemplazar su propia definición (recursión) — verificar siempre con pytest.

**Commit:** `b6afe52` (30 archivos, 738+/236-).

**Deuda detectada:** `pad/migration_v2.py` `_atributos_extra` y `importar_pad` con `PAD-{gestion}` siguen dependiendo de años (consistente); VersionCatalogoPlan.gestion (codificacion) sigue int → PIP-DB-003 pendiente.
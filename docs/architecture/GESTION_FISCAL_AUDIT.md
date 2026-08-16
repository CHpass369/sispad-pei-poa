# Auditoría de Gestión Fiscal (GESTION_FISCAL_AUDIT)

Auditoría read-only de todos los campos `gestion*` que guardan el año fiscal como entero suelto (sin FK), comparados contra la canónica `GestionFiscal` (`backend/apps/gestion/models.py:7`, tabla `gestion_gestionfiscal`). Fase 1 de la TASK [PIP-DB-001](../../tasks/active/PIP-DB-001-fk-gestion-fiscal.md) — 100% read-only, sin migraciones.

## 1. Canónica

`GestionFiscal` define `anio = PositiveIntegerField(unique=True)`. Año único por gestión; en esta base solo existen **2 gestiones reales: `[2026, 2027]`** (verificado con datos reales, §4). La canónica NO cambia en esta fase.

Patrón FK ya correcto (referencia, no aplica migración):

| App | Modelo | Campo | on_delete |
|---|---|---|---|
| budget | DirectiveCeiling | `gestion` OneToOneField → GestionFiscal | CASCADE |
| budget | RecursoTecho, DistribucionVersion, DistribucionTerritorial, CategoriaProgramatica, Importacion, Reforma, GastoObligatorio… | `gestion` FK → GestionFiscal | CASCADE |
| gestion | CicloFormulacion | `gestion` FK → GestionFiscal | CASCADE |

> **Deuda asociada**: budget/gestion ya usan FK correcta, pero con `on_delete=CASCADE`. La decisión de gobernanza (§6) es `ON DELETE PROTECT`; uniformar budget a PROTECT es deuda a documentar, no parte de esta fase.

## 2. Inventario completo por app (enteros sueltos sin FK)

Censo `Select-String "gestion"` sobre todos los `models*.py` de `backend/apps/*/` + verificación ORM (26 apps, 76 campos en tablas concretas, 24 apps con al menos un campo afectado).

Leyenda riesgo:
- **ALTO** — tabla con datos reales y/o años huérfanos que romperían la FK.
- **MEDIO** — tabla con datos reales, sin huérfanos (FK directa segura hoy).
- **BAJO** — tabla vacía (FK directa segura, solo schema).

### CORE

| App | Modelo (tabla) | Campo | Línea | Tipo | null/blank | Riesgo | Convención |
|---|---|---|---|---|---|---|---|
| acciones_correctivas | AccionCorrectiva | `gestion` | models.py:58 | PositiveIntegerField | — | BAJO (0 filas) | gestion |
| auditoria | EventoAuditoria | `gestion` | models.py:36 | PositiveIntegerField | null=True, blank=True | MEDIO (1 fila, 2027) | gestion |
| core | DemoDatasetManifest | `gestion` | models.py:56 | PositiveIntegerField | — | BAJO (0 filas) | gestion |
| core | VersionableModel (abstract) | `gestion` | models.py:46 | PositiveIntegerField | — | BAJO (abstracta) | gestion |
| documentos | DocumentoAdjunto | `gestion` | models.py:21 | PositiveIntegerField | — | BAJO (0 filas) | gestion |
| notificaciones | Notificacion | `gestion` | models.py:66 | PositiveIntegerField | — | BAJO (0 filas) | gestion |
| normativa | VersionNormativa | `gestion` | models.py:21 | PositiveIntegerField | — | ALTO (huérfanos 2015, 2021) | gestion |
| normativa | ReglaPresupuestariaLegal | `gestion_desde` / `gestion_hasta` | models.py:69/70 | PositiveIntegerField | hasta: null=True | BAJO (0 filas) | gestion_desde/hasta |
| organizacion | UnidadOrganizacional | `gestion` | models.py:37 | PositiveIntegerField | — | MEDIO (8 filas, 2027) | gestion |
| organizacion | DireccionAdministrativa | `gestion` | models.py:54 | PositiveIntegerField | — | MEDIO (5 filas, 2027) | gestion |
| organizacion | UnidadEjecutora | `gestion` | models.py:85 | PositiveIntegerField | — | MEDIO (11 filas, 2027) | gestion |
| organizacion | AsignacionUsuarioUnidad | `gestion` | models.py:112 | PositiveIntegerField | — | BAJO (0 filas) | gestion |
| reportes | ReporteGenerado | `gestion` | models.py:38 | PositiveIntegerField | — | BAJO (0 filas) | gestion |
| territorio | LocalizacionTerritorial | `gestion` | models.py:58 | PositiveIntegerField | — | BAJO (0 filas) | gestion |
| workflow | EnvioFormulacion | `gestion` | models.py:14 | PositiveIntegerField | — | BAJO (0 filas) | gestion |
| workflow | Observacion | `gestion` | models.py:111 | PositiveIntegerField | — | BAJO (0 filas) | gestion |
| workflow | Aprobacion | `gestion` | models.py:126 | PositiveIntegerField | — | BAJO (0 filas) | gestion |

### SHARED

| App | Modelo (tabla) | Campo | Línea | Tipo | null/blank | Riesgo | Convención |
|---|---|---|---|---|---|---|---|
| catalogos | VersionClasificador | `gestion` | models.py:74 | PositiveIntegerField | — | MEDIO (8 filas, 2026+2027) | gestion |
| catalogos | CatalogoBase (abstract) → 13 subclases (ClasificadorInstitucional, RubroRecurso, ObjetoGasto, FuenteFinanciamiento, OrganismoFinanciador, EntidadTransferencia, FinalidadFuncion, UnidadMedida, TipoOperacion, TipoProducto, TipoProyecto, TipoFinanciamiento, SectorEconomicoPresupuestario) | `gestion` | models.py:154 | PositiveIntegerField | — | MEDIO (varias con 2027) | gestion |
| catalogos | VersionCatalogo | `gestion` | models.py:440 | PositiveIntegerField | — | BAJO (0 filas) | gestion |
| codificacion | VersionCatalogoPlan | `gestion` | models.py:60 | PositiveIntegerField | — | **ALTO (huérfanos 2021, 2025)** | gestion |
| codificacion | SecuenciaCodigo | `gestion` | models.py:678 | PositiveIntegerField | — | BAJO (0 filas) | gestion |
| codificacion | HomologacionCodigo | `gestion` | models.py:755 | PositiveIntegerField | — | BAJO (0 filas) | gestion |
| codificacion | EjecucionMigracionSIM | `gestion` | models.py:841 | PositiveIntegerField | — | BAJO (0 filas) | gestion |

### SIS-PE

| App | Modelo (tabla) | Campo | Línea | Tipo | null/blank | Riesgo | Convención |
|---|---|---|---|---|---|---|---|
| pad | PoliticaPAD | `gestion` | models.py:26 | PositiveIntegerField | — | MEDIO (1 fila, 2027) | gestion |
| pad | LineamientoEstrategico | `gestion` | models.py:46 | PositiveIntegerField | — | MEDIO (1 fila, 2027) | gestion |
| pad | ResultadoTerritorial | `gestion` | models.py:100 | PositiveIntegerField | — | MEDIO (1 fila, 2027) | gestion |
| pad | ProductoTerritorial | `gestion` | models.py:191 | PositiveIntegerField | — | MEDIO (1 fila, 2027) | gestion |
| pad | ArticulacionSIPEB | `gestion` | models.py:338 | PositiveIntegerField | — | MEDIO (1 fila, 2027) | gestion |
| pad | ProgramacionAnualPAD | `anio` | models.py:217 | PositiveIntegerField | — | BAJO (0 filas) | **anio (no gestion)** |
| indicadores | MetaProgramada | `gestion` | models.py:51 | PositiveIntegerField | — | BAJO (0 filas) | gestion |
| evaluacion | Evaluacion | `fiscal_year` | models.py:45 | PositiveIntegerField | — | BAJO (0 filas) | **fiscal_year (no gestion)** |
| articulacion | LineamientoPAD | `gestion_desde` / `gestion_hasta` | models.py:104/105 | **IntegerField** | — | BAJO (0 filas) | gestion_desde/hasta |
| articulacion | AccionPOA | `gestion` | models.py:483 | **IntegerField** | — | MEDIO (1 fila, 2027) | gestion |
| articulacion | SeguimientoPresupuesto | `gestion` | models.py:796 | **IntegerField** | — | BAJO (0 filas) | gestion |
| articulacion | AsignacionObjetoGasto | `gestion` | models.py:902 | **IntegerField** | — | BAJO (0 filas) | gestion |
| articulacion | BorradorMatrizPAD | `gestion` | models.py:1039 | **IntegerField** default=2026 | — | MEDIO (4 filas, 2026) | gestion |
| planificacion | Plan | `gestion_inicio` / `gestion_fin` | models.py:23/24 | PositiveIntegerField | — | **ALTO (rango plurianual: inicio 2015/2021/2026, fin 2025/2030/2045/2050)** | gestion_inicio/fin |
| planificacion | NodoPlanificacion | `gestion` | models.py:74 | PositiveIntegerField | — | **ALTO (604 filas, huérfanos 2021 y 2025)** | gestion |
| planificacion | AccionMedianoPlazo | `gestion_inicio` / `gestion_fin` | models.py:115/116 | PositiveIntegerField | — | BAJO (0 filas) | gestion_inicio/fin |
| planificacion | AccionCortoPlazo | `gestion` | models.py:146 | PositiveIntegerField | — | BAJO (0 filas) | gestion |
| planificacion | ArticulacionPlanificacion | `gestion` | models.py:172 | PositiveIntegerField | — | **ALTO (61 filas, huérfano 2021)** | gestion |

### SIS-POA

| App | Modelo (tabla) | Campo | Línea | Tipo | null/blank | Riesgo | Convención |
|---|---|---|---|---|---|---|---|
| techos | TechoPresupuestario | `gestion` | models.py:15 | PositiveIntegerField | — | BAJO (0 filas) | gestion |
| presupuesto | ProgramaPresupuestario | `gestion` | models.py:24 | PositiveIntegerField | — | BAJO (0 filas) | gestion |
| presupuesto | ProyectoPresupuestario | `gestion` | models.py:47 | PositiveIntegerField | — | BAJO (0 filas) | gestion |
| presupuesto | ActividadPresupuestaria | `gestion` | models.py:66 | PositiveIntegerField | — | BAJO (0 filas) | gestion |
| presupuesto | AsignacionPresupuestariaUnidad | `gestion` | models.py:265 | PositiveIntegerField | — | BAJO (0 filas) | gestion |
| presupuesto | LineaPresupuestaria | `gestion` | models.py:405 | PositiveIntegerField | — | BAJO (0 filas) | gestion |
| recursos | EstimacionRecurso | `gestion` | models.py:10 | PositiveIntegerField | — | BAJO (0 filas) | gestion |
| recursos | EstimacionPlurianual | `anio` | models.py:37 | PositiveIntegerField | — | BAJO (0 filas) | **anio (no gestion)** |
| poau | POAU | `gestion` | models.py:25 | PositiveIntegerField | — | BAJO (0 filas) | gestion |
| poau | PoAInstitucional (V2) | `gestion` | models_v2.py:35 | PositiveIntegerField | — | **ALTO (2 filas, huérfano 2028)** | gestion |
| poau | ProgramacionActividad (V2) | `anio` | models_v2.py:222 | PositiveIntegerField | — | BAJO (0 filas) | **anio (no gestion)** |
| seguimiento | ReporteSeguimiento | `gestion` | models.py:18 | PositiveIntegerField | — | BAJO (0 filas) | gestion |
| modificaciones | SolicitudModificacion | `gestion_fiscal` | models.py:35 | PositiveIntegerField | — | BAJO (0 filas) | **gestion_fiscal** |

### SIS-PRO

| App | Modelo (tabla) | Campo | Línea | Tipo | null/blank | Riesgo | Convención |
|---|---|---|---|---|---|---|---|
| inversion | ProyectoInversion (V1) | `gestion_inicio` / `gestion_fin` | models.py:37/38 | PositiveIntegerField | fin: null=True | BAJO (0 filas) | gestion_inicio/fin |
| inversion | ProgramacionPlurianualProyecto (V1) | `anio` | models.py:53 | PositiveIntegerField | — | BAJO (0 filas) | **anio (no gestion)** |
| inversion | ProgramacionFisicaFinanciera (V1) | `gestion` | models.py:67 | PositiveIntegerField | — | BAJO (0 filas) | gestion |
| inversion | Proyecto (V2) | `gestion` | models_v2.py:123 | PositiveIntegerField | — | MEDIO (3 filas, 2027) | gestion |
| inversion | CostoProyecto (V2) | `anio` | models_v2.py:276 | PositiveIntegerField | — | **ALTO (2 filas, huérfano 2028)** | **anio (no gestion)** |

> `planificacion/models_v2.py:81 horizonte_anios` (PositiveIntegerField null=True) es un conteo de años del horizonte, NO un año de gestión: fuera del alcance. `accounts`, `presupuesto`/`budget` (FK), `gestion` (canónica + FK) sin campos sueltos.

## 3. Resumen del inventario

- **26 apps** revisadas; **24 apps** con al menos un campo `gestion*` entero sin FK.
- **76 campos en tablas concretas** (63 con nombre `gestion*`, 13 con nombre `anio` o `fiscal_year` que son el mismo concepto semántico de "año fiscal/periodo").
- Tipos: `PositiveIntegerField` (71), `IntegerField` (5, todos en articulacion).
- Convenciones inconsistentes: `gestion` (mayoría), `gestion_fiscal` (modificaciones), `gestion_inicio`/`gestion_fin` (planificacion, normativa, inversion), `anio` (pad, recursos, inversion, poau), `fiscal_year` (evaluacion).
- Campos **abstractos** que se propagan por herencia: `core.VersionableModel.gestion`, `catalogos.CatalogoBase.gestion` (13 subclases). Migrar CatalogoBase migra 13 tablas a la vez.

## 4. Estado de acceso a DB y análisis de huérfanos

**DB accesible** con la config local (`manage.py shell`). Conteos reales:

- `GestionFiscal.objects.count() = 2` → años `[2026, 2027]`.

### Huérfanos reales (años referenciados sin GestionFiscal)

| App.Modelo | Campo | Años huérfanos | Filas | Conclusión |
|---|---|---|---|---|
| codificacion.VersionCatalogoPlan | gestion | **2021, 2025** | 6 | dato huérfano → data migration requerida |
| inversion.CostoProyecto | anio | **2028** | 2 | dato huérfano → data migration requerida |
| normativa.VersionNormativa | gestion | **2015, 2021** | 5 | dato huérfano → data migration requerida |
| planificacion.Plan | gestion_inicio / gestion_fin | inicio **2015, 2021**; fin **2025, 2030, 2045, 2050** | 6 | rango plurianual de plan (PGDES/PDESA 2015-2025, 2021-2030, 2026-2050): NO son gestiones fiscales operativas → modelo de horizonte, no FK simple |
| planificacion.NodoPlanificacion | gestion | **2021, 2025** | 604 | dato huérfano → data migration requerida |
| planificacion.ArticulacionPlanificacion | gestion | **2021** | 61 | dato huérfano → data migration requerida |
| poau.PoAInstitucional | gestion | **2028** | 2 | dato huérfano → data migration requerida |

### Tablas vacías (0 filas) — FK directa segura sin data migration

acciones_correctivas, core (DemoDatasetManifest), documentos, notificaciones, normativa.ReglaPresupuestariaLegal, organizacion.AsignacionUsuarioUnidad, reportes, territorio, workflow (×3), catalogos.VersionCatalogo + ClasificadorInstitucional/ObjetoGasto/EntidadTransferencia/SectorEconomicoPresupuestario, codificacion (SecuenciaCodigo, HomologacionCodigo, EjecucionMigracionSIM), pad.ProgramacionAnualPAD, indicadores, evaluacion, articulacion (LineamientoPAD, SeguimientoPresupuesto, AsignacionObjetoGasto), planificacion (AccionMedianoPlazo, AccionCortoPlazo), techos, presupuesto (×5), recursos (×2), poau (POAU, ProgramacionActividad), seguimiento, modificaciones, inversion (V1: ProyectoInversion, ProgramacionPlurianualProyecto, ProgramacionFisicaFinanciera).

### Método para fase de ejecución (por app)

```python
# por cada modelo objetivo
origen = set(Modelo.objects.values_list('gestion', flat=True).distinct())
canonico = set(GestionFiscal.objects.values_list('anio', flat=True))
huerfanos = sorted(origen - canonico)
# si huerfanos: decidir crear GestionFiscal (solo si es gestión real operativa) o excluir/sanear
```

## 5. Plan de migración por app (fase 2+, tareas derivadas)

Orden de ejecución recomendado. Cada tarea ejecuta su propia data migration (si aplica) + campo FK `ON DELETE PROTECT` + migración Django de reversa. **Nunca renombrar `gestion_gestionfiscal`.**

| # | Tarea | Dominio | Apps | Data migration | Orden |
|---|---|---|---|---|---|
| 1 | PIP-DB-002 | CORE | organizacion, auditoria, notificaciones, documentos, acciones_correctivas, reportes, territorio, workflow, core | No (todas seguras; auditoria/organizacion con datos válidos 2027) | 1º |
| 2 | PIP-DB-003 | SHARED | catalogos, codificacion | **Sí** (codificacion.VersionCatalogoPlan 2021/2025) | 2º |
| 3 | PIP-DB-004 | SIS-PE | pad, indicadores, evaluacion | No (pad 2027 válido; evaluacion/indicadores vacías) | 3º |
| 4 | PIP-DB-005 | SIS-POA legacy | techos, presupuesto, recursos, seguimiento, modificaciones, poau | **Sí** (poau.PoAInstitucional 2028) | 4º |
| 5 | PIP-DB-006 | SIS-PRO | inversion | **Sí** (inversion.CostoProyecto 2028) | 5º |
| 6 | PIP-DB-007 | SIS-PE / CORE | articulacion, planificacion, normativa | **Sí** (articulacion.BorradorMatrizPAD/AccionPOA validos; planificacion.NodoPlanificacion/ArticulacionPlanificacion huérfanos 2021/2025; normativa.VersionNormativa 2015/2021) | 6º (la más compleja) |

Decisiones dentro del plan:

1. **Articulacion** (IntegerField): renombrar a `PositiveIntegerField` + FK. Aprovechar para alinear tipo.
2. **Modificaciones.gestion_fiscal**: renombrar campo a `gestion` (convención canónica) + FK.
3. **Plan.gestion_inicio/gestion_fin, normativa.ReglaPresupuestariaLegal.gestion_desde/gestion_hasta, articulacion.LineamientoPAD.gestion_desde/gestion_hasta**: son **rangos plurianuales** (2015-2050) que exceden gestiones fiscales reales. NO son candidatas a FK simple directa. Requieren diseño propio (tarea PIP-DB-007): opción A — FK null con `GestionFiscal` solo si el año existe (el resto NULL documentando horizonte); opción B — modelo de horizonte/periodo separado. **Recomendación: mantener `anio` libre para horizonte plurianual, NO forzar FK**; documentar como excepción gobernada (ver §6).
4. **Campos `anio`** (pad.ProgramacionAnualPAD, recursos.EstimacionPlurianual, inversion.ProgramacionPlurianualProyecto/CostoProyecto, poau.ProgramacionActividad): son años de programación plurianual/meta, NO gestión fiscal única. Evaluar caso por caso; CostoProyecto.anio y PoAInstitucional.gestion (2028) son los que hoy tienen datos huérfanos.
5. **evaluacion.fiscal_year**: renombrar a `gestion` para uniformar convención + FK.
6. **core.VersionableModel** (abstract) y **catalogos.CatalogoBase** (abstract): migrar la base migra toda la jerarquía; impactar en una sola tarea (SHARED). `VersionableModel` al ser abstracto y de CORE, se toca en PIP-DB-002.

## 6. Decisión de dominio: `ON DELETE PROTECT`

**Decisión**: toda FK nueva desde apps consumidoras hacia `GestionFiscal` se crea con `on_delete=models.PROTECT`.

**Justificación de integridad**:

1. La gestión fiscal es la dimensión temporal canónica de toda la cadena de articulación `PEI → POA → POAU → presupuesto → SIS-PRO`. Borrar una gestión con datos asociados destruye silenciosamente la trazabilidad histórica (auditoría, seguimiento, reformas).
2. `CASCADE` (usado hoy por budget/gestion) propaga borrado sin aviso y puede borrar subárboles enteros (techos → versiones → distribuciones). PROTECT fuerza el ciclo de vida explícito: **cerrar/archivar la gestión** (estados `cerrada`/`archivada` ya existen en `GestionFiscal.Estado`) antes de cualquier purga.
3. El borrado de gestión es una operación de gobernanza, no una operación de datos: debe requerir intervención manual deliberada (proceso), no ocurrir como efecto lateral de un DELETE.
4. Consistencia con el ciclo presupuestario normativo boliviano: las gestiones cerradas son evidencia fiscal; no se eliminan.
5. Coherente con la regla de ownership (DATA_OWNERSHIP §1 O-1): `gestion` es OWNER; los consumidores leen vía FK protegida, nunca borran la dimensión ajena.

**Contra-propuesta descartada**: `SET_NULL` (perdería el vínculo histórico y viola la unicidad del dato), `CASCADE` (riesgo de borrado en cascada, ver arriba), `SET_DEFAULT` (requiere una gestión sentinela que no existe).

**Excepción gobernada**: los **rangos plurianuales** (Plan, ReglaPresupuestariaLegal, LineamientoPAD) y los **años de programación/meta** (`anio`) NO se someten a FK: son horizontes de planificación que exceden las gestiones fiscales registradas. Si en el futuro se registran esas gestiones, se podrá FK-izar con PROTECT. Esta excepción debe quedar explícita en cada tarea para evitar data migrations que inventen gestiones falsas (crear `GestionFiscal(anio=2015)` para satisfacer una FK sería corromper la canónica con gestiones que nunca fueron operativas).

## 7. Riesgos confirmados

- **R1 (ALTO)**: data migration que inventa gestiones falsas (2015, 2021, 2025, 2028, 2030…) solo para satisfacer la FK → corrompe la canónica. Mitigación: clasificar por semántica (gestión operativa vs horizonte plurianual) ANTES de migrar.
- **R2 (ALTO)**: huérfanos reales confirmados en 7 tablas (2021/2025/2028) con 604+ filas en NodoPlanificacion.
- **R3 (MEDIO)**: convención de tipo inconsistente — articulacion usa `IntegerField` (admite negativos) y el resto `PositiveIntegerField`.
- **R4 (MEDIO)**: 5 convenciones de nombre distintas (`gestion`, `gestion_fiscal`, `gestion_inicio/fin`, `anio`, `fiscal_year`); renombrar rompe contratos V1 (Sunset 2027-01-01) — sincronizar con API.
- **R5 (BAJO)**: `core.VersionableModel` y `catalogos.CatalogoBase` son abstractos: migrar la base es migrar 14 tablas; coordinar.
- **R6**: la canónica no cambia; budget/gestion ya usan FK con CASCADE — decisión pendiente de uniformar a PROTECT (deuda, no bloqueante).

## 8. Deuda detectada

- **D1**: budget/gestion usan `CASCADE` donde la gobernanza pide `PROTECT` — tarea propia fuera de esta fase.
- **D2**: `articulacion` usa `IntegerField` (debe ser `PositiveIntegerField`).
- **D3**: 5 convenciones de nombre de campo; unificar a `gestion` (excepto rangos plurianuales).
- **D4**: `auditoria.EventoAuditoria.gestion` es null=True (eventos sin gestión): con FK debe seguir siendo null=True.
- **D5**: campos `anio` que son programación plurianual no documentados como excepción al patrón FK (hoy no hay regla escrita).

## 9. Referencias

- `docs/architecture/DATA_OWNERSHIP.md` — conflicto O-1: "GestionFiscal suelta… Introducir FK vía contrato en fase 3".
- `docs/architecture/DOMAIN_BOUNDARIES.md` — reglas de ownership por dominio (CORE/SIS-PE/SIS-POA/SIS-PRO/SHARED).
- `tasks/backlog/PIP-DB-002..007` — tareas derivadas con plan por dominio.
- `backend/apps/gestion/models.py` — canónica `GestionFiscal`.

Documento de auditoría — creado en ETAPA A (2026-08-16), read-only, sin impacto de esquema.
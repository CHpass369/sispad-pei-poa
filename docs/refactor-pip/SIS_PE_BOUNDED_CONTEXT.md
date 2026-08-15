# SIS-PE — Frontera del bounded context estratégico

- **Fecha:** 2026-08-15
- **Fase:** 3 del refactor SISPOA→PIP (aislar PAD/PEI)
- **Relacionado con:** ADR-002, ADR-004, ADR-008; `DOMAIN_MAP.md` §1, §2; `AUDITORIA_SISPOA.md`

## 1. Propósito

Definir QUÉ pertenece al contexto **SIS-PE** (estrategia: PGDESA/PDESA/PAD/PEI),
QUÉ NO, qué dependencias entre apps son legítimas, y el mapa de implementación
del **Wizard PEI** que FASE 3 prepara. Es la frontera de aislamiento de la
FASE 3: el Wizard PAD no se rompe, el código acoplado no se mueve.

## 2. Frontera del contexto

### 2.1 Qué pertenece a SIS-PE

| Pieza | Ubicación actual | Rol en SIS-PE |
|---|---|---|
| Planificación V1 estratégica (`Plan`, `PlanVersion`, `NodoPlanificacion`, `AccionMedianoPlazo`, `Sector`) | `apps.planificacion` | Contenedor e instrumento legacy |
| Planificación V2 (kernel) (`InstrumentoPlanificacion`, `VersionInstrumento` inmutable con checksum, `NodoEstrategico`, `VinculoEstrategico`, `TipoInstrumento`, `VersionMetodologia`, `TipoNodoEstrategico`, `TipoVinculoEstrategico`) | `apps.planificacion/models_v2.py` | **Kernel estratégico SIS-PE** (fuente de verdad para SIS-POA, ADR-008) |
| PAD completo (legacy) (`SectorPAD`, `PoliticaPAD`, `LineamientoEstrategico`, `ResultadoTerritorial`, `ProductoTerritorial`, `ProgramacionAnualPAD`, `ArticulacionLog`, `ArticulacionSIPEB`) | `apps.pad` | Instrumento estratégico PAD (cutover V2 pendiente) |
| Catálogo estratégico (`VersionCatalogoPlan`, `EjePGDESA`, `ComponentePDESA`, `SectorEconomico`, `ResultadoSectorial`, `LineamientoPAD`) | `apps.codificacion` | Catálogos PGDESA/PDESA/PAD (compartido con PIP CATÁLOGOS, decisión de `DOMAIN_MAP.md` §1) |
| Articulación estratégica (`ResultadoPAD`, `ProductoPAD`, `ResultadoPEI`, `ProductoPEI`, `ArticulacionPADPEI`, `IndicadorCadena`) | `apps.articulacion` | Cadena estratégica PAD→PEI (SPLIT futuro: estratégico→SIS-PE, operativo→SIS-POA, cadena→PIP INTEGRACIÓN) |
| Evaluación (`Evaluacion`, `CriterioEvaluacion`, `ResultadoEvaluacion`, `LeccionAprendida`, `Recomendacion`) | `apps.evaluacion` | Compartido SIS-PE/SIS-PRO (decisión) |

### 2.2 Qué NO pertenece a SIS-PE

| Pieza | Destino real |
|---|---|
| `AccionPOA`, `OperacionPOAU`, `ActividadPOAU`, `TareaPOAU`, `SeguimientoPresupuesto`, `AsignacionObjetoGasto` y el resto de contenido operativo de `apps.articulacion` | **SIS-POA** (ADR-002; jerarquía canónica V2 en `poau`) |
| `PoA`, `Accion`, `Operacion`, `Actividad`, `Tarea`, `Programacion` | **SIS-POA** (V2 canónico) |
| `budget.*`, `gestion.*`, `techos.*`, `presupuesto.*`, `seguimiento.*`, `modificaciones.*` | **SIS-POA** (ADR-002) |
| `inversion.*` | **SIS-PRO** |
| `CodigoSegmentadoModel` (codificacion/models.py) y `CodificadorService` (16 segmentos) | **Infraestructura compartida PIP** — NO se mueve, es el pegamento de la cadena completa |

## 3. Dependencias permitidas y prohibidas

Verificadas en el código (FASE 3):

### 3.1 Permitidas (existentes, se conservan)

| Dependencia | Evidencia | Nota |
|---|---|---|
| `articulacion` → `codificacion` | `CodigoSegmentadoModel` (codificacion/models.py:408) es base de los 8 modelos codificables | Base de datos compartida: no romper |
| `codificacion` → `planificacion` | FK `VersionCatalogoPlan.plan` → `planificacion.Plan` (codificacion/models.py:54) | Acoplada a `Plan` V1; NO mover la FK |
| `planificacion` → `articulacion` | import lazy en `NodoArbolSerializer._pad_links` (planificacion/serializers.py:117) | Lazy y acotado; conservar |
| `pad` → `planificacion` | `pad/views.py:cadena_completa` usa `NodoPlanificacion`/`AccionCortoPlazo` | Endpoint de la cadena PAD→POA; NO mover |
| `pad` → `planificacion.models_v2` | `pad/migration_v2.py` (kernel V2 + `LegacyMigrationMap`) | NO mover; `codificacion/migration_v2.py` idem |
| `codificacion` → `planificacion.models_v2` | `codificacion/migration_v2.py` | NO mover (usa `LegacyMigrationMap`) |

### 3.2 Prohibidas (objetivo, fase 5+)

| Dependencia | Motivo |
|---|---|
| SIS-POA (poau/budget) → tablas de borrador del kernel | SIS-POA lee SOLO versiones aprobadas e inmutables (`VersionInstrumento.inmutable` + checksum, ADR-008) |
| `articulacion` operativo → `pad` legacy | La cadena operativa se resuelve por IDs/versiones del kernel V2, nunca por modelos legacy |
| Nuevos imports desde SIS-PE hacia `articulacion` operativo (`AccionPOA`…) | Perfora la frontera; el SPLIT de `articulacion` (estratégico/operativo/cadena) es la fase 5 |

## 4. Mapa de implementación del Wizard PEI

### 4.1 Qué existe (FASE 3, listo)

| Pieza | Estado |
|---|---|
| Kernel V2 (`apps/planificacion/models_v2.py`) | Existe y estable: instrumentos, versiones inmutables (checksum SHA-256), nodos, vínculos, tipos parametrizables por metodología |
| API `/api/v2/sis-pe/` (instrumentos, versiones, nodos, vinculos, metodologias) | Existe; capacidades `sis_pe.*` |
| BD sembrada | PAD-2027, PEI-2027, PGDESA-2027 aprobados; v1 inmutables; nodos sembrados (MET-PAD: POLITICA/LINEAMIENTO/RESULTADO/PRODUCTO; OFICIAL-PGDESA: EJE/COMP/SECTOR/RS; MET-PEI-DEMO: OE) |
| Command `importar_pei` (NUEVO, esta fase) | `backend/apps/core/management/commands/importar_pei.py`: crea/actualiza `MET-PEI-OFICIAL` (semver 1.0.0, vigente), tipos de nodo **OE** (Objetivo Estratégico, orden 1) / **RI** (Resultado Intermedio, orden 2) / **PI** (Producto, orden 3) — coherentes con `NIVEL_ARTICULACION_CHOICES` (`resultado_pei`/`producto_pei`) — y el instrumento `PEI-{gestion}` con versión v1 en **BORRADOR** (nunca aprobada). Si PEI-2027 ya existe (aprobado por `cargar_demo_v2`), no lo toca: solo reporta. |
| Metodología parametrizable | `VersionMetodologia.esquema_validacion` permite definir reglas por metodología sin tocar el kernel |

### 4.2 Qué falta (fase futura)

| Pieza | Nota |
|---|---|
| UI del wizard por pasos | Futura `frontend/sispoa/src/app/features/sis-pe/` (análoga a `features/pad/articulador.component.ts` del Wizard PAD) |
| Servicios frontend sobre `/api/v2/sis-pe/` | Endpoints ya existen |
| Flujo de aprobación del PEI | Motor V2 de `workflow` (flujo_instancia) — fuera del alcance FASE 3 |

## 5. Compatibilidad Wizard PAD (FASE 3)

Verificación ejecutada el 2026-08-15:

- **Backend** (`pytest apps/planificacion/ apps/pad/ apps/codificacion/ tests/test_importar_pei.py --ds=config.settings`): **310 passed** (dominio estratégico + command nuevo). El único fallo inicial fue `codificacion/tests/test_app.py::test_app_config`, que aseveraba el `verbose_name` anterior de la app; se actualizó la aserción a `'PIP Catálogos - Codificación oficial'` (es el cambio de identidad de FASE 3, no una regresión).
- **Frontend**: no existen specs en `src/app/features/pad/` (solo `pad.module.ts` y `articulador.component.ts`), por lo que se ejecutó `npx ng build --configuration development`: **OK** (7,5 s, hash `f5c768178e7ee0cc`, sin errores).
- **Identidad**: las tres apps estratégicas ahora exponen `verbose_name` SIS-PE/PIP (registradas sus AppConfig en `config/settings.py` y `config/settings_test_sqlite.py`): `planificacion` = "SIS-PE - Planificación Estratégica", `pad` = "SIS-PE - PAD (Plan Autonómico de Desarrollo)", `codificacion` = "PIP Catálogos - Codificación oficial". `manage.py check`: sin issues.

**Conclusión**: el Wizard PAD permanece íntegro (backend CRUD + frontend por pasos sin cambios); la FASE 3 solo aísla identidad y agrega infraestructura (`importar_pei`) sin tocar la lógica del wizard.

# FASE 1 — MAPA DE DOMINIOS: situación actual → destino PIP

> Mapa dominio a dominio del estado actual hacia la arquitectura objetivo PIP:
> PIP CORE / PIP CATÁLOGOS / SIS-PE / SIS-POA / SIS-PRO / PIP INTEGRACIÓN / PIP AUDITORÍA / PIP GEO / REPORTES.
> Entidades verificadas contra los modelos reales de `backend/apps/*`. Los destinos siguen la regla semántica del prompt maestro (nunca replace global `sispoa → pip`).

## 1. Tabla dominio → destino

| Dominio / Entidades | App actual | Dominio real | Destino PIP | Estado |
|---|---|---|---|---|
| Usuarios, roles, permisos (`Usuario`, `Rol`, `Capacidad`, `AlcanceOrganizacional`) | accounts | IAM transversal | **PIP CORE** | V2 (`me/` + capacidades; tablas `cuentas_*`) |
| Unidades organizacionales (`UnidadOrganizacional`, `UnidadEjecutora`, `DireccionAdministrativa`, `TipoUnidad`, `AsignacionUsuarioUnidad`) | organizacion | Estructura institucional | **PIP CORE** | Legacy (sin V2 propio) |
| Núcleo (`ManifestoDatasetDemo`, `MapaMigracionesLegacy`, admin, dashboard, vista raíz) | core | Infraestructura de plataforma | **PIP CORE** | Legacy (identidad SISPOA pendiente de rename) |
| Motor de workflow (`WorkflowDefinition`, `WorkflowStepDefinition`, `WorkflowTransition`, `WorkflowInstance`, `WorkflowTask`, `WorkflowObservacion`, `WorkflowAprobacion`, `Delegacion` + legacy `EnvioFormulacion`, `Revision`, `Observacion`, `Aprobacion`) | workflow | Motor transversal (V2) + flujos POA legacy | **PIP CORE** (motor) | Mixto: V2 (`platform/workflow-*`) + legacy POA |
| Notificaciones (`TipoNotificacion`, `Notificacion`, `PreferenciaNotificacion`) | notificaciones | Transversal | **PIP CORE** | Legacy |
| Documentos (`DocumentoAdjunto`) | documentos | Repositorio documental (MinIO) | **PIP CORE** | Legacy |
| Acciones correctivas (`AccionCorrectiva`, `CompromisoAccionCorrectiva`) | acciones_correctivas | Mejora continua | **PIP CORE** | Legacy |
| Auditoría (`EventoAuditoria`) | auditoria | Trazabilidad transversal | **PIP AUDITORÍA** | Mixto (tabla + endpoint budget audit `sis_poa.budget.audit_read`) |
| Catálogos (`VersionClasificador`, `ClasificadorInstitucional`, `RubroRecurso`, `ObjetoGasto`, `FuenteFinanciamiento`, `OrganismoFinanciador`, `UbicacionGeograficaPresupuestaria`, `EntidadTransferencia`, `FinalidadFuncion`, `UnidadMedida`, `TipoOperacion`, `TipoProducto`, `TipoProyecto`, `TipoFinanciamiento`, `VersionCatalogo`) | catalogos | Catálogos normativos versionados | **PIP CATÁLOGOS** | V2 parcial (versionado T4 operativo; sin namespace platform/catalogos) |
| Normativa (`VersionNormativa`, `ReglaPresupuestariaLegal`) | normativa | Marco legal | **PIP CATÁLOGOS** | Legacy |
| Codificación (`VersionCatalogoplan`, `EjePGDESA`, `ComponentePDESA`, `SectorEconomico`, `ResultadoSectorial`, `EntidadTerritorialCGEO`, `EntidadCodificadora`, `LineamientoPAD`, `SecuenciaCodigo`, `HomologacionCodigo`) | codificacion | Codificación PGDESA/PDESA | **PIP CATÁLOGOS / SIS-PE** (decisión) | Legacy (`migration_v2.py` migra a planificacion) |
| Planificación estratégica (`Plan`, `Sector`, `NodoPlanificacion`, `AccionMedianoPlazo`, `InstrumentoPlanificacion`, `VersionInstrumento`, `TipoInstrumento`, `VersionMetodologia`, `TipoNodoEstrategico`, `NodoEstrategico`, `TipoVinculoEstrategico`, `VinculoEstrategico`, `ArticulacionPlanificacion`, `PlanVersion`) | planificacion | Estrategia (PDESA/PAD/PEI) | **SIS-PE** | V2 (`sis-pe/*`) |
| PAD (`SectorPAD`, `PoliticaPAD`, `LineamientoEstrategico`, `ResultadoTerritorial`, `ProductoTerritorial`, `ProgramacionAnualPAD`, `ArticulacionLog`, `ArticulacionSIPEB`) | pad | Instrumento estratégico | **SIS-PE** | Legacy (cutover V2 pendiente según `cutover.config.ts`) |
| Articulación estratégica (`AcuerdoInternacional`, `Normativa`, `LineamientoPAD`, `ResultadoPAD`, `ProductoPAD`, `ResultadoPEI`, `ProductoPEI`, `ArticulacionPADPEI`, `IndicadorCadena`, `CodigoNivel`, `ActividadNormativa`, `TareaNormativa`) | articulacion | Cadena PAD-PEI | **PIP INTEGRACIÓN / SIS-PE** | Legacy (SPLIT: estratégico → SIS-PE, POA → SIS-POA) |
| Acciones y jerarquía POA legacy (`AccionPOA`, `OperacionPOAU`, `ActividadPOAU`, `TareaPOAU`, `SeguimientoPresupuesto`, `AsignacionObjetoGasto`) | articulacion | Operativo anual | **SIS-POA** | Legacy (MOVE/MERGE con jerarquía canónica de poau; WP-14) |
| POA / POAU (V2: `PoA`, `Accion`, `Operacion`, `Actividad`, `Tarea`, `Programacion`; legacy: `POAU`, `POAUActividad`, `POAInstitucional`, `AccionCortoPlazo`, `EjecucionFisica`, `EjecucionFinanciera`) | poau | Operativo anual | **SIS-POA** | V2 (jerarquía canónica WP-10) + legacy pendiente de cutover |
| Gestión fiscal (`GestionFiscal`, `CicloFormulacion`, `EtapaFormulacion`) | gestion | Ciclo presupuestario | **SIS-POA** (gestion_fiscal) | Legacy; V2 usa `budget.FiscalYear` (MERGE pendiente) |
| Presupuesto operativo V2 (`FiscalYear`, `DirectiveCeiling`, `RecursoTecho`, `GastoObligatorio`, `Documento`, `DistribucionVersion`, `Apertura`, `AperturaFuente`, `Reserva`, `CategoriaProgramatica`, `Importacion`, `ImportacionDetalle`, `ImportacionError`, `DistribucionTerritorial`, `AsignacionTerritorial`, `AsignacionObjetoGasto`, `Reforma`, `ReformaMovimiento`) | budget | Ciclo presupuestario SIS-POA | **SIS-POA** (NO crear SIS-PRESUPUESTO; ADR-005 / plan maestro §13: `recursos + techos + presupuesto` permanecen separados técnicamente bajo un dominio funcional SIS-POA) | V2 (`sis-poa/budget/*`) |
| Presupuesto legacy (`ProgramaPresupuestario`, `ProyectoPresupuestario`, `ActividadPresupuestaria`, `CategoriaProgramatica`, `AsignacionPresupuestariaUnidad`, `LineaPresupuestaria`) | presupuesto | Presupuesto legacy | **SIS-POA** | DEPRECATE (reemplazado por budget V2) |
| Techos legacy (`TechoPresupuestario`, `DistribucionTecho`, `MovimientoTecho`) | techos | Techos legacy | **SIS-POA** | DEPRECATE (TechoDirectivo V2 en budget; `TechoViewSetV2` ya sirve V2) |
| Recursos (`EstimacionRecurso`, `EstimacionPlurianual`) | recursos | Estimación de recursos | **SIS-POA** | Legacy (conservar/refinar, plan maestro) |
| Proyectos y preinversión (`Proyecto`, `ProyectoInversion`, `ProyectoPreinversion`, `ProgramacionPlurianualProyecto`, `ProgramacionFisicaFinanciera`, `CondicionPrevia`, `CondicionITCP`, `DocumentoTecnico`, `CostoProyecto`, `VinculoProyectoActividad`, `ProyectoTerritorio`, `ComponenteProyecto`, `GrupoBeneficiario`, `AlternativaProyecto`, `SolicitudReformulacion`, `ITCP`, `TDR` + actividades/productos/personal/items, `EDTP` + secciones/estudios/items-costo/financiamiento/cronograma/plan-OM/indicadores, `RevisionPreinversion`, `ObservacionPreinversion`, `AprobacionPreinversion`, `ReferenciaExterna`, `EventoOutbox`, `MensajeEntrante`) | inversion | Ciclo del proyecto | **SIS-PRO** | V2 (`sis-pro/*` completo) + outbox de integración a revisar |
| Indicadores (`Indicador`, `MetaProgramada`, `MedioVerificacion`, `Supuesto` + legacy `Operacion`, `Tarea`, `Producto`) | indicadores | Indicadores estratégicos y operativos | **SIS-PE / SIS-POA** (compartido — decisión) | Legacy; la jerarquía operativa duplicada en poau V2 debe retirarse (WP-14) |
| Evaluación (`Evaluacion`, `CriterioEvaluacion`, `ResultadoEvaluacion`, `LeccionAprendida`, `Recomendacion`) | evaluacion | Evaluación de PEI y proyectos | **SIS-PE / SIS-PRO** (decisión; hoy montado en namespace `sis-pe`) | V2 (`sis-pe/evaluaciones`) |
| Modificaciones (`SolicitudModificacion`, `CambioModificacion`, `ImpactoModificacion`) | modificaciones | Reformulaciones del POA | **SIS-POA** | Legacy (budget `Reforma` V2 cubre parte) |
| Seguimiento (`ReporteSeguimiento`, `EntradaSeguimiento`, `Alerta`, `UmbralConfiguracion`) | seguimiento | Seguimiento operativo y de proyectos | **SIS-POA / SIS-PRO** | Legacy |
| Territorio (`Distrito`, `UnidadTerritorial`, `LocalizacionTerritorial`) | territorio | Base geográfica | **PIP GEO** | Legacy (GeoServer + OpenLayers; sin V2) |
| Reportes (`ReporteGenerado` + tarea Celery `exportar_poa_completo_async`) | reportes | Generación de reportes | **REPORTES** | Mixto |

## 2. Flujo maestro PGDESA → PDESA → PAD → PEI → POA → POAU → Proyecto

```
PGDESA (codificacion: EjePGDESA, ComponentePDESA)
  └─ PDESA (codificacion: SectorEconomico, ResultadoSectorial, EntidadTerritorialCGEO)
       └─ PAD (pad: SectorPAD → PoliticaPAD → LineamientoEstrategico → ResultadoTerritorial → ProductoTerritorial → ProgramacionAnualPAD)
            │       (planificacion: Plan / PlanVersion como contenedor)
            └─ PEI (planificacion: InstrumentoPlanificacion + VersionInstrumento; NodoEstrategico / VinculoEstrategico)
                 │   (articulacion: ResultadoPEI, ProductoPEI, ArticulacionPADPEI, IndicadorCadena)
                 └─ POA (poau V2: PoA → Accion; legacy articulacion.AccionPOA, planificacion.AccionCortoPlazo)
                      └─ POAU (poau V2: Operacion → Actividad → Tarea + Programacion; legacy POAUActividad)
                           └─ Proyecto (inversion: Proyecto + VinculoProyectoActividad hacia SIS-POA)
```

Encadenamiento por IDs/versiones: las versiones aprobadas del kernel estratégico (`VersionInstrumento`) son inmutables (checksum SHA-256) y el SIS-POA lee desde ellas; SIS-PRO vincula proyectos a actividades del POA (`VinculoProyectoActividad`, `models_v2.py:290`).

## 3. Flujo SIS-POA (ciclo presupuestario completo, fases 1-12)

```
1. Habilitar gestión fiscal   budget.FiscalYear enable  → /api/v2/sis-poa/budget/fiscal-years/{id}/enable/   (legacy: gestion.GestionFiscal)
2. Techo directivo            budget.DirectiveCeiling (submit/observe/approve/freeze)                        (legacy: techos.* DEPRECATE)
3. Distribución               budget.DistribucionVersion + DistribucionTerritorial / AsignacionTerritorial
4. Asignación                 budget.Apertura + AperturaFuente (categoría programática + objeto de gasto)
5. POA                        poau V2: PoA / Accion → /api/v2/sis-poa/poas|acciones
6. POAU                       poau V2: Operacion / Actividad / Tarea
7. Programación               /api/v2/sis-poa/poas/{id}/programaciones/ (físico-financiera) + validar_techo
8. Consolidación              workflow.consolidacion (consolidación institucional, exportable)
9. Aprobación                 workflow V2 (flujo_instancia / flujo_aprobacion_motor) + budget approve/freeze
10. Seguimiento               seguimiento: ReporteSeguimiento / EntradaSeguimiento / Alerta / UmbralConfiguracion
11. Modificaciones            modificaciones (SolicitudModificacion) + budget.Reforma (reform/approve/apply)
12. Importación SIGEP/planillas  budget.Importacion (perfiles SISPOA_GASTOS_HISTORICO/ACTUAL — valores de datos, KEEP)
```

## 4. Notas de decisión (para las fases 2-8)

- **Articulación es la única app que cruza tres destinos**: estratégico (SIS-PE), operativo (SIS-POA) y cadena (PIP INTEGRACIÓN). Es el SPLIT más delicado del refactor.
- **Indicadores y evaluación** son compartidos SIS-PE/SIS-POA (e SIS-PRO en evaluación): definir el contrato de compartición (IDs + versiones) antes de mover tablas.
- **`presupuesto` + `techos` + `recursos` (legacy) → SIS-POA**: se deprecan a favor de `budget` V2; no crear un SIS-PRESUPUESTO separado (ADR-005 / plan maestro §13).
- **`gestion.GestionFiscal` vs `budget.FiscalYear`**: ambos modelan la gestión; el V2 ya manda (habilitación/cierre). MERGE pendiente.
- **`inversion` (SIS-PRO)** contiene los artefactos de integración (`EventoOutbox`, `MensajeEntrante`, `ReferenciaExterna`, `SolicitudReformulacion` con `sistema_origen='SISPOA'`) que deberían vivir en PIP INTEGRACIÓN.

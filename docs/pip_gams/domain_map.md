# Domain Map — conceptos legacy → V2 (PIP-GAMS)

**WP-01.** Mapa de equivalencias entre los 68 modelos actuales y el destino
V2, anclado en el inventario real del código. La migración de datos sigue la
estrategia expand→backfill→reconciliar→cortar→retirar (ver ADR-004) usando
`LegacyMigrationMap` (WP-05).

**Regla:** ningún modelo legacy se renombra ni elimina en esta fase; las
equivalencias definen destino conceptual, no cambio físico.

## 1. Núcleo transversal (Plataforma)

| Modelo legacy | App | Destino V2 | Acción |
|---|---|---|---|
| `Usuario`, `Rol` | accounts | IAM (usuario vinculado a OIDC, rol, capacidad, alcance) | Fortalecer (WP-03) |
| `GestionFiscal`, `CicloFormulacion`, `EtapaFormulacion` | gestion | Periodos/ciclos reutilizables | Convertir (WP-02 núcleo) |
| `TipoUnidad`, `UnidadOrganizacional`, `DireccionAdministrativa`, `UnidadEjecutora`, `AsignacionUsuarioUnidad` | organizacion | Organización GAMS + alcances organizacionales | Conservar |
| `VersionClasificador` y catálogos versionados | catalogos | Catálogos plataforma | Conservar |
| `VersionNormativa`, `ReglaPresupuestariaLegal` | normativa | Normativa plataforma | Conservar |
| `Distrito`, `UnidadTerritorial`, `LocalizacionTerritorial` | territorio | Territorio PostGIS transversal | Conservar y ampliar |
| `EnvioFormulacion`, `Revision`, `Observacion`, `Aprobacion` | workflow | `WorkflowDefinition/Step/Transition/Instance/Task` configurables | Refactor |
| `DocumentoAdjunto` | documentos | Documentos plataforma (S3/MinIO) | Conservar |
| `Notificacion`, `TipoNotificacion`, `PreferenciaNotificacion` | notificaciones | Notificaciones | Conservar |
| `EventoAuditoria` | auditoria | Auditoría append-only | Conservar |
| `ReporteGenerado` | reportes | Reportes por plantilla/SIS | Conservar |
| `DemoDatasetManifest` | core | Datos de demostración (temporal) | Conservar |

## 2. SIS-PE — kernel estratégico V2

| Modelo legacy | App | Destino V2 | Acción |
|---|---|---|---|
| `Plan` | planificacion | `InstrumentoPlanificacion` | Migrar (WP-04/07) |
| `PlanVersion` | planificacion | `VersionInstrumento` | Migrar |
| `NodoPlanificacion` | planificacion | `NodoEstrategico` | Migrar |
| `ArticulacionPlanificacion` | planificacion | `VinculoEstrategico` | Migrar |
| `AccionMedianoPlazo` | planificacion | Nodo/tipo de acción PEI | Migrar |
| `AccionCortoPlazo` | planificacion | SIS-POA `AccionPOA` | Mover a SIS-POA |
| `Sector` | planificacion | Catálogo/nodo según metodología | Evaluar |
| `SectorPAD`, `PoliticaPAD` | pad | Nodos PAD parametrizables | Migrar (WP-07) |
| `LineamientoEstrategico`, `ResultadoTerritorial`, `ProductoTerritorial` | pad | Nodos PAD (lineamiento/resultado/producto) | Migrar |
| `ProgramacionAnualPAD` | pad | Programación física PAD normalizada | Migrar |
| `ArticulacionSIPEB` | pad | Múltiples `VinculoEstrategico` (no columnas fijas) | Migrar |
| `ArticulacionLog` | pad | Auditoría de articulación | Migrar |
| `EjePGDESA`, `ComponentePDESA`, `SectorEconomico`, `ResultadoSectorial` | codificacion | Nodos de instrumento nacional/sectorial importado | Migrar (WP-06) |
| `EntidadTerritorialCGEO`, `EntidadCodificadora`, `SecuenciaCodigo`, `HomologacionCodigo` | codificacion | Motor de codificación (se mantiene) | Conservar motor |
| `VersionCatalogoPlan` | codificacion | Metodología/versión de instrumento | Migrar |
| `CodigoNivel` | articulacion | Motor de codificación | Conservar |
| `AcuerdoInternacional`, `Normativa`, `ActividadNormativa`, `TareaNormativa` | articulacion | Marco superior/compromisos configurables | Migrar |
| `LineamientoPAD`, `ResultadoPAD`, `ProductoPAD` | articulacion | Nodos PAD (fusionar con `pad`) | Fusionar y migrar |
| `ResultadoPEI`, `ProductoPEI` | articulacion | Nodos PEI | Migrar (WP-06 PEI) |
| `ArticulacionPADPEI` | articulacion | `VinculoEstrategico` PAD→PEI | Migrar |
| `IndicadorCadena` | articulacion | Banco de indicadores + vínculos | Migrar (WP-07) |

## 3. Banco Municipal de Indicadores

| Modelo legacy | App | Destino V2 | Acción |
|---|---|---|---|
| `Indicador` | indicadores | `Indicador` (banco único, con versión) | Migrar |
| `MetaProgramada` | indicadores | `MetaIndicador` (metas plurianuales) | Migrar |
| `MedioVerificacion`, `Supuesto` | indicadores | `MedioVerificacion`, `Supuesto` (vinculados) | Migrar |
| `Operacion`, `Tarea`, `Producto` | indicadores | SIS-POA (jerarquía operativa canónica) | **Mover fuera** |
| `Evaluacion`, `CriterioEvaluacion`, `ResultadoEvaluacion`, `LeccionAprendida`, `Recomendacion` | evaluacion | Motor de evaluación por alcance | Refactor |

## 4. SIS-POA

| Modelo legacy | App | Destino V2 | Acción |
|---|---|---|---|
| `POAU`, `POAUActividad` | poau | SIS-POA (POAU; actividad → jerarquía canónica) | Refactor |
| `EjecucionFisica`, `EjecucionFinanciera` | poau | Programación físico-financiera | Conservar |
| `AccionPOA` | articulacion | SIS-POA `AccionPOA` (canónico) | Migrar |
| `OperacionPOAU`, `ActividadPOAU`, `TareaPOAU` | articulacion | Jerarquía operativa canónica | Migrar |
| `SeguimientoPresupuesto`, `AsignacionObjetoGasto` | articulacion | SIS-POA presupuesto/seguimiento | Migrar |
| `TechoPresupuestario`, `DistribucionTecho`, `MovimientoTecho` | techos | Techos SIS-POA | Conservar |
| `EstimacionRecurso`, `EstimacionPlurianual` | recursos | Recursos SIS-POA | Conservar |
| `ProgramaPresupuestario`, `ProyectoPresupuestario`, `ActividadPresupuestaria`, `CategoriaProgramatica`, `AsignacionPresupuestariaUnidad`, `LineaPresupuestaria` | presupuesto | Presupuesto SIS-POA | Conservar |
| `ReporteSeguimiento`, `EntradaSeguimiento`, `Alerta`, `UmbralConfiguracion` | seguimiento | Motor de seguimiento con alcance por dominio | Generalizar |
| `AccionCorrectiva`, `CompromisoAccionCorrectiva` | acciones_correctivas | Integrar al motor de seguimiento | Integrar |
| `SolicitudModificacion`, `CambioModificacion`, `ImpactoModificacion` | modificaciones | Motor transversal de ajustes | Refactor |

## 5. SIS-PRO

| Modelo legacy | App | Destino V2 | Acción |
|---|---|---|---|
| `ProyectoInversion` | inversion | Semilla de `Proyecto` SIS-PRO | Evolucionar |
| `ProgramacionPlurianualProyecto`, `ProgramacionFisicaFinanciera` | inversion | Programación de proyecto | Evolucionar |

## 6. Reglas de resolución de duplicidades (orden)

1. Definir kernel `NodoEstrategico` V2 (WP-04).
2. Crear este mapa como fuente de equivalencias (hecho).
3. Migrar `planificacion.NodoPlanificacion`.
4. Migrar catálogos PGDESA/PDESA desde `codificacion` (WP-06).
5. Migrar PAD de `pad`.
6. Comparar con PAD de `articulacion`.
7. Resolver duplicados por **código + versión + significado**, nunca por texto.
8. Migrar PEI de `articulacion`.
9. Migrar articulaciones y vínculos.
10. Migrar indicadores al banco único.
11. Separar POA/POAU de `articulacion` hacia SIS-POA.
12. Marcar legacy read-only tras cutover.
13. Eliminar solo después del retiro (ADR-004).

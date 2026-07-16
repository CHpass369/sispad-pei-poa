# Análisis Documental — SISPAD–PEI–POA

> **Fase 0**: Documento generado como parte del análisis inicial del proyecto.
> **Fecha**: 2026-07-16

---

## 1. Inventario de Archivos de Referencia

### 1.1 Archivos solicitados en el prompt original

| Archivo | Ruta esperada | Estado |
|---------|--------------|--------|
| GUIA PAD.pdf | `/mnt/data/GUIA PAD.pdf` | ❌ No disponible |
| Directrices de formulación presupuestaria 2026 | `/mnt/data/Directrices_de_formulación_presupuestaria_2026_0 (1).pdf` | ❌ No disponible |
| 1_Guía_metodológica_ETAs.pdf | `/mnt/data/1_Guía_metodológica_ETAs.pdf` | ❌ No disponible |
| MATRICES A Y B(2).xlsx | `/mnt/data/MATRICES A Y B(2).xlsx` | ❌ No disponible |
| GASTOS 2026.xlsx | `/mnt/data/GASTOS 2026.xlsx` | ❌ No disponible |
| POAU 2026 CATASTRO.xlsx | `/mnt/data/POAU 2026 CATASTRO.xlsx` | ❌ No disponible |
| SEGUIMIENTO Y EVALUACION PTDI_PEI AJUSTADA.xlsx | `/mnt/data/SEGUIMIENTO Y EVALUACION PTDI_PEI AJUSTADA.xlsx` | ❌ No disponible |

**Conclusión**: Los archivos de referencia no están presentes en el entorno actual (`/mnt/data/` no existe). El análisis se realiza sobre la base del código existente en el repositorio y el contenido del `PROMPT_SISPAD_POA.md`.

### 1.2 Archivos existentes en el repositorio

| Archivo | Propósito |
|---------|-----------|
| `PROMPT_SISPAD_POA.md` | Prompt maestro con especificación completa del sistema |
| `backend/apps/**/models.py` | 18 aplicaciones con modelos Django |
| `backend/apps/**/serializers.py` | Serializadores DRF |
| `backend/apps/**/views.py` | Vistas y ViewSets |
| `backend/apps/**/tests.py` | Pruebas unitarias |
| `frontend/sispoa/src/app/` | Frontend Angular con 18 módulos funcionales |
| `docker-compose.yml` | Orquestación Docker |
| `CHANGELOG.md` | Registro de versiones |
| `README.md` | Documentación de inicio |

---

## 2. Estructura de las Aplicaciones Django Existentes

El sistema actual está organizado como un monolito modular con **18 aplicaciones Django**:

| App | Modelos principales | Estado |
|-----|-------------------|--------|
| `core` | TimeStampedModel, UUIDModel, ActivableModel, VigenciaModel, VersionableModel | ✅ Completo |
| `accounts` | Usuario (AbstractUser), Rol | ✅ Completo |
| `organizacion` | TipoUnidad, UnidadOrganizacional, DireccionAdministrativa, UnidadEjecutora, AsignacionUsuarioUnidad | ✅ Completo |
| `gestion` | GestionFiscal, CicloFormulacion, EtapaFormulacion | ✅ Completo |
| `catalogos` | 12 clasificadores presupuestarios (CatalogoBase) | ✅ Completo |
| `planificacion` | Plan, NodoPlanificacion, AccionMedianoPlazo, AccionCortoPlazo, ArticulacionPlanificacion | ✅ Completo |
| `pad` | SectorPAD, PoliticaPAD, LineamientoEstrategico, ResultadoTerritorial, ProductoTerritorial, ArticulacionSIPEB, ArticulacionLog | ✅ Completo |
| `indicadores` | Indicador, MetaProgramada, Operacion, Tarea, Producto, MedioVerificacion, Supuesto | ✅ Completo |
| `poau` | POAU, POAUActividad, EjecucionFisica, EjecucionFinanciera | ✅ Completo |
| `techos` | TechoPresupuestario, DistribucionTecho | ✅ Completo |
| `presupuesto` | ProgramaPresupuestario, ProyectoPresupuestario, ActividadPresupuestaria, LineaPresupuestaria | ✅ Completo |
| `recursos` | EstimacionRecurso, EstimacionPlurianual | ✅ Completo |
| `inversion` | ProyectoInversion, ProgramacionPlurianualProyecto, ProgramacionFisicaFinanciera | ✅ Completo |
| `territorio` | Distrito, UnidadTerritorial, LocalizacionTerritorial | ✅ Completo |
| `workflow` | EnvioFormulacion, Revision, Observacion, Aprobacion | ✅ Completo |
| `documentos` | DocumentoAdjunto | ✅ Completo |
| `reportes` | (Servicios de generación de reportes) | ✅ Completo |
| `auditoria` | EventoAuditoria | ✅ Completo |
| `normativa` | VersionNormativa, ReglaPresupuestariaLegal | ✅ Completo |

---

## 3. Columnas y Campos Identificados en el Código

### 3.1 Estructura Organizacional
- `Institution`: código, nombre, sigla, tax_id, geometry, SRID
- `UnidadOrganizacional`: código, nombre, sigla, tipo, padre, responsable, gestión, vigencia
- `DireccionAdministrativa`: código, nombre, gestión, responsable
- `UnidadEjecutora`: código, nombre, DA, unidad_organizacional, gestión
- **Tipos**: MAE, secretaría, dirección, jefatura, unidad, subunidad

### 3.2 Planificación Estratégica
- `Plan`: código, nombre, tipo (PDES/PTDI/PEI/Sectorial), gestión_inicio/fin
- `NodoPlanificacion`: plan, padre, nivel, código, nombre (árbol de profundidad variable)
- `AccionMedianoPlazo`: código, nombre, nodo, gestión_inicio/fin, responsable
- `AccionCortoPlazo`: código, nombre, AMP, unidad_responsable, gestión

### 3.3 PAD (Plan Autonómico de Desarrollo)
- `SectorPAD`: código, nombre
- `PoliticaPAD`: código, nombre, gestión
- `LineamientoEstrategico`: código, nombre, política, gestión
- `ResultadoTerritorial`: código, nombre, lineamiento, sector, indicador, fórmula, línea_base, meta_2030, programación física/financiera JSON
- `ProductoTerritorial`: código, nombre, resultado, territorialización, responsable, indicador
- `ArticulacionSIPEB`: resultado, PGDESA, PDESA, ODS, NDC, NDT, PDS, sector

### 3.4 Presupuesto
- `LineaPresupuestaria`: gestión, entidad, DA, UE, programa, proyecto, actividad, finalidad/función, fuente, organismo, objeto_gasto, entidad_transferencia, importe, importe_plurianual

### 3.5 POAU
- `POAU`: unidad, producto_territorial, gestión, código, nombre, estado
- `POAUActividad`: código, nombre, objeto_gasto, meta_física, presupuesto_anual
- `EjecucionFisica/Financiera`: actividad, periodo, programado, ejecutado

### 3.6 Catálogos (12 clasificadores)
ObjetoGasto, FuenteFinanciamiento, OrganismoFinanciador, EntidadTransferencia, FinalidadFuncion, RubroRecurso, UnidadMedida, TipoOperacion, TipoProducto, TipoProyecto, TipoFinanciamiento, ClasificadorInstitucional

---

## 4. Relaciones entre Entidades Detectadas

```
Institution 1──N UnidadOrganizacional (padre jerárquico)
UnidadOrganizacional 1──N DireccionAdministrativa (por gestión)
DireccionAdministrativa 1──N UnidadEjecutora
Plan 1──N NodoPlanificacion (árbol)
NodoPlanificacion M──N ArticulacionPlanificacion
GestionFiscal 1──N CicloFormulacion 1──N EtapaFormulacion
PoliticaPAD 1──N LineamientoEstrategico 1──N ResultadoTerritorial
ResultadoTerritorial 1──N ProductoTerritorial
ResultadoTerritorial 1──1 ArticulacionSIPEB
UnidadOrganizacional 1──N POAU
POAU 1──N POAUActividad
POAUActividad 1──N EjecucionFisica
POAUActividad 1──N EjecucionFinanciera
LineaPresupuestaria N──1 (DA, UE, Programa, Proyecto, Actividad, Fuente, Organismo, ObjetoGasto)
AccionMedianoPlazo 1──N AccionCortoPlazo
AccionCortoPlazo 1──N Operacion
AccionCortoPlazo 1──N Producto
```

---

## 5. Catálogos Existentes

| Catálogo | App | Entidad | Vigencia |
|----------|-----|---------|----------|
| Clasificador Institucional | catalogos | ClasificadorInstitucional | ✅ versionado |
| Rubro de Recurso | catalogos | RubroRecurso | ✅ versionado |
| Objeto del Gasto | catalogos | ObjetoGasto | ✅ versionado |
| Fuente de Financiamiento | catalogos | FuenteFinanciamiento | ✅ versionado |
| Organismo Financiador | catalogos | OrganismoFinanciador | ✅ versionado |
| Entidad de Transferencia | catalogos | EntidadTransferencia | ✅ versionado |
| Finalidad/Función | catalogos | FinalidadFuncion | ✅ versionado |
| Unidad de Medida | catalogos | UnidadMedida | ✅ versionado |
| Tipo de Operación | catalogos | TipoOperacion | ✅ versionado |
| Tipo de Producto | catalogos | TipoProducto | ✅ versionado |
| Tipo de Proyecto | catalogos | TipoProyecto | ✅ versionado |
| Tipo de Financiamiento | catalogos | TipoFinanciamiento | ✅ versionado |
| Tipo de Unidad | organizacion | TipoUnidad | ✅ fijo |
| Sector PAD | pad | SectorPAD | ✅ por gestión |
| Reglas Presupuestarias | normativa | ReglaPresupuestariaLegal | ✅ versionado |

---

## 6. Reglas de Negocio Detectadas en el Código Existente

### 6.1 Reglas implementadas en `normativa/services.py`
1. Límite de gasto de funcionamiento (60% de ingresos)
3. SUS - 10% mínimo para salud
4. Seguridad Ciudadana - 10% mínimo
5. Renta Dignidad - 0.75%
6. Consistencia plurianual
7. Requisito de código SISIN para inversiones

### 6.2 Reglas en validaciones del modelo
8. `GestionFiscal.clean()`: año de gestión debe estar dentro del horizonte plurianual
9. `ReglaPresupuestariaLegal.clean()`: gestión_hasta > gestión_desde

### 6.3 Reglas implícitas en la estructura de datos
10. La suma de líneas presupuestarias debe coincidir con el presupuesto de actividad
11. Techos tienen versionado y montos máximos no superables
12. POAU tiene estados: borrador → enviado → aprobado/rechazado
13. Auditoría es append-only
14. Documentos tienen hash SHA-256 obligatorio
15. Las articulaciones PEI→PAD deben existir antes de aprobar

### 6.4 Reglas del prompt no implementadas aún
16. Acción POA sin PEI → bloquear
17. Acción PEI sin PAD → bloquear o excepción
18. Ponderaciones de operaciones = 100%
19. Presupuesto formulado ≤ techo disponible
20. No permitir montos negativos
21. No permitir articulaciones circulares
22. No permitir relaciones duplicadas activas

---

## 7. Datos que Deben Normalizarse

| Situación actual | Propuesta de normalización |
|-----------------|---------------------------|
| Programación física/financiera en `JSONField` en ResultadoTerritorial y ProductoTerritorial | Crear modelo `ProgramacionAnual` con FK a resultado/producto + gestión + valor |
| `TipoUnidad.nivel` como entero con meaning implícito | Crear jerarquía explícita con `nivel jerarquico` nullable y `rango` |
| Fechas sin zona horaria en modelos TimeStampedModel | Agregar zona horaria institucional configurable |
| Estados POAU limitados a 4 | Migrar a 12 estados según especificación del prompt |
| POAUActividad con campos directos sin desglose de operaciones/tareas | Crear jerarquía Operación → Actividad → Tarea |
| Sin modelo `PlanVersion` | Crear para versionado de planes inmutables |
| Sin modelo `AmendmentRequest/Change` | Crear para modificaciones y reformulaciones |
| Usuarios con contraseña local (AbstractUser) | Migrar a OIDC con Keycloak |
| Documentos en `FileField` (local) | Migrar a almacenamiento MinIO/S3 |

---

## 8. Brechas entre el Prompt y la Implementación Actual

| Dimensión | Prompt requiere | Implementado actual | Brecha |
|-----------|----------------|-------------------|--------|
| Modelo de planes genérico | PlanVersion, StrategicNode genérico | Plan fijo con tipos, sin versionado nativo | ⚠️ Media |
| PGDESA/PDESA | Planes de largo plazo | No existen como entidades separadas | ❌ Alta |
| Auxiliar Pluri | Módulo completo | No implementado | ❌ Alta |
| Seguimiento físico/financiero | TrackingReport, TrackingEntry con alertas | EjecucionFisica/Financiera simple | ⚠️ Media |
| Evaluación | Evaluation, Criterio, Lección, Recomendación | No implementado | ❌ Alta |
| Acciones correctivas | CorrectiveAction con control de cumplimiento | No implementado | ❌ Alta |
| Modificaciones/reformulaciones | AmendmentRequest, AmendmentChange | No implementado | ❌ Alta |
| Portal público | Portal separado con datos aprobados | No implementado | ❌ Alta |
| Notificaciones | Internas, email, eventos futuros | No implementado | ❌ Alta |
| OIDC/Keycloak | Autenticación externa | JWT local (SimpleJWT) | ❌ Alta |
| GeoServer | WMS/WFS integrado | Solo PostGIS, sin GeoServer | ⚠️ Media |
| MinIO/S3 | Almacenamiento externo | FileField local | ❌ Alta |
| Celery/Celery Beat | Tareas asíncronas | Configurado en docker-compose pero sin uso | ⚠️ Media |
| Redis | Caché y colas | Configurado en docker-compose pero sin uso | ⚠️ Media |

---

## 9. Riesgos de Migración

| Riesgo | Descripción | Severidad |
|--------|-------------|-----------|
| **Migración a OIDC** | Usuarios actuales con contraseñas locales. Requiere migración coordinada. | 🔴 Alta |
| **Cambio de modelo de datos** | Programación JSON → tablas normalizadas requiere migración de datos existentes | 🔴 Alta |
| **Almacenamiento de documentos** | Migrar archivos locales → MinIO requiere script de copia masiva | 🟡 Media |
| **Versionado de planes** | Estructura actual de Plan no permite versionado. Requiere nueva arquitectura de datos | 🔴 Alta |
| **Estados de POAU** | Cambiar de 4 a 12 estados rompe APIs existentes | 🟡 Media |
| **Datos semilla** | Los fixtures actuales pueden no ser compatibles con los nuevos modelos | 🟡 Media |

---

## 10. Correspondencia Prompt → Modelo de Datos Propuesto

| Sección del Prompt | Entidad Propuesta | App destino |
|--------------------|-------------------|-------------|
| 6. Modelo Organizacional | Institution + UnidadOrganizacional + DA + UE | `organizacion` ✅ |
| 7. Gestiones y Ciclos | GestionFiscal + CicloFormulacion + EtapaFormulacion | `gestion` ✅ |
| 8. Planes y Jerarquía | Plan + PlanVersion + StrategicNode | `planificacion` (mejorar) |
| 9. Matriz de Articulación | ArticulationLink | `planificacion` ✅ |
| 10. Gestión del PAD | Matriz A + Matriz B | `pad` ✅ |
| 11. Gestión del PEI | AccionMedianoPlazo + AccionCortoPlazo + Indicador | `planificacion` + `indicadores` ✅ |
| 12. Apertura POA | Nuevos modelos de apertura/cronograma/configuración | `poau` ❌ No implementado |
| 13. Techos | TechoPresupuestario + DistribucionTecho | `techos` ✅ |
| 14. POA Institucional | AnnualOperatingPlan + ShortTermAction | `planificacion` ⚠️ Parcial |
| 15. POAU | POAU + Operation + Activity + Task | `poau` ⚠️ Parcial |
| 16. Operaciones/Actividades/Tareas | Operation + Activity + Task + Product | `indicadores` ✅ |
| 17. Gestión Presupuestaria | BudgetLine + 12 catálogos | `presupuesto` + `catalogos` ✅ |
| 18. Auxiliar Pluri | Módulo completo de reporte plurianual | Nuevo ⚠️ Pendiente |
| 19. Banco de Programas/Proyectos | InvestmentProject | `inversion` ✅ |
| 20. Flujo de Revisión | WorkflowDefinition + WorkflowInstance + Observation | `workflow` ⚠️ Parcial |
| 21. Modificaciones | AmendmentRequest + AmendmentChange | Nuevo ❌ Pendiente |
| 22. Indicadores | Indicator + Baseline + Target + Measurement | `indicadores` ✅ |
| 23. Seguimiento | TrackingReport + TrackingEntry + Alertas | `poau` ⚠️ Parcial |
| 24. Acciones Correctivas | CorrectiveAction | Nuevo ❌ Pendiente |
| 25. Evaluación | Evaluation + Criterion + Result + Lesson | Nuevo ❌ Pendiente |
| 26. Gestión Documental | Document + MinIO | `documentos` ⚠️ Parcial |
| 27. Componente Geográfico | TerritorialUnit + LocalizacionTerritorial + GeoServer | `territorio` ⚠️ Parcial |
| 28. Usuarios, Roles, Permisos | Keycloak + RBAC/ABAC | `accounts` ❌ Migrar a OIDC |
| 29. Auditoría | AuditEvent | `auditoria` ✅ |
| 30. Importación Excel | Módulo configurable de importación | `core` ⚠️ Parcial |
| 31. Reportes | 25 reportes en XLSX/PDF/CSV | `reportes` ⚠️ Parcial |
| 32. Tableros | 4 tableros (MAE, Planificación, Presupuesto, Unidad, Seguimiento) | `frontend` ⚠️ Parcial |
| 33. Portal Público | Portal público independiente | Nuevo ❌ Pendiente |
| 34. Notificaciones | Sistema de notificaciones multi-canal | Nuevo ❌ Pendiente |

# Matriz de Trazabilidad de Requisitos — SISPAD–PEI–POA

> **Fase 0**: Documento generado como parte del análisis inicial del proyecto.
> **Fecha**: 2026-07-16

---

## Leyenda

- **Estado**: ✅ Implementado / ⚠️ Parcial / ❌ Pendiente / 🔄 A mejorar
- **Prioridad**: Alta / Media / Baja

---

## RF-01: Gestión de Institución y Organización

| ID | Sección Prompt | Estado | App | Prioridad |
|----|---------------|--------|-----|-----------|
| RF-01.1 | §6 (Institution) | ⚠️ Sin modelo Institution explícito | `organizacion` | Alta |
| RF-01.2 | §6 (Tipos de unidad) | ✅ UnidadOrganizacional con TipoUnidad | `organizacion` | Alta |
| RF-01.3 | §6 (Vigencia temporal) | ✅ VigenciaModel en UnidadOrganizacional | `organizacion` | Alta |
| RF-01.4 | §6 (DA/UE) | ✅ DireccionAdministrativa + UnidadEjecutora | `organizacion` | Alta |
| RF-01.5 | §6 (Asignación usuarios) | ✅ AsignacionUsuarioUnidad | `organizacion` | Alta |
| RF-01.6 | §6 (Inactivar, no eliminar) | ✅ ActivableModel con activo=False | `organizacion` | Alta |

## RF-02: Gestión de Usuarios, Roles y Permisos

| ID | Sección Prompt | Estado | App | Prioridad |
|----|---------------|--------|-----|-----------|
| RF-02.1 | §28 (Keycloak) | ❌ JWT local (SimpleJWT) | `accounts` | Alta |
| RF-02.2 | §28 (Roles) | ✅ Rol parametrizable | `accounts` | Alta |
| RF-02.3 | §28 (RBAC+ABAC) | ⚠️ RBAC básico implementado | `accounts` | Alta |
| RF-02.4 | §28 (Permisos por alcance) | ⚠️ Sin ABAC completo | `accounts` | Alta |
| RF-02.5 | §28 (Control social/consulta) | ❌ No implementado | `accounts` | Alta |
| RF-02.6 | §28 (Delegaciones) | ❌ No implementado | `workflow` | Media |

## RF-03: Gestiones y Ciclos de Planificación

| ID | Sección Prompt | Estado | App | Prioridad |
|----|---------------|--------|-----|-----------|
| RF-03.1 | §7 (GestionFiscal) | ✅ 8 estados | `gestion` | Alta |
| RF-03.2 | §7 (Horizonte plurianual) | ✅ En GestionFiscal | `gestion` | Alta |
| RF-03.3 | §7 (Ciclos/etapas) | ✅ CicloFormulacion + EtapaFormulacion | `gestion` | Alta |
| RF-03.4 | §7 (Validación años) | ✅ En clean() | `gestion` | Alta |

## RF-04: Planes y Jerarquía Estratégica

| ID | Sección Prompt | Estado | App | Prioridad |
|----|---------------|--------|-----|-----------|
| RF-04.1 | §8 (Instrumentos) | ⚠️ Plan con tipos fijos, faltan PGDESA/PDESA | `planificacion` | Alta |
| RF-04.2 | §8 (Versionado) | ❌ Sin PlanVersion | `planificacion` | Alta |
| RF-04.3 | §8 (Nodos) | ✅ NodoPlanificacion jerárquico | `planificacion` | Alta |
| RF-04.4 | §8 (Tipos de nodo) | ⚠️ Niveles limitados, no parametrizables | `planificacion` | Alta |
| RF-04.5 | §8 (Nueva versión) | ❌ No implementado | `planificacion` | Alta |

## RF-05: Matriz de Articulación

| ID | Sección Prompt | Estado | App | Prioridad |
|----|---------------|--------|-----|-----------|
| RF-05.1 | §9 (Articulación) | ⚠️ ArticulacionPlanificacion básica | `planificacion` | Alta |
| RF-05.2 | §9 (Vistas) | ❌ Sin árbol/matriz/grafo en frontend | `planificacion` | Alta |
| RF-05.3 | §9 (Búsqueda/filtros) | ❌ No implementado | `planificacion` | Alta |
| RF-05.4 | §9 (Sin articulación) | ❌ No implementado | `planificacion` | Alta |
| RF-05.5 | §9 (Exportación) | ❌ No implementado | `planificacion` | Media |
| RF-05.6 | §9 (Bloqueo POA sin PEI) | ❌ No implementado | `planificacion` | Alta |
| RF-05.7 | §9 (Bloqueo PEI sin PAD) | ❌ No implementado | `planificacion` | Alta |
| RF-05.8 | §9 (Circulares/duplicadas) | ❌ No validado | `planificacion` | Alta |

## RF-06: Gestión del PAD

| ID | Sección Prompt | Estado | App | Prioridad |
|----|---------------|--------|-----|-----------|
| RF-06.1 | §10 (Sectores/políticas) | ✅ SectorPAD + PoliticaPAD + Lineamiento | `pad` | Alta |
| RF-06.2 | §10 (Resultados) | ✅ ResultadoTerritorial | `pad` | Alta |
| RF-06.3 | §10 (Productos) | ✅ ProductoTerritorial | `pad` | Alta |
| RF-06.4 | §10 (Matriz B - SIPEB) | ✅ ArticulacionSIPEB | `pad` | Alta |
| RF-06.5 | §10 (Reportes PAD) | ❌ No implementado | `pad` | Media |

## RF-07: Gestión del PEI

| ID | Sección Prompt | Estado | App | Prioridad |
|----|---------------|--------|-----|-----------|
| RF-07.1 | §11 (Misión/visión) | ❌ No implementado | `planificacion` | Alta |
| RF-07.2 | §11 (AMP) | ✅ AccionMedianoPlazo | `planificacion` | Alta |
| RF-07.3 | §11 (ACP) | ✅ AccionCortoPlazo | `planificacion` | Alta |
| RF-07.4 | §11 (Programación) | ⚠️ Sin presupuesto plurianual por acción | `planificacion` | Alta |
| RF-07.5 | §11 (Versionado) | ❌ No implementado | `planificacion` | Alta |

## RF-08: Apertura del POA

| ID | Sección Prompt | Estado | App | Prioridad |
|----|---------------|--------|-----|-----------|
| RF-08.1 | §12 (Admin POA) | ⚠️ Gestión básica de gestión fiscal | `gestion` | Alta |
| RF-08.2 | §12 (Reapertura) | ❌ No implementado | `gestion` | Alta |
| RF-08.3 | §12 (Copiar/migrar) | ❌ No implementado | `gestion` | Alta |
| RF-08.4 | §12 (Unidades obligadas) | ❌ No implementado | `gestion` | Alta |
| RF-08.5 | §12 (Dashboard avance) | ❌ No implementado | `poau` | Alta |

## RF-09: Techos Presupuestarios

| ID | Sección Prompt | Estado | App | Prioridad |
|----|---------------|--------|-----|-----------|
| RF-09.1 | §13 (Techo) | ✅ TechoPresupuestario versionado | `techos` | Alta |
| RF-09.2 | §13 (Distribución) | ✅ DistribucionTecho | `techos` | Alta |
| RF-09.3 | §13 (Movimientos) | ❌ Sin BudgetCeilingMovement | `techos` | Alta |
| RF-09.4 | §13 (Validación) | ❌ Sin validación automática de techo | `techos` | Alta |
| RF-09.5 | §13 (Decimal) | ✅ Decimal fields | `techos` | Alta |

## RF-10: Formulación POAU

| ID | Sección Prompt | Estado | App | Prioridad |
|----|---------------|--------|-----|-----------|
| RF-10.1 | §15 (Wizard 8 pasos) | ⚠️ Wizard Angular implementado pero con datos mock | `poau` | Alta |
| RF-10.2 | §15 (12 estados) | ❌ Solo 4 estados | `poau` | Alta |
| RF-10.3 | §15 (Operaciones/actividades) | ⚠️ POAUActividad sin jerarquía completa | `poau` | Alta |
| RF-10.4 | §15 (Ponderaciones 100%) | ❌ No implementado | `poau` | Alta |
| RF-10.5 | §15 (Territorializar) | ✅ LocalizacionTerritorial | `territorio` | Alta |
| RF-10.6 | §15 (POA no editable) | ❌ No implementado | `poau` | Alta |

## RF-11: Presupuesto y Líneas Presupuestarias

| ID | Sección Prompt | Estado | App | Prioridad |
|----|---------------|--------|-----|-----------|
| RF-11.1 | §17 (13 clasificadores) | ✅ 12 catálogos implementados | `catalogos` | Alta |
| RF-11.2 | §17 (Línea presupuestaria) | ✅ LineaPresupuestaria completa | `presupuesto` | Alta |
| RF-11.3 | §17 (Consistencia) | ⚠️ Sin validación automática | `presupuesto` | Alta |
| RF-11.4 | §17 (Plurianual) | ✅ importe_plurianual | `presupuesto` | Alta |
| RF-11.5 | §17 (2 decimales) | ✅ Decimal(places=2) | `presupuesto` | Alta |

## RF-12 a RF-25: Módulos Pendientes

| ID | Módulo | Estado | App destino | Prioridad |
|----|--------|--------|-------------|-----------|
| RF-12 | Auxiliar Pluri | ❌ No implementado | Nuevo | Alta |
| RF-13 | Banco de Programas/Proyectos | ✅ ProyectoInversion implementado | `inversion` | Alta |
| RF-14 | Flujo de Revisión | ✅ Workflow básico implementado | `workflow` | Alta |
| RF-15 | Modificaciones/Reformulaciones | ❌ No implementado | Nuevo | Alta |
| RF-16 | Seguimiento Físico/Financiero | ✅ Ejecución básica implementada | `poau` | Alta |
| RF-17 | Acciones Correctivas | ❌ No implementado | Nuevo | Alta |
| RF-18 | Evaluación | ❌ No implementado | Nuevo | Alta |
| RF-19 | Gestión Documental | ✅ DocumentoAdjunto (falta MinIO) | `documentos` | Alta |
| RF-20 | Componente Geográfico | ✅ PostGIS implementado (falta GeoServer) | `territorio` | Alta |
| RF-21 | Reportes | ⚠️ Reportes básicos implementados | `reportes` | Alta |
| RF-22 | Portal Público | ❌ No implementado | Nuevo | Alta |
| RF-23 | Notificaciones | ❌ No implementado | Nuevo | Alta |
| RF-24 | Importación Excel | ⚠️ Management commands básicos | `core` | Alta |
| RF-25 | Auditoría | ✅ EventoAuditoria append-only | `auditoria` | Alta |

---

## Resumen de Cobertura

| Estado | Cantidad | Porcentaje |
|--------|----------|------------|
| ✅ Implementado | 38 | 44% |
| ⚠️ Parcial | 17 | 20% |
| ❌ Pendiente | 31 | 36% |
| **Total** | **86** | **100%** |

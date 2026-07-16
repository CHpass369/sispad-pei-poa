# Backlog por Fases y Riesgos Técnicos — SISPAD–PEI–POA

> **Fase 0**: Documento generado como parte del análisis inicial del proyecto.
> **Fecha**: 2026-07-16

---

## 1. Backlog de Implementación por Fases

### FASE 1: Infraestructura ⏳ Pendiente (ajustar)

> Ya existe infraestructura base. Esta fase se reduce a pendientes.

| # | Tarea | Prioridad | Dependencias |
|---|-------|-----------|--------------|
| 1.1 | Migrar almacenamiento documentos a MinIO | Alta | - |
| 1.2 | Configurar Celery + Redis para procesamiento asíncrono | Alta | - |
| 1.3 | Configurar GeoServer con PostGIS | Alta | PostGIS existente |
| 1.4 | Implementar Keycloak y migrar usuarios de SimpleJWT a OIDC | Alta | - |
| 1.5 | Agregar health checks a docker-compose | Media | - |
| 1.6 | Scripts de backup/restore para MinIO y GeoServer | Media | 1.1, 1.3 |
| 1.7 | Makefile completo con comandos faltantes | Media | - |
| 1.8 | Configurar rate limiting en producción | Alta | - |

### FASE 2: Núcleo Organizacional 🔵 Refinar

> Mayoría ya implementada. Refinar modelos existentes.

| # | Tarea | Prioridad | Dependencias |
|---|-------|-----------|--------------|
| 2.1 | Crear modelo Institution para soporte multitenant | Alta | - |
| 2.2 | Agregar jerarquía explícita de TipoUnidad con nivel y rango | Media | - |
| 2.3 | Implementar ABAC (permisos por atributo) | Alta | Keycloak |
| 2.4 | Migrar GestionFiscal a estados expandidos (12 estados) | Alta | - |
| 2.5 | Mejorar asignación de usuarios con alcances territoriales | Media | - |
| 2.6 | Implementar tabla de permisos completa (matriz roles x módulos) | Alta | 2.3 |

### FASE 3: Planificación Estratégica 🟡 Refactor mayor

| # | Tarea | Prioridad | Dependencias |
|---|-------|-----------|--------------|
| 3.1 | Crear modelo PlanVersion con inmutabilidad de versiones aprobadas | Alta | - |
| 3.2 | Agregar tipos de plan: PGDESA, PDESA, PSD | Alta | - |
| 3.3 | Hacer StrategicNode parametrizable (tipos de nodo configurables) | Alta | - |
| 3.4 | Agregar misión, visión y valores institucionales al PEI | Alta | - |
| 3.5 | Implementar ArticulationLink completo con porcentaje de contribución | Alta | - |
| 3.6 | Vistas de articulación: árbol, matricial, grafo | Alta | 3.5 |
| 3.7 | Validación de articulación (sin POA sin PEI, sin PEI sin PAD) | Alta | 3.5 |
| 3.8 | Reportes PAD: Matriz A, Matriz B, presupuesto quinquenal | Media | - |

### FASE 4: Formulación POA 🟡 Refactor mayor

| # | Tarea | Prioridad | Dependencias |
|---|-------|-----------|--------------|
| 4.1 | Expandir estados POAU a 12 (borrador → cerrado) | Alta | - |
| 4.2 | Agregar modelo Operation completo (independiente de indicadores) | Alta | - |
| 4.3 | Agregar modelo Activity y Task con ponderaciones | Alta | 4.2 |
| 4.4 | Asistente de formulación POAU con 8 pasos funcionales | Alta | 4.2, 4.3 |
| 4.5 | Validar suma de ponderaciones = 100% | Alta | 4.3 |
| 4.6 | Implementar movimientos de techo (BudgetCeilingMovement) | Alta | - |
| 4.7 | Validación techo disponible vs presupuesto formulado | Alta | 4.6 |
| 4.8 | Crear AnnualOperatingPlan con consolidación desde POAU | Alta | - |
| 4.9 | Implementar Auxiliar Pluri | Alta | - |
| 4.10 | Copiar datos de gestión anterior al abrir nueva gestión | Media | - |

### FASE 5: Workflow 🔵 Refinar

| # | Tarea | Prioridad | Dependencias |
|---|-------|-----------|--------------|
| 5.1 | Implementar WorkflowDefinition y WorkflowStepDefinition configurables | Alta | - |
| 5.2 | WorkflowInstance automatizada por flujo de aprobación | Alta | 5.1 |
| 5.3 | Delegaciones temporales y suplencias | Media | - |
| 5.4 | Notificaciones automáticas en cada transición de estado | Alta | - |
| 5.5 | Control de plazos en observaciones | Alta | - |
| 5.6 | No permitir auto-aprobación con conflicto de funciones | Alta | - |

### FASE 6: Seguimiento y Evaluación 🟢 Nuevo desarrollo

| # | Tarea | Prioridad | Dependencias |
|---|-------|-----------|--------------|
| 6.1 | Crear TrackingReport y TrackingEntry con programación/ejecución | Alta | - |
| 6.2 | Semáforo configurable (verde/amarillo/rojo) | Alta | 6.1 |
| 6.3 | Alertas automáticas por desviación | Alta | 6.1 |
| 6.4 | Acciones correctivas con control de cumplimiento | Alta | 6.1 |
| 6.5 | Módulo de Evaluación (anual, medio término, final) | Alta | - |
| 6.6 | Criterios de evaluación parametrizables | Alta | 6.5 |
| 6.7 | Dashboard de seguimiento con gráficos ECharts | Alta | 6.1 |
| 6.8 | Dashboard MAE, Planificación, Presupuesto, Unidad | Alta | 6.1 |

### FASE 7: Modificaciones y Reformulaciones 🟢 Nuevo desarrollo

| # | Tarea | Prioridad | Dependencias |
|---|-------|-----------|--------------|
| 7.1 | Crear AmendmentRequest con tipos parametrizables | Alta | - |
| 7.2 | Crear AmendmentChange con control de valores anteriores/posteriores | Alta | 7.1 |
| 7.3 | Workflow de aprobación de modificaciones | Alta | 7.1 |
| 7.4 | Versionado automático al modificar entidades aprobadas | Alta | - |

### FASE 8: Componente Geográfico 🟡 Refinar

| # | Tarea | Prioridad | Dependencias |
|---|-------|-----------|--------------|
| 8.1 | Configurar GeoServer con PostGIS | Alta | - |
| 8.2 | Publicar capas WMS/WFS desde PostGIS | Alta | 8.1 |
| 8.3 | Automatizar creación de workspaces/stores/layers vía API REST de GeoServer | Media | 8.1 |
| 8.4 | Mapa interactivo en frontend con OpenLayers | Alta | - |
| 8.5 | Edición de geometrías en navegador | Media | 8.4 |
| 8.6 | Cálculo de superficies y análisis urbano-rural | Media | - |

### FASE 9: Reportes y Portal Público 🟢 Nuevo desarrollo

| # | Tarea | Prioridad | Dependencias |
|---|-------|-----------|--------------|
| 9.1 | Implementar 25 reportes en XLSX/PDF/CSV | Alta | - |
| 9.2 | Reportes asíncronos con Celery | Alta | 1.2 |
| 9.3 | Dashboard interactivo con ECharts | Alta | - |
| 9.4 | Portal público independiente (solo datos aprobados) | Alta | - |
| 9.5 | Datos abiertos descargables desde el portal | Media | 9.4 |
| 9.6 | Proteger portal contra acceso a datos no publicados | Alta | 9.4 |

### FASE 10: Calidad y Documentación 🔵 Refinar

| # | Tarea | Prioridad | Dependencias |
|---|-------|-----------|--------------|
| 10.1 | Pruebas unitarias faltantes en módulos nuevos | Alta | Todo lo anterior |
| 10.2 | Cobertura ≥80% en servicios críticos | Alta | 10.1 |
| 10.3 | Pruebas E2E con Playwright (15 casos) | Media | Todo lo anterior |
| 10.4 | Pruebas de permisos (RBAC + ABAC) | Alta | 2.3 |
| 10.5 | Pruebas de reglas presupuestarias (≥90%) | Alta | - |
| 10.6 | Documentación OpenAPI completa | Alta | - |
| 10.7 | Pruebas de seguridad (OWASP) | Alta | - |
| 10.8 | Pruebas de rendimiento y carga | Media | - |
| 10.9 | Documentación de administrador y usuario | Media | - |
| 10.10 | Despliegue documentado en servidor Linux | Alta | - |

---

## 2. Riesgos Técnicos Identificados

| # | Riesgo | Probabilidad | Impacto | Mitigación |
|---|--------|--------------|---------|------------|
| **R01** | Migración de SimpleJWT a Keycloak requiere migrar todos los usuarios existentes | Alta | Alto | Planificar migración en ventana de mantenimiento; mantener convivencia temporal |
| **R02** | Cambio de modelo de datos (JSONField → tablas) puede romper datos existentes | Alta | Alto | Crear migraciones de datos por pasos; mantener backward compatibility |
| **R03** | Migración de FileField local a MinIO requiere reubicar archivos | Media | Medio | Script de copia con verificación de hash SHA-256 |
| **R04** | Refactor de estados POAU de 4 a 12 rompe APIs y frontend existente | Alta | Alto | Versionar API; actualizar frontend en paralelo |
| **R05** | GeoServer requiere Java y recursos adicionales en el servidor | Media | Medio | Dockerizar GeoServer; ajustar recursos |
| **R06** | Keycloak es un servicio pesado (Java/Quarkus) que requiere recursos | Media | Medio | Dockerizar; considerar Keycloak optimizado |
| **R07** | La normalización de programación física/financiera de JSON a tablas afecta rendimiento de consultas actuales | Media | Medio | Crear vistas materializadas para reportes |
| **R08** | Los fixtures existentes pueden no ser compatibles con nuevos modelos | Alta | Medio | Regenerar fixtures después de cada cambio mayor |
| **R09** | El frontend Angular tiene componentes conectados a APIs mock que deben migrarse a APIs reales | Alta | Alto | Migrar por módulo; mantener convivencia temporal |
| **R10** | La auditoría append-only no soporta borrado físico — la tabla EventoAuditoria crecerá sin límite | Media | Bajo | Particionar por gestión; política de retención |
| **R11** | Sin tests para módulos nuevos (Amendment, Evaluation, Tracking), la calidad puede verse afectada | Alta | Alto | Exigir tests en cada PR; cobertura mínima |
| **R12** | La articulación PGDESA→PDESA→PAD→PEI→POA requiere datos reales que no están disponibles en el entorno actual | Alta | Alto | Solicitar datos al GAM Sacaba; crear datos semilla de demostración |

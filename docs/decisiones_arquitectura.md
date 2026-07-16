# Decisiones Arquitectónicas — SISPAD–PEI–POA

> **Fase 0**: Documento generado como parte del análisis inicial del proyecto.
> **Fecha**: 2026-07-16

---

## ADR-01: Monolito Modular en Django

**Contexto**: El sistema requiere 20+ módulos funcionales con alta cohesión interna y bajo acoplamiento externo.

**Decisión**: Implementar monolito modular Django con aplicaciones independientes. Cada app tiene su propio models, serializers, services, views, urls y tests.

**Consecuencias**:
- ✅ Despliegue simple (un proceso)
- ✅ Compartición de modelos base (TimeStampedModel, UUIDModel)
- ✅ APIs rápidas sin latencia de red entre módulos
- ✅ Migraciones coordinadas
- ❌ Escalado horizontal monolítico (mitigable con Celery para tareas pesadas)
- ❌ Acoplamiento potencial si no se respetan los límites de módulo

**Estado**: ✅ Implementado

---

## ADR-02: PostgreSQL + PostGIS como Base de Datos

**Contexto**: El sistema requiere almacenamiento geoespacial para territorializar programas, proyectos y operaciones.

**Decisión**: Usar PostgreSQL con extensión PostGIS y pg_trgm.

**SRID Oficial**: EPSG:32719 (UTM zona 19S, métrico — Bolivia)
**SRID Publicación**: EPSG:4326 (WGS84) y EPSG:3857 (Web Mercator)

**Consecuencias**:
- ✅ Consultas geoespaciales nativas
- ✅ Índices espaciales (GIST)
- ✅ Trigram search para búsqueda de texto
- ✅ Migraciones Django con GeoDjango
- ❌ Mayor complejidad de backups (pg_dump + --blobs)

**Estado**: ✅ Implementado

---

## ADR-03: UUID como Identificador Primario Público

**Contexto**: Los IDs son expuestos en URLs, APIs y reportes. Se requiere imposibilidad de enumeración y compatibilidad con multitenant futuro.

**Decisión**: UUID v4 como PK pública en todas las tablas. AutoField interno para joins (no expuesto).

**Consecuencias**:
- ✅ No enumerable
- ✅ Seguro para exposición en URLs
- ✅ Compatible con merge futuro de bases de datos
- ❌ Mayor tamaño de índice (16 bytes vs 4)
- ❌ Rendimiento de joins ligeramente menor (mitigable con índices)

**Estado**: ✅ Implementado

---

## ADR-04: Decimal para Montos (Nunca Float)

**Contexto**: El sistema maneja presupuestos municipales. Los errores de redondeo por float son inaceptables.

**Decisión**: Usar `DecimalField(max_digits=20, decimal_places=2)` para todos los montos, con `MinValueValidator(0)` para montos no negativos.

**Consecuencias**:
- ✅ Precisión exacta
- ✅ Sin errores de redondeo
- ✅ Validación de no negatividad
- ❌ Mayor uso de CPU en operaciones aritméticas (irrelevante para este contexto)

**Estado**: ✅ Implementado

---

## ADR-05: Auditoría Append-Only

**Contexto**: Se requiere trazabilidad completa de todas las modificaciones para cumplimiento normativo y control social.

**Decisión**: Tabla `EventoAuditoria` con modo append-only (sin UPDATE ni DELETE desde la aplicación). Almacena datos previos/posteriores en JSON.

**Consecuencias**:
- ✅ Trazabilidad inmutable
- ✅ Comparación before/after
- ✅ Sin posibilidad de alteración desde la app
- ❌ Crecimiento de tabla (mitigable con particionado por gestión)
- ❌ Los eventos no se pueden corregir (se registra una acción compensatoria)

**Estado**: ✅ Implementado

---

## ADR-06: API REST Versionada con DRF

**Contexto**: El frontend Angular y potenciales integradores externos necesitan APIs estables.

**Decisión**: API REST versionada bajo `/api/v1/` con Django REST Framework, paginación, filtros, ordenamiento y documentación OpenAPI.

**Consecuencias**:
- ✅ APIs predecibles y versionadas
- ✅ Documentación OpenAPI automática
- ✅ Separación frontend-backend
- ❌ Overhead de serialización (mitigable con select_related/prefetch_related)

**Estado**: ✅ Implementado

---

## ADR-07: Frontend Angular con Angular Material

**Contexto**: Interfaz institucional compleja con formularios de múltiples pasos, tablas con filtros y mapas.

**Decisión**: Angular + TypeScript estricto + Angular Material + Angular CDK + Reactive Forms + Signals.

**Consecuencias**:
- ✅ Framework completo y tipado
- ✅ Componentes Material Design institucionales
- ✅ Formularios reactivos complejos
- ✅ OpenLayers para mapas; ECharts para gráficos
- ❌ Mayor tamaño de bundle (mitigable con lazy loading)

**Estado**: ✅ Implementado

---

## ADR-08: Procesamiento Asíncrono con Celery + Redis

**Contexto**: Importaciones Excel, reportes pesados y generación de matrices no deben bloquear la API.

**Decisión**: Celery para tareas asíncronas, Celery Beat para tareas programadas, Redis como broker.

**Consecuencias**:
- ✅ Reportes sin bloqueo
- ✅ Importaciones en segundo plano
- ✅ Notificaciones asíncronas
- ✅ Tareas programadas (cierres automáticos, alertas)
- ❌ Complejidad operativa adicional (worker + beat + redis)

**Estado**: ⚠️ Infraestructura configurada en docker-compose, workers sin implementar

---

## ADR-09: Almacenamiento de Archivos en MinIO (S3-compatible)

**Contexto**: El sistema maneja documentos adjuntos (informes, actas, evidencias, mapas). No deben almacenarse en PostgreSQL.

**Decisión**: MinIO como almacenamiento de objetos S3-compatible. Archivos grandes fuera de la BD.

**Consecuencias**:
- ✅ Escalable horizontalmente
- ✅ Backup independiente de la BD
- ✅ Los documentos grandes no afectan la performance de la BD
- ❌ Servicio adicional que administrar
- ❌ Migración desde FileField local

**Estado**: ❌ Pendiente de implementar (actualmente FileField local)

---

## ADR-10: Keycloak para Autenticación OIDC

**Contexto**: Se requiere autenticación centralizada con soporte para SSO y múltiples proveedores de identidad.

**Decisión**: Keycloak como proveedor OIDC. No almacenar contraseñas en tablas funcionales.

**Consecuencias**:
- ✅ SSO
- ✅ MFA integrado
- ✅ Roles desde Keycloak
- ✅ Sesiones gestionadas externamente
- ❌ Servicio adicional pesado (Java/Quarkus)
- ❌ Migración desde SimpleJWT actual

**Estado**: ❌ Pendiente de implementar (actualmente SimpleJWT)

---

## ADR-11: GeoServer para Servicios WMS/WFS

**Contexto**: El sistema publica capas geoespaciales para consulta interna y portal público.

**Decisión**: GeoServer publicando capas desde PostGIS mediante WMS y WFS.

**Consecuencias**:
- ✅ Estándares OGC
- ✅ Integración con OpenLayers/QGIS
- ✅ Estilo SLD configurable
- ❌ Servicio Java adicional
- ❌ Complejidad de configuración

**Estado**: ❌ Pendiente de implementar

---

## ADR-12: SRID Configurable por Institución

**Contexto**: Diferentes municipios bolivianos pueden usar distintos sistemas de referencia. Sacaba usa EPSG:32719.

**Decisión**: El SRID oficial de almacenamiento es configurable por institución. Publicación en EPSG:4326 y EPSG:3857.

**Consecuencias**:
- ✅ Reutilizable para otros GAMs
- ✅ Doble almacenamiento (oficial + web)
- ✅ Conversión automática

**Estado**: ⚠️ SRID parcialmente implementado en LocalizacionTerritorial

---

## ADR-13: Versionado de Planes Inmutables

**Contexto**: Los planes aprobados no deben modificarse. Las correcciones requieren nueva versión.

**Decisión**: Cada plan tiene versiones inmutables. Al aprobarse una versión, se marca como `immutable=True`. Las modificaciones crean una nueva versión.

**Consecuencias**:
- ✅ Trazabilidad completa de cambios
- ✅ Los usuarios ven siempre la versión correcta
- ❌ Mayor complejidad de consultas (JOIN con versión activa)
- ❌ Almacenamiento adicional

**Estado**: ❌ Pendiente de implementar

---

## Resumen de Decisiones

| # | Decisión | Estado | Prioridad |
|---|----------|--------|-----------|
| 01 | Monolito modular Django | ✅ Implementado | - |
| 02 | PostgreSQL + PostGIS | ✅ Implementado | - |
| 03 | UUID como PK | ✅ Implementado | - |
| 04 | Decimal para montos | ✅ Implementado | - |
| 05 | Auditoría append-only | ✅ Implementado | - |
| 06 | API REST versionada | ✅ Implementado | - |
| 07 | Frontend Angular | ✅ Implementado | - |
| 08 | Celery + Redis | ⚠️ Configurado, sin implementar | Alta |
| 09 | MinIO S3 | ❌ Pendiente | Alta |
| 10 | Keycloak OIDC | ❌ Pendiente | Alta |
| 11 | GeoServer | ❌ Pendiente | Alta |
| 12 | SRID configurable | ⚠️ Parcial | Media |
| 13 | Versionado de planes | ❌ Pendiente | Alta |

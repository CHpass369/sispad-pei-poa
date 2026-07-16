# Requisitos No Funcionales — SISPAD–PEI–POA

> **Fase 0**: Documento generado como parte del análisis inicial del proyecto.
> **Fecha**: 2026-07-16

---

## RNF-01: Usabilidad

| ID | Descripción | Prioridad |
|----|-------------|-----------|
| RNF-01.1 | Interfaz en español con posibilidad de internacionalización futura | Alta |
| RNF-01.2 | Diseño responsive (escritorio + tablet + móvil) | Alta |
| RNF-01.3 | Menú contextual según permisos del usuario | Alta |
| RNF-01.4 | Breadcrumbs visibles en toda la aplicación | Media |
| RNF-01.5 | Tablas con filtros, ordenamiento, búsqueda y paginación | Alta |
| RNF-01.6 | Guardado automático de borradores en formularios largos | Alta |
| RNF-01.7 | Diálogos de confirmación antes de acciones destructivas | Alta |
| RNF-01.8 | Estados de carga visibles (skeleton/spinner) | Alta |
| RNF-01.9 | Mensajes de error claros y accionables | Alta |
| RNF-01.10 | Navegación mediante teclado | Media |
| RNF-01.11 | Modo claro y oscuro (opcional) | Baja |

## RNF-02: Rendimiento

| ID | Descripción | Prioridad |
|----|-------------|-----------|
| RNF-02.1 | Tiempo de respuesta API < 500ms para consultas comunes | Alta |
| RNF-02.2 | Reportes pesados ejecutados de forma asíncrona (Celery) | Alta |
| RNF-02.3 | Importaciones Excel procesadas en segundo plano | Alta |
| RNF-02.4 | Paginación obligatoria en endpoints de listado | Alta |
| RNF-02.5 | Índices de base de datos en columnas de filtrado y búsqueda | Alta |
| RNF-02.6 | Caché con Redis para consultas de alta frecuencia | Media |
| RNF-02.7 | Compresión de respuestas JSON | Media |

## RNF-03: Seguridad

| ID | Descripción | Prioridad |
|----|-------------|-----------|
| RNF-03.1 | Autenticación OIDC con Keycloak | Alta |
| RNF-03.2 | HTTPS obligatorio en producción | Alta |
| RNF-03.3 | CORS restrictivo | Alta |
| RNF-03.4 | Rate limiting en APIs públicas | Alta |
| RNF-03.5 | Validación de tipos MIME y tamaño máximo de archivos | Alta |
| RNF-03.6 | Protección contra inyección SQL, XSS y clickjacking | Alta |
| RNF-03.7 | Encabezados de seguridad (HSTS, CSP, X-Frame-Options) | Alta |
| RNF-03.8 | Secretos por variables de entorno | Alta |
| RNF-03.9 | Políticas de sesión y revocación de tokens | Alta |
| RNF-03.10 | Registro de intentos fallidos de autenticación | Alta |
| RNF-03.11 | Principio de mínimo privilegio en RBAC + ABAC | Alta |
| RNF-03.12 | Logs sin datos sensibles | Alta |

## RNF-04: Fiabilidad y Disponibilidad

| ID | Descripción | Prioridad |
|----|-------------|-----------|
| RNF-04.1 | Health checks en todos los servicios | Alta |
| RNF-04.2 | Respaldos automáticos de base de datos, MinIO, GeoServer | Alta |
| RNF-04.3 | Scripts de restauración documentados | Alta |
| RNF-04.4 | Transacciones atómicas en operaciones críticas | Alta |
| RNF-04.5 | Idempotencia en endpoints de operaciones críticas | Media |

## RNF-05: Mantenibilidad

| ID | Descripción | Prioridad |
|----|-------------|-----------|
| RNF-05.1 | Código organizado en aplicaciones Django modulares | Alta |
| RNF-05.2 | Lógica de negocio en servicios y validadores (no en views/serializers) | Alta |
| RNF-05.3 | Documentación OpenAPI de todos los endpoints (DRF spectacular) | Alta |
| RNF-05.4 | Logging estructurado con rotación | Alta |
| RNF-05.5 | Uso de type hints en Python | Media |
| RNF-05.6 | TypeScript estricto en frontend | Alta |

## RNF-06: Portabilidad

| ID | Descripción | Prioridad |
|----|-------------|-----------|
| RNF-06.1 | Despliegue mediante Docker Compose (desarrollo y producción) | Alta |
| RNF-06.2 | Variables de entorno para configuración | Alta |
| RNF-06.3 | Volúmenes persistentes para datos | Alta |
| RNF-06.4 | Preparado para servidor Linux | Alta |
| RNF-06.5 | Arquitectura multitenant preparada para otros GAMs | Media |
| RNF-06.6 | SRID institucional configurable (no hardcodeado) | Alta |

## RNF-07: Pruebas

| ID | Descripción | Prioridad |
|----|-------------|-----------|
| RNF-07.1 | Cobertura ≥80% en servicios críticos | Alta |
| RNF-07.2 | Cobertura ≥90% en reglas presupuestarias | Alta |
| RNF-07.3 | Cobertura ≥90% en reglas de aprobación y permisos críticos | Alta |
| RNF-07.4 | Pruebas unitarias de servicios, validaciones, permisos, API y workflow | Alta |
| RNF-07.5 | Pruebas de componentes Angular, formularios, guards y servicios | Alta |
| RNF-07.6 | 15 casos E2E mínimos con Playwright | Media |

## RNF-08: Integridad de Datos

| ID | Descripción | Prioridad |
|----|-------------|-----------|
| RNF-08.1 | UUID como identificador primario público | Alta |
| RNF-08.2 | Decimal para montos (nunca float) | Alta |
| RNF-08.3 | Hash SHA-256 en documentos adjuntos | Alta |
| RNF-08.4 | Auditoría append-only de todas las modificaciones | Alta |
| RNF-08.5 | Inmutabilidad de versiones aprobadas | Alta |
| RNF-08.6 | Fuente única de información (no duplicar datos) | Alta |

## RNF-09: Interfaces Externas

| ID | Descripción | Prioridad |
|----|-------------|-----------|
| RNF-09.1 | API REST versionada bajo `/api/v1/` | Alta |
| RNF-09.2 | Respuestas de error consistentes con códigos HTTP correctos | Alta |
| RNF-09.3 | Servicios WMS/WFS de GeoServer | Alta |
| RNF-09.4 | Almacenamiento S3 compatible con MinIO | Alta |
| RNF-09.5 | OIDC con Keycloak | Alta |

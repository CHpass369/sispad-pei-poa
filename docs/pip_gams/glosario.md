# Glosario PIP-GAMS

**Plataforma Integral de Planificación del Gobierno Autónomo Municipal de
Sacaba (PIP-GAMS).** Documento rector del WP-01. Define la nomenclatura
oficial de la plataforma. Cualquier término que no esté aquí debe consultarse
con el responsable de arquitectura antes de usarse en código, API o UI.

---

## 1. Nivel plataforma

| Término | Definición |
|---|---|
| **PIP-GAMS** | Plataforma integral de planificación del GAM Sacaba. Contenedor de los sistemas SIS-PE, SIS-POA y SIS-PRO sobre un núcleo transversal común. |
| **Núcleo transversal (Plataforma)** | Capacidades compartidas por los tres SIS: IAM (identidad/roles/capacidades/alcances), organización, periodos/ciclos, catálogos, normativa, codificación, territorio, workflow, documentos, notificaciones, auditoría, reportes e interoperabilidad. |
| **Sistema (SIS)** | Agrupación funcional dentro de la plataforma con sus propios dashboards, rutas y dominios de datos. |
| **Módulo** | Unidad de código (app Django / feature Angular) dentro de un SIS o del núcleo. |
| **Legacy** | Cualquier modelo, endpoint o componente existente previo a V2, preservado hasta su retiro controlado. |

## 2. Sistemas

### SIS-PE — Sistema de Planificación Estratégica

Gestión de instrumentos de planificación y su cadena estratégica:

- instrumentos y metodologías;
- marco superior (PGDESA/PGDES, PDESA/PDES, planes sectoriales, compromisos);
- diagnóstico integral;
- participación y demanda social;
- formulación PAD y PEI;
- articulación estratégica;
- banco municipal de indicadores y metas;
- territorialización;
- programación plurianual;
- seguimiento y evaluación estratégica.

### SIS-POA — Sistema de Planificación Operativa Anual

Gestión de la cadena operativa anual:

- POA institucional;
- POAU (por unidad organizacional);
- acciones de corto plazo;
- operaciones, actividades y tareas;
- recursos, techos y presupuesto;
- programación física-financiera;
- modificaciones;
- seguimiento operativo.

### SIS-PRO — Sistema de Gestión del Ciclo del Proyecto

Gestión del ciclo completo de proyectos de inversión:

- cartera;
- condiciones previas;
- preinversión (ITCP/EDTP y equivalentes);
- formulación y costos;
- contratación;
- ejecución;
- supervisión/fiscalización;
- cierre y evaluación.

## 3. Conceptos de planificación

| Término | Definición oficial |
|---|---|
| **PGDESA / PGDES** | Plan General de Desarrollo Económico y Social (departamental/nacional). Instrumento superior de referencia. |
| **PDESA / PDES** | Plan de Desarrollo Económico y Social (departamental/sectorial). Instrumento superior de referencia. |
| **PAD** | Plan Anual de Desarrollo del municipio. Instrumento estratégico de mediano plazo del GAMS. |
| **PEI** | Plan Estratégico Institucional del GAMS. Contribución institucional a resultados territoriales; **no duplica el PAD**. |
| **POA** | Plan Operativo Anual institucional consolidado. |
| **POAU** | Plan Operativo Anual por Unidad (organizacional). |
| **Acción de corto plazo** | Descomposición anual del PEI/PAD que vincula estrategia con operación. |
| **Operación / Actividad / Tarea** | Jerarquía operativa canónica del SIS-POA (operación → actividad → tarea). |
| **Instrumento de planificación** | Entidad versionable que materializa un plan (PAD, PEI, PDESA…). |
| **Metodología** | Conjunto parametrizable de tipos de nodo, vínculos y reglas de validación aplicables a un instrumento. |
| **Versión** | Estado inmutable aprobado de un instrumento o metodología. |
| **Nodo estratégico** | Elemento de la jerarquía de un instrumento (eje, lineamiento, resultado, producto…). |
| **Vínculo estratégico** | Relación articulada entre dos nodos (PAD→PEI, PEI→POA…). |
| **Proyecto (SIS-PRO)** | Inversión gestionada a lo largo de su ciclo (idea→cierre). |
| **Banco Municipal de Indicadores** | Catálogo único de indicadores definido una sola vez y vinculado a nodos, POA o proyectos. |

## 4. Núcleo transversal

| Término | Definición |
|---|---|
| **IAM** | Identidad y acceso: autenticación (OIDC/Keycloak) + autorización de negocio (roles, capacidades, alcances). |
| **Capacidad** | Permiso atómico expresado como `<sistema>.<dominio>.<accion>` (p. ej. `sis_pe.pad.edit`). |
| **Alcance** | Restricción de una asignación de rol a un ámbito organizacional, territorial o temporal. |
| **Ciclo / Periodo** | Gestiones fiscales y etapas del ciclo de formulación (reutilizable por todos los SIS). |
| **Workflow** | Definiciones/instancias de flujos de aprobación configurables por instrumento. |
| **Auditoría** | Registro append-only de eventos relevantes del dominio. |
| **LegacyMigrationMap** | Tabla técnica que traza cada registro legacy hacia su destino V2 durante la migración. |

## 5. Reglas de nomenclatura

1. Los nombres públicos (UI, API) usan los términos de este glosario en
   español, sin siglas heredadas (PTDI/PDES) como semántica principal; estas
   quedan como compatibilidad histórica.
2. Los identificadores técnicos (modelos, tablas, claves) usan el término
   oficial; los nombres legacy no se renombran hasta su retiro (ver
   `domain_map.md`).
3. Los códigos de capacidad siguen el patrón `<sistema>.<dominio>.<accion>`.
4. Rutas API v2: `/api/v2/{sis-pe|sis-poa|sis-pro|platform|me}/...`.

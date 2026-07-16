# Requisitos Funcionales — SISPAD–PEI–POA

> **Fase 0**: Documento generado como parte del análisis inicial del proyecto.
> **Fecha**: 2026-07-16

---

## RF-01: Gestión de Institución y Organización

| ID | Descripción | Prioridad | App |
|----|-------------|-----------|-----|
| RF-01.1 | Registrar institución con datos generales (código, nombre, sigla, tax_id, geometría oficial) | Alta | `organizacion` |
| RF-01.2 | Gestionar estructura organizacional jerárquica con tipos parametrizables (MAE, secretaría, dirección, jefatura, unidad, subunidad) | Alta | `organizacion` |
| RF-01.3 | Mantener vigencia temporal de unidades organizacionales (fecha_desde, fecha_hasta) | Alta | `organizacion` |
| RF-01.4 | Gestionar Direcciones Administrativas y Unidades Ejecutoras por gestión | Alta | `organizacion` |
| RF-01.5 | Asignar usuarios a unidades organizacionales con rol de responsable POA | Alta | `organizacion` |
| RF-01.6 | No eliminar unidades que participaron en gestiones anteriores — solo inactivar | Alta | `organizacion` |

## RF-02: Gestión de Usuarios, Roles y Permisos

| ID | Descripción | Prioridad | App |
|----|-------------|-----------|-----|
| RF-02.1 | Autenticar usuarios mediante OIDC con Keycloak | Alta | `accounts` |
| RF-02.2 | Gestionar roles parametrizables (Superadmin, MAE, Admin POA, Planificación, Presupuesto, Inversión, Secretario, Director, Jefe, Técnico, Seguimiento, Evaluador, Auditor, Control Social, Consulta) | Alta | `accounts` |
| RF-02.3 | Implementar RBAC + ABAC (permisos por rol + institución + unidad + gestión + módulo + territorio + estado + propiedad + delegación) | Alta | `accounts` |
| RF-02.4 | Los técnicos editan solo registros de su unidad; jefes revisan dependientes; secretaría revisa direcciones; presupuesto valida solo montos | Alta | `accounts` |
| RF-02.5 | Control social accede solo a información aprobada; consulta pública solo al portal público | Alta | `accounts` |
| RF-02.6 | Delegaciones temporales y suplencias | Media | `workflow` |

## RF-03: Gestiones y Ciclos de Planificación

| ID | Descripción | Prioridad | App |
|----|-------------|-----------|-----|
| RF-03.1 | Gestionar gestión fiscal con estados (preparación, abierta, formulación, revisión, consolidación, aprobación, cerrada, archivada) | Alta | `gestion` |
| RF-03.2 | Configurar horizonte plurianual por gestión | Alta | `gestion` |
| RF-03.3 | Gestionar ciclos y etapas de formulación con fechas de apertura y cierre | Alta | `gestion` |
| RF-03.4 | Validar que el año de gestión esté dentro del horizonte plurianual | Alta | `gestion` |

## RF-04: Planes y Jerarquía Estratégica

| ID | Descripción | Prioridad | App |
|----|-------------|-----------|-----|
| RF-04.1 | Gestionar instrumentos de planificación (PGDESA, PDESA, PSD, PAD, PEI, POA, POAU) | Alta | `planificacion` |
| RF-04.2 | Versionar planes con inmutabilidad de versiones aprobadas | Alta | `planificacion` |
| RF-04.3 | Implementar nodos estratégicos parametrizables con árbol de profundidad variable | Alta | `planificacion` |
| RF-04.4 | Soportar tipos de nodo: eje, objetivo de impacto/efecto, política, lineamiento, resultado, acción, producto, programa, proyecto, ACP | Alta | `planificacion` |
| RF-04.5 | Al modificar una versión aprobada, crear nueva versión y mantener vínculo con anterior | Alta | `planificacion` |

## RF-05: Matriz de Articulación

| ID | Descripción | Prioridad | App |
|----|-------------|-----------|-----|
| RF-05.1 | Articular PGDESA → PDESA → PAD → PEI → POA → POAU | Alta | `planificacion` |
| RF-05.2 | Mostrar vista de árbol, matricial y grafo de articulación | Alta | `planificacion` |
| RF-05.3 | Buscar por código o descripción; filtrar por instrumento | Alta | `planificacion` |
| RF-05.4 | Identificar acciones sin articulación y duplicidades | Alta | `planificacion` |
| RF-05.5 | Exportar matriz de articulación a Excel y PDF | Media | `planificacion` |
| RF-05.6 | Bloquear acción POA sin acción PEI asociada | Alta | `planificacion` |
| RF-05.7 | Bloquear acción PEI sin relación PAD (excepto excepción autorizada) | Alta | `planificacion` |
| RF-05.8 | No permitir articulaciones circulares ni relaciones duplicadas activas | Alta | `planificacion` |

## RF-06: Gestión del PAD

| ID | Descripción | Prioridad | App |
|----|-------------|-----------|-----|
| RF-06.1 | Gestionar sectores, políticas y lineamientos estratégicos del PAD | Alta | `pad` |
| RF-06.2 | Gestionar resultados territoriales con indicador, línea base, meta quinquenal y programación física/financiera | Alta | `pad` |
| RF-06.3 | Gestionar productos territoriales vinculados a resultados | Alta | `pad` |
| RF-06.4 | Articular resultados PAD con PGDESA/PDESA/PDS/ODS/NDC/NDT (Matriz B - SIPEB) | Alta | `pad` |
| RF-06.5 | Generar Matriz A, Matriz B, Presupuesto quinquenal y cartera de programas/proyectos | Media | `pad` |

## RF-07: Gestión del PEI

| ID | Descripción | Prioridad | App |
|----|-------------|-----------|-----|
| RF-07.1 | Gestionar misión, visión, valores institucionales y objetivos estratégicos | Alta | `planificacion` |
| RF-07.2 | Gestionar acciones de mediano plazo (AMP) con indicadores, metas, responsable | Alta | `planificacion` |
| RF-07.3 | Gestionar acciones de corto plazo (ACP) articuladas a AMP | Alta | `planificacion` |
| RF-07.4 | Programación física y presupuesto plurianual por acción PEI | Alta | `planificacion` |
| RF-07.5 | Versionado de acciones PEI aprobadas | Alta | `planificacion` |

## RF-08: Apertura del POA

| ID | Descripción | Prioridad | App |
|----|-------------|-----------|-----|
| RF-08.1 | El administrador POA puede crear gestión, configurar cronograma, definir etapas, establecer fechas límite | Alta | `gestion` |
| RF-08.2 | Publicar instructivos; abrir/cerrar formulación; habilitar reapertura con justificación | Alta | `gestion` |
| RF-08.3 | Copiar información válida de gestión anterior; migrar acciones PEI | Alta | `gestion` |
| RF-08.4 | Definir unidades obligadas a formular POAU | Alta | `gestion` |
| RF-08.5 | Mostrar % de avance por unidad, estado del POAU, observaciones pendientes, unidades retrasadas | Alta | `poau` |

## RF-09: Techos Presupuestarios

| ID | Descripción | Prioridad | App |
|----|-------------|-----------|-----|
| RF-09.1 | Gestionar techo presupuestario por fuente/organismo con versionado | Alta | `techos` |
| RF-09.2 | Distribuir techo a nivel de DA/UE/Unidad/Programa con control de saldos | Alta | `techos` |
| RF-09.3 | Registrar movimientos de techo (asignación, incremento, reducción, transferencia, reserva, liberación, ajuste, reversión) | Alta | `techos` |
| RF-09.4 | Validar que presupuesto formulado ≤ techo disponible | Alta | `techos` |
| RF-09.5 | Utilizar Decimal (nunca float); moneda en bolivianos | Alta | `techos` |

## RF-10: Formulación POAU

| ID | Descripción | Prioridad | App |
|----|-------------|-----------|-----|
| RF-10.1 | Implementar asistente de formulación en 8 pasos (unidad → resultado → operaciones → cronograma → presupuesto → territorio → riesgos → validación) | Alta | `poau` |
| RF-10.2 | Gestionar POAU con estado (12 estados: borrador → ... → cerrado) | Alta | `poau` |
| RF-10.3 | Gestionar operaciones, actividades y tareas con ponderaciones | Alta | `poau` |
| RF-10.4 | La suma de ponderaciones de operaciones debe ser 100% | Alta | `poau` |
| RF-10.5 | Territorializar actividades con geometrías PostGIS | Alta | `territorio` |
| RF-10.6 | El POA consolidado no debe ser editable sin proceso formal de modificación | Alta | `poau` |

## RF-11: Presupuesto y Líneas Presupuestarias

| ID | Descripción | Prioridad | App |
|----|-------------|-----------|-----|
| RF-11.1 | Gestionar 13 clasificadores presupuestarios versionados | Alta | `catalogos` |
| RF-11.2 | Gestionar línea presupuestaria con llave completa (Entidad+DA+UE+Programa+Proyecto+Actividad+Finalidad+Fuente+Organismo+Objeto+Importe) | Alta | `presupuesto` |
| RF-11.3 | Validar consistencia: suma líneas = presupuesto actividad = POAU = POA consolidado | Alta | `presupuesto` |
| RF-11.4 | Registrar importe plurianual y de gestión anterior | Alta | `presupuesto` |
| RF-11.5 | Mantener precisión de 2 decimales en todos los montos | Alta | `presupuesto` |

## RF-12: Auxiliar Pluri

| ID | Descripción | Prioridad | App |
|----|-------------|-----------|-----|
| RF-12.1 | Generar automáticamente desde líneas presupuestarias aprobadas | Alta | Nuevo |
| RF-12.2 | Mostrar: unidad, acción PEI/POA, operación, actividad, objeto gasto, fuente, organismo, gestión, monto anual/plurianual, total | Alta | Nuevo |
| RF-12.3 | Exportar a Excel; comparar contra presupuesto institucional | Media | Nuevo |
| RF-12.4 | Detectar diferencias, registros sin articulación, partidas sin memoria de cálculo | Media | Nuevo |

## RF-13: Banco de Programas y Proyectos

| ID | Descripción | Prioridad | App |
|----|-------------|-----------|-----|
| RF-13.1 | Gestionar proyectos de inversión con código SISIN y etapas (idea → perfil → preinversión → diseño → inversión → ejecución → cierre → operación) | Alta | `inversion` |
| RF-13.2 | Priorizar proyectos (continuidad → financiamiento asegurado → estratégicos nuevos → otros) | Alta | `inversion` |
| RF-13.3 | Programación plurianual de proyectos | Alta | `inversion` |

## RF-14: Flujo de Revisión y Aprobación

| ID | Descripción | Prioridad | App |
|----|-------------|-----------|-----|
| RF-14.1 | Flujo: borrador → revisión interna → jefe → dirección → secretaría → planificación → presupuesto → inversión → consolidación → MAE → aprobado | Alta | `workflow` |
| RF-14.2 | Gestionar observaciones con tipo (forma/fondo/legal/presupuestaria/técnica), severidad y estado | Alta | `workflow` |
| RF-14.3 | Registrar historial de cambios con comparación antes/después | Alta | `workflow` |
| RF-14.4 | Soporte para delegaciones temporales y suplencias | Media | `workflow` |
| RF-14.5 | No permitir auto-aprobación cuando exista conflicto de funciones | Alta | `workflow` |

## RF-15: Modificaciones y Reformulaciones

| ID | Descripción | Prioridad | App |
|----|-------------|-----------|-----|
| RF-15.1 | Gestionar solicitudes de modificación con tipo (meta, operación, reprogramación, presupuesto, fuente, etc.) | Alta | Nuevo |
| RF-15.2 | Nunca sobrescribir versión aprobada — crear nueva versión | Alta | Nuevo |
| RF-15.3 | Mantener valores anteriores y registrar impacto físico/financiero/estratégico | Alta | Nuevo |

## RF-16: Seguimiento Físico y Financiero

| ID | Descripción | Prioridad | App |
|----|-------------|-----------|-----|
| RF-16.1 | Registrar ejecución física y financiera por periodo (mensual, trimestral, semestral, anual) | Alta | `poau` |
| RF-16.2 | Calcular eficacia física, ejecución financiera, eficiencia, desviación y proyección al cierre | Alta | `poau` |
| RF-16.3 | Semáforo configurable (verde ≥80%, amarillo 50-79%, rojo <50%) | Alta | `poau` |
| RF-16.4 | Generar alertas (ejecución baja, sobreejecución, meta vencida, evidencia faltante, etc.) | Alta | Nuevo |

## RF-17: Acciones Correctivas

| ID | Descripción | Prioridad | App |
|----|-------------|-----------|-----|
| RF-17.1 | Gestionar acciones correctivas vinculadas a desviaciones de seguimiento | Alta | Nuevo |
| RF-17.2 | Controlar cumplimiento de compromisos correctivos y emitir alertas | Alta | Nuevo |

## RF-18: Evaluación

| ID | Descripción | Prioridad | App |
|----|-------------|-----------|-----|
| RF-18.1 | Evaluar planes por tipo (anual, medio término, final, específica) | Alta | Nuevo |
| RF-18.2 | Evaluar por criterios (eficacia, eficiencia, efectividad, pertinencia, impacto, sostenibilidad) | Alta | Nuevo |
| RF-18.3 | Generar brechas, recomendaciones, lecciones aprendidas | Media | Nuevo |

## RF-19: Gestión Documental

| ID | Descripción | Prioridad | App |
|----|-------------|-----------|-----|
| RF-19.1 | Almacenar documentos en MinIO con hash SHA-256 | Alta | `documentos` |
| RF-19.2 | Controlar versiones y permisos de descarga | Alta | `documentos` |
| RF-19.3 | Tipos documentales: informe, acta, resolución, ley, contrato, evidencia, etc. | Media | `documentos` |

## RF-20: Componente Geográfico

| ID | Descripción | Prioridad | App |
|----|-------------|-----------|-----|
| RF-20.1 | Almacenar geometrías en PostGIS con EPSG:32719 (oficial) y publicar en EPSG:4326/3857 (web) | Alta | `territorio` |
| RF-20.2 | Gestionar distritos, OTB, comunidades, zonas con geometría | Alta | `territorio` |
| RF-20.3 | Vincular acciones/proyectos con geometrías (Point, LineString, Polygon) | Alta | `territorio` |
| RF-20.4 | Publicar capas WMS/WFS mediante GeoServer | Alta | `territorio` |
| RF-20.5 | Mapa de inversiones, presupuesto por distrito, análisis urbano-rural | Media | `territorio` |

## RF-21: Reportes

| ID | Descripción | Prioridad | App |
|----|-------------|-----------|-----|
| RF-21.1 | Generar 25 reportes mínimos en PDF, XLSX, CSV | Alta | `reportes` |
| RF-21.2 | Reportes pesados mediante Celery | Media | `reportes` |
| RF-21.3 | Dashboard MAE, Planificación, Presupuesto, Unidad, Seguimiento | Alta | `reportes` |

## RF-22: Portal Público

| ID | Descripción | Prioridad | App |
|----|-------------|-----------|-----|
| RF-22.1 | Portal público con POA aprobado, presupuesto agregado, programas, proyectos, ejecución, mapas | Alta | Nuevo |
| RF-22.2 | No publicar información personal, borradores, documentos confidenciales | Alta | Nuevo |

## RF-23: Notificaciones

| ID | Descripción | Prioridad | App |
|----|-------------|-----------|-----|
| RF-23.1 | Notificaciones internas y por email (apertura, vencimiento, POAU enviado/observado/aprobado, alertas) | Alta | Nuevo |
| RF-23.2 | Marcar como leída / no leída / atendida | Media | Nuevo |

## RF-24: Importación Excel

| ID | Descripción | Prioridad | App |
|----|-------------|-----------|-----|
| RF-24.1 | Importar matrices A/B, estructura de gasto, POAU, seguimiento, catálogos | Alta | `core` |
| RF-24.2 | Mostrar vista previa, errores y advertencias antes de confirmar | Alta | `core` |
| RF-24.3 | Ejecutar importación de forma asíncrona y generar reporte final | Media | `core` |

## RF-25: Auditoría

| ID | Descripción | Prioridad | App |
|----|-------------|-----------|-----|
| RF-25.1 | Registro append-only de eventos (creación, modificación, eliminación lógica, aprobación, login, exportación) | Alta | `auditoria` |
| RF-25.2 | Almacenar datos previos/posteriores en JSON | Alta | `auditoria` |
| RF-25.3 | No permitir editar ni eliminar eventos de auditoría desde la aplicación | Alta | `auditoria` |

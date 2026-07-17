# Referencia API — SISPAD-PEI-POA

Base URL: `http://localhost:8000/api/v1/`

Autenticacion: `Authorization: Bearer <jwt_token>`

Formato de respuesta paginada:
```json
{
  "count": N,
  "next": "url",
  "previous": "url",
  "results": [...]
}
```

---

## Autenticacion

### POST `/auth/login/`
Iniciar sesion con email y password.

**Request:**
```json
{
  "email": "usuario@correo.com",
  "password": "contrasena"
}
```

**Response 200:**
```json
{
  "access": "<jwt_access_token>",
  "refresh": "<jwt_refresh_token>",
  "user": {
    "id": "uuid",
    "email": "usuario@correo.com",
    "first_name": "Nombre",
    "last_name": "Apellido",
    "roles": ["superadmin"],
    "roles_detalle": [
      {"codigo": "superadmin", "nombre": "Super Administrador"}
    ]
  }
}
```

### POST `/auth/token/refresh/`
Renovar access token.

**Request:**
```json
{
  "refresh": "<jwt_refresh_token>"
}
```

**Response 200:**
```json
{
  "access": "<nuevo_jwt_access_token>"
}
```

### GET `/auth/usuarios/me/`
Obtener perfil del usuario autenticado.

**Response 200:**
```json
{
  "id": "uuid",
  "email": "usuario@correo.com",
  "first_name": "Nombre",
  "last_name": "Apellido",
  "cargo": "Cargo",
  "telefono": "70123456",
  "roles": ["superadmin"],
  "roles_detalle": [
    {"codigo": "superadmin", "nombre": "Super Administrador"}
  ],
  "activo": true
}
```

### POST `/auth/usuarios/{id}/cambiar_password/`
Cambiar contrasena de un usuario.

**Request:**
```json
{
  "password": "nueva_contrasena"
}
```

### GET/POST `/auth/roles/`
CRUD de roles del sistema.

### GET/POST `/auth/usuarios/`
CRUD de usuarios.

---

## Catalogos

### GET `/catalogos/fuentes-financiamiento/`
Lista de fuentes de financiamiento (CT, RE, ORE, IDH, TGN).

### GET `/catalogos/organismos-financiadores/`
Lista de organismos financiadores.

### GET `/catalogos/objetos-gasto/`
Lista de objetos de gasto (clasificacion presupuestaria).

### GET `/catalogos/unidades-medida/`
Lista de unidades de medida para indicadores.

### GET `/catalogos/tipos-operacion/`
Lista de tipos de operacion.

### GET `/catalogos/tipos-producto/`
Lista de tipos de producto (terminal, intermedio).

### GET `/catalogos/finalidades-funciones/`
Lista de finalidad/funcion.

### GET `/catalogos/entidades-transferencia/`
Lista de entidades de transferencia.

### GET `/catalogos/categorias-programaticas/`
Categorias programaticas municipales (34 semillas).

---

## Organizacion

### GET/POST `/organizacion/tipos-unidad/`
CRUD de tipos de unidad organizacional.

### GET/POST `/organizacion/unidades/`
CRUD de unidades organizacionales.

**Filtros:**
- `?gestion=2026`
- `?tipo=<tipo_id>`
- `?padre=<padre_id>`

### GET/POST `/organizacion/direcciones-administrativas/`
CRUD de direcciones administrativas (SMFA, CM, SMPDT, etc.).

### GET/POST `/organizacion/unidades-ejecutoras/`
CRUD de unidades ejecutoras.

**Filtros:**
- `?da=<da_id>`
- `?gestion=2026`

### GET/POST `/organizacion/asignaciones-usuario-unidad/`
Asignacion de usuarios a unidades.

---

## Gestion

### GET/POST `/gestion/gestiones/`
CRUD de gestiones fiscales.

### GET/POST `/gestion/gestiones/{id}/`
Detalle de gestion.

**Estados del ciclo de vida:**
`preparacion → formulacion → revision → consolidacion → aprobacion → ejecucion → evaluacion → archivada`

---

## Planificacion

### GET/POST `/planificacion/planes/`
CRUD de planes (PEI, PTDI, PDES, Sectorial, Municipal).

**Filtros:**
- `?tipo=pei`
- `?gestion_inicio=2024`
- `?gestion_fin=2028`

### GET/POST `/planificacion/nodos/`
CRUD de nodos de planificacion (arbol jerarquico).

**Filtros:**
- `?plan=<plan_id>`
- `?nivel=accion_mediano`
- `?padre=<nodo_padre_id>`

### GET/POST `/planificacion/acciones-mediano-plazo/`
CRUD de acciones de mediano plazo (AMP).

**Filtros:**
- `?nodo_planificacion=<nodo_id>`

### GET/POST `/planificacion/acciones-corto-plazo/`
CRUD de acciones de corto plazo (ACP).

**Filtros:**
- `?accion_mediano_plazo=<amp_id>`
- `?unidad_responsable=<unidad_id>`
- `?gestion=2026`

### GET/POST `/planificacion/plan-versions/`
CRUD de versiones de plan.

**Estados:** `borrador → aprobado → obsoleto`

### GET/POST `/planificacion/articulaciones/`
Articulaciones entre nodos de planificacion.

---

## PAD (Plan Anual de Desarrollo)

### GET/POST `/pad/sectores/`
CRUD de sectores del PAD (salud, educacion, infraestructura).

### GET/POST `/pad/politicas/`
CRUD de politicas del PAD.

**Filtros:**
- `?gestion=2026`

### GET/POST `/pad/lineamientos/`
CRUD de lineamientos estrategicos.

**Filtros:**
- `?politica=<politica_id>`
- `?gestion=2026`

### GET/POST `/pad/resultados/`
CRUD de resultados territoriales.

**Estados:** `borrador → enviado → aprobado / rechazado`

**Filtros:**
- `?lineamiento=<lineamiento_id>`
- `?sector=<sector_id>`
- `?gestion=2026`
- `?estado=aprobado`

### GET/POST `/pad/productos/`
CRUD de productos territoriales.

**Filtros:**
- `?resultado=<resultado_id>`
- `?gestion=2026`

### GET/POST `/pad/programaciones/`
CRUD de programaciones anuales PAD (fisica/financiera).

### GET/POST `/pad/articulaciones-sipeb/`
Articulacion del PAD con instrumentos nacionales (PGDESA, PDES, ODS, NDC, NDT).

---

## POAU (Plan Operativo Anual por Unidad)

### GET/POST `/poau/poaus/`
CRUD de POAUs.

**Estados:** `borrador → enviado → aprobado / rechazado`

**Filtros:**
- `?gestion=2026`
- `?unidad=<unidad_id>`
- `?estado=aprobado`

### GET/POST `/poau/poaus/{id}/actividades/`
CRUD de actividades de un POAU.

### GET/POST `/poau/ejecuciones-fisicas/`
CRUD de ejecuciones fisicas.

**Filtros:**
- `?actividad=<actividad_id>`
- `?periodo=2026-Q1`
- `?tipo_periodo=trimestral`

### GET/POST `/poau/ejecuciones-financieras/`
CRUD de ejecuciones financieras.

**Filtros:**
- `?actividad=<actividad_id>`
- `?periodo=2026-Q1`
- `?tipo_periodo=trimestral`

---

## Techos Presupuestarios

### GET/POST `/techos/techos/`
CRUD de techos presupuestarios.

**Filtros:**
- `?gestion=2026`
- `?fuente=<fuente_id>`
- `?organismo=<organismo_id>`

### GET/POST `/techos/distribuciones/`
CRUD de distribuciones de techo.

**Filtros:**
- `?techo=<techo_id>`
- `?da=<da_id>`
- `?ue=<ue_id>`
- `?unidad=<unidad_id>`
- `?programa=<programa_id>`

### GET/POST `/techos/movimientos/`
CRUD de movimientos de techo.

**Tipos de movimiento:** `asignacion`, `incremento`, `reduccion`, `transferencia`, `reserva`, `liberacion`, `ajuste`, `reversion`

**Filtros:**
- `?techo=<techo_id>`
- `?movement_type=transferencia`

---

## Presupuesto

### GET/POST `/presupuesto/programas/`
CRUD de programas presupuestarios.

**Filtros:**
- `?gestion=2026`

### GET/POST `/presupuesto/proyectos/`
CRUD de proyectos presupuestarios.

### GET/POST `/presupuesto/actividades-presupuestarias/`
CRUD de actividades presupuestarias.

### GET/POST `/presupuesto/lineas/`
CRUD de lineas presupuestarias (llave completa).

**Filtros:**
- `?gestion=2026`
- `?programa=<programa_id>`
- `?fuente=<fuente_id>`
- `?objeto_gasto=<objeto_id>`
- `?ue=<ue_id>`

---

## Indicadores

### GET/POST `/indicadores/indicadores/`
CRUD de indicadores.

**Tipos de comportamiento:** `acumulable`, `no_acumulable`, `promedio`, `hito`, `porcentaje`, `cualitativo`

**Filtros:**
- `?tipo_comportamiento=acumulable`
- `?activo=true`

### GET/POST `/indicadores/metas-programadas/`
CRUD de metas programadas con programacion trimestral.

**Filtros:**
- `?indicador=<indicador_id>`
- `?gestion=2026`

### GET/POST `/indicadores/operaciones/`
CRUD de operaciones (vinculadas a ACP).

### GET/POST `/indicadores/tareas/`
CRUD de tareas (vinculadas a operaciones).

### GET/POST `/indicadores/productos-esperados/`
CRUD de productos esperados.

### GET/POST `/indicadores/medios-verificacion/`
CRUD de medios de verificacion.

### GET/POST `/indicadores/supuestos/`
CRUD de supuestos criticos.

---

## Inversion

### GET/POST `/inversion/proyectos/`
CRUD de proyectos de inversion.

**Campos:** codigo_interno, nombre, codigo_sisin, prioridad, etapa, costo_total

**Filtros:**
- `?gestion=2026`
- `?prioridad=alta`
- `?etapa=ejecucion`

---

## Workflow

### GET/POST `/workflow/envios-formulacion/`
CRUD de envios de formulacion.

**Filtros:**
- `?unidad=<unidad_id>`
- `?gestion=2026`

### GET/POST `/workflow/revisiones/`
CRUD de revisiones.

**Tipos:** `planificacion`, `presupuesto`, `inversion`, `juridica`

**Estados:** `pendiente → en_curso → completada / devuelta`

### GET/POST `/workflow/observaciones/`
CRUD de observaciones.

**Tipos:** `forma`, `fondo`, `legal`, `presupuestaria`, `tecnica`, `documental`

**Severidades:** `leve`, `moderada`, `grave`

**Estados:** `abierta → respondida → aceptada / rechazada → cerrada`

**Filtros:**
- `?revision=<revision_id>`
- `?tipo=legal`
- `?severidad=grave`
- `?estado=abierta`
- `?gestion=2026`

### GET/POST `/workflow/aprobaciones/`
CRUD de aprobaciones con huella SHA-256.

**Tipos:** `unidad`, `planificacion`, `presupuesto`, `consolidacion`, `control_social`, `mae`, `concejo`

**Filtros:**
- `?gestion=2026`
- `?tipo=consolidacion`

### GET/POST `/workflow/consolidacion/`
Consolidacion institucional con alertas por programa.

---

## Documentos

### GET/POST `/documentos/documentos/`
CRUD de documentos adjuntos.

**Campos:** archivo, nombre, tipo_documento, hash_sha256

---

## Reportes

### GET `/reportes/poa-unidad/?gestion=2026&unidad_id=<id>`
XLSX del POA por unidad organizacional.

### GET `/reportes/poa-consolidado/?gestion=2026`
XLSX del POA consolidado institucional.

### GET `/reportes/proyectos/?gestion=2026`
XLSX de proyectos de inversion.

### GET `/reportes/observaciones/?gestion=2026`
CSV de observaciones del workflow.

### GET `/reportes/territorio/?gestion=2026`
GeoJSON de localizaciones territoriales.

### GET `/reportes/acta-aprobacion/?gestion=2026`
PDF de acta de aprobacion.

### GET `/reportes/auxiliar-pluri/?gestion=2026`
XLSX del auxiliar plurianual por grupo de gasto.

### GET `/reportes/evaluacion-cuadro1/?gestion=2026`
XLSX Cuadro N1: Comparacion PTDI vs PEI vs POA por fuente.

### GET `/reportes/evaluacion-cuadro2/?gestion=2026`
XLSX Cuadro N2: Vinculacion PTDI/PGTC con PEI y POA.

### GET `/reportes/evaluacion-cuadro3/?gestion=2026`
XLSX Cuadro N3: Seguimiento ejecucion fisica y financiera.

### GET `/reportes/avance-programacion/?gestion=2026`
JSON avance de programacion por UE con semaforo.

### GET `/reportes/ejecucion-presupuestaria-por-fuente/?fuente_id=<id>`
JSON ejecucion presupuestaria por fuente de financiamiento.

### GET `/reportes/presupuesto-por-linea/?linea_id=<id>`
JSON detalle de movimientos de linea presupuestaria.

### GET `/reportes/comparativo-mensual/?gestion=2026`
JSON comparacion mensual fisica vs financiera.

### GET `/reportes/indicadores-por-sector/?sector_id=<id>`
JSON indicadores agregados por sector.

### GET `/reportes/acciones-correctivas-pendientes/`
JSON acciones correctivas pendientes.

### GET `/reportes/solicitudes-modificacion-pendientes/`
JSON solicitudes de modificacion pendientes.

### GET `/reportes/evaluaciones-por-periodo/?fecha_inicio=YYYY-MM-DD&fecha_fin=YYYY-MM-DD`
JSON evaluaciones en un periodo con puntajes.

### GET `/reportes/desempeno-unidad/?gestion=2026&unidad_id=<id>`
JSON desempeno de una UE con todos sus indicadores.

### GET `/reportes/alertas-activas/`
JSON alertas activas con severidad.

### GET `/reportes/seguimiento-reciente/?dias=30`
JSON entradas de seguimiento recientes.

### GET `/reportes/supuestos-criticos/?gestion=2026`
JSON supuestos criticos con nivel de riesgo.

### GET `/reportes/productos-por-pad/?pad_id=<id>`
JSON productos de un PAD con resultados.

### GET `/reportes/programacion-presupuestaria/?gestion=2026`
JSON programacion presupuestaria completa por POAU.

---

## Auditoria

### GET `/auditoria/registros/`
Log de auditoria del sistema.

**Filtros:**
- `?usuario=<usuario_id>`
- `?accion=crear`
- `?modelo=gestion`
- `?fecha_desde=2026-01-01`
- `?fecha_hasta=2026-12-31`

---

## Evaluacion

### GET/POST `/evaluacion/evaluaciones/`
CRUD de evaluaciones.

**Tipos:** `anual`, `medio_termino`, `final`, `especifica`

**Periodos:** `Q1`, `Q2`, `Q3`, `Q4`, `S1`, `S2`, `AN`

**Estados:** `borrador → en_curso → completada → aprobada`

**Filtros:**
- `?plan=<plan_id>`
- `?fiscal_year=2026`
- `?evaluation_type=anual`

### GET/POST `/evaluacion/criterios/`
CRUD de criterios de evaluacion.

**Criterios:** `eficacia`, `eficiencia`, `efectividad`, `pertinencia`, `impacto`, `sostenibilidad`

**Campos:** `score` (0-100), `weight` (0-1)

**Puntaje ponderado** = `score * weight`

### GET/POST `/evaluacion/resultados/`
CRUD de resultados de evaluacion.

**Estados:** `cumple`, `parcial`, `no_cumple`

### GET/POST `/evaluacion/lecciones-aprendidas/`
CRUD de lecciones aprendidas.

**Categorias:** `tecnica`, `organizacional`, `financiera`, `institucional`

### GET/POST `/evaluacion/recomendaciones/`
CRUD de recomendaciones.

**Prioridades:** `alta`, `media`, `baja`

**Estados:** `pendiente → en_proceso → cumplida`

---

## Modificaciones

### GET/POST `/modificaciones/solicitudes/`
CRUD de solicitudes de modificacion.

**Tipos:** `meta`, `operacion`, `reprogramacion`, `responsable`, `inscripcion`, `eliminacion`, `incremento`, `reduccion`, `traspaso`, `fuente`, `organismo`, `categoria`, `reformulacion`

**Estados:** `borrador → en_revision → aprobada / rechazada → cumplida`

**Filtros:**
- `?gestion_fiscal=2026`
- `?estado=en_revision`
- `?tipo=incremento`

### GET/POST `/modificaciones/cambios/`
CRUD de cambios individuales dentro de una solicitud.

### GET/POST `/modificaciones/impactos/`
CRUD de impactos de modificacion (fisico, financiero, estrategico).

---

## Notificaciones

### GET/POST `/notificaciones/tipos/`
CRUD de tipos de notificacion (con templates de correo).

### GET/POST `/notificaciones/notificaciones/`
CRUD de notificaciones internas.

**Prioridades:** `alta`, `media`, `baja`

**Filtros:**
- `?user=<user_id>`
- `?is_read=false`
- `?priority=alta`
- `?gestion=2026`

### POST `/notificaciones/notificaciones/{id}/marcar_leida/`
Marcar notificacion como leida.

### GET/POST `/notificaciones/preferencias/`
Preferencias de notificacion del usuario.

**Frecuencias:** `inmediata`, `diaria`, `semanal`

---

## Seguimiento

### GET/POST `/seguimiento/reportes-seguimiento/`
CRUD de reportes de seguimiento periodico.

**Estados:** `borrador → enviado → validado → aprobado`

**Filtros:**
- `?gestion=2026`
- `?periodo=2026-Q1`
- `?unidad_organizacional=<unidad_id>`

### GET/POST `/seguimiento/entradas-seguimiento/`
CRUD de entradas de seguimiento por actividad.

**Campos:**
- `programado_fisico`, `ejecutado_fisico`, `porcentaje_avance_fisico`
- `presupuesto_inicial`, `presupuesto_actual`
- `programado_financiero`, `ejecutado_financiero`, `porcentaje_avance_financiero`
- `desviacion`, `causa_desviacion`, `accion_correctiva`
- `proyeccion_cierre`, `evidencia`

**Filtros:**
- `?reporte=<reporte_id>`
- `?actividad=<actividad_id>`

### GET/POST `/seguimiento/alertas/`
CRUD de alertas generadas.

**Tipos:** `ejecucion_fisica_baja`, `ejecucion_financiera_baja`, `avance_sin_financiera`, `financiera_sin_avance`, `sobreejecucion`, `meta_vencida`, `sin_evidencia`, `incumplimiento_correctivo`, `presupuesto_sin_actividad`, `actividad_sin_presupuesto`

**Severidades:** `leve`, `moderada`, `grave`

**Filtros:**
- `?activa=true`
- `?tipo=ejecucion_fisica_baja`
- `?severidad=grave`

### POST `/seguimiento/alertas/{id}/resolver/`
Resolver una alerta.

### GET/POST `/seguimiento/umbrales/`
CRUD de configuracion de umbrales para alertas.

---

## Acciones Correctivas

### GET/POST `/acciones-correctivas/acciones/`
CRUD de acciones correctivas.

**Estados:** `pendiente → en_ejecucion → cumplida / incumplida → cerrada / cancelada`

**Filtros:**
- `?gestion=2026`
- `?status=pendiente`
- `?responsible=<user_id>`

**Propiedades calculadas:**
- `esta_vencida`: `True` si fecha_limite < hoy y estado pendiente/en_ejecucion
- `porcentaje_cumplimiento`: % de compromisos cumplidos

### GET/POST `/acciones-correctivas/compromisos/`
CRUD de compromisos de acciones correctivas.

**Estados:** `pendiente → cumplido / incumplido`

**Propiedad calculada:**
- `esta_vencido`: `True` si pendiente y fecha_limite < hoy

---

## Endpoints Adicionales

### GET `/health/`
Health check del sistema.

### GET `/api/v1/schema/`
Schema OpenAPI 3.0 (YAML).

### GET `/api/v1/docs/`
Swagger UI (documentacion interactiva).

### GET `/admin/`
Django Admin (requiere superusuario).

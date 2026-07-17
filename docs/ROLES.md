# Roles del Sistema — SISPAD-PEI-POA

El sistema define 12 roles con permisos granulares. La autenticacion se basa en JWT con roles asignados al usuario.

## Matriz de Permisos

| Modulo                | superadmin | tecnico_admin | planificador | evaluador | jefe_ue | director | tecnico_ue | operador | beneficiario | proveedor | control_interno | control_social |
| --------------------- | :--------: | :-----------: | :----------: | :-------: | :-----: | :------: | :--------: | :------: | :----------: | :-------: | :-------------: | :------------: |
| Dashboard             | R/W        | R/W           | R/W          | R/W       | R/W     | R/W      | R          | R        | R            | -         | R               | R              |
| Usuarios              | R/W        | R/W           | R            | -         | -       | -        | -          | -        | -            | -         | -               | -              |
| Organizacion          | R/W        | R/W           | R            | -         | R       | R        | R          | -        | R            | -         | R               | -              |
| Catalogos             | R/W        | R/W           | R            | -         | -       | -        | -          | -        | R            | -         | -               | -              |
| Gestion Fiscal        | R/W        | R/W           | R/W          | R         | R/W     | R/W      | R          | R        | R            | -         | R               | R              |
| Planificacion         | R/W        | R/W           | R/W          | R         | R       | R        | R          | -        | R            | -         | R               | -              |
| PAD                   | R/W        | R/W           | R/W          | R         | R       | R        | R          | R        | R            | -         | R               | R              |
| POAU                  | R/W        | R/W           | R            | R         | R/W     | R/W      | R/W        | R/W      | R            | -         | R               | R              |
| Indicadores           | R/W        | R/W           | R/W          | R         | R/W     | R        | R/W        | R        | R            | -         | R               | -              |
| Presupuesto           | R/W        | R/W           | R/W          | R         | R       | R        | R          | R        | R            | -         | R               | -              |
| Techos                | R/W        | R/W           | R/W          | -         | R       | R        | -          | -        | R            | -         | R               | -              |
| Inversion             | R/W        | R/W           | R/W          | R         | R       | R        | R          | -        | R            | R         | R               | -              |
| Territorio            | R/W        | R/W           | R            | -         | R       | R        | R          | -        | R            | -         | -               | -              |
| Workflow              | R/W        | R/W           | R/W          | R         | R/W     | R/W      | R          | -        | R            | -         | R               | R              |
| Reportes              | R/W        | R/W           | R            | R         | R       | R        | R          | R        | R            | R         | R               | R              |
| Auditoria             | R          | R             | -            | -         | -       | -        | -          | -        | -            | -         | R               | -              |
| Evaluacion            | R/W        | R/W           | R            | R/W       | R       | R        | -          | -        | R            | -         | R               | R              |
| Modificaciones        | R/W        | R/W           | R/W          | R         | R/W     | R/W      | R          | R        | R            | -         | R               | R              |
| Notificaciones        | R/W        | R/W           | R            | R         | R       | R        | R          | R        | R            | R         | R               | R              |
| Seguimiento           | R/W        | R/W           | R            | R         | R/W     | R        | R/W        | R/W      | R            | -         | R               | R              |
| Acciones Correctivas  | R/W        | R/W           | R            | R         | R/W     | R        | R/W        | R        | R            | -         | R               | R              |
| Consolidacion         | R/W        | R/W           | R/W          | R         | R/W     | R/W      | R          | -        | R            | -         | R               | R              |
| Portal Publico        | R          | R             | R            | R         | R       | R        | R          | R        | R            | R         | R               | R              |

**Leyenda:** R = Lectura, W = Escritura, - = Sin acceso

---

## superadmin — Super Administrador

**Descripcion:** Acceso total al sistema. Control completo de configuracion, usuarios, datos y funcionalidad.

**Permisos:**
- CRUD completo en todos los modulos
- Gestionar usuarios y roles
- Acceder a Django Admin
- Ver auditoria completa
- Configurar umbrales de alertas
- Ejecutar migraciones y seeds
- Generar y descargar todos los reportes
- Resolver alertas
- Aprobar/rechazar en cualquier etapa del workflow

**Modulos accesibles:** Todos (lectura y escritura)

---

## tecnico_admin — Tecnico Administrativo

**Descripcion:** Funciones administrativas de gestion del sistema. Puede gestionar usuarios, configurar catalogos y supervisar procesos.

**Permisos:**
- CRUD en usuarios y roles
- CRUD en catalogos presupuestarios
- CRUD en organizacion
- Supervisar workflow y aprobar/rechazar
- Generar todos los reportes
- Ver auditoria
- Gestionar techos presupuestarios
- Administrar consolidacion

**Modulos accesibles:** Todos (con algunas restricciones en escritura)

---

## planificador — Planificador

**Descripcion:** Creacion y gestion de planes estrategicos y presupuestarios. Responsable de la formulacion del POA.

**Permisos:**
- CRUD en planificacion (PEI, PTDI, PDES, nodos, AMP, ACP)
- CRUD en PAD (politicas, lineamientos, resultados, productos)
- CRUD en indicadores y metas programadas
- CRUD en presupuesto (lineas, programas)
- CRUD en techos presupuestarios
- CRUD en inversion (proyectos)
- Enviar formulacion en workflow
- Consolidar institucionalmente
- Generar reportes de planificacion

**Modulos accesibles:** Planificacion, PAD, Indicadores, Presupuesto, Techos, Inversion, Workflow (envio/consolidacion), Reportes

---

## evaluador — Evaluador

**Descripcion:** Funciones de evaluacion del desempeno del POA. Evalua criterios de eficacia, eficiencia, efectividad, pertinencia, impacto y sostenibilidad.

**Permisos:**
- CRUD en evaluaciones (anual, medio termino, final, especifica)
- CRUD en criterios de evaluacion (ponderados)
- CRUD en resultados de evaluacion
- CRUD en lecciones aprendidas
- CRUD en recomendaciones
- Consultar POA, indicadores, seguimiento
- Generar reportes de evaluacion
- Comentar en observaciones del workflow
- Ver notificaciones

**Modulos accesibles:** Evaluacion (escritura), Planificacion, PAD, POAU, Indicadores, Seguimiento, Workflow (lectura), Reportes, Notificaciones

---

## jefe_ue — Jefe de Unidad Ejecutora

**Descripcion:** Director de una Unidad Ejecutora. Supervisa la formulacion y ejecucion del POA de su unidad.

**Permisos:**
- CRUD en POAU de su unidad
- CRUD en actividades y ejecuciones de su unidad
- CRUD en indicadores de su unidad
- Enviar y recibir observaciones en workflow
- Aprobar POA de su unidad
- CRUD en seguimiento de su unidad
- Gestionar acciones correctivas de su unidad
- Solicitar modificaciones
- Generar reportes de su unidad

**Modulos accesibles:** POAU, Indicadores, Workflow (envio/aprobacion unidad), Seguimiento, Acciones Correctivas, Modificaciones, Reportes (filtrados por unidad)

---

## director — Director Institucional

**Descripcion:** Direccion institucional del GAM Sacaba. Supervision general de todas las unidades ejecutoras.

**Permisos:**
- Lectura en todos los modulos de planificacion
- Supervision de POAUs de todas las unidades
- Aprobacion en workflow (tipo consolidacion)
- Revision de indicadores y metas
- Generar reportes institucionales
- Aprobar POA consolidado
- Ver consolidacion institucional

**Modulos accesibles:** Todos (lectura), POAU (aprobacion), Workflow (aprobacion consolidacion), Consolidacion, Reportes

---

## tecnico_ue — Tecnico de Unidad Ejecutora

**Descripcion:** Trabajo tecnico dentro de una Unidad Ejecutora. Formulacion y seguimiento de actividades.

**Permisos:**
- Lectura en POAU de su unidad
- Registro de ejecuciones fisicas y financieras
- Registro de entradas de seguimiento
- Registro de evidencia
- Actualizar avance de actividades
- Ver indicadores y metas
- Ver notificaciones

**Modulos accesibles:** POAU (lectura/registro ejecucion), Seguimiento (escritura), Indicadores (lectura), Notificaciones

---

## operador — Operador del POA

**Descripcion:** Operaciones del POA. Registro de actividades, seguimiento y reportes operativos.

**Permisos:**
- Lectura en POAU
- Registro de ejecuciones fisicas y financieras
- Registro de entradas de seguimiento
- Verificar avance de actividades
- Generar reportes operativos
- Solicitar modificaciones simples
- Ver notificaciones

**Modulos accesibles:** POAU (lectura/registro), Seguimiento (escritura), Modificaciones (solicitud), Reportes (operativos), Notificaciones

---

## beneficiario — Beneficiario (Portal Publico)

**Descripcion:** Acceso de solo lectura al portal publico. Consulta de informacion del POA sin autenticacion requerida.

**Permisos:**
- Consultar POA aprobado
- Ver indicadores y metas publicas
- Ver productos del PAD
- Descargar reportes publicos
- Ver informacion del portal publico

**Modulos accesibles:** Portal Publico (sin auth), Dashboard (basico)

---

## proveedor — Proveedor Externo

**Descripcion:** Proveedores externos que participan en proyectos de inversion. Acceso limitado a informacion de sus proyectos.

**Permisos:**
- Ver proyectos de inversion asignados
- Registrar avance de proyectos
- Subir documentos de respaldo
- Ver notificaciones relacionadas
- Generar reportes de sus proyectos

**Modulos accesibles:** Inversion (lectura/registro avance), Documentos, Notificaciones, Reportes (proyectos)

---

## control_interno — Control Interno

**Descripcion:** Control interno de la entidad. Supervision de la ejecucion presupuestaria y cumplimiento normativo.

**Permisos:**
- Acceso completo de lectura en todos los modulos
- Ver auditoria completa
- Ver workflow y observaciones
- Verificar cumplimiento de reglas presupuestarias
- Generar reportes de control
- Verificar acciones correctivas
- Revisar modificaciones
- Ver evaluaciones

**Modulos accesibles:** Todos (lectura), Auditoria, Workflow (lectura), Evaluacion (lectura), Acciones Correctivas (lectura), Modificaciones (lectura), Reportes

---

## control_social — Control Social

**Descripcion:** Control social de la comunidad. Pronunciamiento sobre el POA consolidado y seguimiento ciudadano.

**Permisos:**
- Ver POA consolidado
- Pronunciar sobre consolidacion (aprobacion/rechazo)
- Ver indicadores y avances
- Ver seguimiento y alertas
- Generar reportes publicos
- Ver notificaciones
- Ver evaluaciones

**Modulos accesibles:** Consolidacion (pronunciamiento), PAD (lectura), Indicadores (lectura), Seguimiento (lectura), Evaluacion (lectura), Reportes (publicos), Notificaciones

---

## Flujo de Aprobacion por Rol

```
1. tecnico_ue/operador  →  Registra actividades y ejecucion
2. jefe_ue              →  Revisa y aprueba POA de su unidad
3. planificador         →  Consolida institucionalmente
4. director             →  Aprueba consolidacion
5. control_social       →  Pronunciamiento ciudadano
6. tecnico_admin        →  Aprobacion final administrativa
```

### Estados del Workflow

```
borrador → enviado → en_revision → aprobado / devuelto
                                    ↓
                              consolidacion → aprobado institucional
                                    ↓
                              control_social → pronunciamiento
                                    ↓
                              aprobacion_final → aprobado MAE / Concejo
```

## Autenticacion y Sesiones

- **Access Token**: 4 horas de duracion
- **Refresh Token**: 1 dia de duracion
- **Rotacion**: Los refresh tokens se rotan automaticamente
- **Contrasena**: Obligatoria cambio en primer login (`debe_cambiar_password`)
- **Bloqueo**: No automatico, configurable por admin

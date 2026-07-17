# Flujos de Aprobacion — SISPAD-PEI-POA

Documento completo de todos los flujos de aprobacion del sistema, incluyendo estados, transiciones, roles responsables, documentos requeridos y condiciones.

---

## 1. Flujo de Formulacion del PAD

El Plan Anual de Desarrollo (PAD) sigue una jerarquia: **Sector → Politica → Lineamiento → Resultado → Producto**. Cada nivel tiene su propio ciclo de aprobacion.

### 1.1 Diagrama General del PAD

```
┌─────────────────────────────────────────────────────────────┐
│                    FORMULACION DEL PAD                       │
│                                                              │
│  SectorPAD (catalogo)                                       │
│       │                                                      │
│       └── PoliticaPAD ──┐                                   │
│                         │                                    │
│              LineamientoEstrategico ──┐                      │
│                                      │                       │
│                         ResultadoTerritorial                │
│                              │                               │
│              ┌───────────────┼───────────────┐              │
│              │               │               │              │
│     ProductoTerritorial  ArticulacionSIPEB  Programacion   │
│              │               │            AnualPAD          │
│              │               │                               │
│              └───────┬───────┘                               │
│                      │                                       │
│              Vinculo al POAU                                │
└─────────────────────────────────────────────────────────────┘
```

### 1.2 Flujo de Resultado Territorial

| Estado | Transicion | Rol Responsable | Condiciones |
|--------|-----------|-----------------|-------------|
| `borrador` | → `enviado` | planificador | Todos los campos obligatorios completos, indicador definido, formula definida, linea base registrada, meta 2030 definida |
| `enviado` | → `aprobado` | tecnico_admin / superadmin | Sin observaciones pendientes, coherencia con lineamiento, articulacion SIPEB completa |
| `enviado` | → `rechazado` | tecnico_admin / superadmin | Observaciones registradas en ArticulacionLog, detalle de rechazo obligatorio |
| `rechazado` | → `borrador` | planificador | Correccion de observaciones, actualizacion de ArticulacionLog |
| `aprobado` | → `borrador` (reapertura) | superadmin | Motivo de reapertura registrado, es_reapertura=True en Aprobacion |

**Documentos requeridos para envio:**
- Indicador definido con formula
- Linea base y meta 2030
- Articulacion SIPEB (Matriz B) completa
- Programacion anual (fisica y financiera)

**Validaciones automaticas:**
- Codigo unico por lineamiento y gestion
- Valores no negativos en programacion
- Referencia al menos a resultado o producto en ProgramacionAnualPAD

### 1.3 Flujo de Producto Territorial

Los productos dependen de un ResultadoTerritorial ya aprobado:

| Estado | Transicion | Rol Responsable | Condiciones |
|--------|-----------|-----------------|-------------|
| Creado | Edicion libre | planificador | Resultado territorial aprobado como padre |
| Guardado | Validacion automatica | sistema | Codigo unico por resultado y gestion, campos obligatorios |

**Campos obligatorios:** codigo, nombre, resultado (FK), gestion

**Validaciones:**
- Unicidad de `(codigo, resultado, gestion)`
- cuenta_con_financiamiento debe ser SI o NO
- presupuesto_total_pad >= 0

### 1.4 Registro de Cambios (ArticulacionLog)

Cada cambio en el flujo PAD genera un registro:

| Campo | Descripcion |
|-------|-------------|
| entidad | 'resultado' o 'producto' |
| entidad_id | UUID del registro |
| accion | 'crear', 'modificar', 'enviar', 'aprobar', 'rechazar' |
| usuario | Quien ejecuto la accion |
| detalle | JSON con cambios especificos |

---

## 2. Flujo de Formulacion del POAU

El Plan Operativo Anual por Unidad sigue un ciclo: **borrador → enviado → aprobado/rechazado**.

### 2.1 Diagrama de Estados

```
                    ┌──────────────────┐
                    │                  │
          ┌────────>   BORRADOR        │
          │         │                  │
          │         └────────┬─────────┘
          │                  │
          │         enviar (jefe_ue)
          │                  │
          │         ┌────────▼─────────┐
          │         │                  │
          │         │   ENVIADO        │<──────────────────┐
          │         │                  │                   │
          │         └──┬──────────┬────┘                   │
          │            │          │                        │
          │     aprobar│          │rechazar                │
          │            │          │                        │
          │    ┌───────▼───┐  ┌──▼────────────┐           │
          │    │           │  │               │           │
          │    │ APROBADO  │  │  RECHAZADO    │───────────┘
          │    │           │  │               │  (corregir y reenviar)
          │    └───────────┘  └───────────────┘
          │
          │  (reapertura por superadmin)
          └────────────────────────────────────────────────┘
```

### 2.2 Detalle de Transiciones del POAU

| Estado | Transicion | Rol Responsable | Condiciones | Documentos |
|--------|-----------|-----------------|-------------|------------|
| (creacion) | → `borrador` | jefe_ue, tecnico_admin, planificador | Unidad asignada, gestion activa, codigo unico | Datos basicos del POAU |
| `borrador` | → `enviado` | jefe_ue | Al menos 1 actividad creada, metas trimestrales coherentes, presupuesto definido | Actividades con programacion trimestral |
| `enviado` | → `aprobado` | jefe_ue (unidad) | Todas las actividades validadas, presupuesto dentro del techo | Revision completa |
| `enviado` | → `rechazado` | jefe_ue (unidad) / director | Observaciones registradas, motivo de rechazo | Detalle de observaciones |
| `rechazado` | → `borrador` | jefe_ue | Correccion de observaciones, actualizacion de actividades | Actividades corregidas |
| `aprobado` | → `borrador` (reapertura) | superadmin | Motivo de reapertura registrado | Documento de soporte |

### 2.3 Validaciones del POAU al Enviar

1. **Actividades:** Al menos una actividad creada
2. **Metas trimestrales:** Suma de Q1+Q2+Q3+Q4 = meta_fisica_anual (si todos estan definidos)
3. **Presupuesto:** presupuesto_anual >= 0
4. **Objeto de gasto:** Si se define, debe existir en catalogo
5. **Articulacion:** Si tiene accion_corto_plazo, debe existir en planificacion
6. **Producto territorial:** Si se vincula, debe existir y estar aprobado

---

## 3. Flujo de Consolidacion del POA

La consolidacion institucional reune los POAUs de todas las unidades en un POA consolidado.

### 3.1 Diagrama de Estados

```
┌────────────────────────────────────────────────────────────────────┐
│                   FLUJO DE CONSOLIDACION                           │
│                                                                    │
│  POAUs individuales (por unidad)                                  │
│       │                                                            │
│       ├── UE 1: Aprobada ✓                                        │
│       ├── UE 2: Aprobada ✓                                        │
│       ├── UE 3: Borrador  ✗  ← bloquea consolidacion              │
│       └── UE N: Aprobada ✓                                        │
│                                                                    │
│  ──────────────────────────────────────────────────────────────── │
│                                                                    │
│  planificador ejecuta consolidacion                               │
│       │                                                            │
│       ▼                                                            │
│  ┌──────────────┐                                                 │
│  │ BORRADOR     │  (consolidacion generada)                       │
│  │ CONSOLIDADO  │                                                 │
│  └──────┬───────┘                                                 │
│         │                                                          │
│         │ enviar a validacion                                     │
│         ▼                                                          │
│  ┌──────────────┐                                                 │
│  │ ENVIADO      │                                                 │
│  │ (a revision) │                                                 │
│  └──┬───────┬───┘                                                 │
│     │       │                                                     │
│     │       │  ┌────────────────┐                                 │
│     │       └─>│ OBSERVADO      │──> reenviar ──> ENVIADO        │
│     │          └────────────────┘                                 │
│     │                                                              │
│     │  aprobado por planificacion                                │
│     ▼                                                              │
│  ┌──────────────────┐                                             │
│  │ VALIDADO         │  (Planificacion validada)                   │
│  │ PLANIFICACION    │                                             │
│  └──────┬───────────┘                                             │
│         │                                                          │
│         │  aprobado por director                                  │
│         ▼                                                          │
│  ┌──────────────────┐                                             │
│  │ VALIDADO         │  (Presupuesto validado)                     │
│  │ PRESUPUESTO      │                                             │
│  └──────┬───────────┘                                             │
│         │                                                          │
│         │  consolidacion institucional                            │
│         ▼                                                          │
│  ┌──────────────────┐                                             │
│  │ CONSOLIDACION    │                                             │
│  │ INSTITUCIONAL    │                                             │
│  └──────┬───────────┘                                             │
│         │                                                          │
│         │  pronunciamiento control social                         │
│         ▼                                                          │
│  ┌──────────────────┐                                             │
│  │ CONTROL SOCIAL   │                                             │
│  │ PRONUNCIAMIENTO  │                                             │
│  └──────┬───────────┘                                             │
│         │                                                          │
│         │  aprobacion final (MAE / Concejo Municipal)             │
│         ▼                                                          │
│  ┌──────────────────┐                                             │
│  │ APROBADO FINAL   │  ← POA Institucional vigente               │
│  └──────────────────┘                                             │
└────────────────────────────────────────────────────────────────────┘
```

### 3.2 Detalle de Transiciones de Consolidacion

| Estado | Transicion | Rol Responsable | Condiciones |
|--------|-----------|-----------------|-------------|
| (inicio) | → `borrador` | planificador | Todos los POAUs aprobados por sus unidades |
| `borrador` | → `enviado` (planificacion) | planificador | Consolidacion completa, todos los POAUs incluidos |
| `enviado` | → `validado_planificacion` | planificador | Validacion de coherencia entre unidades, sin duplicidades |
| `enviado` | → `observado` | tecnico_admin | Observaciones de planificacion |
| `observado` | → `enviado` | planificador | Correccion de observaciones |
| `validado_planificacion` | → `validado_presupuesto` | director | Verificacion de techos presupuestarios, coherencia financiera |
| `validado_presupuesto` | → `consolidacion_institucional` | planificador | Consolidacion final generada |
| `consolidacion_institucional` | → `control_social` | tecnico_admin | Expediente completo para pronunciamiento |
| `control_social` | → `aprobado_final` | control_social (tecnico_admin ejecuta) | Pronunciamiento positivo del control social |

### 3.3 Validaciones de Consolidacion

1. **Totalidad:** Todos los POAUs aprobados deben estar incluidos
2. **Presupuesto:** Suma de presupuestos de POAUs <= Techo total institucional
3. **Indicadores:** Sin duplicidad de indicadores entre unidades
4. **Articulacion:** Todas las ACP articuladas a AMP del PEI
5. **Reglas legales:** Todas las reglas de normativa vigente pasan validacion

---

## 4. Flujo de Solicitud de Modificacion

Las modificaciones al POA aprobado siguen un proceso riguroso con trazabilidad completa.

### 4.1 Tipos de Modificacion

| Codigo | Tipo | Descripcion |
|--------|------|-------------|
| meta | Modificacion de Meta | Cambio en metas fisicas o financieras |
| operacion | Modificacion de Operacion | Cambio en operaciones del POA |
| reprogramacion | Reprogramacion | Cambio de fechas o periodos |
| responsable | Cambio de Responsable | Asignacion a nuevo responsable |
| inscripcion | Inscripcion | Adicion de nueva actividad |
| eliminacion | Eliminacion | Supresion de actividad existente |
| incremento | Incremento Presupuestario | Aumento de presupuesto |
| reduccion | Reduccion Presupuestaria | Disminucion de presupuesto |
| traspaso | Traspaso Presupuestario | Mover presupuesto entre actividades |
| fuente | Cambio de Fuente | Cambio de fuente de financiamiento |
| organismo | Cambio de Organismo | Cambio de organismo financiador |
| categoria | Cambio de Categoria | Cambio de clasificacion |
| reformulacion | Reformulacion | Reformulacion integral |

### 4.2 Diagrama de Estados

```
┌────────────────────────────────────────────────────────────┐
│               FLUJO DE MODIFICACION                        │
│                                                            │
│  ┌──────────────┐                                         │
│  │  BORRADOR    │  (solicitud en creacion)                │
│  └──────┬───────┘                                         │
│         │                                                  │
│         │  enviar a revision (solicitado_por)             │
│         ▼                                                  │
│  ┌──────────────┐                                         │
│  │  EN_REVISION  │                                        │
│  └──┬───────┬───┘                                         │
│     │       │                                             │
│     │       │  ┌────────────┐                             │
│     │       └─>│ RECHAZADA  │──> borrador (corregir)     │
│     │          └────────────┘                             │
│     │                                                      │
│     │  aprobada por tecnico_admin                         │
│     ▼                                                      │
│  ┌──────────────┐                                         │
│  │  APROBADA    │                                         │
│  └──────┬───────┘                                         │
│         │                                                  │
│         │  aplicar modificacion (servicio)                │
│         ▼                                                  │
│  ┌──────────────┐                                         │
│  │  CUMPLIDA    │  (modificacion aplicada en BD)          │
│  └──────────────┘                                         │
└────────────────────────────────────────────────────────────┘
```

### 4.3 Detalle de Transiciones

| Estado | Transicion | Rol Responsable | Condiciones |
|--------|-----------|-----------------|-------------|
| (creacion) | → `borrador` | jefe_ue, operador, planificador, director, tecnico_admin | Entidad afectada identificada, motivo registrado |
| `borrador` | → `en_revision` | solicitante | Motivo completo, informe tecnico opcional, cambios registrados en CambioModificacion |
| `en_revision` | → `aprobada` | tecnico_admin / superadmin | Verificacion de compatibilidad, impacto evaluado |
| `en_revision` | → `rechazada` | tecnico_admin / superadmin | Observaciones detalladas, justificacion del rechazo |
| `rechazada` | → `borrador` | solicitante | Correccion basada en observaciones |
| `aprobada` | → `cumplida` | tecnico_admin (servicio automatico) | Ejecucion del servicio `aplicar_modificacion()` |

### 4.4 Documentos Requeridos por Tipo

| Tipo | Informe Tecnico | Documento Legal | Impacto Financiero |
|------|:---------------:|:---------------:|:------------------:|
| meta | Obligatorio | Opcional | Si >= 10% del techo |
| operacion | Obligatorio | Opcional | Si >= 10% del techo |
| reprogramacion | Obligatorio | No | No |
| responsable | No | No | No |
| inscripcion | Obligatorio | Si es nuevo programa | Obligatorio |
| eliminacion | Obligatorio | Si hay compromiso | Obligatorio |
| incremento | Obligatorio | Obligatorio | Obligatorio |
| reduccion | Obligatorio | Obligatorio | Obligatorio |
| traspaso | Obligatorio | Opcional | Obligatorio |
| fuente | Obligatorio | Opcional | Si cambio monto |
| reformulacion | Obligatorio | Obligatorio | Obligatorio |

### 4.5 Validaciones de Compatibilidad

El servicio `verificar_compatibilidad()` valida:
1. **Presupuesto:** El nuevo monto no excede el techo de la UE
2. **Fuente:** La fuente de financiamiento tiene saldo disponible
3. **Actividad:** La actividad afectada esta vigente en la gestion
4. **Reglas legales:** La modificacion no incumple reglas presupuestarias
5. **Dependencias:** No genera inconsistencias con otras actividades

---

## 5. Flujo de Evaluacion

### 5.1 Tipos de Evaluacion

| Tipo | Periodo | Descripcion |
|------|---------|-------------|
| anual | AN | Evaluacion al cierre de gestion |
| medio_termino | S1 o S2 | Evaluacion a mitad de gestion |
| final | AN | Evaluacion final de cerrar el plan |
| especifica | Q1-Q4, S1-S2 | Evaluacion de un modulo o programa especifico |

### 5.2 Diagrama de Estados

```
┌────────────────────────────────────────────────────────────┐
│                  FLUJO DE EVALUACION                       │
│                                                            │
│  ┌──────────────┐                                         │
│  │  BORRADOR    │  (evaluacion en creacion)               │
│  └──────┬───────┘                                         │
│         │                                                  │
│         │  iniciar evaluacion (evaluador)                 │
│         ▼                                                  │
│  ┌──────────────┐                                         │
│  │  EN_CURSO    │  (criterios siendo evaluados)           │
│  └──────┬───────┘                                         │
│         │                                                  │
│         │  completar criterios (evaluador)                │
│         ▼                                                  │
│  ┌──────────────┐                                         │
│  │ COMPLETADA   │  (todos los criterios evaluados)        │
│  └──────┬───────┘                                         │
│         │                                                  │
│         │  aprobar (superadmin / tecnico_admin)           │
│         ▼                                                  │
│  ┌──────────────┐                                         │
│  │  APROBADA    │  (evaluacion aprobada y archivada)      │
│  └──────────────┘                                         │
└────────────────────────────────────────────────────────────┘
```

### 5.3 Detalle de Transiciones

| Estado | Transicion | Rol Responsable | Condiciones |
|--------|-----------|-----------------|-------------|
| (creacion) | → `borrador` | evaluador, tecnico_admin, superadmin | Plan seleccionado, gestion y tipo definidos |
| `borrador` | → `en_curso` | evaluador | Equipo responsable asignado, periodo definido |
| `en_curso` | → `completada` | evaluador | Todos los criterios evaluados, puntaje global calculado |
| `completada` | → `aprobada` | superadmin / tecnico_admin | Conclusiones redactadas, recomendaciones incluidas |

### 5.4 Criterios de Evaluacion

| Criterio | Descripcion | Rango Puntaje | Peso Default |
|----------|-------------|:-------------:|:------------:|
| eficacia | Alcanza los objetivos propuestos | 0-100 | 0.20 |
| eficiencia | Optimiza recursos utilizados | 0-100 | 0.15 |
| efectividad | Produce resultados esperados | 0-100 | 0.20 |
| pertinencia | Es relevante para la necesidad | 0-100 | 0.15 |
| impacto | Genera cambios significativos | 0-100 | 0.15 |
| sostenibilidad | Es mantenible en el tiempo | 0-100 | 0.15 |

**Formula de puntaje global:**
```
Puntaje Global = Suma(Criterio.puntaje * Criterio.peso) / Suma(Criterio.peso)
```

### 5.5 Resultados de Evaluacion por POAU/Unidad

Cada resultado puede ser:
- **cumple:** Avance >= 80%
- **parcial:** Avance >= 40% y < 80%
- **no_cumple:** Avance < 40%

---

## 6. Flujo de Seguimiento

### 6.1 Diagrama de Estados del Reporte de Seguimiento

```
┌────────────────────────────────────────────────────────────┐
│               FLUJO DE SEGUIMIENTO                         │
│                                                            │
│  ┌──────────────┐                                         │
│  │  BORRADOR    │  (reporte en creacion)                  │
│  └──────┬───────┘                                         │
│         │                                                  │
│         │  enviar (tecnico_ue / operador)                 │
│         ▼                                                  │
│  ┌──────────────┐                                         │
│  │  ENVIADO     │                                         │
│  └──────┬───────┘                                         │
│         │                                                  │
│         │  validar (jefe_ue)                              │
│         ▼                                                  │
│  ┌──────────────┐                                         │
│  │  VALIDADO    │                                         │
│  └──────┬───────┘                                         │
│         │                                                  │
│         │  aprobar (tecnico_admin / planificador)         │
│         ▼                                                  │
│  ┌──────────────┐                                         │
│  │  APROBADO    │  ← reporte cerrado                     │
│  └──────────────┘                                         │
└────────────────────────────────────────────────────────────┘
```

### 6.2 Generacion Automatica de Alertas

Al registrar cada EntradaSeguimiento, el motor de alertas evalua:

| Alerta | Condicion | Severidad | Accion Automatica |
|--------|-----------|-----------|-------------------|
| ejecucion_fisica_baja | avance_fisico < 50% | grave | Notificar a jefe_ue y planificador |
| ejecucion_financiera_baja | avance_financiero < 50% | moderada | Notificar a jefe_ue |
| avance_sin_financiera | fisico > 0 y financiero = 0 | leve | Notificar a operador |
| financiera_sin_avance | financiero > 0 y fisico = 0 | leve | Notificar a operador |
| sobreejecucion | avance > 100% | grave | Notificar a director y control_interno |
| meta_vencida | fecha_fin < hoy y avance < 100% | grave | Notificar a jefe_ue |
| sin_evidencia | evidencia = "" | leve | Notificar a operador |
| presupuesto_sin_actividad | techo asignado sin actividades | moderada | Notificar a planificador |
| actividad_sin_presupuesto | actividad sin distribucion de techo | moderada | Notificar a planificador |

---

## 7. Flujo de Gestion Fiscal

### 7.1 Ciclo de Vida de la Gestion

```
┌──────────────────────────────────────────────────────────────────┐
│                 CICLO DE VIDA DE LA GESTION                      │
│                                                                  │
│  ┌──────────────┐                                               │
│  │ PREPARACION  │  Configuracion inicial, carga de catalogos    │
│  └──────┬───────┘                                               │
│         │  abrir gestion                                        │
│         ▼                                                        │
│  ┌──────────────┐                                               │
│  │   ABIERTA    │  Gestion activa, editable                     │
│  └──────┬───────┘                                               │
│         │  iniciar formulacion                                  │
│         ▼                                                        │
│  ┌──────────────┐                                               │
│  │ FORMULACION  │  Unidades formulan POAUs                      │
│  └──────┬───────┘                                               │
│         │  cerrar formulacion                                   │
│         ▼                                                        │
│  ┌──────────────┐                                               │
│  │  REVISION    │  Revision por area tecnica                    │
│  └──────┬───────┘                                               │
│         │  consolidar                                           │
│         ▼                                                        │
│  ┌──────────────┐                                               │
│  │ CONSOLIDACION│  Consolidacion institucional                  │
│  └──────┬───────┘                                               │
│         │  aprobacion                                           │
│         ▼                                                        │
│  ┌──────────────┐                                               │
│  │ APROBACION   │  Aprobacion final MAE/Concejo                 │
│  └──────┬───────┘                                               │
│         │  cerrar gestion                                       │
│         ▼                                                        │
│  ┌──────────────┐                                               │
│  │  CERRADA     │  Gestion en ejecucion                         │
│  └──────┬───────┘                                               │
│         │  archivar                                             │
│         ▼                                                        │
│  ┌──────────────┐                                               │
│  │ ARCHIVADA    │  Gestion historica                            │
│  └──────────────┘                                               │
└──────────────────────────────────────────────────────────────────┘
```

### 7.2 Transiciones

| Estado | Transicion | Rol Responsable | Condiciones |
|--------|-----------|-----------------|-------------|
| `preparacion` | → `abierta` | superadmin / tecnico_admin | Catalogos cargados, gestiones anteriores archivadas |
| `abierta` | → `formulacion` | superadmin / tecnico_admin | Ciclo de formulacion creado, etapas definidas |
| `formulacion` | → `revision` | tecnico_admin | Fecha de cierre de formulacion alcanzada |
| `revision` | → `consolidacion` | planificador | Revisiones completadas por todas las areas |
| `consolidacion` | → `aprobacion` | planificador | Consolidacion generada y validada |
| `aprobacion` | → `cerrada` | tecnico_admin / superadmin | Aprobacion final registrada |
| `cerrada` | → `archivada` | superadmin | Siguiente gestion abierta |

---

## 8. Flujo de Aprobacion de Movimientos de Techo

### 8.1 Diagrama

```
┌────────────────────────────────────────────────────────────┐
│          FLUJO DE MOVIMIENTOS DE TECHO                     │
│                                                            │
│  planificador solicita movimiento                         │
│       │                                                    │
│       ▼                                                    │
│  ┌──────────────┐                                         │
│  │  SOLICITADO  │  (requested_by registrado)              │
│  └──────┬───────┘                                         │
│         │                                                  │
│         │  aprobar (tecnico_admin)                        │
│         ▼                                                  │
│  ┌──────────────┐                                         │
│  │  APROBADO    │  (approved_by registrado, fecha)        │
│  └──────────────┘                                         │
└────────────────────────────────────────────────────────────┘
```

### 8.2 Tipos de Movimiento

| Tipo | Descripcion | Validaciones |
|------|-------------|--------------|
| asignacion | Asignacion inicial de techo | Monto <= Techo total |
| incremento | Aumento de techo | Monto adicional <= Disponible |
| reduccion | Reduccion de techo | Monto <= Asignado actual |
| transferencia | Transferencia entre techos | Origen y destino definidos |
| reserva | Reserva de techo | Monto <= Disponible |
| liberacion | Liberacion de reserva | Monto <= Reservado |
| ajuste | Ajuste tecnico | Justificacion obligatoria |
| reversion | Reversion de movimiento | Movimiento original identificado |

---

## 9. Flujo de Acciones Correctivas

### 9.1 Diagrama

```
┌────────────────────────────────────────────────────────────┐
│          FLUJO DE ACCIONES CORRECTIVAS                     │
│                                                            │
│  Alerta generada (automatica)                             │
│       │                                                    │
│       │  jefe_ue crea accion correctiva                   │
│       ▼                                                    │
│  ┌──────────────┐                                         │
│  │  PENDIENTE   │                                         │
│  └──────┬───────┘                                         │
│         │                                                  │
│         │  iniciar ejecucion                              │
│         ▼                                                  │
│  ┌──────────────┐                                         │
│  │ EN_EJECUCION │  (compromisos en curso)                 │
│  └──────┬───────┘                                         │
│         │                                                  │
│         ├──── todos cumplidos ──> ┌────────────┐          │
│         │                        │  CUMPLIDA   │          │
│         │                        └─────────────┘          │
│         │                                                  │
│         ├──── alguno incumplido ─> ┌────────────┐         │
│         │                          │ INCUMPLIDA  │         │
│         │                          └─────────────┘         │
│         │                                                  │
│         │  vencimiento automatico                         │
│         ▼                                                  │
│  ┌──────────────┐                                         │
│  │   CERRADA    │  (verificada por jefe_ue)               │
│  └──────────────┘                                         │
│                                                            │
│  ┌──────────────┐                                         │
│  │  CANCELADA   │  (cancelada por jefe_ue)                │
│  └──────────────┘                                         │
└────────────────────────────────────────────────────────────┘
```

### 9.2 Propiedades Calculadas

**esta_vencida:** True si estado es PENDIENTE o EN_EJECUCION y due_date < fecha_actual

**porcentaje_cumplimiento:** (compromisos con estado='cumplido' / total compromisos) * 100

---

## 10. Resumen de Todos los Estados del Sistema

| Modulo | Estados | Total |
|--------|---------|:-----:|
| GestionFiscal | preparacion, abierta, formulacion, revision, consolidacion, aprobacion, cerrada, archivada | 8 |
| ResultadoTerritorial | borrador, enviado, aprobado, rechazado | 4 |
| POAU | borrador, enviado, aprobado, rechazado | 4 |
| Consolidacion | borrador, enviado, observado, validado_planificacion, validado_presupuesto, consolidacion_institucional, control_social, aprobado_final | 8 |
| SolicitudModificacion | borrador, en_revision, aprobada, rechazada, cumplida | 5 |
| Evaluacion | borrador, en_curso, completada, aprobada | 4 |
| ReporteSeguimiento | borrador, enviado, validado, aprobado | 4 |
| Revision | pendiente, en_curso, completada, devuelta | 4 |
| Observacion | abierta, respondida, aceptada, rechazada, cerrada | 5 |
| Aprobacion | aprobado, observado, rechazado | 3 |
| AccionCorrectiva | pendiente, en_ejecucion, cumplida, incumplida, cerrada, cancelada | 6 |
| CompromisoAccionCorrectiva | pendiente, cumplido, incumplido | 3 |
| PlanVersion | borrador, aprobado, obsoleto | 3 |

**Total de estados unicos en el sistema: 62**

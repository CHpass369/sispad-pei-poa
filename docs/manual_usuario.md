# Manual del Usuario — SISPAD-PEI-POA

Guia de uso del sistema organizada por rol y funcion.

---

## 1. Informacion General

### 1.1 Acceso al Sistema

1. Abrir el navegador web (Chrome, Firefox o Edge recomendados)
2. Ingresar la URL: `https://tu-dominio.gob.bo`
3. Ingresar email y contrasena
4. Si es el primer login, sera redirigido a cambio de contrasena

### 1.2 Cambio de Contrasena

Al iniciar sesion por primera vez (o cuando `debe_cambiar_password` esta activo):

1. Ingresar contrasena actual
2. Ingresar nueva contrasena (minimo 8 caracteres, con mayuscula, minuscula, numero y especial)
3. Confirmar nueva contrasena
4. Hacer clic en "Guardar"

### 1.3 Elementos de la Interfaz

```
┌─────────────────────────────────────────────────────────────┐
│  [Logo]  SISPAD-PEI-POA          [Notificaciones] [Usuario]│
├──────────┬──────────────────────────────────────────────────┤
│          │                                                  │
│  Menu    │         Contenido Principal                      │
│  Lateral │                                                  │
│          │                                                  │
│ Dashboard│                                                  │
│ POAU     │                                                  │
│ Indicad. │                                                  │
│ ...      │                                                  │
│          │                                                  │
│          │                                                  │
│          │                                                  │
│          │                                                  │
├──────────┴──────────────────────────────────────────────────┤
│  Footer                                                     │
└─────────────────────────────────────────────────────────────┘
```

- **Menu Lateral:** Navegacion por modulos (varia segun rol)
- **Barra Superior:** Notificaciones, perfil de usuario, cerrar sesion
- **Contenido Principal:** Tablas, formularios, dashboards
- **Breadcrumbs:** Ubicacion actual en la navegacion

---

## 2. Funciones Comunes (Todos los Roles)

### 2.1 Dashboard

Al iniciar sesion, cada usuario ve un dashboard adaptado a su rol:

- **Graficos de avance:** Porcentaje de ejecucion fisica y financiera
- **Alertas:** Notificaciones de incumplimiento
- **Resumen de POAU:** Estado de actividades
- **Indicadores clave:** Metas vs avance real

### 2.2 Notificaciones

1. Hacer clic en el icono de campana en la barra superior
2. Ver listado de notificaciones (no leidas resaltadas)
3. Hacer clic en una notificacion para ir al registro relacionado
4. Opcion "Marcar todas como leidas"

**Configurar preferencias:**
1. Ir a Notificaciones > Preferencias
2. Seleccionar: notificaciones internas, correo electronico
3. Elegir frecuencia: inmediata, diaria, semanal
4. Guardar

### 2.3 Busqueda y Filtros

Cada modulo permite:

- **Busqueda por texto:** Campo de busqueda en la parte superior de la tabla
- **Filtros:** Combobox para filtrar por gestion, estado, unidad, etc.
- **Ordenamiento:** Hacer clic en los encabezados de columna
- **Paginacion:** Navegar entre paginas (25 elementos por pagina)

### 2.4 Exportar Datos

En la mayoria de modulos, la tabla de datos ofrece opciones de exportacion:

1. Hacer clic en "Exportar"
2. Seleccionar formato: PDF, XLSX o CSV
3. El archivo se descarga automaticamente
4. Abrir con la aplicacion correspondiente

---

## 3. Rol: Planificador

El planificador es responsable de crear y mantener la planificacion estrategica y presupuestaria.

### 3.1 Gestionar Planes (PEI, PTDI, PDES)

**Crear un plan nuevo:**
1. Navegar a Planificacion > Planes
2. Hacer clic en "Nuevo Plan"
3. Completar:
   - Codigo del plan
   - Nombre
   - Tipo (PDES, PTDI, PEI, Sectorial, Municipal)
   - Gestion de inicio y fin
   - Descripcion
4. Guardar

**Crear nodos de planificacion:**
1. Seleccionar el plan
2. Hacer clic en "Ver Arbol"
3. Hacer clic en "Agregar Nodo"
4. Seleccionar nivel (Pilar, Eje, Meta, Resultado, AMP, ACP)
5. Completar codigo, nombre, descripcion
6. Seleccionar nodo padre (si aplica)
7. Guardar

**Articular nodos:**
1. Seleccionar nodo origen
2. Hacer clic en "Articular"
3. Seleccionar nodo destino
4. Marcar si es articulacion principal
5. Guardar

### 3.2 Gestionar Indicadores

**Crear indicador:**
1. Navegar a Indicadores > Nuevo Indicador
2. Completar:
   - Codigo y nombre
   - Formula de calculo
   - Unidad de medida
   - Tipo de comportamiento (acumulable, promedio, etc.)
   - Linea base y anio
   - Meta anual
   - Medio de verificacion
   - Frecuencia de medicion
3. Guardar

**Programar metas:**
1. Seleccionar indicador
2. Ir a pestana "Metas Programadas"
3. Hacer clic en "Nueva Meta"
4. Seleccionar gestion
5. Ingresar meta anual y metas trimestrales (Q1-Q4)
6. Guardar

### 3.3 Gestionar Presupuesto

**Definir techos presupuestarios:**
1. Navegar a Presupuesto > Techos
2. Hacer clic en "Nuevo Techo"
3. Seleccionar gestion, fuente de financiamiento, monto total
4. Guardar

**Distribuir techos:**
1. Seleccionar techo
2. Hacer clic en "Distribuir"
3. Para cada linea, indicar: DA, UE, Unidad, Programa, monto
4. Verificar que la suma de distribuciones <= techo total
5. Confirmar

**Crear lineas presupuestarias:**
1. Navegar a Presupuesto > Lineas
2. Hacer clic en "Nueva Linea"
3. Completar la llave presupuestaria completa:
   - DA, UE, Programa, Proyecto, Actividad
   - Finalidad/Funcion, Fuente, Organismo
   - Objeto de Gasto, Entidad de Transferencia
   - Importe
4. Guardar

### 3.4 Consolidar POA

1. Verificar que todos los POAUs de las unidades estan aprobados
2. Navegar a Consolidacion
3. Hacer clic en "Consolidar"
4. El sistema genera el POA consolidado
5. Revisar la consolidacion
6. Enviar a validacion de planificacion
7. Esperar validacion del director

---

## 4. Rol: Jefe de Unidad Ejecutora

El jefe de UE supervisa y aprueba el POA de su unidad.

### 4.1 Aprobar POAU

1. Navegar a POAU > Pendientes de Revision
2. Seleccionar el POAU de su unidad
3. Revisar actividades, metas y presupuesto
4. Hacer clic en "Aprobar" o "Rechazar con Observaciones"
5. Si aprueba: el POAU pasa a estado "aprobado"
6. Si rechaza: ingresar observaciones y devolver al borrador

### 4.2 Seguimiento de Ejecucion

1. Navegar a Seguimiento > Reportes
2. Ver reportes de seguimiento de su unidad
3. Revisar avance fisico y financiero por actividad
4. Verificar alertas generadas
5. Responder o escalar segun corresponda

### 4.3 Solicitar Modificaciones

1. Navegar a Modificaciones > Nueva Solicitud
2. Seleccionar tipo de modificacion
3. Indicar entidad afectada
4. Registrar motivo e informe tecnico
5. Enviar a revision

### 4.4 Gestionar Acciones Correctivas

1. Navegar a Acciones Correctivas
2. Ver alertas que requieren accion
3. Crear accion correctiva
4. Asignar responsable y fecha limite
5. Seguir compromisos hasta cierre

---

## 5. Rol: Tecnico de Unidad Ejecutora

El tecnico registra la ejecucion del POA en campo.

### 5.1 Registrar Ejecucion Fisica

1. Navegar a POAU > Actividades
2. Seleccionar actividad
3. Ir a pestana "Ejecucion Fisica"
4. Hacer clic en "Registrar Periodo"
5. Seleccionar periodo (mensual, trimestral, semestral)
6. Ingresar: programado, ejecutado, observaciones
7. Guardar

### 5.2 Registrar Ejecucion Financiera

1. Seleccionar actividad
2. Ir a pestana "Ejecucion Financiera"
3. Hacer clic en "Registrar Periodo"
4. Ingresar: programado, ejecutado, observaciones
5. Guardar

### 5.3 Registrar Entradas de Seguimiento

1. Navegar a Seguimiento > Nueva Entrada
2. Seleccionar reporte de seguimiento
3. Seleccionar actividad del POAU
4. Completar:
   - Programado fisico vs ejecutado fisico
   - Presupuesto inicial vs actual
   - Programado financiero vs ejecutado financiero
   - Porcentajes de avance (calculados automaticamente)
   - Desviacion y causa (si aplica)
   - Evidencia documental
5. Guardar

### 5.4 Ver Indicadores

1. Navegar a Indicadores
2. Filtrar por unidad
3. Ver avance de cada indicador
4. Ver metas programadas vs reales

---

## 6. Rol: Operador del POA

### 6.1 Registrar Actividades

1. Navegar a POAU > Actividades
2. Hacer clic en "Nueva Actividad"
3. Completar:
   - Codigo y nombre
   - Objeto de gasto
   - Meta fisica anual y presupuesto
   - Metas trimestrales (Q1-Q4)
   - Accion de corto plazo (si aplica)
4. Guardar

### 6.2 Registrar Avances

1. Seleccionar actividad
2. Ir a "Registro de Avance"
3. Ingresar datos del periodo
4. Adjuntar evidencia (documentos, fotos)
5. Guardar

### 6.3 Generar Reportes

1. Navegar a Reportes
2. Seleccionar tipo de reporte (POA unidad, seguimiento, etc.)
3. Configurar filtros
4. Hacer clic en "Generar"
5. Esperar generacion
6. Descargar en formato deseado

---

## 7. Rol: Evaluador

### 7.1 Crear Evaluacion

1. Navegar a Evaluacion > Nueva Evaluacion
2. Seleccionar:
   - Plan a evaluar
   - Tipo de evaluacion (anual, medio termino, final, especifica)
   - Periodo (Q1-Q4, S1-S2, AN)
   - Gestion
   - Equipo responsable
3. Guardar

### 7.2 Definir Criterios

1. Seleccionar la evaluacion
2. Ir a pestana "Criterios"
3. Hacer clic en "Agregar Criterio"
4. Para cada criterio:
   - Seleccionar tipo (eficacia, eficiencia, efectividad, pertinencia, impacto, sostenibilidad)
   - Asignar peso (0 a 1, suma total = 1.0)
5. Guardar

### 7.3 Evaluar Criterios

1. Para cada criterio, ingresar:
   - Puntaje (0 a 100)
   - Justificacion
   - Observaciones
2. El sistema calcula el puntaje global automaticamente

### 7.4 Registrar Resultados

1. Ir a pestana "Resultados"
2. Hacer clic en "Agregar Resultado"
3. Seleccionar POAU o unidad a evaluar
4. Calificar: cumple, cumple parcialmente, no cumple
5. Agregar observaciones
6. Guardar

### 7.5 Registrar Lecciones Aprendidas

1. Ir a pestana "Lecciones"
2. Hacer clic en "Nueva Leccion"
3. Completar titulo, descripcion, categoria, recomendaciones
4. Guardar

### 7.6 Generar Recomendaciones

1. Ir a pestana "Recomendaciones"
2. Hacer clic en "Nueva Recomendacion"
3. Completar:
   - Descripcion
   - Prioridad (alta, media, baja)
   - Unidad responsable
   - Fecha limite
4. Guardar

---

## 8. Rol: Director Institucional

### 8.1 Supervision General

1. Dashboard muestra resumen de todas las unidades
2. Ver POAUs consolidados
3. Ver indicadores institucionales
4. Ver alertas y seguimiento

### 8.2 Aprobar Consolidacion

1. Navegar a Consolidacion
2. Revisar POA consolidado
3. Verificar coherencia entre unidades
4. Hacer clic en "Aprobar" o "Observar"
5. Si aprueba: el POA pasa a validacion de presupuesto

---

## 9. Rol: Evaluador de Control Social

### 9.1 Pronunciamiento

1. Navegar a Consolidacion > Pronunciamiento
2. Revisar el POA consolidado
3. Verificar que cumple con las necesidades de la comunidad
4. Registrar pronunciamiento: aprobado o con observaciones
5. Enviar

---

## 10. Rol: Proveedor Externo

### 10.1 Ver Proyectos

1. Navegar a Inversion > Mis Proyectos
2. Ver proyectos asignados
3. Filtrar por etapa, prioridad

### 10.2 Registrar Avance

1. Seleccionar proyecto
2. Hacer clic en "Registrar Avance"
3. Ingresar descripcion del avance
4. Subir documentos de respaldo
5. Guardar

---

## 11. FAQ (Preguntas Frecuentes)

### 11.1 Olvide mi contrasena

Contactar al administrador del sistema para restablecer la contrasena. El administrador puede:
1. Ir a Usuarios > [su usuario] > Editar
2. Hacer clic en "Restablecer contrasena"
3. Ingresar nueva contrasena

### 11.2 No puedo ver un modulo

Verificar que su rol tiene permisos para ese modulo. Si necesita acceso adicional, contactar al administrador.

### 11.3 El sistema esta lento

1. Verificar su conexion a internet
2. Intentar con otro navegador
3. Limpiar cache del navegador
4. Contactar al administrador si el problema persiste

### 11.4 Como exportar un reporte

1. Navegar al modulo con los datos
2. Hacer clic en "Exportar"
3. Seleccionar formato (PDF, XLSX, CSV)
4. Esperar la generacion
5. El archivo se descarga automaticamente

### 11.5 Error al guardar un registro

1. Verificar que todos los campos requeridos estan completos
2. Verificar que los codigos referenciados existen
3. Verificar que las fechas son validas
4. Verificar que los montos son positivos
5. Si el error persiste, contactar al administrador

### 11.6 Como subir un documento

1. En el formulario del registro, buscar campo "Documento adjunto"
2. Hacer clic en "Seleccionar archivo"
3. Elegir el archivo (maximo 10 MB)
4. Guardar el registro
5. El archivo se almacena automaticamente con hash SHA-256

### 11.7 Que hago si detecto un error en los datos

1. Registrar una solicitud de modificacion
2. Indicar el tipo de error
3. Proporcionar evidencia
4. Enviar a revision del tecnico administrativo

### 11.8 Como consultar el historial de cambios

Solo los roles de auditoria (superadmin, control_interno) pueden acceder al log de auditoria. Si necesita verificar un cambio, contactar al administrador.

### 11.9 El sistema muestra "Sesion expirada"

Su token de acceso expiro (4 horas de duracion). El sistema deberia refrescar automaticamente. Si no lo hace:
1. Cerrar sesion
2. Volver a iniciar sesion
3. Si el problema persiste, contactar al administrador

### 11.10 Como ver el estado de mis alertas

1. Navegar a Seguimiento > Alertas
2. Filtrar por estado (activas, resueltas)
3. Revisar severidad y tipo
4. Tomar accion segun corresponda

# Importacion de Excel — SISPAD-PEI-POA

Guia completa de la funcionalidad de importacion de archivos Excel (.xlsx / .xls) al sistema.

---

## 1. Formatos Soportados

| Formato | Extension | Soporte |
|---------|-----------|:-------:|
| Microsoft Excel | `.xlsx` | Completo |
| Microsoft Excel 97-2003 | `.xls` | Completo |
| OpenDocument Spreadsheet | `.ods` | No soportado |
| CSV | `.csv` | No soportado (usar endpoint CSV dedicado) |

**Tamano maximo por archivo:** 10 MB (configurado en `FILE_UPLOAD_MAX_MEMORY_SIZE` y `DATA_UPLOAD_MAX_MEMORY_SIZE`).

---

## 2. Entidades Importables

### 2.1 Catalogos Presupuestarios

#### ObjetoGasto

| Columna Excel | Campo BD | Tipo | Requerido | Validacion |
|---------------|----------|------|:---------:|------------|
| CODIGO | codigo | varchar(50) | Si | Unico por gestion |
| DENOMINACION | denominacion | varchar(500) | Si | No vacio |
| DESCRIPCION | descripcion | text | No | - |
| GESTION | gestion | int | Si | >= 2020 |
| FUENTE NORMATIVA | fuente_normativa | varchar(500) | No | - |

#### FuenteFinanciamiento

| Columna Excel | Campo BD | Tipo | Requerido | Validacion |
|---------------|----------|------|:---------:|------------|
| CODIGO | codigo | varchar(50) | Si | Unico por gestion |
| DENOMINACION | denominacion | varchar(500) | Si | No vacio |
| DESCRIPCION | descripcion | text | No | - |
| GESTION | gestion | int | Si | >= 2020 |

#### OrganismoFinanciador

| Columna Excel | Campo BD | Tipo | Requerido | Validacion |
|---------------|----------|------|:---------:|------------|
| CODIGO | codigo | varchar(50) | Si | Unico por gestion |
| DENOMINACION | denominacion | varchar(500) | Si | No vacio |
| DESCRIPCION | descripcion | text | No | - |
| GESTION | gestion | int | Si | >= 2020 |

#### FinalidadFuncion

| Columna Excel | Campo BD | Tipo | Requerido | Validacion |
|---------------|----------|------|:---------:|------------|
| CODIGO | codigo | varchar(50) | Si | Unico por gestion |
| DENOMINACION | denominacion | varchar(500) | Si | No vacio |
| GESTION | gestion | int | Si | >= 2020 |

#### RubroRecurso

| Columna Excel | Campo BD | Tipo | Requerido | Validacion |
|---------------|----------|------|:---------:|------------|
| CODIGO | codigo | varchar(50) | Si | Unico por gestion |
| DENOMINACION | denominacion | varchar(500) | Si | No vacio |
| GESTION | gestion | int | Si | >= 2020 |

#### UnidadMedida

| Columna Excel | Campo BD | Tipo | Requerido | Validacion |
|---------------|----------|------|:---------:|------------|
| CODIGO | codigo | varchar(50) | Si | Unico por gestion |
| DENOMINACION | denominacion | varchar(500) | Si | No vacio |
| GESTION | gestion | int | Si | >= 2020 |

#### EntidadTransferencia

| Columna Excel | Campo BD | Tipo | Requerido | Validacion |
|---------------|----------|------|:---------:|------------|
| CODIGO | codigo | varchar(50) | Si | Unico por gestion |
| DENOMINACION | denominacion | varchar(500) | Si | No vacio |
| GESTION | gestion | int | Si | >= 2020 |

### 2.2 Techos Presupuestarios

| Columna Excel | Campo BD | Tipo | Requerido | Validacion |
|---------------|----------|------|:---------:|------------|
| GESTION | gestion | int | Si | >= 2020, gestion activa |
| FUENTE | fuente_codigo | varchar | Si | Debe existir en FuenteFinanciamiento |
| ORGANISMO | organismo_codigo | varchar | No | Debe existir si se indica |
| MONTO TOTAL | monto_total | decimal(20,2) | Si | >= 0 |
| DESCRIPCION | descripcion | text | No | - |

### 2.3 Distribuciones de Techo

| Columna Excel | Campo BD | Tipo | Requerido | Validacion |
|---------------|----------|------|:---------:|------------|
| GESTION | gestion | int | Si | >= 2020 |
| FUENTE CODIGO | fuente_codigo | varchar | Si | Debe existir |
| DA CODIGO | da_codigo | varchar | Si | Debe existir en DireccionAdministrativa |
| UE CODIGO | ue_codigo | varchar | Si | Debe existir en UnidadEjecutora |
| UNIDAD CODIGO | unidad_codigo | varchar | No | Debe existir si se indica |
| PROGRAMA CODIGO | programa_codigo | varchar | No | Debe existir si se indica |
| MONTO ASIGNADO | monto_asignado | decimal(20,2) | Si | >= 0, suma <= techo |
| MONTO RESERVA | monto_reserva | decimal(20,2) | No | Default 0 |

### 2.4 POAU y Actividades

#### POAU (Plan Operativo Anual)

| Columna Excel | Campo BD | Tipo | Requerido | Validacion |
|---------------|----------|------|:---------:|------------|
| CODIGO | codigo | varchar(50) | Si | Unico en el sistema |
| NOMBRE | nombre | text | Si | No vacio |
| DESCRIPCION | descripcion | text | No | - |
| GESTION | gestion | int | Si | Gestion activa |
| UNIDAD CODIGO | unidad_codigo | varchar | Si | Debe existir |
| PRODUCTO TERRITORIAL CODIGO | producto_codigo | varchar | No | Debe existir si se indica |
| RESPONSABLE EMAIL | responsable_email | varchar | No | Debe existir usuario si se indica |

#### POAUActividad

| Columna Excel | Campo BD | Tipo | Requerido | Validacion |
|---------------|----------|------|:---------:|------------|
| POAU CODIGO | poau_codigo | varchar | Si | Debe existir POAU |
| CODIGO | codigo | varchar(50) | Si | Unico dentro del POAU |
| NOMBRE | nombre | text | Si | No vacio |
| OBJETO GASTO CODIGO | objeto_gasto_codigo | varchar | No | Debe existir si se indica |
| META FISICA ANUAL | meta_fisica_anual | decimal(20,4) | No | >= 0 |
| PRESUPUESTO ANUAL | presupuesto_anual | decimal(20,2) | No | >= 0 |
| META Q1 | meta_q1 | decimal(20,4) | No | Si se define Q1-Q4, suma = meta_anual |
| META Q2 | meta_q2 | decimal(20,4) | No | - |
| META Q3 | meta_q3 | decimal(20,4) | No | - |
| META Q4 | meta_q4 | decimal(20,4) | No | - |

### 2.5 Indicadores

| Columna Excel | Campo BD | Tipo | Requerido | Validacion |
|---------------|----------|------|:---------:|------------|
| CODIGO | codigo | varchar(50) | Si | Unico |
| NOMBRE | nombre | text | Si | No vacio |
| DESCRIPCION | descripcion | text | No | - |
| FORMULA | formula | text | No | - |
| UNIDAD MEDIDA CODIGO | unidad_medida_codigo | varchar | No | Debe existir si se indica |
| TIPO COMPORTAMIENTO | tipo_comportamiento | varchar | Si | Valor valido: acumulable, no_acumulable, promedio, hito, porcentaje, cualitativo |
| LINEA BASE | linea_base | decimal(20,4) | No | - |
| ANIO LINEA BASE | anio_linea_base | int | No | - |
| META ANUAL | meta_anual | decimal(20,4) | No | >= 0 |
| MEDIO VERIFICACION | medio_verificacion | text | No | - |
| RESPONSABLE EMAIL | responsable_email | varchar | No | Debe existir usuario si se indica |

### 2.6 Metas Programadas

| Columna Excel | Campo BD | Tipo | Requerido | Validacion |
|---------------|----------|------|:---------:|------------|
| INDICADOR CODIGO | indicador_codigo | varchar | Si | Debe existir indicador |
| GESTION | gestion | int | Si | >= 2020 |
| META ANUAL | meta_anual | decimal(20,4) | Si | >= 0 |
| TRIMESTRE 1 | trimestre1 | decimal(20,4) | No | - |
| TRIMESTRE 2 | trimestre2 | decimal(20,4) | No | - |
| TRIMESTRE 3 | trimestre3 | decimal(20,4) | No | - |
| TRIMESTRE 4 | trimestre4 | decimal(20,4) | No | - |
| OBSERVACIONES | observaciones | text | No | - |

### 2.7 Lineas Presupuestarias

| Columna Excel | Campo BD | Tipo | Requerido | Validacion |
|---------------|----------|------|:---------:|------------|
| GESTION | gestion | int | Si | Gestion activa |
| ENTIDAD | entidad | varchar(20) | Si | Codigo de entidad |
| DA CODIGO | da_codigo | varchar | Si | Debe existir |
| UE CODIGO | ue_codigo | varchar | Si | Debe existir |
| PROGRAMA CODIGO | programa_codigo | varchar | Si | Debe existir |
| PROYECTO CODIGO | proyecto_codigo | varchar | No | Debe existir si se indica |
| ACTIVIDAD CODIGO | actividad_codigo | varchar | No | Debe existir si se indica |
| FINALIDAD CODIGO | finalidad_funcion_codigo | varchar | Si | Debe existir |
| FUENTE CODIGO | fuente_codigo | varchar | Si | Debe existir |
| ORGANISMO CODIGO | organismo_codigo | varchar | No | Debe existir si se indica |
| OBJETO GASTO CODIGO | objeto_gasto_codigo | varchar | Si | Debe existir |
| ENTIDAD TRANSFERENCIA CODIGO | entidad_transferencia_codigo | varchar | No | Debe existir si se indica |
| IMPORTE | importe | decimal(20,2) | Si | >= 0 |

### 2.8 Proyectos de Inversion

| Columna Excel | Campo BD | Tipo | Requerido | Validacion |
|---------------|----------|------|:---------:|------------|
| CODIGO INTERNO | codigo_interno | varchar(50) | Si | Unico |
| CODIGO SISIN | codigo_sisin | varchar(100) | No | - |
| NOMBRE | nombre | varchar(500) | Si | No vacio |
| DESCRIPCION | descripcion | text | No | - |
| TIPO CODIGO | tipo_codigo | varchar | No | Debe existir en TipoProyecto |
| PRIORIDAD | prioridad | int | Si | 1-4 |
| ETAPA | etapa | varchar | Si | preinversion, inversion, cierre, operacion |
| UE CODIGO | ue_codigo | varchar | Si | Debe existir |
| PROGRAMA CODIGO | programa_codigo | varchar | Si | Debe existir |
| FUENTE CODIGO | fuente_codigo | varchar | Si | Debe existir |
| COSTO TOTAL | costo_total | decimal(20,2) | Si | >= 0 |
| GESTION INICIO | gestion_inicio | int | Si | >= 2020 |
| GESTION FIN | gestion_fin | int | No | >= gestion_inicio |

### 2.9 Resultados Territoriales del PAD

| Columna Excel | Campo BD | Tipo | Requerido | Validacion |
|---------------|----------|------|:---------:|------------|
| CODIGO | codigo | varchar(50) | Si | Unico por lineamiento y gestion |
| NOMBRE | nombre | text | Si | No vacio |
| LINEAMIENTO CODIGO | lineamiento_codigo | varchar | Si | Debe existir |
| SECTOR CODIGO | sector_codigo | varchar | No | Debe existir si se indica |
| GESTION | gestion | int | Si | >= 2020 |
| INDICADOR | indicador | text | No | - |
| FORMULA | formula | text | No | - |
| LINEA BASE | linea_base | decimal(20,4) | No | >= 0 |
| META 2030 | meta_2030 | decimal(20,4) | No | >= 0 |
| CODIGO GEOGRAFICO | cod_geografico | varchar(20) | No | - |

### 2.10 Programacion Anual del PAD

| Columna Excel | Campo BD | Tipo | Requerido | Validacion |
|---------------|----------|------|:---------:|------------|
| RESULTADO CODIGO | resultado_codigo | varchar | Si* | *Obligatorio si no se indica producto |
| PRODUCTO CODIGO | producto_codigo | varchar | Si* | *Obligatorio si no se indica resultado |
| ANIO | anio | int | Si | >= 2020 |
| TIPO | tipo | varchar | Si | fisica, financiera |
| VALOR | valor | decimal(20,4) | Si | >= 0 |

---

## 3. Reglas de Validacion Generales

### 3.1 Validaciones de Cabecera

1. **Formato:** El archivo debe ser .xlsx o .xls
2. **Tamano:** Maximo 10 MB
3. **Hoja:** Se procesa la primera hoja del libro
4. **Encabezados:** La primera fila debe contener los nombres de columnas exactos
5. **Filas vacias:** Se omiten filas completamente vacias
6. **Minimo:** Al menos 1 fila de datos (ademas de encabezados)

### 3.2 Validaciones de Campo

| Regla | Descripcion |
|-------|-------------|
| Requerido | No puede estar vacio ni ser null |
| Unico | No puede duplicarse en la misma gestion |
| FK existente | La referencia debe existir en la tabla destino |
| Tipo numerico | Debe ser numero valido (entero o decimal) |
| Tipo fecha | Formato: YYYY-MM-DD o DD/MM/YYYY |
| Tipo texto | Maximo de caracteres segun campo |
| Rango | Valor dentro del rango permitido |

### 3.3 Validaciones de Negocio

1. **Suma de trimestres:** Q1+Q2+Q3+Q4 = meta_fisica_anual
2. **Presupuesto <= Techo:** No puede exceder el techo asignado
3. **Fechas consistentes:** fecha_inicio < fecha_fin
4. **Gestion vigente:** La gestion debe estar en estado abierto o formulacion
5. **Coherencia jerarquica:** Proyecto pertenece a Programa, Actividad a Proyecto

---

## 4. Manejo de Errores

### 4.1 Formato del Reporte de Errores

Cuando la importacion encuentra errores, retorna un archivo Excel con:

| Columna | Descripcion |
|---------|-------------|
| Fila | Numero de fila en el archivo original (empezando en 2) |
| Columna | Nombre de la columna con error |
| Error | Descripcion del error en espanol |
| Valor | Valor encontrado en la celda |
| Sugerencia | Sugerencia de correccion (cuando aplica) |

### 4.2 Tipos de Error

| Codigo | Tipo | Descripcion | Accion |
|--------|------|-------------|--------|
| E001 | Requerido | Campo obligatorio vacio | Completar el campo |
| E002 | Unico | Codigo duplicado en la gestion | Usar un codigo diferente |
| E003 | FK | Referencia a registro inexistente | Verificar el codigo en el catalogo |
| E004 | Tipo | Tipo de dato incorrecto | Corregir el formato |
| E005 | Rango | Valor fuera de rango permitido | Ajustar el valor |
| E006 | Negocio | Incumplimiento de regla de negocio | Corregir segun la regla |
| E007 | Formato | Formato de archivo invalido | Convertir a .xlsx o .xls |
| E008 | Tamanio | Archivo excede el limite | Reducir el tamano del archivo |
| E009 | Encabezado | Columna requerida no encontrada | Verificar encabezados |
| E010 | Duplicado | Fila duplicada en el archivo | Eliminar duplicados |

### 4.3 Modo de Procesamiento

El sistema procesa las importaciones en modo **transaccional**:
- Si hay errores, **ningun registro se inserta** (rollback completo)
- Se retorna el reporte de errores
- El usuario corrige y re-intenta
- Solo cuando todas las filas pasan validacion se ejecuta la insercion

---

## 5. Guia Paso a Paso

### 5.1 Importar Catalogos

1. Navegar a **Catalogos** en el menu lateral
2. Seleccionar el tipo de catalogo (ej: ObjetoGasto)
3. Hacer clic en **Importar Excel**
4. Descargar la **plantilla Excel** (opcional pero recomendado)
5. Llenar la plantilla con los datos
6. Arrastrar o seleccionar el archivo .xlsx
7. El sistema muestra una **vista previa** con conteo de filas
8. Hacer clic en **Validar**
9. Revisar el reporte de errores (si existe)
10. Corregir errores en el archivo
11. Re-subir y re-validar
12. Hacer clic en **Confirmar Importacion**
13. El sistema muestra resumen: "X registros importados exitosamente"

### 5.2 Importar Techos Presupuestarios

1. Navegar a **Presupuesto > Techos**
2. Hacer clic en **Importar Techos**
3. Seleccionar archivo con formato de columnas establecido
4. Validar que los codigos de fuente y organismo existan
5. Confirmar la importacion
6. Verificar que la suma de distribuciones no exceda el techo total

### 5.3 Importar POAU con Actividades

1. Navegar a **POAU**
2. Hacer clic en **Importar POAU**
3. Seleccionar archivo con POAUs y actividades
4. El sistema valida:
   - Que la unidad organizacional exista
   - Que el producto territorial exista (si se indica)
   - Que el objeto de gasto exista (si se indica)
   - Coherencia de metas trimestrales
5. Confirmar importacion

### 5.4 Importar Indicadores

1. Navegar a **Indicadores**
2. Hacer clic en **Importar Indicadores**
3. Seleccionar archivo con indicadores y metas programadas
4. El sistema valida:
   - Unicidad de codigo de indicador
   - Tipo de comportamiento valido
   - Unidad de medida existente
   - Responsable existente (si se indica email)
5. Confirmar importacion

---

## 6. Plantillas Excel

Las plantillas se generan dinamicamente y contienen:
- Encabezados con los nombres exactos de columnas
- Primera fila de ejemplo con datos validos
- Comentarios en celdas con formato esperado
- Validaciones de lista desplegable (donde aplica)
- Formato condicional para campos requeridos (resaltados en amarillo)

Para descargar una plantilla:
1. Ir al modulo correspondiente
2. Hacer clic en **Importar**
3. Hacer clic en **Descargar Plantilla**

---

## 7. Consideraciones Tecnicas

### 7.1 Rendimiento

- **Maximo recomendado:** 10,000 filas por importacion
- **Tiempo estimado:** ~100 filas/segundo (dependiendo de validaciones)
- **Memoria:** Procesamiento streaming para archivos grandes

### 7.2 Concurrencia

- Las importaciones se procesan de forma secuencial por modulo
- Si hay una importacion en curso, se bloquea otra para el mismo modulo
- No hay bloqueo entre modulos diferentes

### 7.3 Auditoria

Cada importacion exitosa genera:
- Registro en `EventoAuditoria` con accion = 'importar'
- `datos_previos`: conteo de registros antes
- `datos_posteriores`: conteo de registros despues
- Usuario que ejecuto la importacion
- Timestamp y direccion IP

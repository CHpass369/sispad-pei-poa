# PLAN MAESTRO DE REFACTORIZACIÓN
## Plataforma Integral de Planificación del Gobierno Autónomo Municipal de Sacaba (PIP-GAMS)
### SIS-PE + SIS-POA + SIS-PRO

**Base revisada:** proyecto `SIS PAD PEI.zip` entregado el 9 de agosto de 2026.  
**Estrategia:** refactorización incremental, preservando datos y funcionalidad; monolito modular Django + Angular + PostgreSQL/PostGIS.

---

## 1. Objetivo de la refactorización

Transformar el sistema actual SISPAD/PEI/POA en una **Plataforma Integral de Planificación del GAMS**, organizada por tres dominios funcionales:

1. **SIS-PE — Sistema de Planificación Estratégica**
   - instrumentos de planificación;
   - PGDESA/PGDES, PDESA/PDES y otros instrumentos superiores;
   - PAD;
   - PEI;
   - diagnóstico;
   - participación;
   - articulación estratégica;
   - indicadores y metas;
   - territorialización;
   - seguimiento y evaluación estratégica.
2. **SIS-POA — Sistema de Planificación Operativa Anual**
   - POA institucional;
   - POAU por unidad;
   - acciones de corto plazo;
   - operaciones, actividades y tareas;
   - techos;
   - recursos;
   - presupuesto;
   - programación física-financiera;
   - modificaciones;
   - seguimiento operativo.
3. **SIS-PRO — Sistema de Gestión del Ciclo del Proyecto**
   - cartera de proyectos;
   - condiciones previas;
   - preinversión;
   - ITCP/EDTP y documentos equivalentes;
   - costos y presupuesto de proyecto;
   - programación;
   - contratación;
   - ejecución;
   - supervisión/fiscalización;
   - cierre y evaluación.

Los tres SIS compartirán un **núcleo transversal único** para identidad, organización, periodos, catálogos, normativa, territorio, indicadores, workflow, documentos, auditoría, notificaciones, reportes e interoperabilidad.

---

## 2. Diagnóstico del código actual

La base existente es aprovechable y no debe reescribirse desde cero.

### 2.1 Inventario técnico observado

- 26 aplicaciones Django.
- 27 áreas funcionales Angular.
- Django/DRF + PostgreSQL/PostGIS.
- Angular + Angular Material.
- Redis/Celery previstos.
- MinIO previsto.
- GeoServer previsto.
- Keycloak/OIDC previsto.
- Auditoría, workflow, documentos, reportes y seguimiento ya iniciados.
- Versionado de planes parcialmente implementado.
- Programación PAD parcialmente normalizada desde JSON hacia tablas relacionales.

### 2.2 Problemas arquitectónicos prioritarios

1. **Solapamiento de dominios.**
   `planificacion`, `pad`, `articulacion` y `codificacion` representan parcialmente la misma cadena estratégica.
2. **Duplicidad conceptual.**
   Existen representaciones distintas de lineamientos, resultados y productos PAD, y estructuras PEI/POA dentro de `articulacion`.
3. **App `articulacion` sobredimensionada.**
   Contiene elementos estratégicos PAD/PEI, indicadores, POA, POAU, tareas, seguimiento presupuestario y objeto del gasto.
4. **App `indicadores` mezcla dominios.**
   Además de indicadores contiene Operación, Tarea y Producto, que son conceptos de planificación operativa.
5. **`planificacion` mezcla mediano y corto plazo.**
   `AccionMedianoPlazo` pertenece al dominio estratégico/PEI, pero `AccionCortoPlazo` pertenece a SIS-POA.
6. **PAD rígido y parcialmente duplicado.**
   El modelo actual tiene tablas específicas y una articulación SIPEB con columnas fijas para PGDESA, PDESA, ODS, NDC, NDT, etc.
7. **Tipos de nodo rígidos.**
   `NodoPlanificacion.NIVEL_CHOICES` está codificado en Python. Debe ser configurable por metodología/versión.
8. **Permisos frontend hard-codeados por rol.**
   El menú y acciones dependen de códigos como `superadmin`, `tecnico_admin`, `planificador`, etc.
9. **Autorización backend heterogénea.**
   Debe consolidarse una política uniforme y revisar individualmente todo endpoint `AllowAny`.
10. **Rutas API poco consistentes.**
    Hay aplicaciones montadas en el prefijo raíz y otras bajo subrutas, e incluso `planificacion` se incluye bajo dos prefijos.
11. **Documentación desalineada con el código.**
    Algunos documentos marcan como pendientes componentes que ya existen parcialmente y las versiones de infraestructura difieren entre documentos.
12. **Nomenclatura heredada.**
    Persisten referencias a PTDI/PDES y descripciones departamentales en componentes destinados a planificación municipal; deben mantenerse como compatibilidad histórica, no como semántica principal.

---

## 3. Principios no negociables

1. Una sola fuente de verdad para cada concepto.
2. No duplicar estructuras PAD/PEI/POA entre apps.
3. Instrumentos y metodologías parametrizables.
4. Versiones aprobadas inmutables.
5. Trazabilidad completa de relaciones y modificaciones.
6. UUID para identificadores públicos.
7. Auditoría append-only para eventos relevantes.
8. Relaciones de negocio con integridad referencial real; evitar `tipo + id` genérico para relaciones críticas.
9. Datos territoriales en PostGIS.
10. API versionada.
11. Backend como autoridad de permisos.
12. Menú frontend derivado de capacidades, no de roles hard-codeados.
13. Refactor incremental sin big-bang.
14. Compatibilidad temporal con API V1.
15. Pruebas y reconciliación de datos como condición para retirar legacy.
16. No introducir microservicios en esta etapa.

---

## 4. Arquitectura funcional objetivo

```text
PIP-GAMS
|
|-- Inicio / Tablero Integral
|
|-- SIS-PE
|   |-- Instrumentos y metodologías
|   |-- Marco nacional/sectorial/internacional
|   |-- Diagnóstico integral
|   |-- Participación
|   |-- PAD
|   |-- PEI
|   |-- Articulación estratégica
|   |-- Indicadores y metas
|   |-- Territorialización
|   |-- Programación plurianual
|   |-- Validación metodológica
|   |-- Seguimiento estratégico
|   `-- Evaluación y ajustes
|
|-- SIS-POA
|   |-- POA institucional
|   |-- POAU
|   |-- Acciones de corto plazo
|   |-- Operaciones
|   |-- Actividades
|   |-- Tareas
|   |-- Recursos
|   |-- Techos
|   |-- Presupuesto
|   |-- Programación física-financiera
|   |-- Modificaciones
|   `-- Seguimiento operativo
|
|-- SIS-PRO
|   |-- Cartera de proyectos
|   |-- Condiciones previas
|   |-- Preinversión
|   |-- Formulación
|   |-- Costos
|   |-- Contratación
|   |-- Ejecución
|   |-- Supervisión/Fiscalización
|   `-- Cierre/Evaluación
|
`-- Plataforma / Administración
    |-- Usuarios, roles, permisos y alcances
    |-- Organización GAMS
    |-- Periodos y ciclos
    |-- Catálogos
    |-- Normativa
    |-- Codificación
    |-- Banco Municipal de Indicadores
    |-- Territorio
    |-- Workflow
    |-- Documentos
    |-- Notificaciones
    |-- Auditoría
    |-- Reportes
    `-- Interoperabilidad
```

---

## 5. Estrategia física de Django

### 5.1 Regla principal

**No renombrar ni mover masivamente las apps existentes durante las primeras fases.** Los app labels de Django y sus migraciones forman parte del estado histórico de la base de datos.

Primero se reorganizan:

- límites de dominio;
- servicios;
- endpoints;
- modelos V2;
- frontend;
- permisos.

Los cambios de nombres físicos son opcionales al final y solo si aportan valor real.

### 5.2 Apps existentes que se conservan como núcleo transversal

- `core`
- `accounts`
- `organizacion`
- `gestion`
- `catalogos`
- `normativa`
- `codificacion` — reducido a motor de codificación/catálogos oficiales, no como segundo modelo estratégico.
- `territorio`
- `workflow`
- `documentos`
- `notificaciones`
- `auditoria`
- `reportes`

### 5.3 Apps a refactorizar por dominio

- `planificacion` → núcleo genérico de instrumentos estratégicos.
- `pad` → contenido específico del PAD que no pueda representarse genéricamente.
- `articulacion` → migrar y dividir; dejar de ser contenedor de todo el ciclo.
- `indicadores` → Banco Municipal de Indicadores; sacar Operación/Tarea/Producto.
- `poau` → SIS-POA.
- `recursos`, `techos`, `presupuesto` → SIS-POA financiero/presupuestario.
- `seguimiento`, `acciones_correctivas` → motor de seguimiento con alcance por dominio.
- `evaluacion` → motor de evaluación con alcance estratégico/operativo.
- `modificaciones` → motor transversal de ajustes, con reglas específicas por dominio.
- `inversion` → semilla del futuro SIS-PRO, no sistema completo.

### 5.4 Apps nuevas necesarias

- `pei` — contenido institucional específico del PEI.
- `poa` — POA institucional consolidado, separado del POAU.
- para SIS-PRO, según crecimiento:
  - `proyectos` o evolución controlada de `inversion`;
  - `preinversion`;
  - `contratacion`;
  - `ejecucion_proyectos`.

No crear todas las apps SIS-PRO en la primera iteración si todavía no existe lógica funcional; primero definir contratos y límites.

---

## 6. Mapa de los 26 módulos actuales

| App actual | Destino | Acción |
|---|---|---|
| `core` | Plataforma | Conservar y fortalecer |
| `accounts` | IAM Plataforma | Refactor mayor de autorización |
| `organizacion` | Plataforma | Conservar; agregar institución/alcances |
| `gestion` | Plataforma | Convertir en periodos/ciclos reutilizables |
| `catalogos` | Plataforma | Conservar y normalizar versionado |
| `normativa` | Plataforma | Conservar; unificar normativa duplicada |
| `codificacion` | Plataforma + soporte SIS-PE | Conservar motor; retirar jerarquía estratégica duplicada cuando migre |
| `territorio` | Plataforma GIS | Conservar y ampliar |
| `workflow` | Plataforma | Refactor a definiciones/instancias configurables |
| `documentos` | Plataforma | Conservar; migrar almacenamiento a S3/MinIO |
| `notificaciones` | Plataforma | Conservar |
| `auditoria` | Plataforma | Conservar y reforzar append-only |
| `reportes` | Plataforma | Conservar; separar plantillas por SIS |
| `planificacion` | SIS-PE | Transformar en kernel estratégico V2 |
| `pad` | SIS-PE/PAD | Refactor y migración hacia kernel estratégico |
| `articulacion` | SIS-PE + SIS-POA + Plataforma | Dividir; app legacy temporal |
| `indicadores` | Banco Municipal de Indicadores | Conservar indicadores; mover entidades operativas |
| `poau` | SIS-POA | Refactor |
| `recursos` | SIS-POA | Conservar |
| `techos` | SIS-POA | Conservar/refinar |
| `presupuesto` | SIS-POA | Conservar/refinar |
| `seguimiento` | Seguimiento | Generalizar por dominio |
| `acciones_correctivas` | Seguimiento | Integrar con seguimiento |
| `evaluacion` | Evaluación | Refactor por alcance |
| `modificaciones` | Ajustes | Refactor transversal |
| `inversion` | SIS-PRO | Usar como semilla y ampliar |

---

## 7. SIS-PE V2 — núcleo estratégico

### 7.1 Módulos funcionales

1. Instrumentos de planificación.
2. Metodologías y versiones.
3. Marco superior: PGDESA/PGDES, PDESA/PDES, planes sectoriales y compromisos pertinentes.
4. Diagnóstico integral municipal.
5. Participación y demanda social.
6. Formulación PAD.
7. Formulación PEI.
8. Articulación estratégica.
9. Banco de indicadores y metas.
10. Territorialización.
11. Competencias y responsables.
12. Programación plurianual.
13. Validación metodológica y concordancia.
14. Workflow y aprobación.
15. Seguimiento estratégico.
16. Evaluación y ajustes.
17. Generación documental y matrices.

### 7.2 Modelo estratégico genérico propuesto

#### `TipoInstrumento`
- código;
- nombre;
- nivel: nacional/sectorial/territorial/institucional/operativo;
- horizonte;
- entidad emisora;
- activo.

#### `InstrumentoPlanificacion`
- UUID;
- tipo;
- código;
- nombre;
- institución responsable;
- periodo inicio/fin;
- ámbito;
- estado;
- descripción.

#### `VersionInstrumento`
- instrumento;
- número;
- nombre/etiqueta;
- metodología;
- estado;
- vigencia;
- fecha de aprobación;
- aprobado por;
- norma/documento de aprobación;
- motivo del cambio;
- inmutable;
- checksum/version de datos.

#### `VersionMetodologia`
- código;
- nombre;
- instrumento aplicable;
- vigencia;
- fuente oficial;
- estado;
- esquema de validación.

#### `TipoNodoEstrategico`
- código;
- denominación;
- metodología;
- nivel/orden;
- permite hijos;
- cardinalidad;
- reglas de código;
- campos obligatorios parametrizados.

#### `NodoEstrategico`
- versión de instrumento;
- tipo de nodo;
- padre;
- código;
- nombre;
- descripción;
- orden;
- estado;
- atributos adicionales controlados.

#### `TipoVinculoEstrategico`
- código;
- origen permitido;
- destino permitido;
- cardinalidad;
- requiere ponderación;
- requiere justificación.

#### `VinculoEstrategico`
- nodo origen;
- nodo destino;
- tipo;
- es principal;
- ponderación/contribución;
- justificación;
- estado;
- validador/fecha de validación.

### 7.3 Regla estructural

Las matrices deben ser **proyecciones de estas relaciones**, no tablas maestras independientes.

---

## 8. Migración de los modelos estratégicos actuales

### 8.1 Equivalencias

| Modelo legacy | Destino V2 |
|---|---|
| `planificacion.Plan` | `InstrumentoPlanificacion` |
| `planificacion.PlanVersion` | `VersionInstrumento` |
| `planificacion.NodoPlanificacion` | `NodoEstrategico` |
| `planificacion.ArticulacionPlanificacion` | `VinculoEstrategico` |
| `planificacion.AccionMedianoPlazo` | nodo/tipo de acción PEI |
| `planificacion.AccionCortoPlazo` | SIS-POA `AccionPOA` |
| `pad.LineamientoEstrategico` | nodo PAD |
| `pad.ResultadoTerritorial` | nodo PAD resultado |
| `pad.ProductoTerritorial` | nodo PAD producto |
| `articulacion.LineamientoPAD` | fusionar/migrar a nodo PAD |
| `articulacion.ResultadoPAD` | fusionar/migrar a nodo PAD |
| `articulacion.ProductoPAD` | fusionar/migrar a nodo PAD |
| `articulacion.ResultadoPEI` | nodo PEI |
| `articulacion.ProductoPEI` | nodo PEI |
| `articulacion.ArticulacionPADPEI` | vínculo estratégico PAD→PEI |
| `pad.ArticulacionSIPEB` | varios vínculos estratégicos, no columnas fijas |
| `codificacion.EjePGDESA` | nodo de instrumento nacional importado |
| `codificacion.ComponentePDESA` | nodo de instrumento nacional importado |
| `codificacion.SectorEconomico` | nodo/catálogo asociado según metodología |
| `codificacion.ResultadoSectorial` | nodo de instrumento sectorial |
| `articulacion.IndicadorCadena` | Banco Municipal de Indicadores + vínculos |
| `articulacion.AccionPOA` | SIS-POA |
| `articulacion.OperacionPOAU` | SIS-POA |
| `articulacion.ActividadPOAU` | SIS-POA |
| `articulacion.TareaPOAU` | SIS-POA |
| `articulacion.SeguimientoPresupuesto` | SIS-POA seguimiento/presupuesto |
| `articulacion.AsignacionObjetoGasto` | SIS-POA presupuesto |

### 8.2 Regla de migración

No borrar los modelos legacy al crear V2.

Implementar:

`expandir → backfill → reconciliar → cortar escritura legacy → cambiar API/frontend → observar → retirar legacy`.

Crear una tabla técnica `LegacyMigrationMap` con:

- app/model legacy;
- UUID legacy;
- tipo destino;
- UUID destino;
- lote de migración;
- checksum;
- estado;
- fecha;
- observaciones.

---

## 9. PAD V2

El PAD debe ser un flujo guiado por metodología, no un conjunto de formularios independientes.

### 9.1 Componentes

- contexto y configuración del PAD;
- diagnóstico territorial;
- datos base e indicadores;
- participación social;
- problemas;
- potencialidades;
- desafíos;
- políticas/lineamientos según metodología vigente;
- resultados;
- productos/acciones según metodología;
- indicadores;
- línea base;
- metas plurianuales;
- territorialización;
- responsables;
- competencias;
- programación física;
- programación financiera;
- fuentes de verificación;
- riesgos/supuestos;
- articulación con instrumentos superiores;
- validación;
- generación de matrices/documento.

### 9.2 Avance metodológico

Cada sección debe producir un estado:

- no iniciado;
- en elaboración;
- con observaciones;
- completo;
- validado;
- aprobado.

El sistema debe calcular porcentaje de avance por requisito metodológico y no solamente por número de formularios.

---

## 10. PEI V2

Crear app `pei` para información institucional específica que no sea jerarquía estratégica genérica.

### 10.1 Componentes PEI

- diagnóstico institucional;
- mandato legal y competencias;
- misión;
- visión;
- principios/valores cuando la metodología lo requiera;
- análisis de capacidades;
- objetivos estratégicos institucionales;
- resultados/acciones estratégicas institucionales;
- indicadores;
- líneas base;
- metas plurianuales;
- responsables organizacionales;
- presupuesto plurianual indicativo;
- riesgos/supuestos;
- articulación PAD→PEI;
- seguimiento y evaluación.

### 10.2 Regla principal

El PEI no debe duplicar el PAD. Debe representar la contribución institucional del GAMS a resultados territoriales y prioridades superiores.

---

## 11. Banco Municipal de Indicadores

Refactorizar `indicadores` para que sea transversal.

### 11.1 Separar del app

Mover fuera de `indicadores`:

- `Operacion`;
- `Tarea`;
- `Producto` cuando represente producto operativo;
- cualquier entidad POA/POAU.

### 11.2 Modelo objetivo

- `Indicador`;
- `DefinicionIndicador`/versión;
- `LineaBaseIndicador`;
- `MetaIndicador`;
- `MedicionIndicador`;
- `FuenteDatoIndicador`;
- `MedioVerificacion`;
- `ResponsableIndicador`;
- `DesagregacionIndicador`;
- `VinculoIndicadorNodo`;
- `VinculoIndicadorProyecto` cuando corresponda;
- `CalidadDatoIndicador`.

El indicador se define una sola vez y se vincula a PAD, PEI, POA, proyectos o tableros según corresponda.

---

## 12. Territorialización

Mantener `territorio` como servicio transversal.

### 12.1 Evolución

- catálogo territorial jerárquico;
- geometrías oficiales versionadas;
- distrito/OTB/comunidad/u otras unidades;
- vínculo espacial con nodos estratégicos;
- vínculo con indicadores;
- vínculo con acciones POA;
- vínculo con proyectos SIS-PRO;
- fuente y fecha de geometría;
- SRID institucional configurable;
- representación 4326 para interoperabilidad web cuando corresponda.

### 12.2 Integridad

Para relaciones críticas crear tablas explícitas (`NodoTerritorio`, `ProyectoTerritorio`, etc.). Mantener asociaciones genéricas solo para usos transversales como documentos/auditoría cuando sea razonable.

---

## 13. SIS-POA V2

### 13.1 Cadena operativa objetivo

```text
PEI / Acción Estratégica Institucional
        ↓
POA Institucional
        ↓
Acción de Corto Plazo
        ↓
POAU / Unidad Organizacional
        ↓
Operación
        ↓
Actividad
        ↓
Tarea
        ↓
Programación física + presupuesto
        ↓
Seguimiento
```

### 13.2 Distribución de modelos

- `AccionCortoPlazo` sale del núcleo estratégico.
- `AccionPOA`, `OperacionPOAU`, `ActividadPOAU`, `TareaPOAU` salen de `articulacion`.
- `Operacion` y `Tarea` salen de `indicadores`.
- definir una sola jerarquía canónica SIS-POA.
- `poau.POAUActividad` debe migrar a esa jerarquía o convertirse en vista/adaptador temporal.

### 13.3 Integración presupuestaria

`recursos + techos + presupuesto` permanecen separados técnicamente, pero bajo un dominio funcional SIS-POA y contratos explícitos.

---

## 14. SIS-PRO V2

`inversion` no debe eliminarse; debe convertirse en semilla del sistema de proyectos.

### 14.1 Fases funcionales

1. idea/demanda;
2. vinculación estratégica y POA;
3. condiciones previas;
4. preinversión;
5. formulación técnica;
6. costos/presupuesto;
7. revisión técnica-financiera-legal;
8. contratación;
9. ejecución;
10. supervisión/fiscalización;
11. recepción/cierre;
12. evaluación.

### 14.2 Regla de trazabilidad

Un proyecto debe poder mostrar su cadena ascendente:

`Proyecto → POA → PEI → PAD → PDESA → PGDESA`.

---

## 15. IAM — usuarios, roles, permisos y alcances

### 15.1 Separación de responsabilidades

- Keycloak/OIDC: autenticación e identidad.
- Base PIP-GAMS: autorización de negocio y alcances.

### 15.2 Modelo de autorización

- Usuario local vinculado a identidad OIDC.
- Rol.
- Permiso/capacidad.
- RolPermiso.
- AsignaciónUsuarioRol.
- AlcanceOrganizacional.
- AlcanceTerritorial.
- AlcanceTemporal.
- Delegación/Suplencia.

### 15.3 Códigos de capacidad sugeridos

```text
sis_pe.instrumento.read
sis_pe.instrumento.create
sis_pe.pad.edit
sis_pe.pad.validate
sis_pe.pei.edit
sis_pe.articulacion.manage
sis_pe.indicadores.measure
sis_pe.approve
sis_poa.formulate
sis_poa.budget.manage
sis_poa.approve
sis_pro.project.create
sis_pro.preinvestment.validate
platform.users.manage
platform.catalogs.manage
platform.audit.read
```

### 15.4 Frontend

El frontend consultará `/api/v2/me/capabilities` y construirá menú y acciones con esas capacidades. Los roles no se codificarán en componentes.

---

## 16. Base de datos general

### 16.1 Decisión

Mantener **una base PostgreSQL/PostGIS principal para PIP-GAMS** por la fuerte consistencia transaccional y trazabilidad entre SIS-PE, SIS-POA y SIS-PRO.

No separar cada SIS en una base distinta.

### 16.2 Estrategia de esquemas

Durante el refactor inicial conservar el esquema físico existente para no multiplicar el riesgo de migraciones. La separación principal será por apps/tablas/servicios.

Una separación PostgreSQL por schemas puede evaluarse después de estabilizar V2, especialmente para analítica, publicación o integraciones; no debe ser requisito para completar el refactor.

### 16.3 Keycloak

Aunque use el mismo servidor PostgreSQL, Keycloak debe tener base/esquema y credenciales separados de los datos de negocio de PIP-GAMS.

---

## 17. API V2

Mantener `/api/v1/` temporalmente.

Crear:

```text
/api/v2/platform/...
/api/v2/sis-pe/...
/api/v2/sis-poa/...
/api/v2/sis-pro/...
/api/v2/me/...
```

Ejemplos:

```text
/api/v2/sis-pe/instrumentos
/api/v2/sis-pe/instrumentos/{id}/versiones
/api/v2/sis-pe/versiones/{id}/nodos
/api/v2/sis-pe/vinculos
/api/v2/sis-pe/pad/{id}/avance
/api/v2/sis-pe/pei/{id}/validacion
/api/v2/sis-pe/indicadores
/api/v2/sis-poa/acciones
/api/v2/sis-pro/proyectos
```

Reglas:

- serializers no contienen lógica compleja;
- servicios para comandos/escritura;
- selectors para lectura compleja;
- validadores de dominio explícitos;
- permisos backend por capacidad/alcance;
- OpenAPI obligatorio;
- contratos de respuesta estables.

---

## 18. Frontend V2

### 18.1 Navegación objetivo

```text
Inicio

SIS-PE
  Dashboard estratégico
  Instrumentos
  Diagnóstico
  PAD
  PEI
  Articulación
  Indicadores
  Territorio
  Seguimiento
  Evaluación

SIS-POA
  Dashboard operativo
  POA
  POAU
  Recursos
  Techos
  Presupuesto
  Seguimiento
  Modificaciones

SIS-PRO
  Dashboard de proyectos
  Cartera
  Preinversión
  Formulación
  Contratación
  Ejecución
  Seguimiento

Administración
  Usuarios y permisos
  Organización
  Gestiones/periodos
  Catálogos
  Normativa
  Documentos
  Auditoría
```

### 18.2 Refactor técnico

- conservar lazy loading;
- crear `PlatformShell` y dashboards por SIS;
- eliminar menú hard-codeado por roles;
- rutas agrupadas `/sis-pe`, `/sis-poa`, `/sis-pro`, `/administracion`;
- servicios API tipados por dominio;
- modelos TypeScript generados o controlados desde OpenAPI cuando sea viable;
- interceptores comunes;
- formularios reactivos;
- componentes de matriz/árbol/grafo reutilizables;
- componentes GIS reutilizables;
- estados de carga/error/vacío uniformes.

---

## 19. Workflow y versionado

### 19.1 Workflow V2

Evolucionar desde workflow específico de formulación a:

- `WorkflowDefinition`;
- `WorkflowStepDefinition`;
- `WorkflowTransition`;
- `WorkflowInstance`;
- `WorkflowTask`;
- `Observation`;
- `Approval`;
- `Delegation`.

Debe poder usarse en PAD, PEI, POA, modificaciones y proyectos.

### 19.2 Estados estratégicos sugeridos

`borrador → formulación → revisión → observado → corregido → validado → remitido → aprobado → ejecución/seguimiento → ajustado → evaluado → cerrado`.

Las transiciones deben ser configurables por metodología y tipo de instrumento.

---

## 20. Estrategia de datos: Expand / Migrate / Contract

### Fase Expand

- agregar tablas V2;
- no borrar columnas/tablas existentes;
- crear índices;
- crear scripts idempotentes de migración;
- crear API V2.

### Fase Migrate

- congelar edición del módulo legacy que se migra;
- backfill;
- comparar conteos;
- comparar códigos;
- comparar sumas presupuestarias;
- comparar articulaciones;
- revisar registros huérfanos;
- validar muestras manualmente.

### Fase Cutover

- frontend usa V2;
- V1 queda read-only o adaptada;
- monitorear errores;
- mantener rollback.

### Fase Contract

- retirar endpoints legacy;
- eliminar escritura legacy;
- retirar modelos/columnas obsoletos únicamente después de una versión estable y respaldo verificable.

---

## 21. Fases de ejecución

### FASE 0 — Congelamiento, respaldo y línea base

**Objetivo:** saber exactamente desde qué estado se parte.

Tareas:
- crear branch `refactor/pip-gams`;
- crear tag de estado previo;
- respaldo lógico PostgreSQL;
- respaldo de media/documentos;
- exportar OpenAPI V1;
- inventario de tablas y conteos;
- ejecutar test suite actual;
- registrar pruebas que fallan antes del refactor;
- registrar build Angular actual;
- documentar variables de entorno;
- revisar endpoints `AllowAny`;
- eliminar secretos del repositorio si existieran;
- no hacer cambios funcionales aún.

**Salida:** baseline reproducible.

### FASE 1 — Glosario, nomenclatura y ADR de arquitectura

Tareas:
- nombre de plataforma;
- definición oficial de SIS-PE/SIS-POA/SIS-PRO;
- glosario PAD/PEI/POA/POAU/proyecto;
- tabla de conceptos legacy→V2;
- política de versiones de metodología;
- ADR de base única;
- ADR de API V2;
- ADR de IAM;
- ADR de estrategia de migración.

**Salida:** arquitectura aprobada antes de tocar entidades centrales.

### FASE 2 — Núcleo transversal e IAM

Tareas:
- fortalecer `accounts`;
- capacidades y alcances;
- autorización backend uniforme;
- endpoint `me/capabilities`;
- organización e institución;
- periodos/ciclos;
- separar identidad de autorización;
- preparar OIDC;
- refactor de menú frontend.

**Salida:** plataforma base independiente de cada SIS.

### FASE 3 — Kernel SIS-PE V2

Tareas:
- TipoInstrumento;
- InstrumentoPlanificacion;
- VersionInstrumento;
- VersionMetodologia;
- TipoNodoEstrategico;
- NodoEstrategico;
- TipoVinculoEstrategico;
- VinculoEstrategico;
- reglas de inmutabilidad;
- API V2;
- tests.

**Salida:** árbol estratégico genérico operativo.

### FASE 4 — Importación/migración PGDESA-PDESA y marco superior

Tareas:
- adaptadores de `codificacion`;
- importar versiones oficiales;
- almacenar fuente y versión;
- migrar Eje/Componente/Resultado;
- motor de actualización sin sobrescribir versiones aprobadas;
- compromisos internacionales como entidades/vínculos configurables.

**Salida:** marco superior versionado.

### FASE 5 — PAD V2

Tareas:
- crear configuración metodológica PAD;
- migrar lineamientos/resultados/productos;
- resolver duplicidades `pad` vs `articulacion`;
- migrar `ArticulacionSIPEB` a vínculos;
- normalizar programación anual;
- diagnóstico;
- participación;
- competencias;
- validación;
- generador de matrices.

**Salida:** PAD V2 funcional y conciliado con legacy.

### FASE 6 — PEI V2

Tareas:
- crear app `pei`;
- diagnóstico institucional;
- misión/visión;
- objetivos/acciones estratégicas;
- migrar ResultadoPEI/ProductoPEI;
- articulación PAD→PEI;
- programación plurianual;
- responsables;
- validaciones.

**Salida:** PEI V2 funcional.

### FASE 7 — Indicadores + territorio + seguimiento estratégico

Tareas:
- banco municipal de indicadores;
- migrar indicadores duplicados;
- metas plurianuales;
- mediciones;
- fuentes/verificación;
- territorialización;
- dashboard estratégico;
- seguimiento PAD/PEI.

**Salida:** trazabilidad de resultados medibles.

### FASE 8 — Workflow, evaluación y ajustes SIS-PE

Tareas:
- workflow configurable;
- observaciones;
- validación;
- aprobación;
- versiones aprobadas inmutables;
- ajustes que creen nuevas versiones;
- evaluación medio término/final;
- lecciones/recomendaciones.

**Salida:** ciclo estratégico completo.

### FASE 9 — Frontend SIS-PE V2 y corte

Tareas:
- nuevo menú;
- dashboard SIS-PE;
- wizard PAD;
- workspace PEI;
- vista árbol;
- matriz de articulación;
- grafo;
- indicadores;
- mapa;
- validación;
- reportes;
- cambiar escritura a API V2;
- dejar módulos legacy read-only.

**Salida:** SIS-PE V2 como interfaz principal.

### FASE 10 — SIS-POA V2

Tareas:
- crear POA institucional;
- consolidar una jerarquía única POA→POAU→operación→actividad→tarea;
- migrar entidades desde `articulacion`, `indicadores`, `planificacion` y `poau`;
- integrar recursos/techos/presupuesto;
- validaciones de techo;
- seguimiento;
- modificaciones;
- conexión obligatoria con PEI.

**Salida:** SIS-POA desacoplado del modelo estratégico pero trazable.

### FASE 11 — SIS-PRO V2

Tareas:
- evolucionar `inversion`;
- diseñar estados del ciclo del proyecto;
- condiciones previas;
- documentos técnicos;
- costos;
- contratación;
- ejecución;
- seguimiento;
- integración POA/PEI/PAD;
- territorio;
- documentos y workflow.

**Salida:** primer ciclo integral de proyecto.

### FASE 12 — Infraestructura y servicios

Tareas:
- MinIO;
- Celery;
- Redis;
- GeoServer;
- OIDC/Keycloak;
- separar almacenamiento/credenciales de Keycloak;
- health checks;
- backups;
- observabilidad;
- jobs de reportes/indicadores;
- pinning de imágenes y dependencias.

### FASE 13 — Calidad, rendimiento y seguridad

Tareas:
- cobertura backend de servicios críticos >=80%;
- reglas de presupuesto y permisos con cobertura superior;
- tests de migración;
- tests de contratos API;
- tests Angular;
- E2E de caminos críticos;
- control de N+1 queries;
- índices;
- cache solo donde mida beneficio;
- pruebas de carga;
- revisión OWASP;
- restauración de respaldo ensayada.

### FASE 14 — Retiro de legacy

Condiciones previas:
- V2 estable;
- reconciliación 100% de registros críticos;
- cero escritura legacy;
- periodo de observación completado;
- respaldo y rollback documentados.

Tareas:
- retirar endpoints V1 obsoletos;
- eliminar componentes Angular legacy;
- eliminar modelos duplicados;
- eliminar JSONFields deprecados;
- limpiar adapters;
- actualizar documentación definitiva.

---

## 22. Orden exacto de resolución de duplicidades

1. Definir `NodoEstrategico` V2.
2. Crear mapa de equivalencias.
3. Migrar `planificacion.NodoPlanificacion`.
4. Migrar catálogos PGDESA/PDESA.
5. Migrar PAD de `pad`.
6. Comparar con PAD de `articulacion`.
7. Resolver duplicados por código + versión + significado, nunca solo por texto.
8. Migrar PEI de `articulacion`.
9. Migrar articulaciones.
10. Migrar indicadores.
11. Separar POA/POAU de `articulacion`.
12. Marcar modelos legacy read-only.
13. Eliminar solo después del cutover.

---

## 23. Validadores SIS-PE obligatorios

- un nodo debe pertenecer a una versión activa;
- versión aprobada no se modifica;
- códigos únicos según regla metodológica;
- padre/hijo válido según metodología;
- articulación origen/destino compatible;
- no auto-articulación;
- no ciclos en jerarquía;
- ponderaciones válidas;
- línea base coherente con metas;
- año meta dentro del periodo;
- responsables activos;
- competencia registrada cuando sea exigida;
- fuente de verificación para indicadores;
- territorialización requerida cuando aplique;
- programación plurianual completa;
- consistencia físico-financiera;
- ningún POA desacoplado de PEI salvo excepción autorizada y auditada.

---

## 24. Reportes y vistas derivados

No crear tablas paralelas para cada matriz oficial. Crear consultas/report builders que proyecten el modelo normalizado.

Vistas previstas:

- árbol PGDESA→PDESA→PAD→PEI;
- matriz de articulación;
- matriz PAD;
- matriz PEI;
- matriz PEI→POA;
- presupuesto plurianual;
- indicadores y metas;
- territorialización;
- cumplimiento por objetivo;
- brechas por distrito/territorio;
- trazabilidad de proyecto a estrategia.

Para dashboards pesados usar vistas/materialized views cuando la medición de rendimiento lo justifique.

---

## 25. Riesgos principales y mitigación

| Riesgo | Nivel | Mitigación |
|---|---|---|
| Perder datos al fusionar PAD duplicado | Crítico | Expand/migrate/contract + mapa legacy + reconciliación |
| Romper migraciones al mover apps | Crítico | No mover app labels al inicio |
| Crear una tercera representación estratégica | Crítico | Kernel V2 único antes de nuevas pantallas |
| Cambios metodológicos nacionales | Alto | Metodologías/nodos parametrizables y versionados |
| Permisos solo en frontend | Alto | Backend capability-based |
| Cortar V1 demasiado pronto | Alto | API V1 temporal y deprecación controlada |
| Doble escritura inconsistente | Alto | Preferir ventanas de freeze por módulo; dual-write solo si es imprescindible |
| Documentación desactualizada | Medio | Docs generadas/revisadas por fase y ADRs |
| JSON no normalizado | Medio | Migrar progresivamente a tablas |
| Acoplamiento SIS-POA ↔ SIS-PRO | Medio | Contratos explícitos por IDs/servicios de dominio |
| Rendimiento de matrices grandes | Medio | índices + selectors + materialized views |
| Keycloak compartiendo datos de negocio | Alto | DB/schema/credencial separada |

---

## 26. Reglas para trabajar con OpenCode

1. Un work package por sesión/cambio importante.
2. OpenCode nunca recibe “refactoriza toda la plataforma”.
3. Cada prompt debe indicar:
   - objetivo;
   - archivos permitidos;
   - archivos prohibidos;
   - modelos afectados;
   - migraciones esperadas;
   - pruebas obligatorias;
   - criterios de aceptación;
   - comandos de verificación;
   - estrategia de rollback.
4. No borrar migraciones históricas.
5. No hacer `squash` de migraciones durante la migración V2.
6. No editar manualmente datos productivos.
7. No cambiar códigos oficiales sin tabla de homologación.
8. Un commit lógico por work package.
9. Ejecutar backend tests + frontend tests/build antes de commit.
10. Actualizar CHANGELOG/ADR cuando exista cambio de arquitectura.

---

## 27. Convención de branches y commits

Branches sugeridas:

```text
refactor/pip-gams
feature/pip-core-iam
feature/sis-pe-kernel-v2
feature/sis-pe-pad-v2
feature/sis-pe-pei-v2
feature/sis-pe-indicators
feature/sis-poa-v2
feature/sis-pro-v2
```

Commits:

```text
refactor(sis-pe): add versioned strategic node kernel
migration(sis-pe): backfill legacy PAD nodes
feat(iam): add capability and organizational scopes
feat(sis-pe): add PAD methodology validator
refactor(sis-poa): move operations out of indicators
```

---

## 28. Gates de aceptación

### Gate A — Kernel estratégico
- jerarquía parametrizable;
- no choices rígidos para niveles centrales;
- versiones;
- vínculos;
- tests.

### Gate B — PAD
- 100% registros legacy críticos mapeados;
- matrices equivalentes;
- sin pérdida de presupuestos/metas;
- articulación superior funcional.

### Gate C — PEI
- PAD→PEI trazable;
- objetivos/acciones/metas versionados;
- validación metodológica.

### Gate D — SIS-PE cutover
- frontend V2;
- permisos V2;
- workflow;
- reportes;
- legacy read-only.

### Gate E — SIS-POA
- PEI→POA obligatorio;
- una sola jerarquía operativa;
- presupuesto y techos conciliados.

### Gate F — SIS-PRO
- proyecto→POA→PEI→PAD trazable;
- ciclo documental y workflow funcional.

---

## 29. Definition of Done por work package

Un cambio no está terminado si no cumple:

- migración Django creada cuando aplica;
- migración de datos idempotente cuando aplica;
- tests backend;
- tests frontend relevantes;
- OpenAPI actualizado;
- permisos evaluados;
- auditoría incluida cuando corresponde;
- logs sin datos sensibles;
- documentación/ADR actualizados;
- rollback definido;
- no quedan imports o rutas legacy nuevas;
- no se introduce duplicación conceptual.

---

## 30. Primer bloque de ejecución recomendado

Antes de tocar PAD/PEI directamente, ejecutar estos seis paquetes:

### WP-00 Baseline
Congelar, respaldar, tests, OpenAPI, inventario de datos.

### WP-01 Glosario y domain map
Formalizar PIP-GAMS, SIS-PE, SIS-POA, SIS-PRO y mapa legacy→V2.

### WP-02 API namespaces
Crear estructura `/api/v2/` sin retirar V1.

### WP-03 IAM capabilities
Permisos/capacidades/alcances y menú dinámico.

### WP-04 Strategic kernel models
Crear modelos V2 sin migrar aún datos legacy.

### WP-05 Migration audit tool
Crear `LegacyMigrationMap`, comandos de dry-run, conteos y reconciliación.

Solo después iniciar `WP-06 PGDESA/PDESA import` y `WP-07 PAD migration`.

---

## 31. Resultado esperado al terminar

La plataforma dejará de ser un conjunto de módulos acumulados y se convertirá en un sistema trazable:

```text
PGDESA / PGDES
        ↓
PDESA / PDES
        ↓
PAD
        ↓
PEI
        ↓
SIS-POA
        ↓
POAU / Operaciones / Actividades
        ↓
SIS-PRO
        ↓
Proyecto / Contratación / Ejecución
        ↓
Seguimiento y Evaluación
        ↺
Ajuste de la planificación
```

Todo sostenido por una base institucional común, identidad y permisos comunes, un banco único de indicadores, territorio PostGIS, workflow, documentos, auditoría y reportes.

---

## 32. Decisión final de implementación

**No reconstruir desde cero. No hacer big-bang. No fusionar físicamente todas las apps.**

La estrategia oficial de refactor será:

> **preservar → normalizar → versionar → migrar → validar → cortar → retirar**.

El primer objetivo técnico será **SIS-PE V2**, porque define el modelo estratégico del que luego deben heredar SIS-POA y SIS-PRO.

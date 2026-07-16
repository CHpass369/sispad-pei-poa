# PROMPT MAESTRO PARA DESARROLLAR SISPAD–PEI–POA

Actúa como arquitecto de software, analista de sistemas públicos, especialista en planificación gubernamental boliviana, desarrollador senior full-stack, especialista PostgreSQL/PostGIS, especialista en seguridad y DevOps.

Debes diseñar y desarrollar una plataforma web institucional completa denominada:

SISPAD–PEI–POA
Sistema Integrado de Planificación, Programación de Operaciones, Seguimiento y Evaluación Municipal

La plataforma será implementada inicialmente para el Gobierno Autónomo Municipal de Sacaba, Bolivia, pero su arquitectura debe permitir que posteriormente pueda adaptarse a otros gobiernos autónomos municipales.

No construyas solamente un prototipo visual. Debes desarrollar una aplicación funcional, persistente, documentada, auditable, segura y desplegable.

==================================================
1. OBJETIVO GENERAL
==================================================

Desarrollar una plataforma web que permita:

1. Gestionar la articulación:

   PGDESA
   → PDESA
   → PAD
   → PEI
   → POA institucional
   → POAU de unidades organizacionales
   → ejecución
   → seguimiento
   → evaluación
   → ajustes y reformulaciones.

2. Gestionar la formulación, revisión, aprobación y consolidación del Plan Operativo Anual Municipal.

3. Gestionar la formulación y seguimiento de los POAU de cada unidad organizacional.

4. Gestionar techos presupuestarios y presupuestos por:
   - unidad organizacional;
   - programa;
   - proyecto;
   - actividad;
   - fuente de financiamiento;
   - organismo financiador;
   - objeto del gasto;
   - categoría programática;
   - dirección administrativa;
   - unidad ejecutora.

5. Gestionar la programación física y financiera.

6. Realizar seguimiento mensual, trimestral, cuatrimestral, semestral y anual.

7. Gestionar indicadores, metas, líneas base, medios de verificación, riesgos, desviaciones y acciones correctivas.

8. Generar automáticamente matrices, reportes, formularios, archivos Excel, PDF, CSV y servicios geográficos.

9. Territorializar programas, proyectos, operaciones, actividades e inversiones mediante PostgreSQL/PostGIS y GeoServer.

10. Implementar gestión avanzada de usuarios, roles, permisos y alcances organizacionales.

==================================================
2. DOCUMENTOS Y ARCHIVOS DE REFERENCIA
==================================================

Antes de diseñar la base de datos y escribir código, analiza los siguientes archivos existentes:

- /mnt/data/GUIA PAD.pdf
- /mnt/data/Directrices_de_formulación_presupuestaria_2026_0 (1).pdf
- /mnt/data/1_Guía_metodológica_ETAs.pdf
- /mnt/data/MATRICES A Y B(2).xlsx
- /mnt/data/GASTOS 2026.xlsx
- /mnt/data/POAU 2026 CATASTRO.xlsx
- /mnt/data/SEGUIMIENTO Y EVALUACION PTDI_PEI AJUSTADA.xlsx

Para analizar los archivos:

- Utiliza Python.
- Utiliza pypdf o pymupdf para PDF.
- Utiliza openpyxl para Excel.
- No modifiques los archivos originales.
- Identifica hojas, columnas, encabezados, fórmulas, catálogos, relaciones y reglas implícitas.
- Detecta duplicidades, referencias externas, fórmulas rotas y estructuras repetidas.
- Genera un informe en:

  docs/analisis_documental.md

El informe debe contener:

1. Inventario de archivos.
2. Hojas de cada Excel.
3. Columnas y campos identificados.
4. Fórmulas utilizadas.
5. Catálogos existentes.
6. Relaciones entre matrices.
7. Datos que deben normalizarse.
8. Reglas de negocio detectadas.
9. Riesgos de migración.
10. Propuesta de correspondencia Excel → modelo de datos.

No comiences la construcción definitiva del modelo sin haber generado este análisis.

==================================================
3. PRINCIPIOS DE DISEÑO
==================================================

La plataforma debe cumplir los siguientes principios:

- Fuente única de información.
- No duplicar datos entre POA, POAU, presupuesto y seguimiento.
- Trazabilidad completa de la planificación.
- Versionado de planes.
- Inmutabilidad de versiones aprobadas.
- Auditoría de toda modificación.
- Separación entre formulación, aprobación, ejecución y evaluación.
- Validación automática de consistencia.
- Interoperabilidad.
- Uso de estándares abiertos.
- Seguridad por defecto.
- Arquitectura modular.
- Diseño responsive.
- Accesibilidad.
- Información en idioma español.
- Posibilidad de crecimiento sin reescribir el sistema.

No almacenes estructuras estratégicas mediante columnas rígidas como:

pilar_1
meta_1
resultado_1

Construye estructuras jerárquicas parametrizables.

==================================================
4. ARQUITECTURA TECNOLÓGICA
==================================================

Utiliza la siguiente arquitectura:

Frontend:
- Angular.
- TypeScript estricto.
- Angular Material.
- Angular CDK.
- Reactive Forms.
- Signals o mecanismo reactivo oficial vigente.
- OpenLayers para cartografía.
- Apache ECharts para gráficos.
- Internacionalización preparada, inicialmente español.

Backend:
- Python.
- Django en versión LTS soportada.
- Django REST Framework.
- GeoDjango.
- OpenAPI.
- API REST versionada.
- WebSocket solamente cuando aporte valor real.

Base de datos:
- PostgreSQL.
- PostGIS.
- Extensión pg_trgm.
- UUID como identificador primario público.
- Secuencias o identificadores internos cuando se requiera eficiencia.

Servicios:
- Redis.
- Celery.
- Celery Beat.
- MinIO compatible con S3.
- GeoServer.
- Keycloak como proveedor OIDC.
- Nginx como proxy inverso.

Reportes:
- openpyxl o XlsxWriter.
- WeasyPrint para PDF.
- Plantillas HTML institucionales.

Pruebas:
- pytest.
- pytest-django.
- factory_boy.
- Angular testing.
- Playwright para pruebas end-to-end.

Infraestructura:
- Docker Compose para desarrollo.
- Archivos preparados para despliegue en servidor Linux.
- Health checks.
- Variables de entorno.
- Volúmenes persistentes.
- Scripts de respaldo y restauración.

No implementes microservicios en la primera versión.

Implementa un monolito modular en Django, con módulos desacoplados y API bien definida.

==================================================
5. ESTRUCTURA DEL REPOSITORIO
==================================================

Organiza el proyecto como monorepositorio:

sispad-pei-poa/
├── backend/
├── frontend/
├── infrastructure/
├── geoserver/
├── scripts/
├── docs/
├── imports/
├── exports/
├── tests/
├── docker-compose.yml
├── docker-compose.prod.yml
├── .env.example
├── Makefile
├── README.md
└── CHANGELOG.md

Estructura inicial del backend:

backend/apps/
├── core/
├── accounts/
├── organizations/
├── catalogs/
├── planning/
├── articulation/
├── pei/
├── poa/
├── poau/
├── budgeting/
├── projects/
├── indicators/
├── workflows/
├── tracking/
├── evaluation/
├── amendments/
├── documents/
├── notifications/
├── geography/
├── reporting/
├── integrations/
└── auditing/

Cada aplicación debe contener:

- models.py o paquete models/.
- serializers.py.
- services.py.
- selectors.py.
- permissions.py.
- validators.py.
- views.py.
- urls.py.
- tests/.
- admin.py.
- migrations/.

Evita colocar toda la lógica de negocio en serializers o views.

La lógica debe estar concentrada en servicios y validadores explícitos.

==================================================
6. MODELO ORGANIZACIONAL
==================================================

Implementa las siguientes entidades:

Institution
- id UUID.
- code.
- name.
- acronym.
- tax_id o identificación institucional.
- active.
- official_geometry.
- default_srid.
- timezone.

OrganizationalUnit
- id.
- institution.
- code.
- name.
- short_name.
- organizational_unit_type.
- parent.
- valid_from.
- valid_to.
- active.
- administrative_direction.
- executing_unit.
- cost_center.

Tipos de unidad:

- MAE.
- secretaría municipal.
- dirección.
- jefatura.
- unidad.
- subunidad.
- entidad desconcentrada.
- subalcaldía.
- unidad ejecutora.

La estructura organizacional debe ser jerárquica y tener vigencia temporal.

No elimines unidades que hayan participado en gestiones anteriores. Deben inactivarse.

==================================================
7. GESTIONES Y CICLOS DE PLANIFICACIÓN
==================================================

Implementa:

PlanningCycle
- periodo de planificación de mediano plazo.
- fecha inicial.
- fecha final.
- estado.
- norma de aprobación.
- documento de respaldo.

FiscalYear
- gestión fiscal.
- estado.
- fecha de apertura.
- fecha de cierre.
- etapa actual.
- permite formulación.
- permite seguimiento.
- permite modificaciones.

PlanningPeriod
- mensual.
- trimestral.
- cuatrimestral.
- semestral.
- anual.

Estados de gestión:

- configuración.
- formulación.
- revisión.
- consolidación.
- aprobación.
- ejecución.
- seguimiento.
- evaluación.
- cierre.

==================================================
8. PLANES Y JERARQUÍA ESTRATÉGICA
==================================================

Construye un modelo genérico para instrumentos de planificación.

Plan
- id.
- institution.
- code.
- name.
- acronym.
- plan_type.
- planning_level.
- start_year.
- end_year.
- status.
- parent_plan.
- approval_rule.
- approval_date.
- approval_document.

Tipos:

- PGDESA.
- PDESA.
- PSD.
- PAD.
- PEI.
- POA.
- POAU.
- otros parametrizables.

PlanVersion
- plan.
- version_number.
- version_name.
- status.
- valid_from.
- valid_to.
- approved_at.
- approved_by.
- change_reason.
- immutable.

StrategicNode
- plan_version.
- parent.
- code.
- node_type.
- name.
- description.
- order.
- active.
- metadata JSONB.

Tipos de nodo configurables:

- eje.
- objetivo de impacto.
- objetivo de efecto.
- política.
- lineamiento estratégico.
- resultado.
- acción.
- producto.
- programa.
- proyecto.
- acción institucional.
- acción de corto plazo.

La estructura debe permitir árboles de profundidad variable.

==================================================
9. MATRIZ DE ARTICULACIÓN
==================================================

Implementa ArticulationLink:

- source_node.
- target_node.
- articulation_type.
- contribution_percentage.
- justification.
- status.
- proposed_by.
- reviewed_by.
- approved_by.
- created_at.
- approved_at.
- observation.

Relaciones necesarias:

- PGDESA → PDESA.
- PDESA → PAD.
- PAD → PEI.
- PEI → POA.
- POA → POAU.
- POAU → operaciones.
- operación → actividad.
- actividad → presupuesto.
- actividad → seguimiento.
- seguimiento → evaluación.

La interfaz debe ofrecer:

1. Vista tipo árbol.
2. Vista matricial.
3. Grafo de articulación.
4. Búsqueda por código o descripción.
5. Filtros por instrumento.
6. Acciones sin articulación.
7. Articulaciones pendientes.
8. Duplicidades.
9. Porcentaje de cobertura.
10. Exportación Excel y PDF.

Reglas:

- Una acción POA no puede aprobarse sin una acción PEI.
- Una acción PEI no puede aprobarse sin relación PAD, excepto mediante excepción autorizada.
- Las excepciones requieren justificación, responsable y documento.
- No se permiten articulaciones circulares.
- No se permiten relaciones duplicadas activas.

==================================================
10. GESTIÓN DEL PAD
==================================================

Implementa las matrices equivalentes a las matrices A y B de la guía.

Debe gestionar:

- sector.
- política.
- lineamiento estratégico.
- resultado PAD.
- producto.
- programa.
- proyecto.
- indicador.
- línea base.
- meta quinquenal.
- programación física anual.
- programación financiera anual.
- entidad responsable.
- entidad concurrente.
- territorialización.
- población beneficiaria.
- fuente de financiamiento.
- presupuesto quinquenal.
- financiamiento asegurado.
- financiamiento por gestionar.
- riesgos.
- medios de verificación.

Genera automáticamente:

- Matriz A.
- Matriz B.
- Presupuesto quinquenal.
- Cartera de programas y proyectos.
- Reporte por resultado PAD.
- Reporte por territorio.
- Reporte por fuente.

==================================================
11. GESTIÓN DEL PEI
==================================================

El PEI debe gestionar:

- misión.
- visión.
- valores institucionales.
- objetivos estratégicos.
- acciones institucionales específicas.
- indicadores de proceso.
- indicadores de resultado.
- línea base.
- metas anuales.
- meta quinquenal.
- responsable institucional.
- corresponsables.
- programación física.
- presupuesto plurianual.
- medio de verificación.
- supuestos.
- riesgos.
- acciones de mitigación.
- articulación PAD.
- articulación PDESA.

Cada acción PEI debe tener un código persistente.

Cuando se modifique una acción PEI aprobada:

- no sobrescribir el registro original;
- crear una nueva versión;
- mantener vínculo con la versión anterior;
- registrar documento justificativo;
- registrar usuario y fecha.

==================================================
12. APERTURA DEL POA
==================================================

El Administrador POA debe poder:

- crear una gestión.
- configurar cronograma.
- definir etapas.
- establecer fechas límite.
- configurar formularios.
- publicar instructivos.
- abrir formulación.
- cerrar formulación.
- habilitar reapertura.
- registrar justificación de reapertura.
- definir periodos de seguimiento.
- configurar validaciones.
- configurar catálogo presupuestario.
- configurar responsables.
- copiar información válida de la gestión anterior.
- migrar acciones PEI.
- definir unidades obligadas a formular POAU.

El sistema debe mostrar:

- porcentaje de avance por unidad;
- estado del POAU;
- observaciones pendientes;
- formularios no iniciados;
- unidades retrasadas;
- fecha de última actualización.

==================================================
13. TECHOS PRESUPUESTARIOS
==================================================

Implementa:

BudgetCeiling
- fiscal_year.
- institution.
- organizational_unit.
- program.
- financing_source.
- financing_organization.
- expense_group.
- ceiling_type.
- initial_amount.
- current_amount.
- reserved_amount.
- committed_amount.
- available_amount.
- status.
- version.

BudgetCeilingMovement
- ceiling.
- movement_type.
- source_ceiling.
- destination_ceiling.
- amount.
- justification.
- document.
- requested_by.
- approved_by.
- date.

Tipos de movimiento:

- asignación inicial.
- incremento.
- reducción.
- transferencia.
- reserva.
- liberación.
- ajuste.
- reversión.

Reglas:

- Utilizar Decimal, nunca float.
- Moneda principal: boliviano.
- El presupuesto formulado no puede superar el techo disponible.
- Toda redistribución debe quedar auditada.
- Los techos aprobados deben estar versionados.
- No permitir montos negativos.
- No permitir transferencias superiores al saldo disponible.
- Permitir escenarios preliminares.
- Solamente un escenario puede publicarse como oficial.

==================================================
14. FORMULACIÓN DEL POA INSTITUCIONAL
==================================================

Implementa:

AnnualOperatingPlan
- fiscal_year.
- plan_version.
- status.
- approved_budget.
- current_budget.
- approval_document.
- consolidated_at.

ShortTermAction
- POA.
- code.
- name.
- description.
- PEI action.
- expected_result.
- indicator.
- annual_target.
- baseline.
- unit_of_measure.
- start_date.
- end_date.
- responsible_unit.
- executing_unit.
- programmatic_category.
- physical_schedule.
- financial_schedule.
- budget.
- verification_method.
- risk.
- territory.

El POA institucional debe consolidarse desde los POAU validados.

No permitas que el POA consolidado sea editado manualmente sin un proceso formal de modificación.

==================================================
15. FORMULACIÓN DEL POAU
==================================================

POAU significa Plan Operativo Anual de Unidad Organizacional.

Implementa un asistente de formulación por pasos:

Paso 1:
- Datos de la unidad.
- Responsable.
- Gestión.
- Acción PEI.
- Acción POA.

Paso 2:
- Resultado anual esperado.
- Producto.
- Indicador.
- Fórmula.
- Línea base.
- Meta.
- Unidad de medida.

Paso 3:
- Operaciones.
- Actividades.
- Tareas.
- Responsables.
- Corresponsables.

Paso 4:
- Cronograma.
- Programación física.
- Hitos.
- Fechas.

Paso 5:
- Presupuesto.
- Objetos de gasto.
- Fuente.
- Organismo financiador.
- Categoría programática.
- Dirección administrativa.
- Unidad ejecutora.

Paso 6:
- Territorialización.
- Distrito.
- OTB.
- comunidad.
- ubicación geográfica.
- población beneficiaria.

Paso 7:
- Riesgos.
- medidas de mitigación.
- medios de verificación.
- documentos.

Paso 8:
- Validaciones.
- resumen.
- envío.

Entidades:

OrganizationalAnnualPlan
Operation
Activity
Task
Product
Milestone
ResponsibilityAssignment
PhysicalSchedule
FinancialSchedule
Risk
MitigationAction
VerificationMethod

Estados:

- borrador.
- en revisión interna.
- enviado.
- observado.
- en subsanación.
- validado técnicamente.
- validado presupuestariamente.
- consolidado.
- aprobado.
- publicado.
- reformulado.
- cerrado.

==================================================
16. OPERACIONES, ACTIVIDADES Y TAREAS
==================================================

Operation:
- POAU.
- code.
- name.
- description.
- weight.
- responsible.
- product.
- indicator.
- target.

Activity:
- operation.
- code.
- name.
- description.
- weight.
- start_date.
- end_date.
- responsible.
- physical_target.
- budget.

Task:
- activity.
- name.
- responsible.
- due_date.
- status.
- evidence_required.

Reglas:

- La suma de ponderaciones de las operaciones debe ser 100%.
- La suma de ponderaciones de actividades por operación debe ser 100%.
- Las actividades deben estar dentro del rango de fechas de la operación.
- Las tareas deben estar dentro del rango de fechas de la actividad.
- Las actividades con presupuesto deben tener línea presupuestaria.
- Las actividades que requieren evidencia deben indicarlo explícitamente.

==================================================
17. GESTIÓN PRESUPUESTARIA
==================================================

Implementa catálogos para:

- entidad.
- dirección administrativa.
- unidad ejecutora.
- programa.
- proyecto.
- actividad presupuestaria.
- código SISIN.
- finalidad y función.
- fuente de financiamiento.
- organismo financiador.
- objeto del gasto.
- entidad de transferencia.
- sector económico.
- rubro de recursos.
- tipo de gasto.
- tipo de inversión.

BudgetLine:
- fiscal_year.
- organizational_unit.
- POAU.
- operation.
- activity.
- administrative_direction.
- executing_unit.
- program.
- project.
- budget_activity.
- SISIN code.
- purpose_function.
- funding_source.
- financing_organization.
- expense_object.
- transfer_entity.
- economic_sector.
- amount.
- current_amount.
- monthly_schedule.
- justification.
- calculation_memory.

Reglas:

- La suma de las líneas debe coincidir con el presupuesto de la actividad.
- La suma de actividades debe coincidir con el POAU.
- La suma de POAU aprobados debe coincidir con el POA institucional consolidado.
- El presupuesto anual debe guardar consistencia con el presupuesto plurianual.
- Los proyectos de inversión deben registrar código SISIN cuando corresponda.
- Los montos deben mantener precisión de dos decimales.

==================================================
18. AUXILIAR PLURI
==================================================

Construye el módulo Auxiliar Pluri.

Debe generarse automáticamente desde las líneas presupuestarias aprobadas.

Debe mostrar:

- unidad.
- acción PEI.
- acción POA.
- operación.
- actividad.
- objeto del gasto.
- fuente.
- organismo financiador.
- gestión.
- monto anual.
- monto plurianual.
- total.
- observaciones.

Debe permitir:

- exportar a Excel.
- comparar contra el presupuesto institucional.
- detectar diferencias.
- realizar ajustes únicamente mediante flujo autorizado.
- identificar registros sin articulación.
- identificar partidas sin memoria de cálculo.

==================================================
19. BANCO DE PROGRAMAS Y PROYECTOS
==================================================

Implementa:

InvestmentProject
- code.
- SISIN code.
- name.
- description.
- project_type.
- stage.
- sector.
- responsible_unit.
- executing_unit.
- total_cost.
- annual_budget.
- counterpart.
- secured_financing.
- financing_to_manage.
- funding_sources.
- financing_organizations.
- beneficiaries.
- start_date.
- end_date.
- status.
- geometry.
- EDTP document.
- agreements.
- contracts.
- risks.

Etapas:

- idea.
- perfil.
- preinversión.
- diseño.
- inversión.
- ejecución.
- cierre.
- operación.

Priorización:

1. Proyectos de continuidad.
2. Proyectos con financiamiento asegurado.
3. Proyectos estratégicos nuevos.
4. Otros proyectos compatibles con los planes.

Implementa una puntuación configurable para priorización.

==================================================
20. FLUJO DE REVISIÓN Y APROBACIÓN
==================================================

Construye un motor de flujo configurable.

Flujo inicial:

Borrador
→ revisión interna
→ jefe de unidad
→ dirección
→ secretaría
→ planificación
→ presupuesto
→ inversión pública, cuando corresponda
→ consolidación
→ MAE
→ aprobado.

Entidades:

WorkflowDefinition
WorkflowStepDefinition
WorkflowInstance
WorkflowStepInstance
WorkflowAction
Observation
Approval
Delegation

Acciones:

- enviar.
- observar.
- devolver.
- subsanar.
- validar.
- aprobar.
- rechazar.
- cancelar.
- reabrir.
- delegar.

Requisitos:

- Observaciones por registro.
- Observaciones generales.
- Respuesta a observaciones.
- Historial completo.
- Comparación antes/después.
- Fecha y usuario.
- Delegaciones temporales.
- Suplencias.
- Notificaciones.
- Control de plazos.
- No permitir que un usuario apruebe su propia solicitud cuando exista conflicto de funciones.

==================================================
21. MODIFICACIONES Y REFORMULACIONES
==================================================

Implementa:

AmendmentRequest
- amendment_type.
- fiscal_year.
- affected_entity_type.
- affected_entity_id.
- reason.
- technical_report.
- legal_document.
- requested_by.
- status.
- effective_date.

AmendmentChange
- field.
- previous_value.
- proposed_value.
- approved_value.

Tipos:

- modificación de meta.
- modificación de operación.
- reprogramación.
- cambio de responsable.
- inscripción.
- eliminación.
- incremento presupuestario.
- reducción presupuestaria.
- traspaso.
- cambio de fuente.
- cambio de organismo.
- cambio de categoría programática.
- reformulación del POA.

Reglas:

- Nunca sobrescribir la versión aprobada.
- Crear nueva versión.
- Mantener valores anteriores.
- Registrar impacto físico.
- Registrar impacto financiero.
- Registrar impacto estratégico.
- Registrar documento de aprobación.
- Registrar fecha de vigencia.

==================================================
22. INDICADORES
==================================================

Implementa:

Indicator
- code.
- name.
- description.
- indicator_type.
- unit_of_measure.
- formula.
- numerator_definition.
- denominator_definition.
- frequency.
- disaggregation.
- verification_source.
- responsible_unit.
- interpretation.
- higher_is_better.
- active.

IndicatorBaseline
IndicatorTarget
IndicatorMeasurement

Tipos:

- impacto.
- efecto.
- resultado.
- producto.
- proceso.
- gestión.
- físico.
- financiero.

Funciones:

- Línea base.
- Meta anual.
- Meta quinquenal.
- Registro de mediciones.
- Desagregación territorial.
- Desagregación por sexo o grupo poblacional cuando corresponda.
- Validación de fórmulas.
- Gráficos históricos.
- Alertas.
- Importación masiva.

==================================================
23. SEGUIMIENTO FÍSICO Y FINANCIERO
==================================================

Implementa:

TrackingReport
- fiscal_year.
- period.
- organizational_unit.
- status.
- submitted_at.
- approved_at.

TrackingEntry
- activity.
- programmed_physical.
- executed_physical.
- physical_progress_percentage.
- initial_budget.
- current_budget.
- programmed_financial.
- executed_financial.
- financial_progress_percentage.
- deviation.
- deviation_cause.
- corrective_action.
- projection_at_year_end.
- evidence.

Permite seguimiento:

- mensual.
- trimestral.
- cuatrimestral.
- semestral.
- anual.

Calcula:

- eficacia física.
- ejecución financiera.
- eficiencia.
- cumplimiento de cronograma.
- desviación.
- proyección al cierre.
- avance acumulado.

Genera alertas para:

- ejecución física baja.
- ejecución financiera baja.
- avance físico sin ejecución financiera.
- ejecución financiera sin avance físico.
- sobreejecución.
- meta vencida.
- ausencia de evidencia.
- incumplimiento de compromiso correctivo.
- presupuesto sin actividad.
- actividad sin presupuesto.

Los umbrales deben ser configurables.

Semáforo inicial:

- verde: 80% o más respecto a lo programado.
- amarillo: 50% a 79.99%.
- rojo: menos de 50%.

No dejes los umbrales codificados permanentemente.

==================================================
24. ACCIONES CORRECTIVAS
==================================================

CorrectiveAction:
- tracking_entry.
- description.
- cause.
- responsible.
- start_date.
- due_date.
- expected_result.
- status.
- evidence.
- verified_by.
- verified_at.

Estados:

- pendiente.
- en ejecución.
- cumplida.
- incumplida.
- cerrada.
- cancelada.

El sistema debe controlar el cumplimiento de compromisos correctivos y emitir alertas.

==================================================
25. EVALUACIÓN
==================================================

Implementa:

Evaluation
- plan.
- fiscal_year.
- evaluation_type.
- period.
- responsible_team.
- status.
- conclusions.
- recommendations.
- approved_document.

EvaluationCriterion
EvaluationResult
LessonLearned
Recommendation

Tipos de evaluación:

- anual.
- medio término.
- final.
- específica.

Criterios:

- eficacia.
- eficiencia.
- efectividad.
- pertinencia.
- impacto.
- sostenibilidad.

El sistema debe generar:

- evaluación por POAU.
- evaluación por unidad.
- evaluación por acción PEI.
- evaluación por resultado PAD.
- evaluación institucional.
- brechas.
- recomendaciones.
- acciones de ajuste.
- lecciones aprendidas.

==================================================
26. GESTIÓN DOCUMENTAL
==================================================

Implementa almacenamiento en MinIO.

Document:
- id.
- document_type.
- title.
- description.
- original_filename.
- stored_filename.
- mime_type.
- size.
- hash_sha256.
- version.
- status.
- confidentiality_level.
- uploaded_by.
- uploaded_at.
- related_content_type.
- related_object_id.

Tipos documentales:

- informe.
- acta.
- resolución.
- ley municipal.
- decreto municipal.
- certificación.
- contrato.
- convenio.
- fotografía.
- mapa.
- planilla.
- dictamen.
- evidencia.
- memoria de cálculo.
- documento de aprobación.

Requisitos:

- No guardar archivos grandes dentro de PostgreSQL.
- Calcular hash SHA-256.
- Controlar versiones.
- Permitir vista previa cuando sea posible.
- Controlar permisos de descarga.
- Registrar auditoría.

==================================================
27. COMPONENTE GEOGRÁFICO
==================================================

Utiliza PostGIS y GeoServer.

Sistema de referencia institucional inicial:

- almacenamiento oficial configurable;
- valor inicial recomendado para Sacaba: EPSG:32719;
- servicios web en EPSG:4326 y EPSG:3857 cuando corresponda.

Entidades geográficas:

TerritorialUnit
- type.
- code.
- name.
- parent.
- geometry.
- valid_from.
- valid_to.

Tipos:

- municipio.
- distrito.
- subdistrito.
- OTB.
- comunidad.
- área urbana.
- área rural.
- zona.
- barrio.

Los programas, proyectos, operaciones y actividades podrán tener geometría:

- Point.
- MultiPoint.
- LineString.
- MultiLineString.
- Polygon.
- MultiPolygon.

Funciones:

- seleccionar territorio.
- dibujar geometría.
- editar geometría.
- importar GeoJSON.
- visualizar WMS.
- consultar WFS.
- filtros espaciales.
- ubicación GPS.
- cálculo de superficies.
- cálculo de longitud.
- análisis de cobertura.
- mapa de inversiones.
- presupuesto por distrito.
- proyectos por OTB.
- beneficiarios por territorio.
- análisis urbano-rural.

Publica capas mediante GeoServer.

Automatiza la creación de espacios de trabajo, almacenes y capas mediante API REST de GeoServer.

==================================================
28. USUARIOS, ROLES Y PERMISOS
==================================================

Implementa autenticación OIDC con Keycloak.

No almacenes contraseñas de usuario en las tablas funcionales.

Roles mínimos:

1. Superadministrador técnico.
2. Administrador funcional.
3. MAE.
4. Administrador POA.
5. Planificación estratégica.
6. Presupuesto.
7. Inversión pública.
8. Secretario municipal.
9. Director.
10. Jefe de unidad.
11. Técnico formulador.
12. Responsable de seguimiento.
13. Evaluador.
14. Auditor.
15. Control social.
16. Consulta pública.

Implementa RBAC y ABAC.

El permiso debe considerar:

- rol.
- institución.
- unidad organizacional.
- gestión.
- módulo.
- territorio.
- estado del trámite.
- propiedad del registro.
- delegación temporal.

Ejemplos:

- Un técnico edita solamente registros de su unidad.
- Un jefe revisa registros de unidades dependientes.
- Una secretaría revisa direcciones dependientes.
- Presupuesto valida montos, pero no modifica metas físicas.
- Planificación valida articulación, pero no altera montos aprobados.
- Auditor tiene acceso de lectura al historial.
- Control social accede solamente a información aprobada y publicada.
- Consulta pública accede únicamente al portal público.

Crea una matriz de permisos en:

docs/matriz_roles_permisos.md

==================================================
29. AUDITORÍA
==================================================

Implementa un registro append-only:

AuditEvent
- user.
- action.
- entity_type.
- entity_id.
- previous_data.
- new_data.
- IP.
- user_agent.
- request_id.
- timestamp.
- reason.

Auditar:

- creación.
- modificación.
- eliminación lógica.
- aprobación.
- observación.
- reapertura.
- exportación sensible.
- descarga de documento.
- inicio de sesión.
- cambio de permiso.
- cambio de techo.
- modificación presupuestaria.

No permitas editar ni eliminar eventos de auditoría desde la aplicación.

==================================================
30. IMPORTACIÓN DE EXCEL
==================================================

Construye un módulo de importación configurable.

Proceso:

1. Cargar archivo.
2. Detectar plantilla.
3. Mostrar hojas.
4. Mapear columnas.
5. Validar.
6. Mostrar vista previa.
7. Mostrar errores y advertencias.
8. Confirmar importación.
9. Ejecutar de manera asíncrona.
10. Generar reporte final.

Importaciones iniciales:

- matrices A y B.
- estructura de gasto.
- POAU.
- seguimiento y evaluación.
- estructura organizacional.
- catálogos presupuestarios.

Cada importación debe registrar:

- archivo.
- usuario.
- fecha.
- plantilla.
- registros procesados.
- registros exitosos.
- registros rechazados.
- errores.
- duración.
- resultado descargable.

No importar registros inválidos silenciosamente.

==================================================
31. REPORTES
==================================================

Genera como mínimo:

1. Matriz de articulación PGDESA–PDESA–PAD–PEI–POA–POAU.
2. Matriz A del PAD.
3. Matriz B del PAD.
4. Matriz de planificación PEI.
5. POA institucional.
6. POAU por unidad.
7. Auxiliar Pluri.
8. Presupuesto por programas.
9. Presupuesto por unidad.
10. Presupuesto por objeto del gasto.
11. Presupuesto por fuente.
12. Presupuesto por organismo financiador.
13. Programación física.
14. Programación financiera.
15. Seguimiento físico-financiero.
16. Evaluación anual.
17. Evaluación de medio término.
18. Evaluación final.
19. Proyectos de inversión.
20. Inversiones por territorio.
21. Reporte de modificaciones.
22. Reporte de observaciones.
23. Reporte de auditoría.
24. Reporte de cumplimiento por unidad.
25. Reporte de alertas.

Formatos:

- PDF.
- XLSX.
- CSV.
- JSON cuando corresponda.

Los reportes pesados deben ejecutarse mediante Celery.

==================================================
32. TABLEROS
==================================================

Tablero MAE:

- presupuesto institucional.
- ejecución física.
- ejecución financiera.
- cumplimiento POA.
- principales alertas.
- proyectos críticos.
- desempeño por secretaría.
- mapa de inversiones.

Tablero Planificación:

- articulación.
- acciones sin relación.
- avance de formulación.
- unidades pendientes.
- POAU observados.
- metas con desviaciones.
- indicadores vencidos.

Tablero Presupuesto:

- techo inicial.
- techo vigente.
- formulado.
- aprobado.
- ejecutado.
- saldo.
- modificaciones.
- partidas críticas.

Tablero Unidad Organizacional:

- POAU.
- operaciones.
- actividades.
- presupuesto.
- observaciones.
- evidencias pendientes.
- próximos vencimientos.
- ejecución del periodo.

Tablero Seguimiento:

- semáforos.
- cumplimiento.
- desviaciones.
- proyección.
- acciones correctivas.
- evidencias faltantes.

==================================================
33. PORTAL PÚBLICO
==================================================

Construye un portal público independiente del panel administrativo.

Debe publicar solamente información aprobada:

- POA institucional.
- presupuesto agregado.
- programas.
- proyectos.
- ejecución física.
- ejecución financiera.
- resultados.
- mapas.
- rendición de cuentas.
- documentos públicos.
- datos abiertos.

No publicar:

- información personal.
- observaciones internas.
- borradores.
- documentos confidenciales.
- datos de autenticación.
- información restringida.

==================================================
34. NOTIFICACIONES
==================================================

Implementa notificaciones:

- internas.
- correo electrónico.
- eventos futuros mediante arquitectura extensible.

Eventos:

- apertura de formulación.
- vencimiento próximo.
- vencimiento incumplido.
- POAU enviado.
- POAU observado.
- POAU aprobado.
- modificación solicitada.
- acción correctiva vencida.
- reporte pendiente.
- documento requerido.
- alerta física o financiera.

Permite marcar como:

- leída.
- no leída.
- atendida.

==================================================
35. API
==================================================

Implementa API REST versionada:

/api/v1/

Ejemplos:

/api/v1/auth/
/api/v1/users/
/api/v1/roles/
/api/v1/organizational-units/
/api/v1/fiscal-years/
/api/v1/plans/
/api/v1/plan-versions/
/api/v1/strategic-nodes/
/api/v1/articulations/
/api/v1/pei-actions/
/api/v1/poa/
/api/v1/poau/
/api/v1/operations/
/api/v1/activities/
/api/v1/budget-ceilings/
/api/v1/budget-lines/
/api/v1/projects/
/api/v1/indicators/
/api/v1/tracking/
/api/v1/evaluations/
/api/v1/amendments/
/api/v1/documents/
/api/v1/reports/
/api/v1/geography/
/api/v1/audit/

Utiliza:

- paginación.
- filtros.
- ordenamiento.
- búsqueda.
- validación.
- permisos por objeto.
- respuestas de error consistentes.
- códigos HTTP correctos.
- documentación OpenAPI.
- idempotencia para operaciones críticas cuando corresponda.

==================================================
36. FRONTEND
==================================================

Construye una aplicación Angular institucional.

Estructura:

frontend/src/app/
├── core/
├── shared/
├── layout/
├── auth/
├── dashboard/
├── administration/
├── planning/
├── articulation/
├── pei/
├── poa/
├── poau/
├── budgeting/
├── projects/
├── tracking/
├── evaluation/
├── maps/
├── reports/
├── audit/
└── public-portal/

Características:

- menú según permisos.
- breadcrumbs.
- tablas con filtros.
- formularios reactivos.
- guardado automático de borradores.
- validaciones visibles.
- mensajes claros.
- diálogos de confirmación.
- navegación con teclado.
- diseño responsive.
- modo claro y oscuro opcional.
- interfaz en español.
- componentes reutilizables.
- estados de carga.
- manejo centralizado de errores.
- rutas protegidas.
- interceptor OIDC.
- interceptor de errores.
- interceptor de request ID.

Pantallas esenciales:

1. Inicio de sesión.
2. Dashboard.
3. Estructura organizacional.
4. Gestión de usuarios y roles.
5. Configuración de gestión.
6. Árbol de planes.
7. Matriz de articulación.
8. Gestión PAD.
9. Gestión PEI.
10. Administración POA.
11. Techos presupuestarios.
12. Formulación POAU.
13. Revisión.
14. Observaciones.
15. Consolidación.
16. Presupuesto.
17. Proyectos.
18. Seguimiento.
19. Evaluación.
20. Modificaciones.
21. Documentos.
22. Cartografía.
23. Reportes.
24. Auditoría.
25. Portal público.

==================================================
37. VALIDACIONES CRÍTICAS
==================================================

Implementa como mínimo:

- Acción POA sin PEI: bloquear.
- Acción PEI sin PAD: bloquear o exigir excepción.
- Meta sin indicador: bloquear.
- Indicador sin unidad: bloquear.
- Actividad fuera del periodo: bloquear.
- Presupuesto mayor al techo: bloquear.
- Ponderaciones diferentes de 100%: bloquear.
- Líneas presupuestarias diferentes al total: bloquear.
- Proyecto sin SISIN cuando sea obligatorio: bloquear.
- Ejecución sin evidencia cuando sea obligatoria: bloquear.
- Modificación sin justificación: bloquear.
- Modificación sin documento cuando sea obligatorio: bloquear.
- Fechas inconsistentes: bloquear.
- Duplicidad de código: bloquear.
- Categoría programática reutilizada con objetivo distinto: bloquear.
- Ejecución negativa: bloquear.
- Meta negativa cuando no corresponda: bloquear.
- Archivo no permitido: bloquear.
- Geometría inválida: bloquear.

Diferencia:

- errores bloqueantes;
- advertencias;
- recomendaciones.

==================================================
38. SEGURIDAD
==================================================

Implementa:

- OIDC.
- HTTPS en producción.
- CORS restrictivo.
- CSRF cuando corresponda.
- rate limiting.
- validación de archivos.
- listas de tipos MIME permitidos.
- tamaño máximo configurable.
- protección contra inyección SQL.
- protección XSS.
- protección clickjacking.
- encabezados de seguridad.
- secretos por variables de entorno.
- rotación de claves.
- logs sin datos sensibles.
- permisos mínimos.
- políticas de sesión.
- cierre de sesión.
- revocación de tokens.
- registro de intentos fallidos.

No incluyas credenciales reales en el repositorio.

==================================================
39. PRUEBAS
==================================================

Backend:

- pruebas unitarias.
- pruebas de servicios.
- pruebas de validaciones.
- pruebas de permisos.
- pruebas de API.
- pruebas de workflow.
- pruebas de importación.
- pruebas de reportes.
- pruebas geográficas.

Frontend:

- pruebas de componentes.
- pruebas de formularios.
- pruebas de guards.
- pruebas de servicios.
- pruebas E2E con Playwright.

Cobertura mínima:

- 80% en servicios críticos.
- 90% en reglas presupuestarias.
- 90% en reglas de aprobación.
- 90% en permisos críticos.

Casos E2E mínimos:

1. Crear gestión.
2. Crear estructura organizacional.
3. Cargar planes.
4. Articular PAD–PEI.
5. Crear techo.
6. Formular POAU.
7. Enviar POAU.
8. Observar POAU.
9. Subsanar.
10. Aprobar.
11. Consolidar POA.
12. Registrar seguimiento.
13. Generar modificación.
14. Generar reporte.
15. Visualizar proyecto en mapa.

==================================================
40. DATOS DEMOSTRATIVOS
==================================================

Crea fixtures o comandos de carga con datos ficticios:

- Gobierno Autónomo Municipal de Sacaba.
- Secretaría Municipal de Planificación y Desarrollo Territorial.
- Dirección de Catastro Multifinalitario y Administración de Tierras.
- Jefatura de Catastro Multifinalitario.
- Unidad de Planificación Estratégica.
- Unidad de Presupuesto.
- Unidad de Inversión Pública.

Crea usuarios demostrativos sin contraseñas reales:

- administrador.
- mae.
- planificador.
- presupuesto.
- jefe_unidad.
- tecnico.
- seguimiento.
- auditor.

Crea una gestión de demostración y una cadena completa:

PGDESA
→ PDESA
→ PAD
→ PEI
→ POA
→ POAU
→ operación
→ actividad
→ presupuesto
→ seguimiento.

==================================================
41. DEVOPS
==================================================

docker-compose.yml debe incluir:

- postgres-postgis.
- backend.
- frontend.
- redis.
- celery-worker.
- celery-beat.
- minio.
- geoserver.
- keycloak.
- nginx.

Incluye:

- health checks.
- depends_on con condiciones saludables cuando sea posible.
- volúmenes.
- redes internas.
- variables de entorno.
- perfiles de desarrollo.
- datos persistentes.
- inicialización de PostGIS.
- inicialización de Keycloak.
- bucket inicial de MinIO.
- workspace inicial de GeoServer.

Crea comandos Makefile:

make setup
make build
make up
make down
make restart
make logs
make migrate
make makemigrations
make createsuperuser
make seed
make test
make test-backend
make test-frontend
make lint
make format
make backup
make restore
make openapi
make clean

==================================================
42. RESPALDOS
==================================================

Crea scripts:

scripts/backup_database.sh
scripts/restore_database.sh
scripts/backup_minio.sh
scripts/restore_minio.sh
scripts/backup_geoserver.sh
scripts/restore_geoserver.sh

El respaldo debe:

- usar timestamp.
- comprimir.
- registrar resultado.
- validar salida.
- permitir restauración documentada.
- no incluir secretos.

==================================================
43. DOCUMENTACIÓN
==================================================

Genera:

README.md
docs/arquitectura.md
docs/requisitos_funcionales.md
docs/requisitos_no_funcionales.md
docs/modelo_datos.md
docs/diagrama_entidad_relacion.md
docs/matriz_roles_permisos.md
docs/flujos_aprobacion.md
docs/importacion_excel.md
docs/api.md
docs/despliegue.md
docs/respaldo_restauracion.md
docs/manual_administrador.md
docs/manual_usuario.md
docs/seguridad.md
docs/decisiones_arquitectura.md
docs/analisis_documental.md
docs/matriz_trazabilidad_requisitos.md

Utiliza Mermaid para:

- arquitectura.
- entidad-relación.
- flujos.
- estados.
- secuencias.
- despliegue.

==================================================
44. DECISIONES ARQUITECTÓNICAS
==================================================

Registra ADR para:

1. Monolito modular.
2. Uso de Keycloak.
3. Uso de PostgreSQL/PostGIS.
4. Uso de GeoServer.
5. Almacenamiento de archivos en MinIO.
6. Versionado de planes.
7. Auditoría append-only.
8. Procesamiento asíncrono.
9. Importación Excel.
10. Uso de UUID.
11. Sistema de referencia espacial.
12. Diseño de workflow.

==================================================
45. FASES DE IMPLEMENTACIÓN
==================================================

Ejecuta el trabajo por fases.

FASE 0: análisis
- revisar documentos;
- revisar Excel;
- redactar requisitos;
- generar modelo conceptual;
- generar matriz de trazabilidad;
- generar ADR;
- presentar hallazgos.

FASE 1: infraestructura
- monorepositorio;
- Docker;
- PostgreSQL/PostGIS;
- Django;
- Angular;
- Redis;
- Celery;
- MinIO;
- GeoServer;
- Keycloak;
- Nginx.

FASE 2: núcleo
- institución;
- estructura organizacional;
- usuarios;
- roles;
- gestiones;
- catálogos;
- auditoría.

FASE 3: planificación
- planes;
- versiones;
- nodos;
- PAD;
- PEI;
- articulación;
- indicadores.

FASE 4: formulación POA
- apertura;
- techos;
- POA;
- POAU;
- operaciones;
- actividades;
- presupuesto;
- Auxiliar Pluri.

FASE 5: workflow
- revisión;
- observación;
- subsanación;
- aprobación;
- consolidación.

FASE 6: seguimiento
- seguimiento físico;
- seguimiento financiero;
- evidencias;
- alertas;
- acciones correctivas.

FASE 7: evaluación
- evaluación anual;
- medio término;
- final;
- ajustes.

FASE 8: SIG
- territorialización;
- mapas;
- GeoServer;
- análisis territorial.

FASE 9: reportes
- Excel;
- PDF;
- dashboards;
- portal público.

FASE 10: calidad
- pruebas;
- seguridad;
- rendimiento;
- documentación;
- despliegue.

No avances a la siguiente fase dejando errores críticos conocidos en la fase anterior.

==================================================
46. CRITERIOS DE ACEPTACIÓN
==================================================

La primera versión funcional será aceptada cuando permita:

1. Iniciar sesión mediante Keycloak.
2. Administrar usuarios y roles.
3. Crear la estructura organizacional.
4. Crear una gestión fiscal.
5. Crear y versionar PGDESA, PDESA, PAD y PEI.
6. Registrar nodos estratégicos.
7. Articular PAD con PEI.
8. Crear acciones POA.
9. Configurar techos presupuestarios.
10. Formular un POAU completo.
11. Registrar operaciones y actividades.
12. Registrar presupuesto.
13. Validar el techo.
14. Enviar el POAU.
15. Observar el POAU.
16. Subsanar observaciones.
17. Aprobar el POAU.
18. Consolidar el POA.
19. Generar el Auxiliar Pluri.
20. Registrar seguimiento físico.
21. Registrar ejecución financiera.
22. Adjuntar evidencias.
23. Generar alertas.
24. Crear una modificación.
25. Evaluar el cumplimiento.
26. Generar PDF y Excel.
27. Visualizar proyectos en mapa.
28. Consultar auditoría.
29. Publicar información aprobada.
30. Ejecutar el sistema mediante Docker Compose.

==================================================
47. FORMA DE TRABAJO
==================================================

Trabaja de forma autónoma, pero ordenada.

Antes de modificar archivos:

1. Revisa el estado del repositorio.
2. Revisa los documentos existentes.
3. Explica brevemente el plan inmediato.
4. Realiza cambios pequeños y verificables.
5. Ejecuta pruebas.
6. Corrige errores.
7. Actualiza documentación.
8. Registra avances en CHANGELOG.md.

No declares que una funcionalidad está terminada sin:

- migraciones;
- API;
- permisos;
- interfaz;
- validaciones;
- pruebas;
- documentación mínima.

No generes código ficticio, funciones vacías ni TODO sin justificación.

No ocultes errores.

Cuando una decisión no esté definida:

- elige una opción razonable;
- registra la decisión en un ADR;
- continúa el desarrollo.

Solamente realiza preguntas cuando exista un bloqueo real que impida continuar.

==================================================
48. PRIMERA EJECUCIÓN
==================================================

En tu primera ejecución realiza únicamente lo siguiente:

1. Inspecciona todos los archivos de referencia.
2. Inspecciona el directorio actual.
3. Genera:
   - docs/analisis_documental.md
   - docs/requisitos_funcionales.md
   - docs/requisitos_no_funcionales.md
   - docs/modelo_datos.md
   - docs/matriz_trazabilidad_requisitos.md
   - docs/decisiones_arquitectura.md
4. Propón el diagrama de arquitectura.
5. Propón el modelo entidad-relación.
6. Crea el backlog por fases.
7. Identifica riesgos técnicos.
8. Presenta un resumen de hallazgos.
9. No construyas todavía toda la aplicación.
10. Espera la revisión de estos documentos antes de ejecutar la fase de infraestructura.

Después de aprobar la Fase 0, continúa con la construcción incremental del sistema.

==================================================
49. RESULTADO ESPERADO DE LA PRIMERA RESPUESTA
==================================================

Al terminar la primera ejecución, informa:

- archivos analizados;
- estructura de las planillas;
- principales campos identificados;
- reglas de negocio detectadas;
- entidades propuestas;
- módulos propuestos;
- riesgos;
- decisiones arquitectónicas;
- archivos generados;
- siguiente fase recomendada;
- comandos exactos para revisar los documentos.

Comienza ahora con la Fase 0.
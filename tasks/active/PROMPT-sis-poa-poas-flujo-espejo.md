Implementá en el módulo POA (http://127.0.0.1:4200/sis-poa/poas) exactamente el mismo
flujo que ya existe en PEI (/sis-pe/pei). Todo lo que cito está commiteado en `main`
(d839174) y verificado: trabajá sobre esa rama.

Referencia viva — estos archivos existen, leelos antes de escribir nada:

  frontend/sispoa/src/app/features/sis-pe/pei/pei-home.component.ts
  frontend/sispoa/src/app/features/sis-pe/pei/pei-registros.component.ts
  frontend/sispoa/src/app/features/sis-pe/pei/pei-borradores.service.ts
  frontend/sispoa/src/app/features/sis-pe/pei/pei-wizard.component.ts
  frontend/sispoa/src/app/features/sis-pe/sis-pe.module.ts
  backend/apps/articulacion/models.py                       (BorradorMatrizPEI, línea 1177)
  backend/apps/articulacion/views.py                        (BorradorMatrizPEIViewSet, línea 517)
  backend/apps/articulacion/permissions.py                  (permisos_revision_matriz, ROLES_APROBADORES)
  backend/apps/articulacion/services/materializacion_matriz_pei.py

Tomá el PEI como espejo, NO el PAD. El PAD tenía el guard de inmutabilidad duplicado
y ya fue corregido; el PEI nació con la forma correcta.

ESTADO ACTUAL DE POA (verificado, no lo redescubras)
  - La ruta 'poas' apunta directo a PoaWizardComponent. No hay portada ni listado.
  - El wizard escribe directo a /articulacion/acciones-poa/ (poa-wizard.component.ts:512).
    No hay borrador: sin él no hay unidad que listar, editar, validar ni borrar.
  - Existen poa-catalogos.ts, poa-matriz.model.ts, poa-matriz-viewer.component.ts.
  - NO existe BorradorMatrizPOA en el backend.
  - Última migración de articulacion: 0011_borrador_matriz_pei. La tuya es la 0012.
  - En sis-poa.module.ts los cinco componentes actuales SÍ están declarados. Mantené
    esa disciplina al agregar los nuevos (ver trampas).

DECISIÓN PREVIA (resolvela antes de codificar)
Creá BorradorMatrizPOA espejo de BorradorMatrizPEI: secciones JSON + colección
acciones[] + action materializar (AccionPOA → OperacionPOAU → ActividadPOAU →
TareaPOAU), y hacé que el wizard POA guarde ahí. Si preferís otra estrategia,
proponela y esperá confirmación antes de avanzar.

1. PORTADA DEL MÓDULO
   /sis-poa/poas muestra dos tarjetas antes de entrar al asistente:
   - "Registro nuevo" -> /sis-poa/poas/nuevo
   - "Matrices POA"   -> /sis-poa/poas/registros
   Rutas: '' = portada, 'nuevo' = wizard, 'nuevo/:id' = wizard en edición,
   'registros' = listado. Usá children, como en sis-pe.module.ts.

2. LISTADO DE REGISTROS (/sis-poa/poas/registros)
   Tabla con: gestión, acción de corto plazo, cantidad de operaciones, estado,
   revisión, última actualización y columna Acciones.

3. MODO EDICIÓN EN EL WIZARD
   'nuevo/:id' carga el borrador y rehidrata TODO el asistente. Migas de pan, aviso
   ámbar de que se está editando, y botón final "Guardar cambios". Si el registro ya
   fue materializado, guardá las secciones y OMITÍ la materialización, avisando que
   los registros operativos ya creados no se recrean.

4. MATRICES CONSOLIDADAS EN EL LISTADO
   Debajo de la tabla, las matrices de TODOS los registros juntas (no una por
   registro), con pestañas:
   - "MATRIZ POA — ARTICULACIÓN Y PROGRAMACIÓN" (la que ya tiene el viewer)
   - "ARTICULACIÓN PEI -> POA" (nueva; el backend ya expone m2_pei_poa en
     views_matrices.py:440)
   Replicá la cabecera de DOS filas con los bloques y colores exactos de
   poa-matriz-viewer.component.ts. Son 15 columnas en 5 bloques:
     ARTICULACIÓN POA – PEI (4, #1F3864) · ACCIÓN DE CORTO PLAZO (3, #2E7D32) ·
     CATEGORÍA PROGRAMÁTICA (4, #6B1A16) · PRESUPUESTO (1, #2E7D32) ·
     PROGRAMACIÓN DE LA ACCIÓN (3, #8A5A1A)
   Verificá el conteo contra el formato oficial antes de darlo por bueno.
   Agregá al inicio una columna REGISTRO (gestión + estado) y al final una columna
   EDITAR con lápiz que abra /sis-poa/poas/nuevo/{idDelBorrador}.
   Etiquetá cada fila con _borradorId, _gestion, _estado.
   Si la matriz de un registro falla, ese registro aporta cero filas y los demás se
   siguen mostrando (catchError(() => of([])) por registro).

5. CIRCUITO DE REVISIÓN (backend + frontend)
   Campos: estado_revision (PENDIENTE/VALIDADO/OBSERVADO/APROBADO), validado_por/en,
   aprobado_por/en, observacion, observado_por/en. Migración aditiva.
   Actions: validar, aprobar, observar. Reglas:
     - Valida el técnico autor (o la jefatura).
     - Aprueba solo la jefatura y solo si está VALIDADO.
     - Observa solo la jefatura, con texto obligatorio.
     - Borran el autor o la jefatura, mientras no esté aprobado.
     - APROBADO = inmutable: bloqueá update, partial_update y destroy.
   REUTILIZÁ permisos_revision_matriz y ROLES_APROBADORES: ya existen en
   permissions.py, no los reescribas.
   Los permisos los calcula el BACKEND y los expone el serializer en un campo
   "permisos"; el frontend solo dibuja lo que recibe. Auditá con registrar_auditoria.
   UI: ✎ editar, ✓ validar, ✔ aprobar, ✎̶ observar, 🗑 borrar, cada uno visible solo
   si el permiso llega en true. Si está aprobado, sin botones y un 🔒. Modal de
   confirmación para borrar y modal con textarea para la observación.

6. SELECCIÓN DE FILAS Y EXPORTACIÓN
   Checkbox por fila y uno en la cabecera. Botones "Excel" y "PDF". Sin selección, el
   reporte incluye toda la matriz (avisalo en pantalla). Cambiar de pestaña limpia la
   selección. Encabezado del reporte, en este orden:
       GOBIERNO AUTÓNOMO MUNICIPAL DE SACABA
       PROGRAMA OPERATIVO ANUAL <gestión>
       MATRIZ POA  (o el nombre de la pestaña activa)
       <alcance de la selección · fecha y hora>
   Los colores de los bloques deben verse en AMBOS formatos.

TRAMPAS YA PAGADAS — no las redescubras

 - DECLARÁ los componentes nuevos en sis-poa.module.ts. Son standalone:false, y con
   Ivy un componente sin declarar IGUAL se instancia, pero sin scope de directivas:
   routerLink queda como atributo inerte y *ngIf/*ngFor no hacen nada. La página
   renderiza y no navega, SIN error en consola. Esto ya nos pasó en el PEI y costó
   caro justamente porque es silencioso.

 - El shell usa ChangeDetectionStrategy.OnPush. Todo subscribe que modifique estado
   necesita cdr.markForCheck(), aunque el componente no lo declare. Sin eso los datos
   llegan y la vista no se pinta hasta que hacés clic en cualquier lado.

 - La API pagina de a 25 y NO acepta page_size. Recorré por páginas siguiendo r.next
   (mirá cargarPagina en pei-registros.component.ts) o vas a leer datos incompletos.

 - AccionPOA.codigo_accion tiene unique=True. Si generás el correlativo, consultá
   primero los ya registrados y continuá la numeración; si reiniciás en 1 chocás
   contra la restricción.

 - Excel ignora "background:". Usá background-color:, más el atributo bgcolor y
   mso-pattern, y colores en 6 dígitos (#FFFFFF, no #fff).

 - Los navegadores descartan los fondos al imprimir: la ventana del PDF necesita
   print-color-adjust: exact (y -webkit-) con !important sobre *.

 - Un test de migración NUNCA debe usar los modelos actuales: si rebobinás el esquema,
   usá los modelos históricos de executor.loader.project_state(...).apps. Agregar
   campos a un modelo rompe esos tests de forma no obvia (nos pasó con ResultadoPEI).

CIERRE
 - Migraciones: generalas Y aplicalas, y verificá las columnas contra la base
   (information_schema.columns), no contra el archivo de migración.
 - Compilá con `ng build --configuration production`. No confíes en el "Compiled
   successfully" del dev server: no valida rutas ni declaraciones, y el bug del PEI
   pasó ese filtro sin problema.
 - Corré los tests del backend, no solo el build. Escribí test_borrador_matriz_poa.py
   cubriendo el circuito de revisión y la materialización.
 - Informá qué quedó fuera y qué decisiones tomaste por tu cuenta.

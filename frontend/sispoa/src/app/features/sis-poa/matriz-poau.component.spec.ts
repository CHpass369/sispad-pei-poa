import { ComponentFixture, TestBed } from '@angular/core/testing';
import { HttpClientTestingModule, HttpTestingController } from '@angular/common/http/testing';
import { RouterTestingModule } from '@angular/router/testing';
import { MatrizPoauComponent } from './matriz-poau.component';
import { FormsModule } from '@angular/forms';
import { ComboBoxComponent } from '../../shared/components/combo-box/combo-box.component';
import { PermissionsService } from '../../core/services/permissions.service';
import { HTTP_INTERCEPTORS } from '@angular/common/http';
import { ErrorInterceptor } from '../../core/interceptors/error.interceptor';
import { GestionHabilitadaService } from '../../core/services/gestion-habilitada.service';
import { gestionHabilitadaStub } from '../../core/testing/gestion-habilitada.stub';

/** Árbol mínimo con las seis ramas del formato: unidad → … → tarea. */
const FILAS = [
  { id: 'u', padre: null, nivel: 'unidad', orden_nivel: 0, hijos: 1, unidad: 'JURÍDICA' },
  { id: 'u|p', padre: 'u', nivel: 'aie', orden_nivel: 1, hijos: 1, accion_institucional: 'AIE' },
  { id: 'u|p|a', padre: 'u|p', nivel: 'accion', orden_nivel: 2, hijos: 1, accion_corto_plazo: 'ACP' },
  { id: 'u|p|a|o', padre: 'u|p|a', nivel: 'operacion', orden_nivel: 3, hijos: 1, operacion: 'OP' },
  { id: 'u|p|a|o|c', padre: 'u|p|a|o', nivel: 'actividad', orden_nivel: 4, hijos: 2, actividad: 'ACT' },
  { id: 'u|p|a|o|c|t1', padre: 'u|p|a|o|c', nivel: 'tarea', orden_nivel: 5, hijos: 0, tarea: 'T1', meta: 75 },
  { id: 'u|p|a|o|c|t2', padre: 'u|p|a|o|c', nivel: 'tarea', orden_nivel: 5, hijos: 0, tarea: 'T2' },
];

/**
 * Cada `cargar()` dispara tres GET independientes: el catálogo de Unidades
 * Organizacionales, el presupuesto y la matriz. El catálogo va por su cuenta
 * justamente para que el selector de la importación siga vivo aunque la matriz
 * —que pesa megabytes— falle.
 */
const CATALOGO = (http: HttpTestingController, unidades: any[] = []) =>
  http.expectOne(r => r.url.includes('/matriz-poau/unidades/'))
      .flush({ gestion: 2027, unidades });

const PRESUPUESTO = (http: HttpTestingController) =>
  http.expectOne(r => r.url.includes('/matriz-poau/presupuesto/'))
      .flush({ categorias: [], total: 0 });

const MATRIZ = (http: HttpTestingController, cuerpo: any) =>
  http.expectOne(r => r.url.includes('/matriz-poau/')
                      && !r.url.includes('/unidades/')
                      && !r.url.includes('/presupuesto/'))
      .flush(cuerpo);

describe('MatrizPoauComponent', () => {
  let componente: MatrizPoauComponent;
  let http: HttpTestingController;

  const responder = (unidades: any[] = [{ codigo: 'EM-DJR-01', nombre: 'JURÍDICA' }]) => {
    CATALOGO(http, unidades);
    PRESUPUESTO(http);
    MATRIZ(http, { gestion: 2027, total_filas: FILAS.length, filas: FILAS });
  };

  /** Recarga con el catálogo ya en memoria: no vuelve a pedirlo. */
  const recargar = () => {
    PRESUPUESTO(http);
    MATRIZ(http, { gestion: 2027, total_filas: FILAS.length, filas: FILAS });
  };

  beforeEach(() => {
    TestBed.configureTestingModule({
      imports: [HttpClientTestingModule, RouterTestingModule, FormsModule],
      declarations: [MatrizPoauComponent, ComboBoxComponent],
      providers: [
        { provide: GestionHabilitadaService, useValue: gestionHabilitadaStub(2027) },
      ],
    });
    componente = TestBed.createComponent(MatrizPoauComponent).componentInstance;
    http = TestBed.inject(HttpTestingController);
  });

  afterEach(() => http.verify());

  it('arranca contraído: sin filtro solo se ve la raíz', () => {
    componente.ngOnInit();
    responder();
    expect(componente.visibles.length).toBe(1);
    expect(componente.visibles[0].nivel).toBe('unidad');
  });

  it('desplegar un nodo muestra a sus hijos, pero no a los nietos', () => {
    componente.ngOnInit();
    responder();
    componente.alternar(FILAS[0]);
    expect(componente.visibles.map(f => f.nivel)).toEqual(['unidad', 'aie']);
    componente.alternar(FILAS[1]);
    expect(componente.visibles.map(f => f.nivel)).toEqual(['unidad', 'aie', 'accion']);
  });

  it('contraer un ancestro esconde toda la rama de golpe', () => {
    componente.ngOnInit();
    responder();
    componente.expandirTodo();
    expect(componente.visibles.length).toBe(FILAS.length);
    componente.alternar(FILAS[0]);
    expect(componente.visibles.length).toBe(1);
  });

  it('filtrar por unidad despliega la rama entera', () => {
    componente.ngOnInit();
    responder();
    componente.filtrar({ target: { value: 'EM-DJR-01' } } as any);
    recargar();
    expect(componente.visibles.length).toBe(FILAS.length);
    // El catálogo de unidades no se pisa con la respuesta filtrada.
    expect(componente.unidades.length).toBe(1);
  });

  it('el selector se llena del catálogo organizacional, no de la matriz', () => {
    componente.ngOnInit();
    CATALOGO(http, [
      { codigo: 'EM-DJR-01', nombre: 'JURÍDICA', sigla: 'DJR' },
      { codigo: 'EM-DAF-01', nombre: 'ADMINISTRATIVA', sigla: 'DAF' },
    ]);
    PRESUPUESTO(http);
    // La matriz cae: el catálogo ya llegó por su cuenta y el selector sobrevive.
    MATRIZ(http, { gestion: 2027, total_filas: 0, filas: [] });
    expect(componente.opcionesUnidadImport.map(o => o.valor))
      .toEqual(['EM-DJR-01', 'EM-DAF-01']);
  });

  it('sin catálogo no deja el selector muerto: reintenta al abrir la importación', () => {
    componente.ngOnInit();
    http.expectOne(r => r.url.includes('/matriz-poau/unidades/'))
        .error(new ProgressEvent('error'));
    PRESUPUESTO(http);
    MATRIZ(http, { gestion: 2027, total_filas: 0, filas: [] });
    expect(componente.opcionesUnidadImport.length).toBe(0);
    expect(componente.errorCatalogo).toBeTruthy();

    componente.abrirImportacion();
    CATALOGO(http, [{ codigo: 'EM-DJR-01', nombre: 'JURÍDICA' }]);
    expect(componente.opcionesUnidadImport.length).toBe(1);
    expect(componente.errorCatalogo).toBe('');
  });

  it('exposes a non-error empty state for a selected authorized unit', () => {
    componente.unidad = 'EM-DJR-01';
    componente.cargando = false;
    componente.filas = [];
    componente.error = '';
    expect(componente.mostrarEstadoVacio).toBeTrue();
  });

  it('cada nivel tiene color propio y una columna donde escribe', () => {
    for (const n of componente.niveles) {
      expect(componente.colorNivel[n]).toMatch(/^#[0-9A-F]{6}$/i);
      expect(componente.columnaNivel[n]).toBeTruthy();
    }
    // Seis colores distintos: es el escalonado de la planilla.
    expect(new Set(Object.values(componente.colorNivel)).size).toBe(6);
  });

  it('la vista matriz declara las 34 columnas del formato oficial', () => {
    componente.modo = 'matriz';
    const claves = componente.bloques.flatMap(b => b.columnas.map(c => c.clave));
    expect(claves.length).toBe(34);
    expect(claves).toContain('total_anual');
    expect(claves).toContain('resultado_logrado');
    expect(claves).toContain('linea_base');
    expect(claves).toContain('ponderacion');
  });
});

describe('MatrizPoauComponent · tinta de las cabeceras', () => {
  let componente: MatrizPoauComponent;

  beforeEach(() => {
    TestBed.configureTestingModule({
      imports: [HttpClientTestingModule, RouterTestingModule, FormsModule],
      declarations: [MatrizPoauComponent, ComboBoxComponent],
    });
    componente = TestBed.createComponent(MatrizPoauComponent).componentInstance;
    TestBed.inject(HttpTestingController).verify();
  });

  it('elige tinta oscura sobre el ámbar, que con blanco queda en 2.19:1', () => {
    expect(componente.tinta('#E8A202')).toBe('#1F2933');
  });

  it('mantiene tinta blanca sobre el rojo, el verde y el azul de la planilla', () => {
    for (const fondo of ['#FF0000', '#127622', '#3465A4']) {
      expect(componente.tinta(fondo)).toBe('#FFFFFF');
    }
  });

  it('cada banda queda legible sobre su propio color', () => {
    const lum = (h: string) => {
      const c = [1, 3, 5].map(i => {
        const v = parseInt(h.slice(i, i + 2), 16) / 255;
        return v <= 0.03928 ? v / 12.92 : Math.pow((v + 0.055) / 1.055, 2.4);
      });
      return 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2];
    };
    for (const b of componente.bloques) {
      const [a, z] = [lum(b.color), lum(componente.tinta(b.color))].sort((x, y) => y - x);
      expect((a + 0.05) / (z + 0.05)).toBeGreaterThan(3);
    }
  });
});

describe('MatrizPoauComponent · aprovechamiento del ancho', () => {
  let componente: MatrizPoauComponent;

  beforeEach(() => {
    TestBed.configureTestingModule({
      imports: [HttpClientTestingModule, RouterTestingModule, FormsModule],
      declarations: [MatrizPoauComponent, ComboBoxComponent],
    });
    componente = TestBed.createComponent(MatrizPoauComponent).componentInstance;
    TestBed.inject(HttpTestingController).verify();
  });

  const ancho = (celdas: any[]) => celdas.reduce((n, c) => n + c.colspan, 0);

  it('toda fila cubre las 34 columnas, absorba lo que absorba', () => {
    componente.modo = 'matriz';
    for (const nivel of componente.niveles) {
      expect(ancho(componente.armarCeldas({ nivel }))).toBe(34);
    }
  });

  it('la denominación se queda con las columnas vacías de la cadena', () => {
    componente.modo = 'matriz';
    const propia = (nivel: string) =>
      componente.armarCeldas({ nivel }).find((c: any) => c.propia);
    // ACTIVIDADES absorbe TAREAS ESPECÍFICAS; TAREAS ya está al final.
    expect(propia('actividad').colspan).toBe(2);
    expect(propia('tarea').colspan).toBe(1);
    expect(propia('operacion').colspan).toBe(3);
    expect(propia('accion').colspan).toBe(6);
  });

  it('no absorbe nunca las columnas de programación ni el cronograma', () => {
    componente.modo = 'matriz';
    for (const nivel of componente.niveles) {
      const celdas = componente.armarCeldas({ nivel });
      const cadena = celdas.filter((c: any, i: number) =>
        celdas.slice(0, i).reduce((n: number, x: any) => n + x.colspan, 0) < 11);
      expect(ancho(cadena)).toBe(11);
      expect(celdas.length - cadena.length).toBe(23);
    }
  });

  it('cada columna declara un ancho propio, no uno parejo', () => {
    componente.modo = 'matriz';
    const anchos = componente.bloques.flatMap(b => b.columnas.map(c => c.ancho));
    expect(anchos.length).toBe(34);
    expect(anchos.every(a => a > 0)).toBe(true);
    expect(new Set(anchos).size).toBeGreaterThan(6);
  });
});

describe('MatrizPoauComponent · importación ETL', () => {
  let componente: MatrizPoauComponent;
  let http: HttpTestingController;
  let fixture: ComponentFixture<MatrizPoauComponent>;

  const preview: any = {
    id: 'preview-1', estado: 'VALIDO',
    resumen: {
      filas_leidas: 3, filas_validas: 3, filas_rechazadas: 0,
      errores: 0, registros_preview: 3,
    },
    errores: [],
    filas: [{
      fila: 2, nivel: 'operacion', operacion_codigo: 'OP-1',
      operacion: 'Operación importada', meta: '1',
    }],
  };

  beforeEach(() => {
    TestBed.configureTestingModule({
      imports: [HttpClientTestingModule, RouterTestingModule, FormsModule],
      declarations: [MatrizPoauComponent, ComboBoxComponent],
      providers: [
        { provide: GestionHabilitadaService, useValue: gestionHabilitadaStub(2027, 'gestion-2027') },
      ],
    });
    fixture = TestBed.createComponent(MatrizPoauComponent);
    componente = fixture.componentInstance;
    componente.unidad = 'UO-01';
    http = TestBed.inject(HttpTestingController);
  });

  afterEach(() => http.verify());

  it('ubica el botón de importar antes de las exportaciones y abre un diálogo accesible', () => {
    fixture.detectChanges();
    // El botón queda deshabilitado mientras la matriz carga.
    CATALOGO(http, [{ codigo: 'UO-01', nombre: 'Unidad de prueba' }]);
    PRESUPUESTO(http);
    MATRIZ(http, { gestion: 2027, total_filas: 0, filas: [] });
    fixture.detectChanges();
    const buttons = Array.from(fixture.nativeElement.querySelectorAll('.encabezado-acciones button')) as HTMLButtonElement[];
    const labels = buttons.map(button => button.textContent?.trim());
    expect(labels.indexOf('⇧ Importar')).toBeLessThan(labels.indexOf('⬇ Excel'));
    buttons.find(button => button.textContent?.includes('Importar'))?.click();
    fixture.detectChanges();
    const dialog = fixture.nativeElement.querySelector('[role="dialog"]');
    expect(dialog).toBeTruthy();
    expect(dialog.getAttribute('aria-modal')).toBe('true');
  });

  it('envía Excel temporal a preview V2 y muestra su resumen', () => {
    componente.archivoImport = new File(['xlsx'], 'poau.xlsx', {
      type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    });
    componente.hojaImport = 'POAU';
    componente.previsualizarImportacion();
    const request = http.expectOne(req =>
      req.url.includes('/api/v2/sis-poa/poau-imports/preview/') &&
      req.url.includes('gestion_id=gestion-2027'));
    expect(request.request.body instanceof FormData).toBeTrue();
    expect(request.request.body.get('unidad_codigo')).toBe('UO-01');
    request.flush(preview);
    expect(componente.previewImport?.resumen.filas_validas).toBe(3);
  });

  it('no previsualiza sin una Unidad Organizacional elegida', () => {
    // El árbol se reconstruye por unidad: sin unidad no hay a qué importarle.
    componente.unidad = '';
    componente.archivoImport = new File(['xlsx'], 'poau.xlsx', {
      type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    });

    componente.previsualizarImportacion();

    http.expectNone(req => req.url.includes('/poau-imports/preview/'));
  });

  it('aplica solo con confirmación, conserva el resumen y recarga la matriz', () => {
    componente.previewImport = preview;
    componente.confirmarReemplazo = true;
    componente.aplicarImportacion();
    const apply = http.expectOne(req => req.url.includes('/preview-1/apply/'));
    apply.flush({
      ...preview, estado: 'APLICADO',
      resultado: { creados: 1, actualizados: 2, eliminados: 0, reemplazados: 2, sin_cambios: 0 },
    });
    CATALOGO(http);
    PRESUPUESTO(http);
    MATRIZ(http, { filas: [] });
    expect(componente.previewImport?.resultado?.creados).toBe(1);
    expect(componente.aviso).toContain('1 creados');
  });

  it('no permite aplicar una vista previa inválida', () => {
    componente.previewImport = { ...preview, estado: 'INVALIDO' };
    componente.confirmarReemplazo = true;
    componente.aplicarImportacion();
    http.expectNone(req => req.url.includes('/apply/'));
  });
});

describe('MatrizPoauComponent · vista de árbol', () => {
  let componente: MatrizPoauComponent;

  beforeEach(() => {
    TestBed.configureTestingModule({
      imports: [HttpClientTestingModule, RouterTestingModule, FormsModule],
      declarations: [MatrizPoauComponent, ComboBoxComponent],
    });
    componente = TestBed.createComponent(MatrizPoauComponent).componentInstance;
    TestBed.inject(HttpTestingController).verify();
  });

  it('arranca en árbol, con la cadena colapsada en una sola columna', () => {
    expect(componente.modo).toBe('arbol');
    const claves = componente.bloques.flatMap(b => b.columnas.map(c => c.clave));
    expect(claves[0]).toBe('desglose');
    // Las once de la cadena se vuelven dos: desglose y código.
    expect(claves.length).toBe(27);
    for (const c of ['operacion', 'actividad', 'tarea', 'unidad', 'cod_producto_pei']) {
      expect(claves).not.toContain(c);
    }
  });

  it('ningún nivel deriva hacia la derecha: todas las celdas ocupan una columna', () => {
    for (const nivel of componente.niveles) {
      const celdas = componente.armarCeldas({ nivel });
      expect(celdas.length).toBe(27);
      expect(celdas.every((c: any) => c.colspan === 1)).toBe(true);
      expect(celdas.filter((c: any) => c.propia).length).toBe(1);
    }
  });

  it('DESGLOSE muestra la denominación del nivel de cada fila', () => {
    expect(componente.celda({ nivel: 'tarea', tarea: 'Archivar' }, 'desglose')).toBe('Archivar');
    expect(componente.celda({ nivel: 'unidad', unidad: 'JURÍDICA' }, 'desglose')).toBe('JURÍDICA');
    expect(componente.celda({ nivel: 'operacion', operacion: 'Ejecutar' }, 'desglose')).toBe('Ejecutar');
  });

  it('exporta siempre el formato oficial, no la vista de pantalla', () => {
    const claves = componente.bloquesMatriz.flatMap(b => b.columnas.map(c => c.clave));
    expect(claves.length).toBe(34);
    expect(claves).toContain('tarea');
  });
});

describe('MatrizPoauComponent · selección y acciones', () => {
  let componente: MatrizPoauComponent;
  let http: HttpTestingController;

  const FILAS_ACC = [
    { id: 'u', padre: null, nivel: 'unidad', orden_nivel: 0, hijos: 1, unidad: 'JURÍDICA' },
    { id: 'u|p', padre: 'u', nivel: 'aie', orden_nivel: 1, hijos: 1, accion_institucional: 'AIE' },
    { id: 'u|p|a', padre: 'u|p', nivel: 'accion', orden_nivel: 2, hijos: 1, accion_corto_plazo: 'ACP' },
    { id: 'u|p|a|o', padre: 'u|p|a', nivel: 'operacion', orden_nivel: 3, hijos: 1,
      operacion: 'OP', objeto_id: 'op-1', tipo: 'operacion', accion_id: 'acc-9', estado: 'BORRADOR' },
    { id: 'u|p|a|o|c', padre: 'u|p|a|o', nivel: 'actividad', orden_nivel: 4, hijos: 1,
      actividad: 'ACT', objeto_id: 'act-1', tipo: 'actividad', accion_id: 'acc-9', estado: 'BORRADOR' },
    { id: 'u|p|a|o|c|t', padre: 'u|p|a|o|c', nivel: 'tarea', orden_nivel: 5, hijos: 0,
      tarea: 'T1', objeto_id: 'tar-1', tipo: 'tarea', accion_id: 'acc-9', estado: 'BORRADOR' },
  ];

  beforeEach(() => {
    TestBed.configureTestingModule({
      imports: [HttpClientTestingModule, RouterTestingModule, FormsModule],
      declarations: [MatrizPoauComponent, ComboBoxComponent],
    });
    componente = TestBed.createComponent(MatrizPoauComponent).componentInstance;
    http = TestBed.inject(HttpTestingController);
    componente.ngOnInit();
    CATALOGO(http);
    PRESUPUESTO(http);
    MATRIZ(http, { gestion: 2027, total_filas: 6, filas: FILAS_ACC });
    componente.expandirTodo();
  });

  afterEach(() => http.verify());

  it('sin selección se exporta la matriz entera', () => {
    expect(componente.seleccion.size).toBe(0);
    expect(componente.filasAExportar().length).toBe(6);
  });

  it('al seleccionar una tarea el reporte arrastra toda su cadena', () => {
    componente.alternarSeleccion(FILAS_ACC[5]);
    const ids = componente.filasAExportar().map((f: any) => f.id);
    // Una tarea suelta no dice de qué unidad ni de qué acción cuelga.
    expect(ids).toEqual(['u', 'u|p', 'u|p|a', 'u|p|a|o', 'u|p|a|o|c', 'u|p|a|o|c|t']);
  });

  it('seleccionar dos veces la misma fila la desmarca', () => {
    componente.alternarSeleccion(FILAS_ACC[5]);
    componente.alternarSeleccion(FILAS_ACC[5]);
    expect(componente.seleccion.size).toBe(0);
    expect(componente.filasAExportar().length).toBe(6);
  });

  it('validar pega en el endpoint del tipo de registro y refleja el estado', () => {
    componente.revisar(FILAS_ACC[5], 'validar');
    const req = http.expectOne(r => r.url.endsWith('/articulacion/tareas/tar-1/validar/'));
    expect(req.request.method).toBe('POST');
    req.flush({ estado: 'VALIDADO', observacion: '' });
    expect(FILAS_ACC[5].estado).toBe('VALIDADO');
  });

  it('cada nivel pega en su propia colección', () => {
    componente.revisar(FILAS_ACC[3], 'aprobar');
    http.expectOne(r => r.url.endsWith('/articulacion/operaciones/op-1/aprobar/'))
        .flush({ estado: 'APROBADO', observacion: '' });
    componente.revisar(FILAS_ACC[4], 'validar');
    http.expectOne(r => r.url.endsWith('/articulacion/actividades/act-1/validar/'))
        .flush({ estado: 'VALIDADO', observacion: '' });
    expect(FILAS_ACC[3].estado).toBe('APROBADO');
  });

  it('observar sin motivo no llega a pegarle al backend', () => {
    spyOn(window, 'prompt').and.returnValue('   ');
    componente.revisar(FILAS_ACC[5], 'observar');
    http.expectNone(() => true);
  });

  it('observar con motivo lo manda en el cuerpo', () => {
    spyOn(window, 'prompt').and.returnValue('Falta el cronograma');
    componente.revisar(FILAS_ACC[5], 'observar');
    const req = http.expectOne(r => r.url.endsWith('/articulacion/tareas/tar-1/observar/'));
    expect(req.request.body).toEqual({ comentario: 'Falta el cronograma' });
    req.flush({ estado: 'OBSERVADO', observacion: 'Falta el cronograma' });
  });

  it('el error del backend se muestra tal cual lo explica', () => {
    componente.revisar(FILAS_ACC[5], 'aprobar');
    http.expectOne(r => r.url.endsWith('/aprobar/')).flush(
      { error: 'Solo se aprueba un registro validado; este está borrador.' },
      { status: 400, statusText: 'Bad Request' });
    expect(componente.error).toContain('Solo se aprueba un registro validado');
  });

  it('eliminar pide confirmación y recarga la matriz', () => {
    spyOn(window, 'confirm').and.returnValue(true);
    componente.eliminar(FILAS_ACC[5]);
    http.expectOne(r => r.url.endsWith('/articulacion/tareas/tar-1/')).flush({});
    CATALOGO(http);
    PRESUPUESTO(http);
    MATRIZ(http, { gestion: 2027, total_filas: 0, filas: [] });
    expect(componente.filas.length).toBe(0);
  });

  it('cancelar la confirmación no borra nada', () => {
    spyOn(window, 'confirm').and.returnValue(false);
    componente.eliminar(FILAS_ACC[5]);
    http.expectNone(() => true);
  });
});

describe('MatrizPoauComponent · eliminar el POAU de una unidad', () => {
  let fixture: ComponentFixture<MatrizPoauComponent>;
  let componente: MatrizPoauComponent;
  let http: HttpTestingController;

  const FILA_UNIDAD = {
    id: 'u', padre: null, nivel: 'unidad', orden_nivel: 0, hijos: 1,
    unidad: 'JURÍDICA', unidad_codigo: 'EM-DJR-01',
  };
  const FILA_TAREA = {
    id: 'u|t', padre: 'u', nivel: 'tarea', orden_nivel: 5, hijos: 0,
    tarea: 'T1', objeto_id: 'tar-1', tipo: 'tarea', estado: 'BORRADOR',
  };
  const IMPACTO = {
    unidad: { codigo: 'EM-DJR-01', nombre: 'JURÍDICA' },
    gestion: 2027,
    eliminaria: {
      'articulacion.AccionPOA': 2, 'articulacion.OperacionPOAU': 5,
      'articulacion.TareaPOAU': 140,
    },
    total: 147,
    bloqueado_por: [],
  };

  const URL_UNIDAD = '/articulacion/matriz-poau/unidad/EM-DJR-01/';

  const montar = (esAdmin: boolean) => {
    TestBed.configureTestingModule({
      imports: [HttpClientTestingModule, RouterTestingModule, FormsModule],
      declarations: [MatrizPoauComponent, ComboBoxComponent],
      providers: [
        { provide: PermissionsService, useValue: { hasAnyRole: () => esAdmin } },
        // El interceptor va acá a propósito: en producción aplana TODO error a
        // `{message, status}` antes de que el componente lo vea. Sin él, el
        // spec verificaría una forma de error que la pantalla nunca recibe.
        { provide: HTTP_INTERCEPTORS, useClass: ErrorInterceptor, multi: true },
      ],
    });
    fixture = TestBed.createComponent(MatrizPoauComponent);
    componente = fixture.componentInstance;
    http = TestBed.inject(HttpTestingController);
    fixture.detectChanges();
    // Con catálogo real queda cacheado: la recarga posterior al borrado no
    // vuelve a pedirlo, igual que en la pantalla.
    CATALOGO(http, [{ codigo: 'EM-DJR-01', nombre: 'JURÍDICA' }]);
    PRESUPUESTO(http);
    MATRIZ(http, {
      gestion: 2027, total_filas: 2, filas: [FILA_UNIDAD, FILA_TAREA],
    });
    componente.expandirTodo();
    fixture.detectChanges();
  };

  afterEach(() => http.verify());

  it('no le ofrece el botón a quien no es administrador', () => {
    montar(false);
    expect(componente.puedeBorrarPoau(FILA_UNIDAD)).toBeFalse();
    expect(fixture.nativeElement.querySelector('.borrar-poau')).toBeNull();
  });

  it('le da al administrador un botón en la fila de unidad, y solo ahí', () => {
    montar(true);
    expect(componente.puedeBorrarPoau(FILA_UNIDAD)).toBeTrue();
    // Una tarea tiene su propio ✕: el del árbol entero no va ahí.
    expect(componente.puedeBorrarPoau(FILA_TAREA)).toBeFalse();
    const botones = fixture.nativeElement.querySelectorAll('.borrar-poau');
    expect(botones.length).toBe(1);
  });

  it('consulta el impacto antes de borrar y exige teclear el código', () => {
    montar(true);
    spyOn(window, 'confirm').and.returnValue(true);
    spyOn(window, 'prompt').and.returnValue('em-djr-01');

    componente.eliminarPoauUnidad(FILA_UNIDAD);
    http.expectOne(r => r.url.includes(URL_UNIDAD) && r.method === 'GET')
        .flush(IMPACTO);

    // El aviso de confirmación lleva el conteo real, no una estimación.
    const texto = (window.confirm as jasmine.Spy).calls.mostRecent().args[0];
    expect(texto).toContain('147');
    expect(texto).toContain('NO se borra');

    http.expectOne(r => r.url.includes(URL_UNIDAD) && r.method === 'DELETE')
        .flush({ ...IMPACTO, eliminados: IMPACTO.eliminaria });
    PRESUPUESTO(http);
    MATRIZ(http, { gestion: 2027, total_filas: 0, filas: [] });
    expect(componente.aviso).toContain('147');
  });

  it('no borra nada si el código tecleado no coincide', () => {
    montar(true);
    spyOn(window, 'confirm').and.returnValue(true);
    spyOn(window, 'prompt').and.returnValue('OTRA-COSA');

    componente.eliminarPoauUnidad(FILA_UNIDAD);
    http.expectOne(r => r.url.includes(URL_UNIDAD) && r.method === 'GET')
        .flush(IMPACTO);

    http.expectNone(r => r.method === 'DELETE');
    expect(componente.aviso).toContain('no coincide');
  });

  it('no borra nada si se cancela la confirmación', () => {
    montar(true);
    spyOn(window, 'confirm').and.returnValue(false);

    componente.eliminarPoauUnidad(FILA_UNIDAD);
    http.expectOne(r => r.url.includes(URL_UNIDAD) && r.method === 'GET')
        .flush(IMPACTO);

    http.expectNone(r => r.method === 'DELETE');
  });

  it('el 409 dice qué está reteniendo el árbol, no «no se pudo»', () => {
    montar(true);
    componente.eliminarPoauUnidad(FILA_UNIDAD);
    http.expectOne(r => r.url.includes(URL_UNIDAD) && r.method === 'GET')
        .flush(
          {
            ...IMPACTO,
            bloqueado_por: [
              { modelo: 'presupuesto.AsignacionPresupuestariaUnidad', registros: 3 },
            ],
            detail: [
              'No se puede eliminar: hay registros que dependen de este POAU '
              + '— Asignaciones presupuestarias (3).',
            ],
          },
          { status: 409, statusText: 'Conflict' },
        );
    expect(componente.error).toContain('Asignaciones presupuestarias (3)');
  });

  it('un error sin motivo no muestra el ruido de transporte de Angular', () => {
    montar(true);
    componente.eliminarPoauUnidad(FILA_UNIDAD);
    http.expectOne(r => r.url.includes(URL_UNIDAD) && r.method === 'GET')
        .flush(null, { status: 500, statusText: 'Server Error' });
    expect(componente.error).toBe('No se pudo calcular qué se eliminaría.');
  });
});

describe('MatrizPoauComponent · denominación de la categoría programática', () => {
  let componente: MatrizPoauComponent;

  beforeEach(() => {
    TestBed.configureTestingModule({
      imports: [HttpClientTestingModule, RouterTestingModule, FormsModule],
      declarations: [MatrizPoauComponent, ComboBoxComponent],
    });
    componente = TestBed.createComponent(MatrizPoauComponent).componentInstance;
    TestBed.inject(HttpTestingController).verify();
  });

  const CATALOGO = {
    categoria_programatica: '000 0 001',
    denominacion_categoria: 'FUNCIONAMIENTO ALCALDIA MUNICIPAL',
    origen_categoria: 'catalogo',
  };
  const APROX = {
    categoria_programatica: '160 0 008',
    denominacion_categoria: 'SERVICIOS ELECTRICOS',
    origen_categoria: 'programa',
  };
  const HUERFANA = {
    categoria_programatica: '131 0 010',
    denominacion_categoria: '', origen_categoria: '',
  };

  it('muestra la denominación del catálogo tal cual', () => {
    expect(componente.celda(CATALOGO, 'denominacion_categoria'))
      .toBe('FUNCIONAMIENTO ALCALDIA MUNICIPAL');
    expect(componente.claseCelda(CATALOGO, 'denominacion_categoria')).toBe('');
  });

  it('marca con ≈ lo que viene del nivel programa, no de la actividad', () => {
    expect(componente.celda(APROX, 'denominacion_categoria'))
      .toBe('≈ SERVICIOS ELECTRICOS');
    expect(componente.claseCelda(APROX, 'denominacion_categoria')).toBe('aprox');
  });

  it('dice "sin catálogo" en vez de dejar la celda vacía', () => {
    // Una celda en blanco se lee como olvido de carga; esto es otra cosa.
    expect(componente.celda(HUERFANA, 'denominacion_categoria')).toBe('sin catálogo');
    expect(componente.claseCelda(HUERFANA, 'denominacion_categoria')).toBe('sin-catalogo');
    expect(componente.tituloCelda(HUERFANA, 'denominacion_categoria'))
      .toContain('131 0 010');
  });

  it('la unidad y la AIE sin categoría no muestran nada', () => {
    const fila = { categoria_programatica: '', denominacion_categoria: '' };
    expect(componente.celda(fila, 'denominacion_categoria')).toBe('');
    expect(componente.claseCelda(fila, 'denominacion_categoria')).toBe('');
  });

  it('solo decora la columna de denominación, no las demás', () => {
    for (const clave of ['operacion', 'tarea', 'meta', 'categoria_programatica']) {
      expect(componente.claseCelda(HUERFANA, clave)).toBe('');
    }
  });
});

describe('MatrizPoauComponent · layout medido en el navegador', () => {
  let fixture: ComponentFixture<MatrizPoauComponent>;
  let componente: MatrizPoauComponent;
  let http: HttpTestingController;

  const FILAS_L = [
    { id: 'u', padre: null, nivel: 'unidad', orden_nivel: 0, hijos: 1, unidad: 'JURÍDICA' },
    { id: 'u|p', padre: 'u', nivel: 'aie', orden_nivel: 1, hijos: 1,
      accion_institucional: 'Ejecutar el 100 % de la programación institucional' },
    { id: 'u|p|a', padre: 'u|p', nivel: 'accion', orden_nivel: 2, hijos: 0,
      accion_corto_plazo: 'Acción de corto plazo' },
  ];

  beforeEach(() => {
    TestBed.configureTestingModule({
      imports: [HttpClientTestingModule, RouterTestingModule, FormsModule],
      declarations: [MatrizPoauComponent, ComboBoxComponent],
    });
    fixture = TestBed.createComponent(MatrizPoauComponent);
    componente = fixture.componentInstance;
    http = TestBed.inject(HttpTestingController);
    fixture.detectChanges();
    CATALOGO(http);
    PRESUPUESTO(http);
    MATRIZ(http, { gestion: 2027, total_filas: 3, filas: FILAS_L });
    componente.expandirTodo();
    fixture.detectChanges();
  });

  afterEach(() => http.verify());

  const tabla = () => fixture.nativeElement.querySelector('table.mz') as HTMLElement;
  const caja = () => fixture.nativeElement.querySelector('.tabla-caja') as HTMLElement;

  it('la tabla crece más allá del contenedor en vez de comprimirse', () => {
    // styles.scss pone width:100% a table.tabla; con table-layout fijo eso
    // aplastaba las 34 columnas dentro del ancho de la caja.
    componente.modo = 'matriz';
    componente.filas.forEach((f: any) => (f.celdas = componente.armarCeldas(f)));
    fixture.detectChanges();
    // El colgroup suma ~4.500px: si la tabla no puede crecer, el navegador
    // reparte ese ancho dentro de la caja y las columnas se aplastan.
    const declarado = Array.from(tabla().querySelectorAll('colgroup col'))
      .reduce((n, c) => n + parseInt((c as HTMLElement).style.width, 10), 0);
    expect(declarado).toBeGreaterThan(4000);
    expect(tabla().offsetWidth).toBeGreaterThanOrEqual(declarado);
    expect(tabla().offsetWidth).toBeGreaterThan(caja().clientWidth);
  });

  it('la caja recorta el alto para que haya scroll vertical', () => {
    const estilo = getComputedStyle(caja());
    expect(estilo.overflowY).toBe('auto');
    expect(estilo.overflowX).toBe('auto');
  });

  it('la segunda fila del encabezado se pega justo debajo de la primera', () => {
    for (const modo of ['arbol', 'matriz'] as const) {
      componente.modo = modo;
      componente.filas.forEach((f: any) => (f.celdas = componente.armarCeldas(f)));
      fixture.detectChanges();
      (componente as any).medirBanda();
      const fila = tabla().querySelector('thead tr:first-child') as HTMLElement;
      const columna = tabla().querySelector('thead tr:nth-child(2) th') as HTMLElement;
      // Si el desnivel queda corto, la segunda fila se monta sobre la primera.
      expect(parseInt(getComputedStyle(columna).top, 10))
        .toBe(Math.round(fila.getBoundingClientRect().height));
    }
  });

  it('las celdas fijas del encabezado tienen fondo opaco', () => {
    // Sin fondo, las filas se ven pasar por debajo al desplazar.
    for (const th of Array.from(tabla().querySelectorAll('thead .th-fija'))) {
      const fondo = getComputedStyle(th as HTMLElement).backgroundColor;
      expect(fondo).not.toBe('rgba(0, 0, 0, 0)');
      expect(fondo).not.toBe('transparent');
    }
  });

  it('el encabezado y las columnas de los costados quedan pegados', () => {
    const banda = tabla().querySelector('thead tr:first-child th:not(.th-fija)') as HTMLElement;
    expect(getComputedStyle(banda).position).toBe('sticky');
    const sel = tabla().querySelector('tbody .td-sel') as HTMLElement;
    const acc = tabla().querySelector('tbody .td-acc') as HTMLElement;
    expect(getComputedStyle(sel).position).toBe('sticky');
    expect(getComputedStyle(sel).left).toBe('0px');
    expect(getComputedStyle(acc).right).toBe('0px');
  });

  it('ninguna fila del cuerpo pierde ni suma columnas', () => {
    for (const modo of ['arbol', 'matriz'] as const) {
      componente.modo = modo;
      componente.filas.forEach((f: any) => (f.celdas = componente.armarCeldas(f)));
      fixture.detectChanges();
      const columnas = tabla().querySelectorAll('colgroup col').length;
      for (const tr of Array.from(tabla().querySelectorAll('tbody tr'))) {
        const ancho = Array.from(tr.querySelectorAll('td'))
          .reduce((n, td) => n + ((td as HTMLTableCellElement).colSpan || 1), 0);
        expect(ancho).toBe(columnas);
      }
    }
  });
});

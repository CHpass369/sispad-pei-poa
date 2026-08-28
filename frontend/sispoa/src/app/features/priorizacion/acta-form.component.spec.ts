import { ComponentFixture, TestBed, fakeAsync, tick } from '@angular/core/testing';
import { HttpClientTestingModule, HttpTestingController } from '@angular/common/http/testing';
import { RouterTestingModule } from '@angular/router/testing';
import { FormsModule } from '@angular/forms';
import { ActaFormComponent } from './acta-form.component';
import { GestionHabilitadaService } from '../../core/services/gestion-habilitada.service';
import { gestionHabilitadaStub } from '../../core/testing/gestion-habilitada.stub';

describe('ActaFormComponent · buscador y carga de proyectos', () => {
  let fixture: ComponentFixture<ActaFormComponent>;
  let componente: ActaFormComponent;
  let http: HttpTestingController;

  const DEL_SIGEP = {
    id: 'c1', nombre: 'CONST. SISTEMA DE MICRORIEGO', sisin: '02874735200000',
    categoria_programatica: '100 02874735200000 000',
    denominacion_categoria: '', origen: 'SIGEP', veces_priorizado: 0,
  };
  const HISTORICO = {
    id: 'c2', nombre: 'ADQ. LUMINARIAS DISTRITO 4', sisin: '',
    categoria_programatica: '', denominacion_categoria: '',
    origen: 'HISTORICO', veces_priorizado: 6,
  };

  const teclear = (texto: string) => {
    componente.buscar({ target: { value: texto } } as any);
    tick(250);
  };

  beforeEach(() => {
    TestBed.configureTestingModule({
      imports: [HttpClientTestingModule, RouterTestingModule, FormsModule],
      declarations: [ActaFormComponent],
      providers: [
        { provide: GestionHabilitadaService, useValue: gestionHabilitadaStub(2027) },
      ],
    });
    fixture = TestBed.createComponent(ActaFormComponent);
    componente = fixture.componentInstance;
    http = TestBed.inject(HttpTestingController);
    componente.ngOnInit();
    http.expectOne(r => r.url.includes('/distritos/')).flush({ results: [] });
    http.expectOne(r => r.url.includes('categorias-programaticas')).flush([]);
    http.expectOne(r => r.url.includes('/saldos/')).flush({
      gestion: 2027, total_techo: 1000000, total_disponible: 800000,
      pares: [
        { par: '41/113', fuente: '41', organismo: '113', fuente_id: 'f1',
          organismo_id: 'o1', techo: 1000000, asignado: 200000,
          comprometido: 0, disponible: 800000 },
        { par: '20/210', fuente: '20', organismo: '210', fuente_id: 'f2',
          organismo_id: 'o2', techo: 50000, asignado: 50000,
          comprometido: 0, disponible: 0 },
      ],
    });
 
    // El formulario trae el padrón de organizaciones al iniciar.
    http.expectOne(r => r.url.includes('/unidades-territoriales/dominio/'))
        .flush({ gestion: 2027, total: 0, resultados: [] });
  });

  afterEach(() => http.verify());

  it('no consulta hasta tener al menos dos caracteres', fakeAsync(() => {
    teclear('l');
    http.expectNone(r => r.url.includes('catalogo-proyectos'));
    expect(componente.sugerencias.length).toBe(0);
  }));

  it('espera a que se deje de escribir: una consulta, no una por tecla',
     fakeAsync(() => {
    componente.buscar({ target: { value: 'lu' } } as any);
    componente.buscar({ target: { value: 'lum' } } as any);
    componente.buscar({ target: { value: 'lumin' } } as any);
    tick(250);
    const pedidos = http.match(r => r.url.includes('catalogo-proyectos'));
    expect(pedidos.length).toBe(1);
    expect(pedidos[0].request.params.get('q')).toBe('lumin');
    pedidos[0].flush({ total: 1, resultados: [HISTORICO] });
    expect(componente.totalHallado).toBe(1);
  }));

  it('elegir del SIGEP arrastra SISIN y categoría', fakeAsync(() => {
    teclear('microriego');
    http.expectOne(r => r.url.includes('catalogo-proyectos'))
        .flush({ total: 1, resultados: [DEL_SIGEP] });
    componente.elegir(DEL_SIGEP);
    const p = componente.acta.proyectos[0];
    expect(p.sisin).toBe('02874735200000');
    expect(p.categoria_programatica).toBe('100 02874735200000 000');
    expect(p.catalogo).toBe('c1');
  }));

  it('un nombre histórico entra sin categoría: la elige el técnico',
     fakeAsync(() => {
    teclear('lumin');
    http.expectOne(r => r.url.includes('catalogo-proyectos'))
        .flush({ total: 1, resultados: [HISTORICO] });
    componente.elegir(HISTORICO);
    expect(componente.acta.proyectos[0].categoria_programatica).toBe('');
    expect(componente.acta.proyectos[0].sisin).toBe('');
  }));

  it('lo que no está en el catálogo se puede cargar igual', fakeAsync(() => {
    teclear('puente peatonal nuevo');
    http.expectOne(r => r.url.includes('catalogo-proyectos'))
        .flush({ total: 0, resultados: [] });
    componente.agregarLibre();
    expect(componente.acta.proyectos[0].nombre).toBe('puente peatonal nuevo');
    expect(componente.acta.proyectos[0].catalogo).toBeNull();
  }));

  it('al elegir se limpia la búsqueda y se cierra la lista', fakeAsync(() => {
    teclear('lumin');
    http.expectOne(r => r.url.includes('catalogo-proyectos'))
        .flush({ total: 1, resultados: [HISTORICO] });
    componente.elegir(HISTORICO);
    expect(componente.consulta).toBe('');
    expect(componente.abierto).toBe(false);
    expect(componente.sugerencias.length).toBe(0);
  }));

  it('el total suma los montos cargados e ignora los vacíos', () => {
    componente.acta.proyectos = [
      { nombre: 'a', sisin: '', categoria_programatica: '', monto: 220000 },
      { nombre: 'b', sisin: '', categoria_programatica: '', monto: null },
      { nombre: 'c', sisin: '', categoria_programatica: '', monto: 10000 },
    ];
    expect(componente.total).toBe(230000);
  });

  it('no deja guardar sin distrito, OTB ni presidente', () => {
    // La fecha ya no entra en la validación: la pone el servidor al registrar
    // (`fecha` es read_only en el serializador) y el campo va de solo lectura.
    expect(componente.valido()).toBe(false);
    componente.acta.distrito = 'd1';
    expect(componente.valido()).toBe(false);
    componente.acta.otb = 'OTB X';
    expect(componente.valido()).toBe(false);
    componente.acta.presidente = 'Juan';
    expect(componente.valido()).toBe(true);
  });

  it('quitar saca solo la fila indicada', () => {
    componente.acta.proyectos = [
      { nombre: 'a', sisin: '', categoria_programatica: '', monto: null },
      { nombre: 'b', sisin: '', categoria_programatica: '', monto: null },
    ];
    componente.quitar(0);
    expect(componente.acta.proyectos.map(p => p.nombre)).toEqual(['b']);
  });
});

describe('ActaFormComponent · techos por FF/OF', () => {
  let componente: ActaFormComponent;
  let http: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({
      imports: [HttpClientTestingModule, RouterTestingModule, FormsModule],
      declarations: [ActaFormComponent],
      providers: [
        { provide: GestionHabilitadaService, useValue: gestionHabilitadaStub(2027) },
      ],
    });
    componente = TestBed.createComponent(ActaFormComponent).componentInstance;
    http = TestBed.inject(HttpTestingController);
    componente.ngOnInit();
    http.expectOne(r => r.url.includes('/distritos/')).flush({ results: [] });
    http.expectOne(r => r.url.includes('categorias-programaticas')).flush([]);
    http.expectOne(r => r.url.includes('/saldos/')).flush({
      gestion: 2027, total_techo: 1000000, total_disponible: 800000,
      pares: [
        { par: '41/113', fuente: '41', organismo: '113', fuente_id: 'f1',
          organismo_id: 'o1', techo: 1000000, asignado: 200000,
          comprometido: 0, disponible: 800000 },
        { par: '20/210', fuente: '20', organismo: '210', fuente_id: 'f2',
          organismo_id: 'o2', techo: 50000, asignado: 50000,
          comprometido: 0, disponible: 0 },
      ],
    });
 
    // El formulario trae el padrón de organizaciones al iniciar.
    http.expectOne(r => r.url.includes('/unidades-territoriales/dominio/'))
        .flush({ gestion: 2027, total: 0, resultados: [] });
  });

  afterEach(() => http.verify());

  const proyecto = (par = '', monto: number | null = null) => ({
    nombre: 'X', sisin: '', categoria_programatica: '', monto,
    par_elegido: par, fuente: null, organismo: null,
  } as any);

  it('pide el saldo sin mandar la gestión y sin excluir nada al crear', () => {
    // Al editar sí se excluye el acta: si no, sus propios montos se
    // descontarían del techo que se le muestra al técnico.
    const otro = TestBed.createComponent(ActaFormComponent).componentInstance;
    otro.ngOnInit();
    http.expectOne(r => r.url.includes('/distritos/')).flush({ results: [] });
    http.expectOne(r => r.url.includes('categorias-programaticas')).flush([]);
    http.expectOne(r => r.url.includes('/unidades-territoriales/dominio/'))
        .flush({ gestion: 2027, total: 0, resultados: [] });
    const pedido = http.expectOne(r => r.url.includes('/saldos/'));
    // La gestión ya no viaja: el saldo es el de la gestión habilitada, que
    // resuelve el backend desde el candado (ADR-007).
    expect(pedido.request.params.get('gestion')).toBeNull();
    expect(pedido.request.params.get('excluir_acta')).toBeNull();
    expect(otro.acta.gestion).toBe(2027);
    pedido.flush({ gestion: 2027, total_techo: 0, total_disponible: 0, pares: [] });
    expect(componente.pares.length).toBe(2);
  });

  it('elegir el par completa los dos identificadores que guarda el acta', () => {
    const p = proyecto('41/113');
    componente.elegirPar(p);
    expect(p.fuente).toBe('f1');
    expect(p.organismo).toBe('o1');
  });

  it('deseleccionar el par limpia los identificadores', () => {
    const p = proyecto('41/113');
    componente.elegirPar(p);
    p.par_elegido = '';
    componente.elegirPar(p);
    expect(p.fuente).toBeNull();
    expect(p.organismo).toBeNull();
  });

  it('el saldo baja con lo que se va cargando en el acta', () => {
    componente.acta.proyectos = [proyecto('41/113', 300000)];
    const par = componente.pares[0];
    expect(componente.cargadoEn('41/113')).toBe(300000);
    expect(componente.saldoTrasCargar(par)).toBe(500000);
  });

  it('varios proyectos contra el mismo par se acumulan', () => {
    componente.acta.proyectos = [proyecto('41/113', 300000),
                                 proyecto('41/113', 200000)];
    expect(componente.saldoTrasCargar(componente.pares[0])).toBe(300000);
  });

  it('cada par descuenta solo lo suyo', () => {
    componente.acta.proyectos = [proyecto('41/113', 300000),
                                 proyecto('20/210', 10000)];
    expect(componente.saldoTrasCargar(componente.pares[0])).toBe(500000);
    expect(componente.saldoTrasCargar(componente.pares[1])).toBe(-10000);
  });

  it('el sobregiro se muestra en negativo, no se recorta a cero', () => {
    componente.acta.proyectos = [proyecto('41/113', 1500000)];
    expect(componente.saldoTrasCargar(componente.pares[0])).toBe(-700000);
    expect(componente.saldoDelProyecto(componente.acta.proyectos[0]))
      .toBe(-700000);
  });

  it('un proyecto sin par no reporta saldo', () => {
    expect(componente.saldoDelProyecto(proyecto())).toBeNull();
  });
});

describe('ActaFormComponent · padrón de organizaciones', () => {
  let componente: ActaFormComponent;
  let http: HttpTestingController;

  const ULINCATE = {
    id: 'u1', codigo: 'D1-002', nombre: 'OTB ULINCATE CENTRO', tipo: 'otb',
    tipo_display: 'OTB', distrito: 'd1', distrito_codigo: 'D1',
    dirigente: 'GROVER COSSIO ORELLANA', cargo: 'PRESIDENTE',
    telefono: '72210053',
  };
  const QUINTO = {
    id: 'u2', codigo: 'D1-022', nombre: 'COMUNIDAD QUINTO ULINCATE',
    tipo: 'comunidad', tipo_display: 'Comunidad', distrito: 'd1',
    distrito_codigo: 'D1', dirigente: 'LUIS FERNANDO ARNEZ VASQUEZ',
    cargo: 'PRESIDENTE', telefono: '72791040',
  };
  const SUBCENTRAL = {
    id: 'u3', codigo: 'DLL-004', nombre: 'SUBCENTRAL U.T.C. TEMPORAL BAJO',
    tipo: 'subcentral', tipo_display: 'Subcentral', distrito: 'dll',
    distrito_codigo: 'DLL', dirigente: 'LUIS ROJAS',
    cargo: 'SECRETARIO GENERAL', telefono: '',
  };
  const PADRON = [ULINCATE, QUINTO, SUBCENTRAL];

  const teclearOtb = (texto: string) =>
    componente.buscarOtb({ target: { value: texto } } as any);
  const tecla = (key: string) =>
    ({ key, preventDefault: jasmine.createSpy('preventDefault') } as any);
  const teclearPresidente = (texto: string) =>
    componente.buscarPresidente({ target: { value: texto } } as any);

  beforeEach(() => {
    TestBed.configureTestingModule({
      imports: [HttpClientTestingModule, RouterTestingModule, FormsModule],
      declarations: [ActaFormComponent],
      providers: [
        { provide: GestionHabilitadaService, useValue: gestionHabilitadaStub(2027) },
      ],
    });
    componente = TestBed.createComponent(ActaFormComponent).componentInstance;
    http = TestBed.inject(HttpTestingController);
    componente.ngOnInit();
    http.expectOne(r => r.url.includes('/distritos/')).flush({ results: [] });
    http.expectOne(r => r.url.includes('categorias-programaticas')).flush([]);
    http.expectOne(r => r.url.includes('/saldos/'))
        .flush({ gestion: 2027, total_techo: 0, total_disponible: 0, pares: [] });
    http.expectOne(r => r.url.includes('/unidades-territoriales/dominio/'))
        .flush({ gestion: 2027, total: PADRON.length, resultados: PADRON });
  });

  afterEach(() => http.verify());

  it('trae el padrón entero una sola vez, sin distrito', () => {
    // Una consulta por tecla satura el backend sin mejorar nada: son 368 filas
    // con los doce distritos, se filtran en memoria.
    expect(componente.organizaciones.length).toBe(3);
    teclearOtb('ulincate');
    teclearOtb('ulincate centro');
    http.expectNone(r => r.url.includes('/unidades-territoriales/dominio/'));
  });

  it('enfocar sin escribir despliega el padrón entero', () => {
    componente.abrir('otb');
    expect(componente.abiertoPadron).toBe('otb');
    expect(componente.sugeridas.length).toBe(3);
  });

  it('cada palabra acota más', () => {
    teclearOtb('ulincate');
    expect(componente.sugeridas.map(o => o.codigo)).toEqual(['D1-002', 'D1-022']);
    teclearOtb('ulincate comunidad');
    expect(componente.sugeridas.map(o => o.codigo)).toEqual(['D1-022']);
  });

  it('busca sin tildes ni puntuación', () => {
    teclearOtb('o.t.b. ulincate');
    expect(componente.sugeridas.map(o => o.codigo)).toEqual(['D1-002']);
  });

  it('el buscador de la OTB también encuentra por dirigente', () => {
    teclearOtb('cossio');
    expect(componente.sugeridas.map(o => o.codigo)).toEqual(['D1-002']);
  });

  it('elegir de la lista completa los dos campos y el distrito', () => {
    componente.abrir('otb');
    componente.tomar(ULINCATE, 'otb');
    expect(componente.acta.otb).toBe('OTB ULINCATE CENTRO');
    expect(componente.acta.presidente).toBe('GROVER COSSIO ORELLANA');
    expect(componente.acta.unidad_territorial).toBe('u1');
    expect(componente.acta.distrito).toBe('d1');
    expect(componente.abiertoPadron).toBe('');
  });

  it('se puede entrar por el presidente y completa la OTB', () => {
    teclearPresidente('rojas');
    expect(componente.sugeridas.map(o => o.codigo)).toEqual(['DLL-004']);
    componente.tomar(componente.sugeridas[0], 'presidente');
    expect(componente.acta.otb).toBe('SUBCENTRAL U.T.C. TEMPORAL BAJO');
    expect(componente.acta.presidente).toBe('LUIS ROJAS');
    expect(componente.acta.distrito).toBe('dll');
  });

  it('escribir el nombre exacto vale lo mismo que elegirlo', () => {
    teclearOtb('OTB ULINCATE CENTRO');
    expect(componente.acta.unidad_territorial).toBe('u1');
    expect(componente.acta.presidente).toBe('GROVER COSSIO ORELLANA');
  });

  it('el distrito elegido acota el padrón', () => {
    componente.cambiarDistrito('d1');
    componente.abrir('otb');
    expect(componente.sugeridas.map(o => o.codigo)).toEqual(['D1-002', 'D1-022']);
  });

  it('cambiar de distrito limpia la organización del distrito anterior', () => {
    componente.tomar(ULINCATE, 'otb');
    componente.cambiarDistrito('dll');
    expect(componente.acta.otb).toBe('');
    expect(componente.acta.unidad_territorial).toBeNull();
    expect(componente.acta.presidente).toBe('');
  });

  it('un nombre fuera del padrón se conserva como texto libre', () => {
    teclearOtb('OTB QUE TODAVIA NO ESTA CARGADA');
    expect(componente.acta.otb).toBe('OTB QUE TODAVIA NO ESTA CARGADA');
    expect(componente.acta.unidad_territorial).toBeNull();
    expect(componente.pistaOtb())
      .toBe('No figura en el padrón: se guarda como texto libre.');
  });

  it('seguir tipeando retira el presidente que había puesto el padrón', () => {
    // Se pasa por coincidencias intermedias al escribir de corrido: dejar
    // pegado al presidente de otra organización sería peor que dejarlo vacío.
    teclearOtb('OTB ULINCATE CENTRO');
    teclearOtb('OTB ULINCATE CENTRO II');
    expect(componente.acta.presidente).toBe('');
    expect(componente.acta.unidad_territorial).toBeNull();
  });

  it('no pisa el presidente escrito a mano', () => {
    componente.acta.presidente = 'OTRO DIRIGENTE';
    componente.tomar(ULINCATE, 'otb');
    expect(componente.acta.presidente).toBe('OTRO DIRIGENTE');
  });

  it('cambiar de organización cambia el presidente que puso el padrón', () => {
    componente.tomar(ULINCATE, 'otb');
    componente.tomar(SUBCENTRAL, 'otb');
    expect(componente.acta.presidente).toBe('LUIS ROJAS');
  });

  it('expone el cargo cuando no es presidente', () => {
    componente.tomar(SUBCENTRAL, 'otb');
    expect(componente.cargoDirigente).toBe('SECRETARIO GENERAL');
  });

  it('la flecha abajo abre la lista y resalta la primera', () => {
    componente.teclaPadron(tecla('ArrowDown'), 'otb');
    expect(componente.abiertoPadron).toBe('otb');
    expect(componente.indiceActivo).toBe(0);
  });

  it('las flechas recorren y dan la vuelta en los extremos', () => {
    componente.abrir('otb');
    expect(componente.indiceActivo).toBe(-1);
    componente.teclaPadron(tecla('ArrowDown'), 'otb');
    componente.teclaPadron(tecla('ArrowDown'), 'otb');
    expect(componente.indiceActivo).toBe(1);
    // Son tres: de la última vuelve a la primera.
    componente.teclaPadron(tecla('ArrowDown'), 'otb');
    componente.teclaPadron(tecla('ArrowDown'), 'otb');
    expect(componente.indiceActivo).toBe(0);
    componente.teclaPadron(tecla('ArrowUp'), 'otb');
    expect(componente.indiceActivo).toBe(2);
  });

  it('Enter elige la opción resaltada', () => {
    componente.abrir('otb');
    // Sin texto la lista es el padrón entero, en orden: ULINCATE es la primera.
    componente.teclaPadron(tecla('ArrowDown'), 'otb');
    componente.teclaPadron(tecla('Enter'), 'otb');
    expect(componente.acta.otb).toBe('OTB ULINCATE CENTRO');
    expect(componente.acta.unidad_territorial).toBe('u1');
    expect(componente.acta.presidente).toBe('GROVER COSSIO ORELLANA');
    expect(componente.abiertoPadron).toBe('');
  });

  it('bajar dos veces y elegir toma la segunda', () => {
    componente.abrir('otb');
    componente.teclaPadron(tecla('ArrowDown'), 'otb');
    componente.teclaPadron(tecla('ArrowDown'), 'otb');
    componente.teclaPadron(tecla('Enter'), 'otb');
    expect(componente.acta.otb).toBe('COMUNIDAD QUINTO ULINCATE');
  });

  it('Enter sin nada resaltado respeta lo tipeado', () => {
    // Es lo que hace NO restrictivo a este combobox: un nombre que no está en
    // el padrón se guarda igual.
    teclearOtb('OTB QUE NO ESTA');
    const evento = tecla('Enter');
    componente.teclaPadron(evento, 'otb');
    expect(componente.acta.otb).toBe('OTB QUE NO ESTA');
    expect(componente.acta.unidad_territorial).toBeNull();
    expect(evento.preventDefault).not.toHaveBeenCalled();
  });

  it('Escape cierra sin borrar lo escrito', () => {
    teclearOtb('ulincate');
    componente.teclaPadron(tecla('Escape'), 'otb');
    expect(componente.abiertoPadron).toBe('');
    expect(componente.acta.otb).toBe('ulincate');
  });

  it('Tab cierra y deja pasar el foco', () => {
    componente.abrir('otb');
    const evento = tecla('Tab');
    componente.teclaPadron(evento, 'otb');
    expect(componente.abiertoPadron).toBe('');
    expect(evento.preventDefault).not.toHaveBeenCalled();
  });

  it('las flechas no mueven el cursor dentro del campo', () => {
    componente.abrir('otb');
    const evento = tecla('ArrowDown');
    componente.teclaPadron(evento, 'otb');
    expect(evento.preventDefault).toHaveBeenCalled();
  });

  it('una tecla cualquiera no la maneja el combobox', () => {
    componente.abrir('otb');
    const evento = tecla('a');
    componente.teclaPadron(evento, 'otb');
    expect(evento.preventDefault).not.toHaveBeenCalled();
    expect(componente.abiertoPadron).toBe('otb');
  });

  it('el lector de pantalla recibe cuál opción está resaltada', () => {
    componente.abrir('presidente');
    expect(componente.opcionActivaId('presidente')).toBeNull();
    componente.teclaPadron(tecla('ArrowDown'), 'presidente');
    expect(componente.opcionActivaId('presidente')).toBe('opcion-presidente-0');
    // Y nunca el del otro campo, que está cerrado.
    expect(componente.opcionActivaId('otb')).toBeNull();
  });

  it('perder el foco cierra la lista', () => {
    componente.abrir('otb');
    componente.cerrarPadron();
    expect(componente.abiertoPadron).toBe('');
    expect(componente.sugeridas.length).toBe(0);
  });

  it('si el padrón no responde, los campos siguen a mano', () => {
    const otro = TestBed.createComponent(ActaFormComponent).componentInstance;
    otro.ngOnInit();
    http.expectOne(r => r.url.includes('/distritos/')).flush({ results: [] });
    http.expectOne(r => r.url.includes('categorias-programaticas')).flush([]);
    http.expectOne(r => r.url.includes('/saldos/'))
        .flush({ gestion: 2027, total_techo: 0, total_disponible: 0, pares: [] });
    http.expectOne(r => r.url.includes('/unidades-territoriales/dominio/'))
        .flush('', { status: 500, statusText: 'Error' });
    expect(otro.organizaciones.length).toBe(0);
    expect(otro.pistaOtb()).toBe('Padrón no disponible: se escribe a mano.');
  });
});

import { ComponentFixture, TestBed, fakeAsync, tick } from '@angular/core/testing';
import { HttpClientTestingModule, HttpTestingController } from '@angular/common/http/testing';
import { RouterTestingModule } from '@angular/router/testing';
import { FormsModule } from '@angular/forms';
import { ActaFormComponent } from './acta-form.component';

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
    });
    fixture = TestBed.createComponent(ActaFormComponent);
    componente = fixture.componentInstance;
    http = TestBed.inject(HttpTestingController);
    componente.ngOnInit();
    http.expectOne(r => r.url.includes('/distritos/')).flush({ results: [] });
    http.expectOne(r => r.url.includes('categorias-programaticas')).flush([]);
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

  it('no deja guardar sin distrito, OTB, presidente ni fecha', () => {
    expect(componente.valido()).toBe(false);
    componente.acta.distrito = 'd1';
    componente.acta.otb = 'OTB X';
    componente.acta.presidente = 'Juan';
    expect(componente.valido()).toBe(false);
    componente.acta.fecha = '2026-09-03';
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

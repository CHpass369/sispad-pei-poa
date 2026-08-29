import { ComponentFixture, TestBed } from '@angular/core/testing';
import { HttpClientTestingModule, HttpTestingController } from '@angular/common/http/testing';
import { RouterTestingModule } from '@angular/router/testing';
import { FormsModule } from '@angular/forms';
import { ActasListadoComponent } from './actas-listado.component';
import { GestionHabilitadaService } from '../../core/services/gestion-habilitada.service';
import { gestionHabilitadaStub } from '../../core/testing/gestion-habilitada.stub';

describe('ActasListadoComponent · orden del listado', () => {
  let fixture: ComponentFixture<ActasListadoComponent>;
  let componente: ActasListadoComponent;
  let http: HttpTestingController;

  const ACTA = {
    id: 'a1', gestion: 2027, distrito: 'd1', distrito_nombre: 'DISTRITO 2',
    otb: 'OTB SAN JOSE', presidente: 'LIZETTE CUBA', responsable_registro: '',
    fecha: '2026-09-03', fecha_hora_registro: '2026-09-03T14:35:00Z',
    estado: 'BORRADOR', monto_total: 230000, esta_completa: true,
    proyectos: [],
  };

  /** Responde el pedido de actas y devuelve la URL con la que se pidió. */
  const responderActas = (extra: Record<string, any> = {}): string => {
    const pedido = http.expectOne(r => r.url.includes('/actas/'));
    pedido.flush({
      count: 1, page_size: 25,
      resumen: { actas: 1, proyectos: 2, monto: 230000 },
      results: [ACTA],
      ...extra,
    });
    fixture.detectChanges();
    return pedido.request.urlWithParams;
  };

  /** Tres páginas de actas: 63 registros con páginas de 25. */
  const TRES_PAGINAS = {
    count: 63, page_size: 25,
    resumen: { actas: 63, proyectos: 140, monto: 9000000 },
  };

  const paginador = (): HTMLElement =>
    fixture.nativeElement.querySelector('.paginador');

  const boton = (texto: string): HTMLButtonElement =>
    Array.from(paginador().querySelectorAll('button'))
         .find(b => (b as HTMLElement).textContent!.includes(texto)) as HTMLButtonElement;

  const encabezado = (titulo: string): HTMLElement =>
    Array.from(fixture.nativeElement.querySelectorAll('th.ordenable'))
         .find(th => (th as HTMLElement).textContent!.trim().startsWith(titulo)) as HTMLElement;

  beforeEach(() => {
    TestBed.configureTestingModule({
      imports: [HttpClientTestingModule, RouterTestingModule, FormsModule],
      declarations: [ActasListadoComponent],
      providers: [
        { provide: GestionHabilitadaService, useValue: gestionHabilitadaStub(2027) },
      ],
    });
    fixture = TestBed.createComponent(ActasListadoComponent);
    componente = fixture.componentInstance;
    http = TestBed.inject(HttpTestingController);
    // El primer `detectChanges` es el que dispara `ngOnInit`: llamarlo a mano
    // además dejaría dos pedidos de actas en la cola.
    fixture.detectChanges();
    http.expectOne(r => r.url.includes('/distritos/')).flush({ results: [] });
  });

  afterEach(() => http.verify());

  it('pide lo último registrado arriba sin que nadie toque el encabezado', () => {
    expect(responderActas()).toContain('ordering=-created_at');
  });

  it('marca en el encabezado por cuál columna está ordenando', () => {
    responderActas();
    expect(encabezado('Registrada').textContent).toContain('▼');
    expect(encabezado('Registrada').getAttribute('aria-sort')).toBe('descending');
    expect(encabezado('OTB').getAttribute('aria-sort')).toBe('none');
  });

  it('ordena por la columna del encabezado que se clickea', () => {
    responderActas();
    encabezado('OTB').click();
    expect(responderActas()).toContain('ordering=otb');
    expect(encabezado('OTB').textContent).toContain('▲');
    expect(encabezado('Registrada').textContent).not.toContain('▼');
  });

  it('el segundo click sobre la misma columna invierte el sentido', () => {
    responderActas();
    encabezado('Presidente').click();
    expect(responderActas()).toContain('ordering=presidente');
    encabezado('Presidente').click();
    expect(responderActas()).toContain('ordering=-presidente');
    expect(encabezado('Presidente').textContent).toContain('▼');
  });

  it('ordena también por las columnas calculadas en el servidor', () => {
    // `Proyectos` y `Monto Bs` no son campos del modelo: el backend los anota.
    // Ordenar acá solo alcanzaría a la página ya recibida.
    responderActas();
    encabezado('Proyectos').click();
    expect(responderActas()).toContain('ordering=cuenta_proyectos');
    encabezado('Monto Bs').click();
    expect(responderActas()).toContain('ordering=suma_monto');
  });

  it('el orden convive con los filtros de distrito y búsqueda', () => {
    responderActas();
    componente.distrito = 'd7';
    componente.busqueda = 'koripila';
    encabezado('Fecha').click();
    const url = responderActas();
    expect(url).toContain('ordering=fecha');
    expect(url).toContain('distrito=d7');
    expect(url).toContain('q=koripila');
  });

  describe('paginación', () => {
    it('no muestra paginador cuando todo entra en una página', () => {
      responderActas();
      expect(paginador()).toBeNull();
    });

    it('dice en qué página está y cuántas actas hay en total', () => {
      responderActas(TRES_PAGINAS);
      expect(paginador().textContent).toContain('Página 1 de 3');
      expect(paginador().textContent).toContain('63 actas');
      expect(boton('Anterior').disabled).toBe(true);
      expect(boton('Siguiente').disabled).toBe(false);
    });

    it('el resumen cuenta todas las actas, no las de la página', () => {
      // Llegan 1 acta y 0 proyectos en `results`; las tarjetas dicen 63 y 140
      // porque el total lo manda el servidor.
      responderActas(TRES_PAGINAS);
      const tarjetas = fixture.nativeElement.querySelectorAll('.tarjeta span');
      expect(tarjetas[0].textContent).toContain('63');
      expect(tarjetas[1].textContent).toContain('140');
    });

    it('«siguiente» pide la página que sigue', () => {
      expect(responderActas(TRES_PAGINAS)).toContain('page=1');
      boton('Siguiente').click();
      expect(responderActas(TRES_PAGINAS)).toContain('page=2');
      expect(paginador().textContent).toContain('Página 2 de 3');
    });

    it('reordenar vuelve a la primera página', () => {
      responderActas(TRES_PAGINAS);
      boton('Siguiente').click();
      responderActas(TRES_PAGINAS);
      encabezado('OTB').click();
      const url = responderActas(TRES_PAGINAS);
      expect(url).toContain('page=1');
      expect(url).toContain('ordering=otb');
    });

    it('filtrar vuelve a la primera página', () => {
      responderActas(TRES_PAGINAS);
      boton('Siguiente').click();
      responderActas(TRES_PAGINAS);
      componente.busqueda = 'koripila';
      componente.filtrar();
      expect(responderActas(TRES_PAGINAS)).toContain('page=1');
    });

    it('borrar la única acta de la página retrocede a la anterior', () => {
      // Sin esto el listado recarga una página que el servidor ya no tiene y
      // responde 404 «Invalid page»: la pantalla queda en el mensaje de error.
      responderActas(TRES_PAGINAS);
      boton('Siguiente').click();
      responderActas({ ...TRES_PAGINAS, count: 26, results: [ACTA] });
      spyOn(window, 'confirm').and.returnValue(true);
      componente.eliminar(ACTA as any);
      http.expectOne(r => r.method === 'DELETE').flush({});
      expect(responderActas({ ...TRES_PAGINAS, count: 25 })).toContain('page=1');
    });
  });
});

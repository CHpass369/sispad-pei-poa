import { ComponentFixture, TestBed } from '@angular/core/testing';
import { HttpClientTestingModule, HttpTestingController } from '@angular/common/http/testing';
import { FormsModule } from '@angular/forms';
import { PresupuestoGastosComponent } from './presupuesto-gastos.component';

/**
 * Payload con la forma real del endpoint. El programa se codifica con el rango
 * de la directriz y el subprograma con el numero de tres digitos.
 */
const ARBOL = {
  gestion: 2027,
  gestion_id: 1,
  columnas: [
    { ff_of: '20/210', denominacion: 'Recursos Específicos' },
    { ff_of: '41/113', denominacion: 'Coparticipación' },
  ],
  techos: { '20/210': '90000000', '41/113': '217742150' },
  diferencia: { '20/210': '4524055', '41/113': '48415836' },
  total: { '20/210': '85475945', '41/113': '169326314' },
  programas: [{
    codigo: '170-179',
    denominacion: 'INFRAESTRUCTURA URBANA Y RURAL',
    finalidad_funcion: '4.4.3; 4.5.1; 6.1',
    sector_economico: '11',
    total: { '20/210': '101000', '41/113': '896021' },
    subprogramas: [{
      codigo: '171',
      denominacion: 'INFRAESTRUCTURA URBANA Y RURAL - VIAS URBANAS',
      total: { '20/210': '101000', '41/113': '896021' },
      actividades: [{
        id: 7, categoria: '171 13120104700000 000',
        denominacion: 'CONST. PAVIMENTO ZONA SUDESTE DISTRITO 1',
        unidad_ejecutora: '', direccion_administrativa: '',
        da_id: '', ue_id: '',
        distrito: '', codigo_sisin: '13120104700000', actividad: '000',
        montos: { '20/210': '101000', '41/113': '896021' },
        estado_revision: 'BORRADOR', observacion: '',
        priorizaciones: [], monto_priorizado: 0,
      }],
    }],
  }],
};

const DIRECCIONES = [
  { id: 'da1', codigo: '1', nombre: 'SECRETARIA DE ADMINISTRACION Y FINANZAS' },
  { id: 'da2', codigo: '2', nombre: 'HOSPITAL DE SEGUNDO NIVEL' },
];

const EJECUTORAS = [
  { id: 'ue1', codigo: '1', nombre: 'FINANZAS', da: 'da1' },
  { id: 'ue2', codigo: '13', nombre: 'STAFF DE ALCALDIA', da: 'da1' },
  { id: 'ue3', codigo: '7', nombre: 'HOSPITAL', da: 'da2' },
];

describe('PresupuestoGastosComponent', () => {
  let fixture: ComponentFixture<PresupuestoGastosComponent>;
  let componente: PresupuestoGastosComponent;
  let http: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({
      imports: [HttpClientTestingModule, FormsModule],
      declarations: [PresupuestoGastosComponent],
    });
    fixture = TestBed.createComponent(PresupuestoGastosComponent);
    componente = fixture.componentInstance;
    http = TestBed.inject(HttpTestingController);
    fixture.detectChanges();
    http.expectOne(r => r.url.includes('presupuesto-gastos')).flush(ARBOL);
    http.expectOne(r => r.url.includes('direcciones-administrativas'))
        .flush({ results: DIRECCIONES });
    http.expectOne(r => r.url.includes('unidades-ejecutoras'))
        .flush({ results: EJECUTORAS });
    fixture.detectChanges();
  });

  afterEach(() => http.verify());

  const texto = () => (fixture.nativeElement as HTMLElement).textContent || '';
  const filas = (clase: string) => Array.from(
    (fixture.nativeElement as HTMLElement).querySelectorAll(`tr.${clase}`));

  it('la tabla no queda vacía: se ve el programa', () => {
    expect(filas('fila-programa').length).toBe(1);
    expect(texto()).toContain('170-179');
    expect(texto()).toContain('INFRAESTRUCTURA URBANA Y RURAL');
  });

  it('el programa muestra su sector y su finalidad', () => {
    expect(texto()).toContain('sector 11');
    expect(texto()).toContain('4.4.3; 4.5.1; 6.1');
  });

  it('la jerarquía va programa, subprograma y categoría', () => {
    expect(filas('fila-subprograma').length).toBe(0);
    componente.alternar('170-179');
    fixture.detectChanges();
    expect(filas('fila-subprograma').length).toBe(1);
    expect(texto()).toContain('171');

    componente.alternar('170-179' + '171');
    fixture.detectChanges();
    expect(filas('fila-actividad').length).toBe(1);
    expect(texto()).toContain('171 13120104700000 000');
  });

  it('el contador cuenta programas y categorías', () => {
    expect(texto()).toContain('1 programas');
    expect(texto()).toContain('1 categorías');
  });

  // --- El aviso de la directriz en el alta ---------------------------------

  const escribir = (codigo: string) => {
    componente.abrirAlta('PROGRAMA');
    (componente as any).alta.codigo = codigo;
    fixture.detectChanges();
  };

  it('al escribir el código dice a qué programa cae', () => {
    escribir('175');
    expect(componente.rangoDelAlta()?.codigo).toBe('170-179');
    expect(texto()).toContain('170-179');
  });

  it('avisa que el programa reservado no se puede usar', () => {
    escribir('050');
    expect(componente.rangoDelAlta()).toBeNull();
    expect(componente.motivoDelAlta()).toContain('10 al 96');
    expect(texto()).toContain('10 al 96');
  });

  it('avisa cuando el programa no cae en ningún rango', () => {
    escribir('999');
    expect(componente.motivoDelAlta()).toContain('no corresponde a ningún rango');
  });

  it('avisa cuando el programa no es numérico', () => {
    escribir('ABC');
    expect(componente.motivoDelAlta()).toContain('numérico');
  });

  it('el código de un subprograma también resuelve su programa', () => {
    escribir('171 0 001');
    expect(componente.rangoDelAlta()?.codigo).toBe('170-179');
  });
});

describe('PresupuestoGastosComponent · DA y UE editables', () => {
  let fixture: ComponentFixture<PresupuestoGastosComponent>;
  let componente: PresupuestoGastosComponent;
  let http: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({
      imports: [HttpClientTestingModule, FormsModule],
      declarations: [PresupuestoGastosComponent],
    });
    fixture = TestBed.createComponent(PresupuestoGastosComponent);
    componente = fixture.componentInstance;
    http = TestBed.inject(HttpTestingController);
    fixture.detectChanges();
    http.expectOne(r => r.url.includes('presupuesto-gastos'))
        .flush(JSON.parse(JSON.stringify(ARBOL)));
    http.expectOne(r => r.url.includes('direcciones-administrativas'))
        .flush({ results: DIRECCIONES });
    http.expectOne(r => r.url.includes('unidades-ejecutoras'))
        .flush({ results: EJECUTORAS });
    componente.alternar('170-179');
    componente.alternar('170-179' + '171');
    fixture.detectChanges();
  });

  afterEach(() => http.verify());

  const actividad = () =>
    componente.arbol!.programas[0].subprogramas[0].actividades[0];

  const elegir = (campo: 'da' | 'ue', valor: string) =>
    componente.elegirOrg(actividad(), campo,
                         { target: { value: valor } } as any);

  it('todas las filas tienen la misma cantidad de columnas', () => {
    // Incluye el pie: un colspan de menos ahí desalinea los totales contra las
    // columnas de fuente, que es justo donde no se puede fallar.
    const tabla = (fixture.nativeElement as HTMLElement)
      .querySelector('table') as HTMLTableElement;
    const columnas = tabla.querySelectorAll('thead th').length;
    const filas = Array.from(tabla.querySelectorAll('tbody tr, tfoot tr'));
    expect(filas.length).toBeGreaterThan(3);
    for (const tr of filas) {
      const ancho = Array.from(tr.querySelectorAll('td'))
        .reduce((n, td) => n + ((td as HTMLTableCellElement).colSpan || 1), 0);
      expect(ancho).toBe(columnas);
    }
  });

  it('la fila de la categoría trae los dos desplegables', () => {
    const fila = (fixture.nativeElement as HTMLElement)
      .querySelector('tr.fila-actividad') as HTMLElement;
    expect(fila.querySelectorAll('select.celda-org').length).toBe(2);
  });

  it('elegir la DA la guarda en el acto', () => {
    elegir('da', 'da1');
    const pedido = http.expectOne(r => r.url.includes('/allocations/7/'));
    expect(pedido.request.method).toBe('PATCH');
    expect(pedido.request.body).toEqual({ da: 'da1', ue: null });
    pedido.flush({});
    expect(actividad().direccion_administrativa).toBe('1');
  });

  it('la UE ofrecida es solo la de su DA', () => {
    expect(componente.ejecutorasDe('da1').map(u => u.id)).toEqual(['ue1', 'ue2']);
    expect(componente.ejecutorasDe('da2').map(u => u.id)).toEqual(['ue3']);
    // Sin DA elegida se ofrecen todas, para no trabar lo que ya viene cargado.
    expect(componente.ejecutorasDe('').length).toBe(3);
  });

  it('cambiar la DA limpia una UE que ya no le pertenece', () => {
    elegir('da', 'da1');
    http.expectOne(r => r.url.includes('/allocations/')).flush({});
    elegir('ue', 'ue2');
    http.expectOne(r => r.url.includes('/allocations/')).flush({});
    expect(actividad().ue_id).toBe('ue2');

    elegir('da', 'da2');
    expect(actividad().ue_id).toBe('');
    const pedido = http.expectOne(r => r.url.includes('/allocations/'));
    expect(pedido.request.body).toEqual({ da: 'da2', ue: null });
    pedido.flush({});
  });

  it('si el guardado falla la celda vuelve a lo que estaba', () => {
    elegir('da', 'da1');
    http.expectOne(r => r.url.includes('/allocations/'))
        .flush({ detail: 'no' }, { status: 500, statusText: 'Error' });
    // Dejarla mostrando algo que no se guardó es peor que no haber editado.
    expect(actividad().da_id).toBe('');
    expect(componente.error).toBeTruthy();
  });
});

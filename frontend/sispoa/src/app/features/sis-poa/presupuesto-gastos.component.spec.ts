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
        unidad_ejecutora: '01', direccion_administrativa: '1',
        distrito: '', codigo_sisin: '13120104700000', actividad: '000',
        montos: { '20/210': '101000', '41/113': '896021' },
        estado_revision: 'BORRADOR', observacion: '',
        priorizaciones: [], monto_priorizado: 0,
      }],
    }],
  }],
};

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

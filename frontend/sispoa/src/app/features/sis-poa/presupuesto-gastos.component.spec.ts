import { ComponentFixture, TestBed } from '@angular/core/testing';
import { HttpClientTestingModule, HttpTestingController } from '@angular/common/http/testing';
import { FormsModule } from '@angular/forms';
import { PresupuestoGastosComponent } from './presupuesto-gastos.component';

/** Payload con la forma real que devuelve el endpoint. */
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
  programas: [],
  rangos: [
    {
      codigo: '100-109',
      denominacion: 'PROMOCIÓN Y FOMENTO A LA PRODUCCIÓN AGROPECUARIA',
      finalidad_funcion: '4.2; 10.9.1',
      sector_economico: '1',
      total: { '20/210': '794589', '41/113': '1346021' },
      programas: [{
        codigo: '100',
        denominacion: 'PROMOCIÓN Y FOMENTO A LA PRODUCCIÓN AGROPECUARIA',
        total: { '20/210': '101000', '41/113': '896021' },
        subprogramas: [{
          codigo: '100 0',
          denominacion: 'PROMOCION Y FOMENTO',
          total: { '20/210': '101000', '41/113': '896021' },
          actividades: [{
            id: 7, categoria: '100 0 008', denominacion: 'DIRECCIÓN PRODUCTIVA',
            unidad_ejecutora: '01', direccion_administrativa: '1',
            distrito: '', codigo_sisin: '0', actividad: '008',
            montos: { '20/210': '101000', '41/113': '896021' },
            estado_revision: 'BORRADOR', observacion: '',
            priorizaciones: [], monto_priorizado: 0,
          }],
        }],
      }],
    },
  ],
};

describe('PresupuestoGastosComponent · árbol por rangos', () => {
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

  const filas = (clase: string) =>
    Array.from((fixture.nativeElement as HTMLElement)
      .querySelectorAll(`tr.${clase}`));

  it('la tabla no queda vacía: se ve la fila del rango', () => {
    expect(filas('fila-rango').length).toBe(1);
    const texto = (fixture.nativeElement as HTMLElement).textContent || '';
    expect(texto).toContain('100-109');
    expect(texto).toContain('PROMOCIÓN Y FOMENTO A LA PRODUCCIÓN AGROPECUARIA');
  });

  it('el rango muestra su sector y su finalidad', () => {
    const texto = (fixture.nativeElement as HTMLElement).textContent || '';
    expect(texto).toContain('sector 1');
    expect(texto).toContain('4.2; 10.9.1');
  });

  it('el rango muestra su total por fuente', () => {
    const texto = (fixture.nativeElement as HTMLElement).textContent || '';
    expect(texto.replace(/\s/g, '')).toContain('794.589');
  });

  it('al desplegar el rango aparecen sus programas', () => {
    expect(filas('fila-programa').length).toBe(0);
    componente.alternar('R100-109');
    fixture.detectChanges();
    expect(filas('fila-programa').length).toBe(1);
  });

  it('desplegando hasta el fondo se llega a la categoría', () => {
    componente.alternar('R100-109');
    componente.alternar('100');
    componente.alternar('100' + '100 0');
    fixture.detectChanges();
    expect(filas('fila-actividad').length).toBe(1);
    expect((fixture.nativeElement as HTMLElement).textContent)
      .toContain('100 0 008');
  });

  it('el contador del encabezado cuenta rangos, programas y categorías', () => {
    const texto = (fixture.nativeElement as HTMLElement).textContent || '';
    expect(texto).toContain('1 rangos');
    expect(texto).toContain('1 programas');
    expect(texto).toContain('1 categorías');
  });
});

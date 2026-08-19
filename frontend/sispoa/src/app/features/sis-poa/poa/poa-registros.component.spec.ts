import { ComponentFixture, TestBed, fakeAsync, tick } from '@angular/core/testing';
import { FormsModule } from '@angular/forms';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';
import { of, throwError } from 'rxjs';
import { PoaRegistrosComponent } from './poa-registros.component';
import { BorradorMatrizPOA, PoaBorradoresService } from './poa-borradores.service';

/** Registro con una acción y dos operaciones, tal como lo devuelve la API. */
function registro(id: string, gestion = 2026): BorradorMatrizPOA {
  return {
    id,
    gestion,
    estado: 'COMPLETO',
    id_accion_poa: null,
    estado_revision: 'PENDIENTE',
    permisos: {
      es_autor: true, es_aprobador: false, editar: true, validar: true,
      aprobar: false, observar: false, borrar: true,
    },
    datos: {
      acciones: [{
        denominacion: `Acción de ${id}`,
        operaciones: [{ actividades: [] }, { actividades: [] }],
      }],
    },
  };
}

function fila(borradorId: string) {
  return {
    cod_producto_pei: '1312.1.1',
    accion_institucional_especifica: 'Servicio ampliado',
    indicador_proceso: 'Porcentaje de avance',
    area_responsable: 'Dirección de Infraestructura',
    cod_accion_poa: `${borradorId}-ACP`,
    accion_corto_plazo: 'Construcción de la red',
    resultado_esperado: 'Red construida',
    programa: '101', proyecto: '0', actividad: '023',
    categoria_programatica: '101 0 023',
    presupuesto_programado: '1500000.00',
    cargo_reacp: 'Jefe de Obras',
    fecha_inicio: '2026-01-02', fecha_fin: '2026-12-31',
    cod_resultado_pei: '1312.1', resultado_pei: 'Resultado institucional',
    producto_pei: 'Servicio ampliado', indicador: 'Porcentaje de avance',
  };
}

describe('PoaRegistrosComponent', () => {
  let fixture: ComponentFixture<PoaRegistrosComponent>;
  let component: PoaRegistrosComponent;
  let servicio: jasmine.SpyObj<PoaBorradoresService>;

  beforeEach(async () => {
    servicio = jasmine.createSpyObj('PoaBorradoresService', [
      'listar', 'matriz', 'validar', 'aprobar', 'observar', 'eliminar',
    ]);

    await TestBed.configureTestingModule({
      declarations: [PoaRegistrosComponent],
      imports: [CommonModule, FormsModule, RouterModule.forRoot([])],
      providers: [{ provide: PoaBorradoresService, useValue: servicio }],
    }).compileComponents();

    fixture = TestBed.createComponent(PoaRegistrosComponent);
    component = fixture.componentInstance;
  });

  function arrancar(registros: BorradorMatrizPOA[], next: string | null = null): void {
    servicio.listar.and.returnValue(of({ count: registros.length, results: registros, next } as any));
    servicio.matriz.and.callFake((id: string) => of([fila(id)]));
    fixture.detectChanges();
  }

  it('pinta la tabla de registros con sus operaciones', () => {
    arrancar([registro('a'), registro('b')]);

    const filas = fixture.nativeElement.querySelectorAll('.tabla tbody tr');
    expect(filas.length).toBe(2);
    // Si el componente no estuviera declarado con su scope de directivas,
    // *ngFor no haría nada y la tabla saldría vacía sin error en consola.
    expect(filas[0].textContent).toContain('Acción de a');
    expect(component.operacionesDe(registro('a'))).toBe(2);
  });

  it('arma la cabecera de dos filas con 15 columnas en 5 bloques', () => {
    arrancar([registro('a')]);

    const grupo = fixture.nativeElement.querySelectorAll('.mz thead tr.grupo th');
    const columna = fixture.nativeElement.querySelectorAll('.mz thead tr.columna th');

    // check + REGISTRO + 5 bloques + EDITAR
    expect(grupo.length).toBe(8);
    expect(columna.length).toBe(15);

    const colspans = Array.from(grupo)
      .map((th: any) => th.getAttribute('colspan'))
      .filter((v: string | null) => v !== null)
      .map(Number);
    expect(colspans).toEqual([4, 3, 4, 1, 3]);
    expect(colspans.reduce((a, b) => a + b, 0)).toBe(15);
  });

  it('etiqueta cada fila con su registro y enlaza el lápiz al borrador', () => {
    arrancar([registro('a')]);

    expect(component.filas[0]._borradorId).toBe('a');
    expect(component.filas[0]._gestion).toBe(2026);
    expect(component.filas[0]._estado).toBe('COMPLETO');

    const lapiz = fixture.nativeElement.querySelector('.col-editar a');
    expect(lapiz.getAttribute('href')).toBe('/sis-poa/poas/nuevo/a');
  });

  it('un registro que falla aporta cero filas y los demás se siguen mostrando', () => {
    servicio.listar.and.returnValue(
      of({ count: 2, results: [registro('ok'), registro('roto')], next: null } as any),
    );
    servicio.matriz.and.callFake((id: string) =>
      id === 'roto' ? throwError(() => new Error('500')) : of([fila(id)]),
    );
    fixture.detectChanges();

    expect(component.filas.length).toBe(1);
    expect(component.filas[0]._borradorId).toBe('ok');
    expect(component.errorMatriz).toBe('');
  });

  it('recorre las páginas siguiendo r.next', () => {
    servicio.matriz.and.callFake((id: string) => of([fila(id)]));
    servicio.listar.and.callFake((params: any) =>
      params.page === 1
        ? of({ count: 2, results: [registro('p1')], next: 'http://api/?page=2' } as any)
        : of({ count: 2, results: [registro('p2')], next: null } as any),
    );
    fixture.detectChanges();

    expect(servicio.listar).toHaveBeenCalledTimes(2);
    expect(component.registros.map(r => r.id)).toEqual(['p1', 'p2']);
  });

  it('cambiar de pestaña limpia la selección y cambia las columnas', () => {
    arrancar([registro('a')]);
    component.alternarTodas();
    expect(component.seleccionadas.size).toBe(1);

    component.cambiarVista('articulacion');
    expect(component.seleccionadas.size).toBe(0);
    expect(component.totalColumnas).toBe(10);

    component.cambiarVista('matriz');
    expect(component.totalColumnas).toBe(15);
  });

  it('formatea el presupuesto y marca los vacíos con guion', () => {
    arrancar([registro('a')]);
    const f = component.filas[0];
    expect(component.celda(f, 'presupuesto_programado')).toBe((1500000).toLocaleString('es-BO'));
    expect(component.celda(f, 'inexistente')).toBe('-');
  });

  it('solo dibuja las acciones cuyo permiso llega en true', () => {
    const aprobado = registro('z');
    aprobado.estado_revision = 'APROBADO';
    aprobado.permisos = {
      es_autor: true, es_aprobador: false, editar: false, validar: false,
      aprobar: false, observar: false, borrar: false,
    };
    arrancar([aprobado]);

    const celda = fixture.nativeElement.querySelector('.tabla tbody tr .col-acciones');
    expect(celda.querySelectorAll('button').length).toBe(0);
    expect(celda.querySelector('.sin-acciones').textContent.trim()).toBe('🔒');
  });

  it('valida el registro y refleja el estado devuelto por el backend', fakeAsync(() => {
    arrancar([registro('a')]);
    const validado = { ...registro('a'), estado_revision: 'VALIDADO' as const };
    servicio.validar.and.returnValue(of(validado));

    component.validar(component.registros[0]);
    tick();
    fixture.detectChanges();

    expect(servicio.validar).toHaveBeenCalledWith('a');
    expect(component.registros[0].estado_revision).toBe('VALIDADO');
    // Sin markForCheck el dato llega y la vista no se repinta (shell OnPush).
    expect(fixture.nativeElement.querySelector('.badge.rev').textContent).toContain('VALIDADO');
  }));
});

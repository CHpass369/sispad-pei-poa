import { ComponentFixture, TestBed } from '@angular/core/testing';
import { of, Subject, throwError } from 'rxjs';
import { MatrizCompletaComponent } from './matriz-completa.component';
import {
  MatrizCompletaService,
  MatrizResponse,
} from './matriz-completa.service';

describe('MatrizCompletaComponent', () => {
  let component: MatrizCompletaComponent;
  let fixture: ComponentFixture<MatrizCompletaComponent>;
  let serviceSpy: jasmine.SpyObj<MatrizCompletaService>;

  const treeResponse: MatrizResponse = {
    data: [{
      id: 'eje-1',
      codigo_completo: '01',
      codigo: '01',
      nombre: 'Eje de prueba',
      nivel: 'eje',
      tipo_plan: 'pgdesa',
      plan_nombre: 'PGDESA demo',
      hijos: [],
      articulaciones: [],
    }],
    stats: { total: 1, por_nivel: { eje: 1 } },
  };

  beforeEach(async () => {
    serviceSpy = jasmine.createSpyObj<MatrizCompletaService>(
      'MatrizCompletaService',
      ['getArbol', 'getResultadosPAD', 'exportXLSX'],
    );
    serviceSpy.getArbol.and.returnValue(of(treeResponse));
    serviceSpy.getResultadosPAD.and.returnValue(of([]));

    await TestBed.configureTestingModule({
      imports: [MatrizCompletaComponent],
      providers: [{ provide: MatrizCompletaService, useValue: serviceSpy }],
    }).compileComponents();

    fixture = TestBed.createComponent(MatrizCompletaComponent);
    component = fixture.componentInstance;
  });

  it('requests the initial tree and renders loaded data', () => {
    fixture.detectChanges();

    expect(serviceSpy.getArbol).toHaveBeenCalledWith(2026);
    expect(serviceSpy.getResultadosPAD).toHaveBeenCalledWith(2026);
    expect(component.cargando).toBeFalse();
    expect(fixture.nativeElement.textContent).toContain('Eje de prueba');
  });

  it('shows the loading state while the initial request is pending', () => {
    const pending = new Subject<MatrizResponse>();
    serviceSpy.getArbol.and.returnValue(pending.asObservable());

    fixture.detectChanges();

    expect(component.cargando).toBeTrue();
    expect(fixture.nativeElement.textContent).toContain(
      'Cargando árbol de articulación completa...',
    );

    pending.next(treeResponse);
    fixture.detectChanges();
    expect(component.cargando).toBeFalse();
  });

  it('shows the empty state when the API returns no nodes', () => {
    serviceSpy.getArbol.and.returnValue(of({
      data: [],
      stats: { total: 0, por_nivel: {} },
    }));

    fixture.detectChanges();

    expect(component.arbolData).toEqual([]);
    expect(fixture.nativeElement.textContent).toContain(
      'No se encontraron nodos de planificación para la gestión 2026',
    );
  });

  it('shows a server error state when the initial request fails', () => {
    serviceSpy.getArbol.and.returnValue(throwError(() => ({ status: 500 })));

    fixture.detectChanges();

    expect(component.error).toBeTrue();
    expect(component.errorMensaje).toBe('Error interno del servidor');
    expect(fixture.nativeElement.textContent).toContain('Error al cargar datos');
  });
});

import { ComponentFixture, TestBed } from '@angular/core/testing';
import { of } from 'rxjs';
import { MatrizCompletaService, NodoArbol } from './matriz-completa.service';
import { MatrizCompletaTreeComponent } from './matriz-completa-tree.component';

describe('MatrizCompletaTreeComponent', () => {
  let component: MatrizCompletaTreeComponent;
  let fixture: ComponentFixture<MatrizCompletaTreeComponent>;
  let serviceSpy: jasmine.SpyObj<MatrizCompletaService>;

  beforeEach(async () => {
    serviceSpy = jasmine.createSpyObj<MatrizCompletaService>(
      'MatrizCompletaService',
      ['updateBridgePAD'],
    );
    serviceSpy.updateBridgePAD.and.returnValue(of({}));

    await TestBed.configureTestingModule({
      imports: [MatrizCompletaTreeComponent],
      providers: [{ provide: MatrizCompletaService, useValue: serviceSpy }],
    }).compileComponents();

    fixture = TestBed.createComponent(MatrizCompletaTreeComponent);
    component = fixture.componentInstance;
  });

  it('renders the complete code and level badge for a row', () => {
    component.nodos = [{
      id: 'eje-1',
      codigo_completo: '01.02',
      codigo: '02',
      nombre: 'Eje visible',
      nivel: 'eje',
      tipo_plan: 'pgdesa',
      plan_nombre: 'PGDESA demo',
      hijos: [],
      articulaciones: [],
    }];

    fixture.detectChanges();

    expect(fixture.nativeElement.querySelector('.codigo').textContent).toContain('01.02');
    expect(fixture.nativeElement.querySelector('.badge-nivel').textContent).toContain(
      'PGDESA Eje',
    );
  });

  it('expands a row and renders its child rows', () => {
    const child: NodoArbol = {
      id: 'meta-1',
      codigo_completo: '01.01',
      codigo: '01',
      nombre: 'Meta hija',
      nivel: 'meta',
      tipo_plan: 'pgdesa',
      plan_nombre: 'PGDESA demo',
      hijos: [],
      articulaciones: [],
    };
    component.nodos = [{
      id: 'eje-1',
      codigo_completo: '01',
      codigo: '01',
      nombre: 'Eje padre',
      nivel: 'eje',
      tipo_plan: 'pgdesa',
      plan_nombre: 'PGDESA demo',
      hijos: [child],
      articulaciones: [],
    }];

    fixture.detectChanges();
    expect(fixture.nativeElement.querySelectorAll('.codigo').length).toBe(1);

    fixture.nativeElement.querySelector('.btn-expand').click();
    fixture.detectChanges();

    expect(fixture.nativeElement.textContent).toContain('01.01');
    expect(fixture.nativeElement.textContent).toContain('Meta hija');
  });

  it('opens the edit action, patches the bridge, and emits an update', () => {
    const action: NodoArbol = {
      id: 'pdesa-action-1',
      codigo_completo: '01.01',
      codigo: '01.01',
      nombre: 'Acción PDESA',
      nivel: 'accion',
      tipo_plan: 'pdesa',
      plan_nombre: 'PDESA demo',
      hijos: [],
      articulaciones: [],
    };
    component.nodos = [action];
    component.resultadosPad = [{
      id: 'pad-1',
      codigo_resultado: 'PAD-001',
      denominacion: 'Resultado PAD seleccionable',
    }];
    const emitted = jasmine.createSpy('bridgeUpdated');
    component.bridgeUpdated.subscribe(emitted);

    fixture.detectChanges();
    fixture.nativeElement.querySelector('.btn-articular').click();
    fixture.detectChanges();

    expect(fixture.nativeElement.textContent).toContain(
      'Resultado PAD seleccionable',
    );
    fixture.nativeElement.querySelector('.picker-item').click();
    fixture.detectChanges();

    expect(serviceSpy.updateBridgePAD).toHaveBeenCalledWith(
      'pad-1',
      'pdesa-action-1',
    );
    expect(emitted).toHaveBeenCalledTimes(1);
    expect(fixture.nativeElement.textContent).toContain('Vinculado con PAD-001');
  });
});

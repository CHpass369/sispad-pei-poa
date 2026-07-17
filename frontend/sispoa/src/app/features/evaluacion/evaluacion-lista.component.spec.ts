import { ComponentFixture, TestBed } from '@angular/core/testing';
import { HttpClientTestingModule } from '@angular/common/http/testing';
import { RouterTestingModule } from '@angular/router/testing';
import { of, throwError } from 'rxjs';
import { EvaluacionListaComponent } from './evaluacion-lista.component';
import { EvaluacionService } from './evaluacion.service';
import { Router } from '@angular/router';

describe('EvaluacionListaComponent', () => {
  let component: EvaluacionListaComponent;
  let fixture: ComponentFixture<EvaluacionListaComponent>;
  let evaluacionServiceSpy: jasmine.SpyObj<EvaluacionService>;
  let routerSpy: jasmine.SpyObj<Router>;

  const mockEvaluaciones = [
    { id: 1, tipo: 'PEI', periodo: '2024', responsable: 'User 1', estado: 'borrador', fecha_creacion: '2024-01-01' },
    { id: 2, tipo: 'POA', periodo: '2024', responsable: 'User 2', estado: 'completada', fecha_creacion: '2024-02-01' },
  ];

  beforeEach(async () => {
    evaluacionServiceSpy = jasmine.createSpyObj('EvaluacionService', ['listar', 'generar']);
    routerSpy = jasmine.createSpyObj('Router', ['navigate']);

    evaluacionServiceSpy.listar.and.returnValue(of(mockEvaluaciones as any));
    evaluacionServiceSpy.generar.and.returnValue(of({} as any));

    await TestBed.configureTestingModule({
      declarations: [EvaluacionListaComponent],
      imports: [HttpClientTestingModule, RouterTestingModule],
      providers: [
        { provide: EvaluacionService, useValue: evaluacionServiceSpy },
        { provide: Router, useValue: routerSpy },
      ],
    }).compileComponents();

    fixture = TestBed.createComponent(EvaluacionListaComponent);
    component = fixture.componentInstance;
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should load evaluations on init', () => {
    fixture.detectChanges();

    expect(evaluacionServiceSpy.listar).toHaveBeenCalled();
    expect(component.evaluaciones.length).toBe(2);
    expect(component.cargando).toBeFalse();
  });

  it('should display empty message when no evaluations found', () => {
    evaluacionServiceSpy.listar.and.returnValue(of([] as any));

    fixture.detectChanges();

    expect(component.evaluaciones.length).toBe(0);
    expect(component.cargando).toBeFalse();
  });

  it('should handle error when loading evaluations', () => {
    evaluacionServiceSpy.listar.and.returnValue(throwError(() => new Error('Error')));

    fixture.detectChanges();

    expect(component.error).toBe('Error al cargar evaluaciones');
    expect(component.cargando).toBeFalse();
  });

  it('should navigate to create evaluation page', () => {
    component.nueva();

    expect(routerSpy.navigate).toHaveBeenCalledWith(['evaluacion/nueva']);
  });

  it('should navigate to evaluation detail page', () => {
    component.verDetalle(mockEvaluaciones[0] as any);

    expect(routerSpy.navigate).toHaveBeenCalledWith(['evaluacion', 1]);
  });

  it('should call generar and reload on success', () => {
    evaluacionServiceSpy.listar.and.returnValue(of(mockEvaluaciones as any));

    component.generar();

    expect(evaluacionServiceSpy.generar).toHaveBeenCalled();
  });

  it('should handle generar error', () => {
    evaluacionServiceSpy.generar.and.returnValue(throwError(() => ({
      error: { detail: 'Error al generar' },
    })));

    component.generar();

    expect(component.error).toBe('Error al generar');
  });

  it('should filter evaluations when searching', () => {
    fixture.detectChanges();

    component.busqueda = 'PEI';
    evaluacionServiceSpy.listar.and.returnValue(of([mockEvaluaciones[0]] as any));

    component.cargar();

    expect(evaluacionServiceSpy.listar).toHaveBeenCalledWith({ search: 'PEI' });
  });
});

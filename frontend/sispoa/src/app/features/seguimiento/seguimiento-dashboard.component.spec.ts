import { ComponentFixture, TestBed } from '@angular/core/testing';
import { HttpClientTestingModule } from '@angular/common/http/testing';
import { RouterTestingModule } from '@angular/router/testing';
import { of, throwError } from 'rxjs';
import { SeguimientoDashboardComponent } from './seguimiento-dashboard.component';
import { SeguimientoService } from './seguimiento.service';

describe('SeguimientoDashboardComponent', () => {
  let component: SeguimientoDashboardComponent;
  let fixture: ComponentFixture<SeguimientoDashboardComponent>;
  let seguimientoServiceSpy: jasmine.SpyObj<SeguimientoService>;

  const mockDashboard = {
    gestion: 2027,
    total_actividades: 25,
    semaforo: { verde: 15, amarillo: 5, rojo: 5 },
    promedio_avance_fisico: 62.5,
    promedio_avance_financiero: 48.3,
  };

  const mockSemaforos = {
    gestion: 2027,
    resumen: { verde: 1, amarillo: 1, rojo: 1, total: 3 },
    detalle: {
      verde: [{ id: '1', actividad_codigo: '001', actividad_nombre: 'Actividad 1', avance_fisico: 80, avance_financiero: 70 }],
      amarillo: [{ id: '2', actividad_codigo: '002', actividad_nombre: 'Actividad 2', avance_fisico: 50, avance_financiero: 40 }],
      rojo: [{ id: '3', actividad_codigo: '003', actividad_nombre: 'Actividad 3', avance_fisico: 20, avance_financiero: 10 }],
    },
  };

  const mockAlertas = [
    { id: 1, severidad: 'alta', mensaje: 'Alerta alta', actividad_descripcion: 'Actividad 1' },
    { id: 2, severidad: 'baja', mensaje: 'Alerta baja', actividad_descripcion: 'Actividad 2' },
  ];

  beforeEach(async () => {
    seguimientoServiceSpy = jasmine.createSpyObj('SeguimientoService', [
      'obtenerDashboard',
      'obtenerSemaforo',
      'listarAlertasActivas',
    ]);

    seguimientoServiceSpy.obtenerDashboard.and.returnValue(of(mockDashboard as any));
    seguimientoServiceSpy.obtenerSemaforo.and.returnValue(of(mockSemaforos as any));
    seguimientoServiceSpy.listarAlertasActivas.and.returnValue(of(mockAlertas as any));

    await TestBed.configureTestingModule({
      declarations: [SeguimientoDashboardComponent],
      imports: [HttpClientTestingModule, RouterTestingModule],
      providers: [
        { provide: SeguimientoService, useValue: seguimientoServiceSpy },
      ],
    }).compileComponents();

    fixture = TestBed.createComponent(SeguimientoDashboardComponent);
    component = fixture.componentInstance;
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should load dashboard data on init', () => {
    fixture.detectChanges();

    expect(seguimientoServiceSpy.obtenerDashboard).toHaveBeenCalledWith(2027);
    expect(seguimientoServiceSpy.obtenerSemaforo).toHaveBeenCalledWith(2027);
    expect(seguimientoServiceSpy.listarAlertasActivas).toHaveBeenCalled();
  });

  it('should set dashboard data after init', () => {
    fixture.detectChanges();

    expect(component.dashboard).toEqual(mockDashboard);
    expect(component.cargando).toBeFalse();
  });

  it('should set semaforo data after init', () => {
    fixture.detectChanges();

    expect(component.semaforos.length).toBe(3);
  });

  it('should set alertas data after init', () => {
    fixture.detectChanges();

    expect(component.alertas.length).toBe(2);
  });

  it('should handle dashboard error gracefully', () => {
    seguimientoServiceSpy.obtenerDashboard.and.returnValue(throwError(() => new Error('Error')));

    fixture.detectChanges();

    expect(component.dashboard).toBeNull();
    expect(component.cargando).toBeFalse();
  });

  it('should handle empty semaforo', () => {
    seguimientoServiceSpy.obtenerSemaforo.and.returnValue(of({
      gestion: 2027,
      resumen: { verde: 0, amarillo: 0, rojo: 0, total: 0 },
      detalle: { verde: [], amarillo: [], rojo: [] },
    } as any));

    fixture.detectChanges();

    expect(component.semaforos.length).toBe(0);
  });

  it('should handle empty alertas', () => {
    seguimientoServiceSpy.listarAlertasActivas.and.returnValue(of([] as any));

    fixture.detectChanges();

    expect(component.alertas.length).toBe(0);
  });

  it('should display semaforo colors correctly', () => {
    fixture.detectChanges();

    const verde = component.semaforos.find(s => s.estado_semaforo === 'verde');
    const amarillo = component.semaforos.find(s => s.estado_semaforo === 'amarillo');
    const rojo = component.semaforos.find(s => s.estado_semaforo === 'rojo');

    expect(verde).toBeDefined();
    expect(amarillo).toBeDefined();
    expect(rojo).toBeDefined();
  });
});

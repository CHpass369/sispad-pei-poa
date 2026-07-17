import { ComponentFixture, TestBed } from '@angular/core/testing';
import { HttpClientTestingModule } from '@angular/common/http/testing';
import { RouterTestingModule } from '@angular/router/testing';
import { of, throwError } from 'rxjs';
import { PortalInicioComponent } from './portal-inicio.component';
import { PortalPublicoService } from './portal-publico.service';

describe('PortalInicioComponent', () => {
  let component: PortalInicioComponent;
  let fixture: ComponentFixture<PortalInicioComponent>;
  let portalServiceSpy: jasmine.SpyObj<PortalPublicoService>;

  const mockResumen = {
    total_presupuesto: 10000000,
    total_ejecutado: 7500000,
    porcentaje_ejecucion: 75,
    total_programas: 12,
    total_acciones: 48,
    por_tipo: [],
    por_sector: [],
    por_mes: [],
  };

  beforeEach(async () => {
    portalServiceSpy = jasmine.createSpyObj('PortalPublicoService', ['obtenerResumenEjecucion']);
    portalServiceSpy.obtenerResumenEjecucion.and.returnValue(of(mockResumen));

    await TestBed.configureTestingModule({
      declarations: [PortalInicioComponent],
      imports: [HttpClientTestingModule, RouterTestingModule],
      providers: [
        { provide: PortalPublicoService, useValue: portalServiceSpy },
      ],
    }).compileComponents();

    fixture = TestBed.createComponent(PortalInicioComponent);
    component = fixture.componentInstance;
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should load summary stats on init', () => {
    fixture.detectChanges();

    expect(portalServiceSpy.obtenerResumenEjecucion).toHaveBeenCalled();
    expect(component.cargando).toBeFalse();
  });

  it('should set total_planes from total_programas', () => {
    fixture.detectChanges();

    expect(component.resumen.total_planes).toBe(12);
  });

  it('should set total_presupuesto from response', () => {
    fixture.detectChanges();

    expect(component.resumen.total_presupuesto).toBe(10000000);
  });

  it('should set default indicadores to 0', () => {
    fixture.detectChanges();

    expect(component.resumen.total_indicadores).toBe(0);
    expect(component.resumen.indicadores_cumplidos).toBe(0);
  });

  it('should handle API error gracefully', () => {
    portalServiceSpy.obtenerResumenEjecucion.and.returnValue(throwError(() => new Error('Error')));

    fixture.detectChanges();

    expect(component.cargando).toBeFalse();
    expect(component.resumen.total_planes).toBeUndefined();
  });

  it('should pass params to service call', () => {
    fixture.detectChanges();

    expect(portalServiceSpy.obtenerResumenEjecucion).toHaveBeenCalledWith(undefined);
  });
});

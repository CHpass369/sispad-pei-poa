import { ComponentFixture, TestBed } from '@angular/core/testing';
import { HttpClientTestingModule } from '@angular/common/http/testing';
import { RouterTestingModule } from '@angular/router/testing';
import { of, throwError } from 'rxjs';
import { ModificacionesListaComponent } from './modificaciones-lista.component';
import { ModificacionesService } from './modificaciones.service';
import { Router } from '@angular/router';

describe('ModificacionesListaComponent', () => {
  let component: ModificacionesListaComponent;
  let fixture: ComponentFixture<ModificacionesListaComponent>;
  let modificacionesServiceSpy: jasmine.SpyObj<ModificacionesService>;
  let routerSpy: jasmine.SpyObj<Router>;

  const mockSolicitudes = [
    { id: 1, tipo: 'Prórroga', entidad: 'UE 1', solicitado_por: 'User 1', estado: 'pendiente', fecha_solicitud: '2024-01-15' },
    { id: 2, tipo: 'Reasignación', entidad: 'UE 2', solicitado_por: 'User 2', estado: 'aprobada', fecha_solicitud: '2024-02-20' },
  ];

  beforeEach(async () => {
    modificacionesServiceSpy = jasmine.createSpyObj('ModificacionesService', ['listar']);
    routerSpy = jasmine.createSpyObj('Router', ['navigate']);

    modificacionesServiceSpy.listar.and.returnValue(of(mockSolicitudes as any));

    await TestBed.configureTestingModule({
      declarations: [ModificacionesListaComponent],
      imports: [HttpClientTestingModule, RouterTestingModule],
      providers: [
        { provide: ModificacionesService, useValue: modificacionesServiceSpy },
        { provide: Router, useValue: routerSpy },
      ],
    }).compileComponents();

    fixture = TestBed.createComponent(ModificacionesListaComponent);
    component = fixture.componentInstance;
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should load modifications on init', () => {
    fixture.detectChanges();

    expect(modificacionesServiceSpy.listar).toHaveBeenCalled();
    expect(component.solicitudes.length).toBe(2);
    expect(component.cargando).toBeFalse();
  });

  it('should display empty message when no modifications found', () => {
    modificacionesServiceSpy.listar.and.returnValue(of([] as any));

    fixture.detectChanges();

    expect(component.solicitudes.length).toBe(0);
    expect(component.cargando).toBeFalse();
  });

  it('should handle error when loading modifications', () => {
    modificacionesServiceSpy.listar.and.returnValue(throwError(() => new Error('Error')));

    fixture.detectChanges();

    expect(component.error).toBe('Error al cargar solicitudes');
    expect(component.cargando).toBeFalse();
  });

  it('should navigate to create modification page', () => {
    component.nueva();

    expect(routerSpy.navigate).toHaveBeenCalledWith(['modificaciones/nueva']);
  });

  it('should navigate to modification detail page', () => {
    component.verDetalle(mockSolicitudes[0] as any);

    expect(routerSpy.navigate).toHaveBeenCalledWith(['modificaciones', 1]);
  });

  it('should filter modifications when searching', () => {
    fixture.detectChanges();

    component.busqueda = 'Prórroga';
    modificacionesServiceSpy.listar.and.returnValue(of([mockSolicitudes[0]] as any));

    component.cargar();

    expect(modificacionesServiceSpy.listar).toHaveBeenCalledWith({ search: 'Prórroga' });
  });

  it('should handle results wrapper in response', () => {
    modificacionesServiceSpy.listar.and.returnValue(of({ results: mockSolicitudes } as any));

    component.cargar();

    expect(component.solicitudes.length).toBe(2);
  });

  it('should reset error on successful reload', () => {
    modificacionesServiceSpy.listar.and.returnValue(throwError(() => new Error()));
    fixture.detectChanges();
    expect(component.error).toBeTruthy();

    modificacionesServiceSpy.listar.and.returnValue(of(mockSolicitudes as any));
    component.cargar();

    expect(component.error).toBe('');
  });
});

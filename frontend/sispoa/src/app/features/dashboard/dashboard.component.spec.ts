import { ComponentFixture, TestBed } from '@angular/core/testing';
import { HttpClientTestingModule } from '@angular/common/http/testing';
import { RouterTestingModule } from '@angular/router/testing';
import { of, BehaviorSubject, throwError } from 'rxjs';
import { DashboardComponent } from './dashboard.component';
import { AuthService } from '../../core/services/auth.service';
import { ApiService } from '../../core/services/api.service';
import { Usuario } from '../../core/models/usuario.model';

describe('DashboardComponent', () => {
  let component: DashboardComponent;
  let fixture: ComponentFixture<DashboardComponent>;
  let authServiceSpy: jasmine.SpyObj<AuthService>;
  let apiServiceSpy: jasmine.SpyObj<ApiService>;

  const mockUser: Usuario = {
    id: '1',
    email: 'admin@test.com',
    first_name: 'Admin',
    last_name: 'User',
    cargo: 'Admin',
    telefono: '7777777',
    roles: ['superadmin'],
    roles_detalle: [{ id: '1', codigo: 'superadmin', nombre: 'Super Admin', descripcion: '', activo: true }],
    activo: true,
    is_staff: true,
    is_superuser: true,
    debe_cambiar_password: false,
    last_login: '2024-01-01',
    date_joined: '2024-01-01',
  };

  const mockKpis = {
    presupuesto_total: 5000000,
    ejecucion_porcentaje: 75,
    aprobaciones_pendientes: 3,
    alertas_count: 2,
    por_tipo: [{ tipo: 'PEI', porcentaje: 80 }],
    por_mes: [{ mes: 'Ene', porcentaje: 60 }],
    actividad_reciente: [{ descripcion: 'Test activity', fecha: '2024-01-01' }],
  };

  const mockNotif = { no_leidas: 5 };

  beforeEach(async () => {
    authServiceSpy = jasmine.createSpyObj('AuthService', ['hasRole', 'init'], {
      user$: new BehaviorSubject<Usuario | null>(mockUser),
    });
    apiServiceSpy = jasmine.createSpyObj('ApiService', ['get']);

    authServiceSpy.hasRole.and.callFake((role: string) => role === 'superadmin');
    apiServiceSpy.get.and.callFake((path: string) => {
      if (path === '/dashboard/kpis/') return of(mockKpis);
      if (path === '/notificaciones/resumen/') return of(mockNotif);
      return of({});
    });

    await TestBed.configureTestingModule({
      declarations: [DashboardComponent],
      imports: [HttpClientTestingModule, RouterTestingModule],
      providers: [
        { provide: AuthService, useValue: authServiceSpy },
        { provide: ApiService, useValue: apiServiceSpy },
      ],
    }).compileComponents();

    fixture = TestBed.createComponent(DashboardComponent);
    component = fixture.componentInstance;
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should load KPIs and notifications on init', () => {
    fixture.detectChanges();

    expect(apiServiceSpy.get).toHaveBeenCalledWith('/dashboard/kpis/');
    expect(apiServiceSpy.get).toHaveBeenCalledWith('/notificaciones/resumen/');
    expect(component.cargando).toBeFalse();
  });

  it('should set user name from auth service', () => {
    fixture.detectChanges();

    expect(component.userName).toBe('Admin User');
    expect(component.userEmail).toBe('admin@test.com');
  });

  it('should set notification count', () => {
    fixture.detectChanges();

    expect(component.notifCount).toBe(5);
  });

  it('should display superadmin role correctly', () => {
    fixture.detectChanges();

    expect(component.isSuperAdmin).toBeTrue();
    expect(component.rolDisplay).toBe('Super Administrador');
  });

  it('should handle API error gracefully for KPIs', () => {
    apiServiceSpy.get.and.callFake((path: string) => {
      if (path === '/dashboard/kpis/') return throwError(() => new Error());
      if (path === '/notificaciones/resumen/') return of(mockNotif);
      return of({});
    });

    fixture.detectChanges();

    expect(component.kpis).toEqual({});
    expect(component.cargando).toBeFalse();
  });

  it('should handle planificador role', () => {
    authServiceSpy.hasRole.and.callFake((role: string) => role === 'planificador');

    component.ngOnInit();

    expect(component.isPlanificador).toBeTrue();
  });

  it('should handle jefe_ue role', () => {
    authServiceSpy.hasRole.and.callFake((role: string) => role === 'jefe_ue');

    component.ngOnInit();

    expect(component.isJefeUe).toBeTrue();
    expect(component.rolDisplay).toBe('Jefe de UE');
  });

  it('should show default role for unknown roles', () => {
    authServiceSpy.hasRole.and.returnValue(false);

    expect(component.rolDisplay).toBe('Usuario');
  });

  it('should fallback notification count to 0', () => {
    apiServiceSpy.get.and.callFake((path: string) => {
      if (path === '/dashboard/kpis/') return of(mockKpis);
      if (path === '/notificaciones/resumen/') return of({});
      return of({});
    });

    fixture.detectChanges();

    expect(component.notifCount).toBe(0);
  });
});

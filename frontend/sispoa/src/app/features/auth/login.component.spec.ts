import { Component } from '@angular/core';
import { ComponentFixture, TestBed, fakeAsync, tick } from '@angular/core/testing';
import { ReactiveFormsModule } from '@angular/forms';
import { By } from '@angular/platform-browser';
import { Router, RouterModule } from '@angular/router';
import { LayoutDashboard, LucideAngularModule, Target } from 'lucide-angular';
import { Subject, of } from 'rxjs';
import { Usuario } from '../../core/models/usuario.model';
import { AuthService } from '../../core/services/auth.service';
import {
  CapabilitiesResponse,
  CapabilitiesService,
} from '../../core/services/capabilities.service';
import {
  GestionHabilitadaService,
  RespuestaGestionHabilitada,
} from '../../core/services/gestion-habilitada.service';
import { PermissionsService } from '../../core/services/permissions.service';
import { SistemasSeleccionComponent } from '../sistemas/sistemas-seleccion.component';
import { LoginComponent } from './login.component';

@Component({ standalone: false, selector: 'app-register-stub', template: '' })
class RegisterStubComponent {}

@Component({ standalone: false, selector: 'app-system-dashboard-stub', template: '' })
class SystemDashboardStubComponent {}

describe('LoginComponent', () => {
  let fixture: ComponentFixture<LoginComponent>;
  let router: Router;
  let auth: jasmine.SpyObj<AuthService>;
  let capabilities: jasmine.SpyObj<CapabilitiesService>;
  let fiscalManagement: jasmine.SpyObj<GestionHabilitadaService>;
  let permissions: jasmine.SpyObj<PermissionsService>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      declarations: [
        LoginComponent,
        RegisterStubComponent,
        SistemasSeleccionComponent,
        SystemDashboardStubComponent,
      ],
      imports: [
        ReactiveFormsModule,
        LucideAngularModule.pick({ Target, LayoutDashboard }),
        RouterModule.forRoot([
          { path: 'auth/register', component: RegisterStubComponent },
          { path: 'sistemas', component: SistemasSeleccionComponent },
          { path: 'sis-pe/dashboard', component: SystemDashboardStubComponent },
          { path: 'sis-poa/dashboard', component: SystemDashboardStubComponent },
        ]),
      ],
      providers: [
        {
          provide: AuthService,
          useValue: jasmine.createSpyObj<AuthService>('AuthService', ['login']),
        },
        {
          provide: CapabilitiesService,
          useValue: jasmine.createSpyObj<CapabilitiesService>('CapabilitiesService', ['cargar']),
        },
        {
          provide: GestionHabilitadaService,
          useValue: jasmine.createSpyObj<GestionHabilitadaService>(
            'GestionHabilitadaService',
            ['cargar', 'anio'],
          ),
        },
        {
          provide: PermissionsService,
          useValue: jasmine.createSpyObj<PermissionsService>(
            'PermissionsService',
            ['hasAnyCapability'],
          ),
        },
      ],
    }).compileComponents();

    router = TestBed.inject(Router);
    auth = TestBed.inject(AuthService) as jasmine.SpyObj<AuthService>;
    capabilities = TestBed.inject(CapabilitiesService) as jasmine.SpyObj<CapabilitiesService>;
    fiscalManagement = TestBed.inject(
      GestionHabilitadaService,
    ) as jasmine.SpyObj<GestionHabilitadaService>;
    fiscalManagement.anio.and.returnValue(null);
    permissions = TestBed.inject(PermissionsService) as jasmine.SpyObj<PermissionsService>;
    fixture = TestBed.createComponent(LoginComponent);
    fixture.detectChanges();
  });

  it('shows the public registration link', () => {
    const text = fixture.nativeElement.textContent as string;
    const link = fixture.debugElement.query(By.css('a[href="/auth/register"]'));

    expect(text).toContain('¿No tienes una cuenta?');
    expect(link.nativeElement.textContent.trim()).toBe('Crear cuenta');
  });

  it('navigates to registration from the public link', fakeAsync(() => {
    const link = fixture.debugElement.query(By.css('a[href="/auth/register"]'));

    link.nativeElement.click();
    tick();

    expect(router.url).toBe('/auth/register');
  }));

  it('initializes authenticated state before selecting and navigating without reload', fakeAsync(() => {
    const capabilitiesLoaded = new Subject<CapabilitiesResponse>();
    const fiscalManagementLoaded = new Subject<RespuestaGestionHabilitada>();
    auth.login.and.returnValue(of({} as Usuario));
    capabilities.cargar.and.returnValue(capabilitiesLoaded);
    fiscalManagement.cargar.and.returnValue(fiscalManagementLoaded);
    permissions.hasAnyCapability.and.returnValue(true);
    const navigate = spyOn(router, 'navigate').and.callThrough();
    fixture.componentInstance.loginForm.setValue({
      email: 'planner@sacaba.gob.bo',
      password: 'safe-password',
    });

    fixture.componentInstance.onSubmit();

    expect(auth.login).toHaveBeenCalled();
    expect(capabilities.cargar).toHaveBeenCalledTimes(1);
    expect(fiscalManagement.cargar).toHaveBeenCalledTimes(1);
    expect(router.navigate).not.toHaveBeenCalled();

    capabilitiesLoaded.next({
      usuario: { id: 'user-1', email: 'planner@sacaba.gob.bo' },
      roles: ['FORMULADOR_POAU'],
      capabilities: ['sis_poa.formulate'],
      alcances: [],
    });
    capabilitiesLoaded.complete();
    expect(router.navigate).not.toHaveBeenCalled();

    fiscalManagementLoaded.next({ habilitada: false, gestion: null });
    fiscalManagementLoaded.complete();
    tick();

    expect(navigate).toHaveBeenCalledOnceWith(['/sistemas']);
    expect(router.url).toBe('/sistemas');

    const selectorFixture = TestBed.createComponent(SistemasSeleccionComponent);
    selectorFixture.detectChanges();
    const sisPoaLink = selectorFixture.debugElement.query(
      By.css('a[aria-label="Ingresar a SIS-POA"]'),
    );
    sisPoaLink.nativeElement.click();
    tick();

    expect(router.url).toBe('/sis-poa/dashboard');
  }));
});

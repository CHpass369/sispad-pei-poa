import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { provideHttpClientTesting } from '@angular/common/http/testing';
import { Router } from '@angular/router';
import { RouterTestingModule } from '@angular/router/testing';
import { BehaviorSubject } from 'rxjs';
import { LucideAngularModule, Target, LayoutDashboard, LogOut } from 'lucide-angular';
import { SistemasSeleccionComponent } from './sistemas-seleccion.component';
import { AuthService } from '../../core/services/auth.service';
import { CapabilitiesService } from '../../core/services/capabilities.service';
import { GestionHabilitadaService } from '../../core/services/gestion-habilitada.service';
import { environment } from '../../../environments/environment';

describe('SistemasSeleccionComponent', () => {
  let component: SistemasSeleccionComponent;
  let fixture: ComponentFixture<SistemasSeleccionComponent>;
  let capabilitiesLoaded: BehaviorSubject<boolean>;
  let granted: Set<string>;
  let capabilitiesSpy: jasmine.SpyObj<CapabilitiesService>;
  let auth: AuthService;
  let router: Router;

  beforeEach(async () => {
    localStorage.removeItem(environment.tokenKey);
    granted = new Set<string>();
    capabilitiesLoaded = new BehaviorSubject<boolean>(false);
    capabilitiesSpy = jasmine.createSpyObj<CapabilitiesService>(
      'CapabilitiesService',
      ['tieneAlguna'],
      { cargadas$: capabilitiesLoaded },
    );
    capabilitiesSpy.tieneAlguna.and.callFake(capabilities =>
      capabilities.some(capability => granted.has(capability)),
    );

    await TestBed.configureTestingModule({
      declarations: [SistemasSeleccionComponent],
      imports: [
        RouterTestingModule,
        LucideAngularModule.pick({ Target, LayoutDashboard, LogOut }),
      ],
      providers: [
        provideHttpClient(),
        provideHttpClientTesting(),
        { provide: CapabilitiesService, useValue: capabilitiesSpy },
        {
          provide: GestionHabilitadaService,
          useValue: { anio: () => null },
        },
      ],
    }).compileComponents();

    fixture = TestBed.createComponent(SistemasSeleccionComponent);
    component = fixture.componentInstance;
    auth = TestBed.inject(AuthService);
    router = TestBed.inject(Router);
  });

  afterEach(() => localStorage.removeItem(environment.tokenKey));

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('shows SIS-PE for the verified module capability shape', () => {
    granted = new Set([
      'sis_pe.articulacion.edit',
      'sis_pe.articulacion.view',
      'sis_pe.evaluacion.view',
      'sis_pe.indicadores.view',
      'sis_pe.pad.edit',
      'sis_pe.pad.validate',
      'sis_pe.pad.view',
      'sis_pe.pei.edit',
      'sis_pe.pei.view',
    ]);
    fixture.detectChanges();
    capabilitiesLoaded.next(true);
    fixture.detectChanges();

    expect(component.sistemas.map(system => system.sigla)).toEqual(['SIS-PE']);
    expect(component.sistemas.some(s => s.ruta.startsWith('/sis-pro'))).toBeFalse();
    expect(component.sinAcceso).toBeFalse();
  });

  it('does not render the final no-access state before capabilities finish loading', () => {
    fixture.detectChanges();

    expect(component.sistemas).toEqual([]);
    expect(component.sinAcceso).toBeFalse();
    expect(fixture.nativeElement.querySelector('.nota')).toBeNull();
  });

  it('recalculates systems when delayed capability loading completes', () => {
    fixture.detectChanges();
    granted.add('sis_pe.pei.view');

    capabilitiesLoaded.next(true);
    fixture.detectChanges();

    expect(component.sistemas.map(system => system.sigla)).toEqual(['SIS-PE']);
    expect(component.sinAcceso).toBeFalse();
  });

  it('keeps no-capability users denied and excludes SIS-PRO', () => {
    fixture.detectChanges();
    capabilitiesLoaded.next(true);
    fixture.detectChanges();

    expect(component.sistemas).toEqual([]);
    expect(component.sinAcceso).toBeTrue();
    expect(fixture.nativeElement.querySelector('.nota')).not.toBeNull();
    expect(fixture.nativeElement.textContent).not.toContain('SIS-PRO');
  });

  it('logs out, clears the session, and returns to login without preserving history', () => {
    localStorage.setItem(environment.tokenKey, JSON.stringify({ access: 'access', refresh: 'refresh' }));
    const navigation = spyOn(router, 'navigateByUrl').and.resolveTo(true);
    fixture.detectChanges();
    capabilitiesLoaded.next(true);
    fixture.detectChanges();

    const button: HTMLButtonElement = fixture.nativeElement.querySelector('.logout-button');
    button.click();

    expect(auth.getToken()).toBeNull();
    expect(navigation).toHaveBeenCalledOnceWith('/auth/login', { replaceUrl: true });
  });
});

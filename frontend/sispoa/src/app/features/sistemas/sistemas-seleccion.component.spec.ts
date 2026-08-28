import { ComponentFixture, TestBed } from '@angular/core/testing';
import { RouterModule } from '@angular/router';
import {
  LayoutDashboard, LogOut, LucideAngularModule, Target,
} from 'lucide-angular';
import { BehaviorSubject } from 'rxjs';
import { AuthService } from '../../core/services/auth.service';
import { CapabilitiesService } from '../../core/services/capabilities.service';
import { GestionHabilitadaService } from '../../core/services/gestion-habilitada.service';
import { SistemasSeleccionComponent } from './sistemas-seleccion.component';

/**
 * La baldosa de SIS-POA exigía literalmente `sis_poa.formulate` y aterrizaba
 * siempre en `/sis-poa/dashboard`. Un perfil POAU de unidad no tiene ninguna
 * de las dos cosas: veía «sin acceso a ningún sistema» y, al arreglar solo la
 * primera mitad, la baldosa aparecía pero el guard lo rebotaba al entrar.
 *
 * Estos casos fijan las dos mitades juntas: la baldosa se ve Y lleva a una
 * pantalla que el usuario puede abrir.
 */
describe('SistemasSeleccionComponent', () => {
  let fixture: ComponentFixture<SistemasSeleccionComponent>;
  let component: SistemasSeleccionComponent;
  let granted: Set<string>;

  const POAU_ONLY = [
    'sis_poa.poau.view',
    'sis_poa.poau.create',
    'sis_poa.poau.edit',
    'sis_poa.poau.submit',
    'sis_poa.poau.review',
  ];

  function render(capacidades: string[]): void {
    granted = new Set(capacidades);
    fixture = TestBed.createComponent(SistemasSeleccionComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  }

  function sistema(sigla: string) {
    return component.sistemas.find(s => s.sigla === sigla);
  }

  beforeEach(async () => {
    granted = new Set<string>();
    const capabilities = {
      cargadas$: new BehaviorSubject<boolean>(true),
      tiene: (codigo: string) => granted.has(codigo),
      tieneAlguna: (codigos: string[]) => codigos.some(c => granted.has(c)),
      listar: () => [...granted],
    };
    const auth = jasmine.createSpyObj<AuthService>('AuthService', ['logout']);
    const gestion = jasmine.createSpyObj<GestionHabilitadaService>(
      'GestionHabilitadaService', ['gestion', 'anio'],
    );
    gestion.anio.and.returnValue(2027);
    gestion.gestion.and.returnValue(null);

    await TestBed.configureTestingModule({
      declarations: [SistemasSeleccionComponent],
      imports: [
        RouterModule.forRoot([]),
        LucideAngularModule.pick({ Target, LayoutDashboard, LogOut }),
      ],
      providers: [
        { provide: CapabilitiesService, useValue: capabilities },
        { provide: AuthService, useValue: auth },
        { provide: GestionHabilitadaService, useValue: gestion },
      ],
    }).compileComponents();
  });

  it('offers SIS-POA to a POAU-only profile', () => {
    render(POAU_ONLY);

    expect(component.sinAcceso).toBeFalse();
    expect(sistema('SIS-POA')).toBeDefined();
  });

  it('lands a POAU-only profile on a screen it can actually open', () => {
    // `/sis-poa/dashboard` exige capacidades POA: aterrizar ahí lo rebota.
    render(POAU_ONLY);

    expect(sistema('SIS-POA')?.ruta).toBe('/sis-poa/poaus');
  });

  it('keeps the POA dashboard as the landing for a POA profile', () => {
    render(['sis_poa.poa.view', 'sis_poa.formulate']);

    expect(sistema('SIS-POA')?.ruta).toBe('/sis-poa/dashboard');
  });

  it('does not offer SIS-PE to a POAU-only profile', () => {
    render(POAU_ONLY);

    expect(sistema('SIS-PE')).toBeUndefined();
  });

  it('still reports no access when the user holds nothing', () => {
    render([]);

    expect(component.sistemas).toEqual([]);
    expect(component.sinAcceso).toBeTrue();
  });
});

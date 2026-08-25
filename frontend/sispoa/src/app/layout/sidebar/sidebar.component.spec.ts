import { ComponentFixture, TestBed } from '@angular/core/testing';
import { ActivatedRoute, Router, RouterModule } from '@angular/router';
import { BehaviorSubject, of } from 'rxjs';
import {
  Activity,
  Banknote,
  Bell,
  Boxes,
  CalendarCheck,
  CalendarDays,
  ChartColumn,
  ChevronLeft,
  ChevronRight,
  ClipboardList,
  Compass,
  FileText,
  Gauge,
  Home,
  LayoutGrid,
  ListTodo,
  ListTree,
  LucideAngularModule,
  MapPin,
  Users,
  Wallet,
} from 'lucide-angular';
import { SidebarComponent } from './sidebar.component';
import { AuthService } from '../../core/services/auth.service';
import { CapabilitiesService } from '../../core/services/capabilities.service';
import { GestionHabilitadaService } from '../../core/services/gestion-habilitada.service';
import { LEGACY_MENU_VISIBLE } from '../../core/config/cutover.config';

describe('SidebarComponent', () => {
  let component: SidebarComponent;
  let fixture: ComponentFixture<SidebarComponent>;
  let capabilitiesSubject: BehaviorSubject<boolean>;
  let granted: Set<string>;

  beforeEach(async () => {
    granted = new Set<string>();
    capabilitiesSubject = new BehaviorSubject<boolean>(false);
    const capabilitiesSpy = jasmine.createSpyObj<CapabilitiesService>(
      'CapabilitiesService',
      ['tieneAlguna'],
      { cargadas$: capabilitiesSubject },
    );
    capabilitiesSpy.tieneAlguna.and.callFake(codigos =>
      codigos.some(codigo => granted.has(codigo)),
    );
    const authSpy = jasmine.createSpyObj('AuthService', [], { user$: of(null) });
    const routerSpy = jasmine.createSpyObj('Router', [
      'createUrlTree', 'serializeUrl', 'isActive',
    ], {
      url: '/dashboard',
      events: of(null),
    });
    routerSpy.createUrlTree.and.returnValue({ toString: () => '/' });
    routerSpy.serializeUrl.and.returnValue('/');

    await TestBed.configureTestingModule({
      declarations: [SidebarComponent],
      imports: [
        RouterModule,
        LucideAngularModule.pick({
          Activity,
          Banknote,
          Bell,
          Boxes,
          CalendarCheck,
          CalendarDays,
          ChartColumn,
          ChevronLeft,
          ChevronRight,
          ClipboardList,
          Compass,
          FileText,
          Gauge,
          Home,
          LayoutGrid,
          ListTodo,
          ListTree,
          MapPin,
          Users,
          Wallet,
        }),
      ],
      providers: [
        { provide: AuthService, useValue: authSpy },
        { provide: CapabilitiesService, useValue: capabilitiesSpy },
        {
          provide: GestionHabilitadaService,
          useValue: {
            cargada$: of(true),
            hayGestion: () => false,
            gestion: () => null,
          },
        },
        { provide: Router, useValue: routerSpy },
        { provide: ActivatedRoute, useValue: { snapshot: {} } },
      ],
    }).compileComponents();

    fixture = TestBed.createComponent(SidebarComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  afterEach(() => {
    for (const route of Object.keys(LEGACY_MENU_VISIBLE)) {
      LEGACY_MENU_VISIBLE[route] = true;
    }
  });

  function navegarA(url: string): void {
    (component as unknown as { router: { url: string } })['router'] = { url } as never;
    component['rebuildMenu']();
    (component as unknown as { cdr: { markForCheck(): void } })['cdr'].markForCheck();
    fixture.detectChanges();
  }

  function rutasVisibles(): string[] {
    return component.visibleSections.flatMap(section => section.items).map(item => item.route);
  }

  function seccion(titulo: string) {
    return component.visibleSections.find(section => section.title.startsWith(titulo));
  }

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('hides TRANSVERSAL when no administrative view capability is granted', () => {
    navegarA('/dashboard');

    expect(seccion('TRANSVERSAL')).toBeUndefined();
    expect(rutasVisibles()).not.toContain('/admin-usuarios');
  });

  it('shows exactly Usuarios y permisos for any administrative view capability', () => {
    const capabilities = [
      'accounts.usuario.view',
      'accounts.rol.view',
      'accounts.capacidad.view',
      'accounts.solicitud.view',
    ];

    for (const capability of capabilities) {
      granted.clear();
      granted.add(capability);
      navegarA('/dashboard');

      expect(seccion('TRANSVERSAL')?.items.map(item => [item.label, item.route]))
        .withContext(capability)
        .toEqual([['Usuarios y permisos', '/admin-usuarios']]);
    }
  });

  it('rebuilds the menu when capabilities finish loading', () => {
    expect(seccion('TRANSVERSAL')).toBeUndefined();
    granted.add('accounts.usuario.view');

    capabilitiesSubject.next(true);
    fixture.detectChanges();

    expect(rutasVisibles()).toContain('/admin-usuarios');
  });

  it('shows FORMULADOR_POAU only the canonical POAU tool in SIS-POA', () => {
    granted = new Set([
      'sis_poa.poau.view',
      'sis_poa.poau.create',
      'sis_poa.poau.edit',
      'sis_poa.poau.submit',
    ]);

    navegarA('/sis-poa/poaus');

    expect(seccion('SIS-POA')?.items.map(item => [item.label, item.route]))
      .toEqual([['POAU', '/sis-poa/poaus']]);
    expect(seccion('TRANSVERSAL')).toBeUndefined();
    expect(rutasVisibles()).not.toContain('/sis-poa/dashboard');
    expect(rutasVisibles()).not.toContain('/sis-poa/poas');
  });

  it('shows JEFE_PE only SIS-PE modules and optional user administration', () => {
    granted = new Set([
      'sis_pe.instrumento.read',
      'sis_pe.pad.view',
      'sis_pe.pei.view',
      'sis_pe.articulacion.view',
      'sis_pe.indicadores.view',
      'sis_pe.evaluacion.view',
      'accounts.usuario.view',
    ]);

    navegarA('/sis-pe/dashboard');

    expect(seccion('SIS-PE')?.items.length).toBe(8);
    expect(seccion('SIS-POA')).toBeUndefined();
    expect(seccion('TRANSVERSAL')?.items.map(item => item.label))
      .toEqual(['Usuarios y permisos']);
    expect(rutasVisibles().some(route => route.startsWith('/sis-pro'))).toBeFalse();
  });

  it('shows JEFE_POA the complete SIS-POA toolset and user administration', () => {
    granted = new Set([
      'sis_poa.poa.view',
      'sis_poa.poau.view',
      'sis_poa.techos.view',
      'sis_poa.distribuciones.view',
      'sis_poa.programacion.view',
      'sis_poa.seguimiento.view',
      'accounts.usuario.view',
    ]);

    navegarA('/sis-poa/dashboard');

    expect(seccion('SIS-POA')?.items.map(item => [item.label, item.route])).toEqual([
      ['Dashboard POA', '/sis-poa/dashboard'],
      ['Habilitación de Gestión', '/sis-poa/budget/gestion-fiscal'],
      ['Presupuesto General de Recursos', '/sis-poa/presupuesto-recursos'],
      ['Presupuesto General de Gastos', '/sis-poa/presupuesto-gastos'],
      ['Priorización POA', '/priorizacion/actas'],
      ['POA', '/sis-poa/poas'],
      ['POAU', '/sis-poa/poaus'],
      ['POAU (Físico)', '/poau'],
      ['POAU (Recursos)', '/poau_recursos'],
      ['Seguimiento y Evaluación', '/sis-poa/seguimiento'],
    ]);
    expect(seccion('TRANSVERSAL')?.items.map(item => item.label))
      .toEqual(['Usuarios y permisos']);
  });

  it('shows SUPER_ADMIN the complete PE/POA matrix and never SIS-PRO', () => {
    granted = new Set([
      'sis_pe.instrumento.read',
      'sis_pe.pad.view',
      'sis_pe.pei.view',
      'sis_pe.articulacion.view',
      'sis_pe.indicadores.view',
      'sis_pe.evaluacion.view',
      'sis_poa.poa.view',
      'sis_poa.poau.view',
      'sis_poa.techos.view',
      'sis_poa.distribuciones.view',
      'sis_poa.programacion.view',
      'sis_poa.seguimiento.view',
      'accounts.usuario.view',
    ]);

    navegarA('/sis-pe/dashboard');
    expect(seccion('SIS-PE')?.items.length).toBe(8);
    expect(seccion('TRANSVERSAL')?.items.length).toBe(1);

    navegarA('/sis-poa/dashboard');
    expect(seccion('SIS-POA')?.items.length).toBe(10);
    expect(seccion('TRANSVERSAL')?.items.length).toBe(1);
    expect(JSON.stringify(component.visibleSections)).not.toContain('sis-pro');
    expect(JSON.stringify(component.visibleSections)).not.toContain('sis_pro');
  });

  it('contains only SIS-PE and SIS-POA system definitions', () => {
    expect(Object.keys(component['sistemasMenu'])).toEqual(['sis-pe', 'sis-poa']);
    expect(JSON.stringify(component['sistemasMenu'])).not.toContain('sis-pro');
    expect(JSON.stringify(component['sistemasMenu'])).not.toContain('sis_pro');
  });

  it('keeps system context on routes outside the /sis-* prefixes', () => {
    granted.add('sis_pe.pad.view');
    navegarA('/matrices-pad');
    expect(seccion('SIS-PE')).toBeDefined();

    granted.clear();
    granted.add('sis_poa.programacion.view');
    navegarA('/poau');
    expect(seccion('SIS-POA')).toBeDefined();
  });

  it('still applies the legacy cutover flag after capability filtering', () => {
    granted.add('sis_poa.programacion.view');
    LEGACY_MENU_VISIBLE['/poau'] = false;

    navegarA('/sis-poa/dashboard');

    expect(rutasVisibles()).not.toContain('/poau');
  });
});

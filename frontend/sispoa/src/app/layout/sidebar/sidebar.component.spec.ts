import { ComponentFixture, TestBed } from '@angular/core/testing';
import { ActivatedRoute, Router, RouterModule } from '@angular/router';
import { BehaviorSubject, of } from 'rxjs';
import { LucideAngularModule, Home, Gauge, Bell, FileText, ClipboardList, Landmark, Compass, Network, LayoutGrid, ChartColumn, MapPin, Activity, CircleCheck, CalendarCheck, CalendarDays, ListTodo, Boxes, Banknote, Wallet, Coins, ChartBar, ListTree, ChartPie, Map, Download, RefreshCw, ScanSearch, PenLine, PencilRuler, Layers, Briefcase, HardHat, DraftingCompass, FolderOpen, FilePenLine, Handshake, Play, Eye, Users, Building2, CalendarRange, BookOpen, ScrollText, Folder, ChartSpline, MapPinned, Workflow, CircleAlert, BadgeCheck, ChevronLeft, ChevronRight } from 'lucide-angular';
import { SidebarComponent } from './sidebar.component';
import { AuthService } from '../../core/services/auth.service';
import { PermissionsService } from '../../core/services/permissions.service';
import { CapabilitiesService } from '../../core/services/capabilities.service';
import { LEGACY_MENU_VISIBLE } from '../../core/config/cutover.config';

describe('SidebarComponent', () => {
  let component: SidebarComponent;
  let fixture: ComponentFixture<SidebarComponent>;
  let permissionsSpy: jasmine.SpyObj<PermissionsService>;
  let capabilitiesSubject: BehaviorSubject<boolean>;

  beforeEach(async () => {
    const authSpy = jasmine.createSpyObj('AuthService', [], { user$: of(null) });
    permissionsSpy = jasmine.createSpyObj('PermissionsService', [
      'hasAnyCapability', 'hasAnyRole',
    ]);
    permissionsSpy.hasAnyCapability.and.returnValue(true);
    permissionsSpy.hasAnyRole.and.returnValue(true);
    capabilitiesSubject = new BehaviorSubject<boolean>(false);
    const capabilitiesSpy = jasmine.createSpyObj('CapabilitiesService', [], {
      cargadas$: capabilitiesSubject,
    });
    const routerSpy = jasmine.createSpyObj('Router', [
      'createUrlTree', 'serializeUrl', 'isActive',
    ], {
      url: '/sis-pro/proyectos',
      events: of(null),
    });
    routerSpy.createUrlTree.and.returnValue({ toString: () => '/' });
    routerSpy.serializeUrl.and.returnValue('/');

    await TestBed.configureTestingModule({
      declarations: [SidebarComponent],
      imports: [
        RouterModule,
        LucideAngularModule.pick({
          Home, Gauge, Bell, FileText, ClipboardList, Landmark, Compass, Network, LayoutGrid,
          ChartColumn, MapPin, Activity, CircleCheck, CalendarCheck, CalendarDays, ListTodo, Boxes, Banknote,
          Wallet, Coins, ChartBar, ListTree, ChartPie, Map, Download, RefreshCw, ScanSearch,
          PenLine, PencilRuler, Layers, Briefcase, HardHat, DraftingCompass, FolderOpen,
          FilePenLine, Handshake, Play, Eye, Users, Building2, CalendarRange, BookOpen,
          ScrollText, Folder, ChartSpline, MapPinned, Workflow, CircleAlert, BadgeCheck,
          ChevronLeft, ChevronRight,
        }),
      ],
      providers: [
        { provide: AuthService, useValue: authSpy },
        { provide: PermissionsService, useValue: permissionsSpy },
        { provide: CapabilitiesService, useValue: capabilitiesSpy },
        { provide: Router, useValue: routerSpy },
        { provide: ActivatedRoute, useValue: { snapshot: {} } },
      ],
    }).compileComponents();

    fixture = TestBed.createComponent(SidebarComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  afterEach(() => {
    // Restaurar la palanca al default (todo visible).
    for (const route of Object.keys(LEGACY_MENU_VISIBLE)) {
      LEGACY_MENU_VISIBLE[route] = true;
    }
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should show legacy items by default (palanca en true)', () => {
    const rutasLegacy = component['visibleSections']
      .flatMap(s => s.items)
      .filter(i => i.legacy)
      .map(i => i.route);
    expect(rutasLegacy).toContain('/inversion');
  });

  it('should hide legacy item when its route is turned off in the palanca', () => {
    LEGACY_MENU_VISIBLE['/inversion'] = false;
    component['rebuildMenu']();
    fixture.detectChanges();

    const rutas = component['visibleSections'].flatMap(s => s.items).map(i => i.route);
    expect(rutas).not.toContain('/inversion');
    // El resto del SIS-PRO V2 permanece visible.
    expect(rutas).toContain('/sis-pro/proyectos');
    expect(rutas).toContain('/sis-pro/preinversion');
  });

  it('should keep other legacy items visible when only one is turned off', () => {
    LEGACY_MENU_VISIBLE['/inversion'] = false;
    // Contexto SIS-POA: la palanca de /inversion no afecta los legacy de POA.
    (component as unknown as { router: { url: string } })['router'] = { url: '/sis-poa/poas' } as never;
    component['rebuildMenu']();
    fixture.detectChanges();

    const rutas = component['visibleSections'].flatMap(s => s.items).map(i => i.route);
    expect(rutas).toContain('/poau');
    expect(rutas).not.toContain('/inversion');
  });

  it('should still filter by capabilities/roles for non-legacy items', () => {
    permissionsSpy.hasAnyCapability.and.callFake(
      (caps: string[]) => !caps.includes('sis_pro.project.read'),
    );
    component['rebuildMenu']();
    fixture.detectChanges();

    const rutas = component['visibleSections'].flatMap(s => s.items).map(i => i.route);
    expect(rutas).not.toContain('/sis-pro/proyectos');
    // Los legacy con rol siguen regidos por roles.
    expect(rutas).toContain('/inversion');
  });

  // --- Contexto del sistema por ruta de módulo (bug: el menú perdía el SIS
  // al navegar a módulos legacy/V2 fuera del prefijo /sis-*) ---
  function rutasVisibles(): string[] {
    return component['visibleSections'].flatMap(s => s.items).map(i => i.route);
  }

  function navegarA(url: string): void {
    (component as unknown as { router: { url: string } })['router'] = { url } as never;
    component['rebuildMenu']();
    fixture.detectChanges();
  }

  it('should keep SIS-PE context when navigating to /matrices-pad (V2 fuera de /sis-*)', () => {
    navegarA('/matrices-pad');
    const rutas = rutasVisibles();
    expect(rutas).toContain('/sis-pe/dashboard');
    expect(rutas).toContain('/matrices-pad');
    expect(rutas).not.toContain('/dashboard');
  });

  it('should not show the removed Articulador PAD-PEI menu item', () => {
    navegarA('/sis-pe/instrumentos');
    const rutas = rutasVisibles();
    expect(rutas).toContain('/sis-pe/instrumentos');
    expect(rutas).not.toContain('/articulacion');

    expect(fixture.nativeElement.querySelector('a[aria-label="Articulador PAD-PEI"]')).toBeNull();
  });

  it('should keep SIS-POA context on legacy routes (POAU, Recursos, Formulación)', () => {
    for (const ruta of ['/poau', '/poau_recursos', '/planificacion/formulacion']) {
      navegarA(ruta);
      expect(rutasVisibles()).toContain('/sis-poa/poas');
    }
  });

  it('should list the SIS-POA tools in the agreed order', () => {
    navegarA('/sis-poa/dashboard');
    const seccion = component['visibleSections']
      .find(s => s.title.startsWith('SIS-POA'))!;

    expect(seccion.items.map(i => [i.label, i.route])).toEqual([
      ['Dashboard POA', '/sis-poa/dashboard'],
      ['Habilitación de Gestión', '/sis-poa/budget/gestion-fiscal'],
      ['Presupuesto General de Recursos', '/sis-poa/presupuesto-recursos'],
      ['Presupuesto General de Gastos', '/sis-poa/presupuesto-gastos'],
      ['Priorización POA', '/priorizacion/actas'],
      ['POA', '/sis-poa/poas'],
      ['POAUs', '/sis-poa/poaus'],
      ['POAU (Físico)', '/poau'],
      ['POAU (Recursos)', '/poau_recursos'],
      ['Seguimiento y Evaluación', '/sis-poa/seguimiento'],
    ]);
  });

  it('should tag Dashboard and Seguimiento as Beta and the rest as V1', () => {
    navegarA('/sis-poa/dashboard');
    const seccion = component['visibleSections']
      .find(s => s.title.startsWith('SIS-POA'))!;

    const beta = seccion.items.filter(i => i.beta || i.pendiente).map(i => i.route);
    const v1 = seccion.items.filter(i => i.legacy || i.v1).map(i => i.route);

    expect(beta).toEqual(['/sis-poa/dashboard', '/sis-poa/seguimiento']);
    expect(v1.length).toBe(8);
    expect(beta.some(r => v1.includes(r))).toBeFalse();
  });

  it('should gate Habilitación de Gestión to the POA lead only', () => {
    permissionsSpy.hasAnyRole.and.callFake((roles: string[]) => roles.includes('tecnico_poa'));
    navegarA('/sis-poa/dashboard');

    const rutas = rutasVisibles();
    expect(rutas).not.toContain('/sis-poa/budget/gestion-fiscal');
    expect(rutas).toContain('/sis-poa/presupuesto-recursos');
  });

  it('should keep POA and POAU visible for the PE team', () => {
    permissionsSpy.hasAnyRole.and.callFake((roles: string[]) => roles.includes('tecnico_pe'));
    navegarA('/sis-poa/dashboard');

    const rutas = rutasVisibles();
    expect(rutas).toContain('/sis-poa/poas');
    expect(rutas).toContain('/sis-poa/poaus');
    expect(rutas).toContain('/poau');
    expect(rutas).toContain('/poau_recursos');
    expect(rutas).not.toContain('/sis-poa/presupuesto-gastos');
  });

  it('should keep SIS-PRO context on legacy /inversion', () => {
    navegarA('/inversion');
    const rutas = rutasVisibles();
    expect(rutas).toContain('/sis-pro/proyectos');
    expect(rutas).toContain('/inversion');
  });

  it('should show PLATAFORMA (Selección/Dashboard/Notificaciones) only on platform routes', () => {
    navegarA('/dashboard');
    const rutas = rutasVisibles();
    expect(rutas).toContain('/sistemas');
    expect(rutas).toContain('/dashboard');
    expect(rutas).toContain('/notificaciones');
    expect(rutas).not.toContain('/sis-pe/dashboard');
    expect(rutas).not.toContain('/sis-poa/poas');
    expect(rutas).not.toContain('/sis-pro/proyectos');
  });

  it('should ignore query strings when detecting the system context', () => {
    navegarA('/sis-pe/instrumentos?gestion=2027');
    expect(rutasVisibles()).toContain('/sis-pe/dashboard');
  });
});

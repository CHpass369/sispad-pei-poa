import { ComponentFixture, TestBed } from '@angular/core/testing';
import { ActivatedRoute, Router, RouterModule } from '@angular/router';
import { BehaviorSubject, of } from 'rxjs';
import { LucideAngularModule, Home, Gauge, Bell, FileText, ClipboardList, Landmark, Compass, Network, LayoutGrid, ChartColumn, MapPin, Activity, CircleCheck, CalendarDays, ListTodo, Boxes, Banknote, Wallet, Coins, ChartBar, ListTree, ChartPie, Map, Download, RefreshCw, ScanSearch, PenLine, PencilRuler, Layers, Briefcase, HardHat, DraftingCompass, FolderOpen, FilePenLine, Handshake, Play, Eye, Users, Building2, CalendarRange, BookOpen, ScrollText, Folder, ChartSpline, MapPinned, Workflow, CircleAlert, BadgeCheck, ChevronLeft, ChevronRight } from 'lucide-angular';
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
          ChartColumn, MapPin, Activity, CircleCheck, CalendarDays, ListTodo, Boxes, Banknote,
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
});

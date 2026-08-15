import { Component, EventEmitter, Output, ChangeDetectionStrategy, ChangeDetectorRef, OnInit, OnDestroy } from '@angular/core';
import { NavigationEnd, Router } from '@angular/router';
import { Subject, filter, takeUntil } from 'rxjs';
import { AuthService } from '../../core/services/auth.service';
import { PermissionsService } from '../../core/services/permissions.service';
import { CapabilitiesService } from '../../core/services/capabilities.service';
import { LEGACY_MENU_VISIBLE } from '../../core/config/cutover.config';

interface NavItem {
  route: string;
  label: string;
  icon: string;
  roles?: string[];
  capacidades?: string[];
  pendiente?: boolean;
  legacy?: boolean;
}

interface NavSection {
  title: string;
  items: NavItem[];
}

@Component({
  standalone: false,
  selector: 'app-sidebar',
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <aside class="sidebar" [class.collapsed]="collapsed" [class.sidebar-open]="mobileOpen">
      @if (mobileOpen) {
        <div class="sidebar-overlay" (click)="toggleMobile()"></div>
      }
      <div class="brand">
        <div class="brand-mark">PIP</div>
        @if (!collapsed) {
          <div class="brand-copy">
            <strong>PIP SACABA</strong>
            <span>Planificación integral</span>
          </div>
        }
        <button class="collapse-btn" (click)="toggleCollapse()"
          [attr.aria-label]="collapsed ? 'Expandir menú' : 'Contraer menú'"
          title="Colapsar menú">
          <lucide-angular [name]="collapsed ? 'chevron-right' : 'chevron-left'" [size]="16"></lucide-angular>
        </button>
      </div>
      <nav class="nav">
        @for (section of visibleSections; track section) {
          @if (!collapsed) {
            <div class="nav-label">{{ section.title }}</div>
          }
          @for (item of section.items; track item) {
            <a
              [routerLink]="item.route"
              routerLinkActive="active"
              class="nav-item"
              [title]="collapsed ? item.label : ''"
              [attr.aria-label]="item.label">
              <span class="ico"><lucide-angular [name]="item.icon" [size]="16"></lucide-angular></span>
              @if (!collapsed) {
                <span>{{ item.label }}</span>
                @if (item.pendiente) {
                  <span class="tag" title="Módulo en desarrollo">Beta</span>
                }
                @if (item.legacy) {
                  <span class="tag ok" title="Módulo V1 (legacy)">V1</span>
                }
              }
            </a>
          }
        }
      </nav>
      @if (!collapsed) {
        <div class="sidebar-foot">
          <div class="status-dot"></div>
          <div><strong>Gestión 2027</strong><span>Formulación activa</span></div>
        </div>
      }
    </aside>
    `,
  styles: [`
    .sidebar {
      position: fixed; left: 0; top: 0; bottom: 0; width: 252px;
      background: var(--pip-green-900); color: #CFE3D6;
      display: flex; flex-direction: column; z-index: 100;
      transition: width .2s ease;
    }
    .sidebar.collapsed { width: 64px; }

    .brand {
      display: flex; align-items: center; gap: 10px;
      padding: 18px 16px 14px;
      border-bottom: 1px solid rgba(255,255,255,.08);
    }
    .brand-mark {
      width: 36px; height: 36px; border-radius: 10px; flex-shrink: 0;
      background: linear-gradient(135deg, var(--pip-green-500), var(--pip-green-700));
      display: grid; place-items: center;
      font-family: var(--font-display); font-weight: 700; font-size: 13px; color: #fff;
      letter-spacing: .5px;
    }
    .brand-copy { display: flex; flex-direction: column; min-width: 0; }
    .brand-copy strong {
      font-family: var(--font-display); font-size: 14px; color: #fff;
      letter-spacing: .4px; white-space: nowrap;
    }
    .brand-copy span {
      font-size: 10.5px; color: #8FB89E; text-transform: uppercase;
      letter-spacing: .5px; white-space: nowrap;
    }
    .collapse-btn {
      margin-left: auto; background: none; border: none; color: #7FA792;
      cursor: pointer; padding: 4px; border-radius: 6px;
      display: grid; place-items: center;
      transition: background .15s, color .15s;
    }
    .collapse-btn:hover { background: rgba(255,255,255,.08); color: #fff; }
    .sidebar.collapsed .collapse-btn { margin-left: auto; }

    .nav { flex: 1; overflow-y: auto; padding: 10px; }
    .nav-label {
      font-size: 10px; letter-spacing: 1.2px; text-transform: uppercase;
      color: #6E9A80; padding: 14px 10px 6px; font-weight: 600; white-space: nowrap;
    }
    .nav-item {
      display: flex; align-items: center; gap: 10px;
      padding: 8px 10px; border-radius: 8px;
      color: #C4D9CB; text-decoration: none; font-size: 13px; font-weight: 500;
      transition: background .15s;
      cursor: pointer; border: none; background: none; width: 100%; text-align: left;
      font-family: inherit;
    }
    .nav-item:hover { background: rgba(255,255,255,.06); color: #fff; }
    .nav-item.active { background: var(--pip-green-700); color: #fff; }
    .nav-item .ico {
      width: 18px; text-align: center; flex-shrink: 0;
      display: grid; place-items: center;
    }
    .nav-item .tag {
      margin-left: auto; font-size: 9.5px; font-weight: 700;
      background: var(--pip-gold); color: var(--pip-green-900);
      border-radius: 20px; padding: 1px 7px; letter-spacing: .3px;
    }
    .nav-item .tag.ok { background: var(--pip-green-500); color: #fff; }

    .sidebar-foot {
      padding: 14px 18px;
      border-top: 1px solid rgba(255,255,255,.08);
      font-size: 11px; color: #7FA792;
      display: flex; align-items: center; gap: 8px;
    }
    .status-dot {
      width: 8px; height: 8px; border-radius: 50%;
      background: var(--pip-gold); flex-shrink: 0;
    }
    .sidebar-foot strong { display: block; color: #CFE3D6; font-size: 11.5px; }
    .sidebar-foot span { font-size: 10px; }

    .sidebar-overlay { display: none; }

    @media (max-width: 1024px) {
      .sidebar {
        transform: translateX(-100%);
        transition: transform 0.3s ease;
      }
      .sidebar.sidebar-open { transform: translateX(0); }
      .sidebar-overlay {
        display: block; position: fixed; top: 0; left: 0; right: 0; bottom: 0;
        background: rgba(0,0,0,0.5); z-index: -1;
      }
      .sidebar.collapsed { width: 252px; }
      .sidebar.collapsed .brand-copy,
      .sidebar.collapsed .nav-label,
      .sidebar.collapsed .nav-item span,
      .sidebar.collapsed .sidebar-foot { display: initial; }
      .sidebar.collapsed .nav-item .ico { width: 18px; }
    }
  `]
})
export class SidebarComponent implements OnInit, OnDestroy {
  @Output() sidebarToggle = new EventEmitter<boolean>();

  collapsed = false;
  mobileOpen = false;

  visibleSections: NavSection[] = [];
  private destroy$ = new Subject<void>();
  private sistemaActual = '';

  /** Módulos del sistema activo según el plan maestro (§18.1).
   *  V2 = capacidades · V1 = roles (legacy insertado en su SIS). */
  private sistemasMenu: Record<string, NavSection> = {
    'sis-pe': {
      title: 'SIS-PE — Planificación Estratégica',
      items: [
        { route: '/sis-pe/dashboard', label: 'Dashboard estratégico', icon: 'gauge', capacidades: ['sis_pe.instrumento.read'] },
        { route: '/sis-pe/instrumentos', label: 'Instrumentos', icon: 'file-text', capacidades: ['sis_pe.instrumento.read'] },
        { route: '/sis-pe/diagnostico', label: 'Diagnóstico', icon: 'clipboard-list', capacidades: ['sis_pe.instrumento.read'], pendiente: true },
        { route: '/articulador', label: 'PAD', icon: 'landmark', roles: ['superadmin', 'tecnico_admin', 'planificador'], legacy: true },
        { route: '/sis-pe/pei', label: 'PEI', icon: 'compass', capacidades: ['sis_pe.instrumento.read'], pendiente: true },
        { route: '/articulacion', label: 'Articulación', icon: 'network', roles: ['superadmin', 'tecnico_admin', 'planificador'], legacy: true },
        { route: '/matrices-pad', label: 'Matrices PAD', icon: 'layout-grid', capacidades: ['sis_pe.instrumento.read'] },
        { route: '/indicadores', label: 'Indicadores', icon: 'chart-column', roles: ['superadmin', 'tecnico_admin', 'planificador'], legacy: true },
        { route: '/territorio', label: 'Territorio', icon: 'map-pin', roles: ['superadmin', 'tecnico_admin'], legacy: true },
        { route: '/sis-pe/seguimiento', label: 'Seguimiento estratégico', icon: 'activity', capacidades: ['sis_pe.instrumento.read'], pendiente: true },
        { route: '/evaluacion', label: 'Evaluación', icon: 'circle-check', roles: ['superadmin', 'tecnico_admin', 'evaluador'], legacy: true },
      ],
    },
    'sis-poa': {
      title: 'SIS-POA — Planificación Operativa',
      items: [
        { route: '/sis-poa/dashboard', label: 'Dashboard operativo', icon: 'gauge', capacidades: ['sis_poa.formulate'] },
        { route: '/sis-poa/poas', label: 'POA', icon: 'calendar-days', capacidades: ['sis_poa.formulate'] },
        { route: '/poau', label: 'POAU', icon: 'list-todo', roles: ['superadmin', 'tecnico_admin', 'jefe_ue', 'director'], legacy: true },
        { route: '/recursos', label: 'Recursos', icon: 'boxes', roles: ['superadmin', 'tecnico_admin'], legacy: true },
        { route: '/sis-poa/techos', label: 'Techos', icon: 'banknote', capacidades: ['sis_poa.formulate'] },
        { route: '/sis-poa/presupuesto', label: 'Presupuesto', icon: 'wallet', capacidades: ['sis_poa.formulate'] },
        { route: '/sis-poa/budget/gestion-fiscal', label: 'Gestión Fiscal', icon: 'coins', capacidades: ['sis_poa.formulate'] },
        { route: '/sis-poa/budget/techo-directivo', label: 'Techo Directivo', icon: 'chart-bar', capacidades: ['sis_poa.formulate'] },
        { route: '/sis-poa/budget/categorias-programaticas', label: 'Categorías Programáticas', icon: 'list-tree', capacidades: ['sis_poa.formulate'] },
        { route: '/sis-poa/budget/distribucion', label: 'Distribución Presupuestaria', icon: 'chart-pie', capacidades: ['sis_poa.formulate'] },
        { route: '/sis-poa/budget/distribucion-territorial', label: 'Distribución Territorial', icon: 'map', capacidades: ['sis_poa.budget.manage', 'sis_poa.formulate'] },
        { route: '/sis-poa/budget/importaciones', label: 'Importaciones', icon: 'download', capacidades: ['sis_poa.budget.import', 'sis_poa.formulate'] },
        { route: '/sis-poa/budget/reformulaciones', label: 'Reformulaciones', icon: 'refresh-cw', capacidades: ['sis_poa.budget.reform', 'sis_poa.formulate'] },
        { route: '/sis-poa/budget/auditoria', label: 'Auditoría', icon: 'scan-search', capacidades: ['sis_poa.budget.audit_read'] },
        { route: '/planificacion/formulacion', label: 'Formulación POA', icon: 'pen-line', roles: ['superadmin', 'tecnico_admin', 'planificador'], legacy: true },
        { route: '/seguimiento', label: 'Seguimiento', icon: 'activity', roles: ['superadmin', 'tecnico_admin', 'jefe_ue', 'director', 'tecnico'], legacy: true },
        { route: '/modificaciones', label: 'Modificaciones', icon: 'pencil-ruler', roles: ['superadmin', 'tecnico_admin'], legacy: true },
        { route: '/consolidacion', label: 'Consolidación', icon: 'layers', roles: ['superadmin', 'tecnico_admin'], legacy: true },
      ],
    },
    'sis-pro': {
      title: 'SIS-PRO — Ciclo del Proyecto',
      items: [
        { route: '/sis-pro/dashboard', label: 'Dashboard proyectos', icon: 'gauge', capacidades: ['sis_pro.project.read'] },
        { route: '/sis-pro/proyectos', label: 'Cartera', icon: 'briefcase', capacidades: ['sis_pro.project.read'] },
        { route: '/inversion', label: 'Proyectos de Inversión', icon: 'hard-hat', roles: ['superadmin', 'tecnico_admin', 'planificador'], legacy: true },
        { route: '/sis-pro/preinversion', label: 'Preinversión', icon: 'drafting-compass', capacidades: ['sis_pro.project.read'] },
        { route: '/sis-pro/preinversion/inventario', label: 'Inventario documental', icon: 'folder-open', capacidades: ['sis_pro.project.read'] },
        { route: '/sis-pro/formulacion', label: 'Formulación', icon: 'file-pen-line', capacidades: ['sis_pro.project.read'], pendiente: true },
        { route: '/sis-pro/contratacion', label: 'Contratación', icon: 'handshake', capacidades: ['sis_pro.project.read'], pendiente: true },
        { route: '/sis-pro/ejecucion', label: 'Ejecución', icon: 'play', capacidades: ['sis_pro.project.read'], pendiente: true },
        { route: '/sis-pro/supervision', label: 'Supervisión', icon: 'eye', capacidades: ['sis_pro.project.read'], pendiente: true },
        { route: '/sis-pro/seguimiento', label: 'Seguimiento', icon: 'activity', capacidades: ['sis_pro.project.read'], pendiente: true },
      ],
    },
  };

  /** Módulos de administración de la plataforma (§18.1 — se muestran siempre). */
  private administracionMenu: NavSection = {
    title: 'TRANSVERSAL',
    items: [
      { route: '/admin-usuarios', label: 'Usuarios y permisos', icon: 'users', roles: ['superadmin', 'tecnico_admin'] },
      { route: '/organizacion', label: 'Organización', icon: 'building-2', roles: ['superadmin', 'tecnico_admin'] },
      { route: '/gestion', label: 'Gestiones / periodos', icon: 'calendar-range', roles: ['superadmin', 'tecnico_admin'] },
      { route: '/catalogos', label: 'Catálogos', icon: 'book-open', roles: ['superadmin', 'tecnico_admin'] },
      { route: '/normativa', label: 'Normativa', icon: 'scroll-text', roles: ['superadmin', 'tecnico_admin'] },
      { route: '/documentos', label: 'Documentos', icon: 'folder', roles: ['superadmin', 'tecnico_admin'] },
      { route: '/auditoria', label: 'Auditoría', icon: 'scan-search', roles: ['superadmin', 'tecnico_admin'] },
      { route: '/reportes', label: 'Reportes', icon: 'chart-spline' },
      { route: '/territorio/mapa', label: 'Mapa inversiones', icon: 'map-pinned' },
      { route: '/workflow', label: 'Revisiones', icon: 'workflow', roles: ['superadmin', 'tecnico_admin', 'jefe_ue', 'director'] },
      { route: '/workflow/observaciones', label: 'Observaciones', icon: 'circle-alert', roles: ['superadmin', 'tecnico_admin', 'jefe_ue', 'director'] },
      { route: '/workflow/aprobaciones', label: 'Aprobaciones', icon: 'badge-check', roles: ['superadmin', 'tecnico_admin'] },
    ],
  };

  constructor(
    public auth: AuthService,
    private permissions: PermissionsService,
    private capabilities: CapabilitiesService,
    private router: Router,
    private cdr: ChangeDetectorRef,
  ) {}

  ngOnInit(): void {
    this.rebuildMenu();
    this.auth.user$.pipe(takeUntil(this.destroy$)).subscribe(() => {
      this.rebuildMenu();
      this.cdr.markForCheck();
    });
    // Menú dinámico: se reconstruye cuando llegan las capacidades (ADR-003)
    this.capabilities.cargadas$.pipe(takeUntil(this.destroy$)).subscribe(() => {
      this.rebuildMenu();
      this.cdr.markForCheck();
    });
    // Menú contextual por sistema (ventana de selección → módulos del SIS)
    this.router.events
      .pipe(
        takeUntil(this.destroy$),
        filter((e): e is NavigationEnd => e instanceof NavigationEnd),
      )
      .subscribe(() => {
        this.rebuildMenu();
        this.cdr.markForCheck();
      });
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
  }

  private rebuildMenu(): void {
    const url = this.router.url;
    this.sistemaActual = ['sis-pe', 'sis-poa', 'sis-pro'].find(
      s => url.startsWith(`/${s}`),
    ) ?? '';

    if (this.sistemaActual) {
      // Dentro de un sistema: selector + módulos del SIS (V2 y V1 insertados)
      const sistema = this.sistemasMenu[this.sistemaActual];
      const items = this.filtrarItems(sistema.items);
      this.visibleSections = [
        {
          title: 'SISTEMAS',
          items: [{ route: '/sistemas', label: 'Selección de sistemas', icon: 'home' }],
        },
        { title: sistema.title, items },
        this.administracionMenu,
      ];
      return;
    }

    this.visibleSections = [
      {
        title: 'PLATAFORMA',
        items: [
          { route: '/sistemas', label: 'Selección de sistemas', icon: 'home' },
          { route: '/dashboard', label: 'Dashboard', icon: 'gauge' },
          { route: '/notificaciones', label: 'Notificaciones', icon: 'bell' },
        ],
      },
      this.administracionMenu,
    ].filter(section => section.items.length > 0);
  }

  private filtrarItems(items: NavItem[]): NavItem[] {
    return items.filter(item => {
      // Cutover V2 (ADR-004 / WP-14): los módulos legacy se ocultan según la
      // palanca LEGACY_MENU_VISIBLE (ver core/config/cutover.config.ts).
      if (item.legacy && LEGACY_MENU_VISIBLE[item.route] === false) {
        return false;
      }
      if (item.capacidades?.length) {
        return this.permissions.hasAnyCapability(item.capacidades);
      }
      return !item.roles || this.permissions.hasAnyRole(item.roles);
    });
  }

  toggleCollapse(): void {
    this.collapsed = !this.collapsed;
    this.sidebarToggle.emit(this.collapsed);
  }

  toggleMobile(): void {
    this.mobileOpen = !this.mobileOpen;
  }
}

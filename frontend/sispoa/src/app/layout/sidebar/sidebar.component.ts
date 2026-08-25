import { Component, EventEmitter, Output, ChangeDetectionStrategy, ChangeDetectorRef, OnInit, OnDestroy } from '@angular/core';
import { NavigationEnd, Router } from '@angular/router';
import { Subject, filter, takeUntil } from 'rxjs';
import { AuthService } from '../../core/services/auth.service';
import { CapabilitiesService } from '../../core/services/capabilities.service';
import { GestionHabilitadaService } from '../../core/services/gestion-habilitada.service';
import { LEGACY_MENU_VISIBLE } from '../../core/config/cutover.config';

interface NavItem {
  route: string;
  label: string;
  icon: string;
  capacidades?: string[];
  /** Módulo sin UI propia todavía: la ruta resuelve a un placeholder. */
  pendiente?: boolean;
  /** Módulo con UI real pero funcionalidad aún no estabilizada.
   *  Manda sobre el chip V1: nada puede estar estabilizado y en beta a la vez. */
  beta?: boolean;
  /** Módulo heredado de la plataforma anterior, sujeto a LEGACY_MENU_VISIBLE.
   *  Es la palanca de cutover, no una marca de madurez: puede convivir con
   *  `beta` cuando el módulo todavía se está estabilizando. */
  legacy?: boolean;
  /** Módulo estabilizado (chip "V1") que no forma parte del cutover legacy.
   *  A diferencia de `legacy`, no queda sujeto a LEGACY_MENU_VISIBLE. */
  v1?: boolean;
}

interface NavSection {
  title: string;
  items: NavItem[];
}

/** Rutas de plataforma que pertenecen a un sistema (módulos legacy V1 y
 *  módulos V2 insertados en su SIS). El sidebar mantiene el contexto del
 *  sistema cuando la URL navega a estas rutas (fuera del prefijo /sis-*). */
const RUTAS_POR_SISTEMA: Record<string, string> = {
  // SIS-PE
  '/indicadores': 'sis-pe',
  '/territorio': 'sis-pe',
  '/matrices-pad': 'sis-pe',
  // SIS-POA
  '/priorizacion': 'sis-poa',
  '/poau': 'sis-poa',
  '/poau_recursos': 'sis-poa',
  '/planificacion': 'sis-poa',
  '/seguimiento': 'sis-poa',
  '/modificaciones': 'sis-poa',
  '/consolidacion': 'sis-poa',
};

const ADMIN_USUARIOS_CAPABILITIES = [
  'accounts.usuario.view',
  'accounts.rol.view',
  'accounts.capacidad.view',
  'accounts.solicitud.view',
];

const SIS_PE_INSTRUMENTOS_CAPABILITIES = [
  'sis_pe.instrumento.read',
  'sis_pe.instrumento.create',
  'sis_pe.approve',
];
const SIS_PE_PAD_CAPABILITIES = ['sis_pe.pad.view', 'sis_pe.pad.edit', 'sis_pe.pad.validate'];
const SIS_PE_PEI_CAPABILITIES = ['sis_pe.pei.view', 'sis_pe.pei.edit'];
const SIS_PE_ARTICULACION_CAPABILITIES = [
  'sis_pe.articulacion.view',
  'sis_pe.articulacion.edit',
  'sis_pe.articulacion.manage',
];
const SIS_PE_INDICADORES_CAPABILITIES = [
  'sis_pe.indicadores.view',
  'sis_pe.indicadores.edit',
  'sis_pe.indicadores.read',
  'sis_pe.indicadores.measure',
];
const SIS_PE_EVALUACION_CAPABILITIES = [
  'sis_pe.evaluacion.view',
  'sis_pe.evaluacion.edit',
  'sis_pe.approve',
];
const SIS_PE_ACCESS_CAPABILITIES = [
  ...SIS_PE_INSTRUMENTOS_CAPABILITIES,
  ...SIS_PE_PAD_CAPABILITIES,
  ...SIS_PE_PEI_CAPABILITIES,
  ...SIS_PE_ARTICULACION_CAPABILITIES,
  ...SIS_PE_INDICADORES_CAPABILITIES,
  ...SIS_PE_EVALUACION_CAPABILITIES,
];

const SIS_POA_POAU_CAPABILITIES = [
  'sis_poa.poau.view',
  'sis_poa.poau.create',
  'sis_poa.poau.edit',
  'sis_poa.poau.submit',
  'sis_poa.poau.review',
  'sis_poa.poau.approve',
];
const SIS_POA_POA_CAPABILITIES = [
  'sis_poa.poa.view',
  'sis_poa.poa.edit',
  'sis_poa.formulate',
  'sis_poa.approve',
];
const SIS_POA_TECHOS_CAPABILITIES = [
  'sis_poa.techos.view',
  'sis_poa.techos.edit',
  'sis_poa.budget.manage',
  'sis_poa.budget.validate',
  'sis_poa.budget.approve',
  'sis_poa.budget.reopen',
  'sis_poa.budget.audit_read',
];
const SIS_POA_DISTRIBUCIONES_CAPABILITIES = [
  'sis_poa.distribuciones.view',
  'sis_poa.distribuciones.edit',
  'sis_poa.budget.manage',
  'sis_poa.budget.import',
  'sis_poa.budget.reform',
];
const SIS_POA_PROGRAMACION_CAPABILITIES = [
  'sis_poa.programacion.view',
  'sis_poa.programacion.edit',
  'sis_poa.formulate',
];
const SIS_POA_SEGUIMIENTO_CAPABILITIES = [
  'sis_poa.seguimiento.view',
  'sis_poa.seguimiento.edit',
  'sis_poa.seguimiento.manage',
  'sis_poa.reportes.view',
];

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
        @if (collapsed) {
          <img class="brand-escudo" src="assets/images/escudo-sacaba.png"
               alt="Gobierno Autónomo Municipal de Sacaba" width="38" height="38">
        } @else {
          <img class="brand-logo" src="assets/images/logo-sacaba-horizontal.png"
               alt="Gobierno Autónomo Municipal de Sacaba — una ciudad con valor"
               width="800" height="252">
        }
        <button class="collapse-btn" (click)="toggleCollapse()"
          [attr.aria-label]="collapsed ? 'Expandir menú' : 'Contraer menú'"
          title="Colapsar menú">
          <lucide-angular [name]="collapsed ? 'chevron-right' : 'chevron-left'" [size]="16"></lucide-angular>
        </button>
      </div>
      <nav class="nav">
        @for (section of visibleSections; track section.title) {
          @if (!collapsed) {
            <div class="nav-label">{{ section.title }}</div>
          }
          @for (item of section.items; track item.route) {
            <a
              [routerLink]="item.route"
              routerLinkActive="active"
              class="nav-item"
              [title]="collapsed ? item.label : ''"
              [attr.aria-label]="item.label">
              <span class="ico"><lucide-angular [name]="item.icon" [size]="16"></lucide-angular></span>
              @if (!collapsed) {
                <span>{{ item.label }}</span>
                @if (item.pendiente || item.beta) {
                  <span class="tag" title="Módulo en desarrollo">Beta</span>
                } @else if (item.legacy || item.v1) {
                  <span class="tag ok" title="Módulo V1">V1</span>
                }
              }
            </a>
          }
        }
      </nav>
      @if (!collapsed) {
        <div class="sidebar-foot" [class.sin-gestion]="!gestion.hayGestion()">
          <div class="status-dot"></div>
          @if (gestion.gestion(); as habilitada) {
            <div>
              <strong>Gestión {{ habilitada.anio }}</strong>
              <span>{{ habilitada.estado_display }}</span>
            </div>
          } @else {
            <div>
              <strong>Sin gestión habilitada</strong>
              <span>SIS-POA no puede operar</span>
            </div>
          }
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
    /* El logo institucional lleva el texto en verde oscuro: sobre el verde
       profundo del sidebar desapareceria. Va sobre placa blanca, que ademas es
       como la marca se usa en papeleria. */
    .brand-logo {
      width: 100%; max-width: 196px; height: auto; display: block;
      background: #fff; border-radius: 8px; padding: 7px 9px;
    }
    .brand-escudo {
      width: 38px; height: 38px; border-radius: 50%; flex-shrink: 0;
      background: #fff; padding: 2px; object-fit: contain;
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
    /* El pie deja de ser un cartel pintado: si no hay gestión habilitada,
       SIS-POA está bloqueado y tiene que verse. */
    .sidebar-foot.sin-gestion .status-dot { background: var(--pip-warn); }
    .sidebar-foot.sin-gestion strong { color: #F0C674; }

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
   *  Tanto V2 como los módulos legacy se filtran por capacidades efectivas. */
  private sistemasMenu: Record<string, NavSection> = {
    'sis-pe': {
      title: 'SIS-PE — Planificación Estratégica',
      items: [
        { route: '/sis-pe/dashboard', label: 'Dashboard PE', icon: 'gauge', capacidades: SIS_PE_ACCESS_CAPABILITIES, beta: true },
        { route: '/sis-pe/instrumentos', label: 'Instrumentos', icon: 'file-text', capacidades: SIS_PE_INSTRUMENTOS_CAPABILITIES, beta: true },
        { route: '/sis-pe/diagnostico', label: 'Diagnóstico Integral', icon: 'clipboard-list', capacidades: SIS_PE_INSTRUMENTOS_CAPABILITIES, pendiente: true },
        { route: '/matrices-pad', label: 'PAD', icon: 'layout-grid', capacidades: SIS_PE_PAD_CAPABILITIES, legacy: true },
        { route: '/sis-pe/pei', label: 'PEI', icon: 'compass', capacidades: SIS_PE_PEI_CAPABILITIES, legacy: true },
        { route: '/indicadores', label: 'Indicadores', icon: 'chart-column', capacidades: SIS_PE_INDICADORES_CAPABILITIES, legacy: true },
        { route: '/territorio', label: 'Territorialización de Acciones', icon: 'map-pin', capacidades: SIS_PE_ARTICULACION_CAPABILITIES, legacy: true },
        { route: '/sis-pe/seguimiento-evaluacion', label: 'Seguimiento y Evaluación', icon: 'activity', capacidades: SIS_PE_EVALUACION_CAPABILITIES, pendiente: true },
      ],
    },
    'sis-poa': {
      title: 'SIS-POA — Planificación Operativa',
      items: [
        { route: '/sis-poa/dashboard', label: 'Dashboard POA', icon: 'gauge', capacidades: SIS_POA_POA_CAPABILITIES, beta: true },
        { route: '/sis-poa/budget/gestion-fiscal', label: 'Habilitación de Gestión', icon: 'calendar-check', capacidades: SIS_POA_TECHOS_CAPABILITIES, v1: true },
        { route: '/sis-poa/presupuesto-recursos', label: 'Presupuesto General de Recursos', icon: 'banknote', capacidades: SIS_POA_DISTRIBUCIONES_CAPABILITIES, v1: true },
        { route: '/sis-poa/presupuesto-gastos', label: 'Presupuesto General de Gastos', icon: 'wallet', capacidades: SIS_POA_DISTRIBUCIONES_CAPABILITIES, v1: true },
        { route: '/priorizacion/actas', label: 'Priorización POA', icon: 'clipboard-list', capacidades: SIS_POA_POA_CAPABILITIES, v1: true },
        { route: '/sis-poa/poas', label: 'POA', icon: 'calendar-days', capacidades: SIS_POA_POA_CAPABILITIES, legacy: true },
        { route: '/sis-poa/poaus', label: 'POAU', icon: 'list-tree', capacidades: SIS_POA_POAU_CAPABILITIES, v1: true },
        { route: '/poau', label: 'POAU (Físico)', icon: 'list-todo', capacidades: SIS_POA_PROGRAMACION_CAPABILITIES, legacy: true },
        { route: '/poau_recursos', label: 'POAU (Recursos)', icon: 'boxes', capacidades: SIS_POA_DISTRIBUCIONES_CAPABILITIES, legacy: true },
        { route: '/sis-poa/seguimiento', label: 'Seguimiento y Evaluación', icon: 'activity', capacidades: SIS_POA_SEGUIMIENTO_CAPABILITIES, beta: true },
      ],
    },
  };

  /** Única entrada transversal del gestor IAM, gobernada por capacidades. */
  private administracionMenu: NavSection = {
    title: 'TRANSVERSAL',
    items: [
      { route: '/admin-usuarios', label: 'Usuarios y permisos', icon: 'users', capacidades: ADMIN_USUARIOS_CAPABILITIES },
    ],
  };

  constructor(
    public auth: AuthService,
    private capabilities: CapabilitiesService,
    public gestion: GestionHabilitadaService,
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
    // El pie muestra la gestión habilitada apenas se conoce (ADR-007).
    this.gestion.cargada$.pipe(takeUntil(this.destroy$)).subscribe(() => {
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
    // Prefijos V2 (/sis-*) primero; luego módulos de plataforma que
    // pertenecen a un sistema (legacy V1 o V2 insertado en su SIS).
    const primerSegmento = '/' + (url.split('?')[0].split('/')[1] ?? '');
    this.sistemaActual =
      ['sis-pe', 'sis-poa'].find(s => url.startsWith(`/${s}`)) ??
      RUTAS_POR_SISTEMA[primerSegmento] ??
      '';

    if (this.sistemaActual) {
      // Dentro de un sistema: selector + módulos del SIS (V2 y V1 insertados)
      const sistema = this.sistemasMenu[this.sistemaActual];
      const items = this.filtrarItems(sistema.items);
      const administracion = this.seccionFiltrada(this.administracionMenu);
      this.visibleSections = [
        {
          title: 'SISTEMAS',
          items: [{ route: '/sistemas', label: 'Selección de sistemas', icon: 'home' }],
        },
        { title: sistema.title, items },
        ...(administracion ? [administracion] : []),
      ].filter(section => section.items.length > 0);
      return;
    }

    const administracion = this.seccionFiltrada(this.administracionMenu);
    this.visibleSections = [
      {
        title: 'PLATAFORMA',
        items: [
          { route: '/sistemas', label: 'Selección de sistemas', icon: 'home' },
          { route: '/dashboard', label: 'Dashboard', icon: 'gauge' },
          { route: '/notificaciones', label: 'Notificaciones', icon: 'bell' },
        ],
      },
      ...(administracion ? [administracion] : []),
    ].filter(section => section.items.length > 0);
  }

  private seccionFiltrada(section: NavSection): NavSection | null {
    const items = this.filtrarItems(section.items);
    return items.length ? { ...section, items } : null;
  }

  private filtrarItems(items: NavItem[]): NavItem[] {
    return items.filter(item => {
      // Cutover V2 (ADR-004 / WP-14): los módulos legacy se ocultan según la
      // palanca LEGACY_MENU_VISIBLE (ver core/config/cutover.config.ts).
      if (item.legacy && LEGACY_MENU_VISIBLE[item.route] === false) {
        return false;
      }
      return !item.capacidades?.length || this.capabilities.tieneAlguna(item.capacidades);
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

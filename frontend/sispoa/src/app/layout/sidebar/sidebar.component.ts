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
    <aside class="sidebar" [class.sidebar-collapsed]="collapsed" [class.sidebar-open]="mobileOpen">
      <div class="sidebar-overlay" *ngIf="mobileOpen" (click)="toggleMobile()"></div>
      <div class="sidebar-header">
        <div class="logo">
          <span class="logo-icon">G</span>
          <div class="logo-text" *ngIf="!collapsed">
            <strong>SISPOA</strong>
            <small>Sacaba</small>
          </div>
        </div>
        <button class="collapse-btn" (click)="toggleCollapse()" title="Colapsar menú">
          <span class="collapse-icon">{{ collapsed ? '»' : '«' }}</span>
        </button>
      </div>
      <nav class="sidebar-nav">
        <ng-container *ngFor="let section of visibleSections">
          <div class="nav-section" *ngIf="!collapsed">{{ section.title }}</div>
          <a *ngFor="let item of section.items"
             [routerLink]="item.route"
             routerLinkActive="active"
             class="nav-item"
             [title]="collapsed ? item.label : ''">
            <span class="nav-icon">{{ item.icon }}</span>
            <span class="nav-label" *ngIf="!collapsed">{{ item.label }}</span>
            <span class="nav-pendiente" *ngIf="item.pendiente && !collapsed" title="Módulo en desarrollo">en desarrollo</span>
            <span class="nav-pendiente nav-v1" *ngIf="item.legacy && !collapsed" title="Módulo V1 (legacy)">V1</span>
          </a>
        </ng-container>
      </nav>
      <div class="sidebar-footer" *ngIf="!collapsed">
        <span class="version">v1.0.0</span>
      </div>
    </aside>
  `,
  styles: [`
    .sidebar {
      position: fixed; left: 0; top: 0; bottom: 0; width: 260px;
      background: var(--sidebar-bg); color: var(--sidebar-text);
      display: flex; flex-direction: column; z-index: 100; overflow-y: auto;
      transition: width 0.2s ease;
    }
    .sidebar-collapsed { width: 64px; }
    .sidebar-header {
      padding: 1.25rem; border-bottom: 1px solid rgba(255,255,255,0.1);
      display: flex; align-items: center; justify-content: space-between;
    }
    .logo { display: flex; align-items: center; gap: 0.75rem; }
    .logo-icon {
      width: 40px; height: 40px; min-width: 40px; background: var(--accent); color: white;
      border-radius: 8px; display: flex; align-items: center; justify-content: center;
      font-weight: 800; font-size: 1.25rem;
    }
    .logo-text strong { display: block; color: white; font-size: 1.1rem; }
    .logo-text small { color: var(--sidebar-text); font-size: 0.75rem; }
    .collapse-btn {
      background: none; border: none; color: var(--sidebar-text); cursor: pointer;
      padding: 0.25rem; border-radius: 4px; font-size: 1rem; opacity: 0.6;
      transition: opacity 0.15s;
    }
    .collapse-btn:hover { opacity: 1; }
    .sidebar-nav { flex: 1; padding: 0.5rem; }
    .nav-section {
      padding: 0.75rem 0.75rem 0.25rem; font-size: 0.625rem;
      text-transform: uppercase; letter-spacing: 0.1em; opacity: 0.5;
    }
    .nav-item {
      display: flex; align-items: center; gap: 0.625rem;
      padding: 0.5rem 0.75rem; border-radius: 6px; color: var(--sidebar-text);
      transition: all 0.15s; cursor: pointer; font-size: 0.8125rem;
      text-decoration: none;
    }
    .nav-item:hover { background: rgba(255,255,255,0.08); color: white; }
    .nav-item.active { background: var(--primary-light); color: white; font-weight: 600; }
    .nav-icon { width: 18px; text-align: center; font-size: 0.875rem; }
    .nav-label { white-space: nowrap; }
    .nav-pendiente {
      margin-left: auto; font-size: 0.5625rem; text-transform: uppercase;
      background: rgba(255,255,255,0.12); color: var(--sidebar-text);
      padding: 0.0625rem 0.375rem; border-radius: 4px; letter-spacing: 0.05em;
    }
    .nav-pendiente.nav-v1 { background: rgba(255,193,7,0.18); color: #FFD54F; }
    .sidebar-footer { padding: 1rem 1.25rem; border-top: 1px solid rgba(255,255,255,0.1); }
    .version { font-size: 0.75rem; opacity: 0.5; }
    .sidebar-overlay { display: none; }

    @media (max-width: 1024px) {
      .sidebar {
        transform: translateX(-100%);
        transition: transform 0.3s ease;
      }
      .sidebar.sidebar-open {
        transform: translateX(0);
      }
      .sidebar-overlay {
        display: block; position: fixed; top: 0; left: 0; right: 0; bottom: 0;
        background: rgba(0,0,0,0.5); z-index: -1;
      }
      .sidebar-collapsed { width: 260px; }
    }

    @media (min-width: 769px) and (max-width: 1280px) {
      .sidebar { width: 64px; }
      .sidebar .nav-label { display: none; }
      .sidebar .sidebar-footer { display: none; }
      .sidebar .collapse-btn { display: none; }
      .sidebar .nav-section { display: none; }
      .sidebar .nav-item { justify-content: center; padding: 0.625rem; }
      .sidebar .nav-icon { width: auto; }
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
        { route: '/sis-pe/dashboard', label: 'Dashboard estratégico', icon: '◉', capacidades: ['sis_pe.instrumento.read'] },
        { route: '/sis-pe/instrumentos', label: 'Instrumentos', icon: '▤', capacidades: ['sis_pe.instrumento.read'] },
        { route: '/sis-pe/diagnostico', label: 'Diagnóstico', icon: '▤', capacidades: ['sis_pe.instrumento.read'], pendiente: true },
        { route: '/articulador', label: 'PAD', icon: '▤', roles: ['superadmin', 'tecnico_admin', 'planificador'], legacy: true },
        { route: '/sis-pe/pei', label: 'PEI', icon: '▤', capacidades: ['sis_pe.instrumento.read'], pendiente: true },
        { route: '/articulacion', label: 'Articulación', icon: '⇄', roles: ['superadmin', 'tecnico_admin', 'planificador'], legacy: true },
        { route: '/indicadores', label: 'Indicadores', icon: '⊡', roles: ['superadmin', 'tecnico_admin', 'planificador'], legacy: true },
        { route: '/territorio', label: 'Territorio', icon: '◈', roles: ['superadmin', 'tecnico_admin'], legacy: true },
        { route: '/sis-pe/seguimiento', label: 'Seguimiento estratégico', icon: '◷', capacidades: ['sis_pe.instrumento.read'], pendiente: true },
        { route: '/evaluacion', label: 'Evaluación', icon: '✓', roles: ['superadmin', 'tecnico_admin', 'evaluador'], legacy: true },
      ],
    },
    'sis-poa': {
      title: 'SIS-POA — Planificación Operativa',
      items: [
        { route: '/sis-poa/dashboard', label: 'Dashboard operativo', icon: '◉', capacidades: ['sis_poa.formulate'] },
        { route: '/sis-poa/poas', label: 'POA', icon: '▤', capacidades: ['sis_poa.formulate'] },
        { route: '/poau', label: 'POAU', icon: '▤', roles: ['superadmin', 'tecnico_admin', 'jefe_ue', 'director'], legacy: true },
        { route: '/recursos', label: 'Recursos', icon: '⊞', roles: ['superadmin', 'tecnico_admin'], legacy: true },
        { route: '/sis-poa/techos', label: 'Techos', icon: '⊡', capacidades: ['sis_poa.formulate'] },
        { route: '/sis-poa/presupuesto', label: 'Presupuesto', icon: '⊞', capacidades: ['sis_poa.formulate'] },
        { route: '/sis-poa/budget/gestion-fiscal', label: 'Gestión Fiscal', icon: '🗓️', capacidades: ['sis_poa.formulate'] },
        { route: '/sis-poa/budget/techo-directivo', label: 'Techo Directivo', icon: '⊡', capacidades: ['sis_poa.formulate'] },
        { route: '/planificacion/formulacion', label: 'Formulación POA', icon: '✎', roles: ['superadmin', 'tecnico_admin', 'planificador'], legacy: true },
        { route: '/seguimiento', label: 'Seguimiento', icon: '◷', roles: ['superadmin', 'tecnico_admin', 'jefe_ue', 'director', 'tecnico'], legacy: true },
        { route: '/modificaciones', label: 'Modificaciones', icon: '✎', roles: ['superadmin', 'tecnico_admin'], legacy: true },
        { route: '/consolidacion', label: 'Consolidación', icon: '⊞', roles: ['superadmin', 'tecnico_admin'], legacy: true },
      ],
    },
    'sis-pro': {
      title: 'SIS-PRO — Ciclo del Proyecto',
      items: [
        { route: '/sis-pro/dashboard', label: 'Dashboard proyectos', icon: '◉', capacidades: ['sis_pro.project.read'] },
        { route: '/sis-pro/proyectos', label: 'Cartera', icon: '▤', capacidades: ['sis_pro.project.read'] },
        { route: '/inversion', label: 'Proyectos de Inversión', icon: '▤', roles: ['superadmin', 'tecnico_admin', 'planificador'], legacy: true },
        { route: '/sis-pro/preinversion', label: 'Preinversión', icon: '▤', capacidades: ['sis_pro.project.read'] },
        { route: '/sis-pro/preinversion/inventario', label: 'Inventario documental', icon: '📚', capacidades: ['sis_pro.project.read'] },
        { route: '/sis-pro/formulacion', label: 'Formulación', icon: '▤', capacidades: ['sis_pro.project.read'], pendiente: true },
        { route: '/sis-pro/contratacion', label: 'Contratación', icon: '⇄', capacidades: ['sis_pro.project.read'], pendiente: true },
        { route: '/sis-pro/ejecucion', label: 'Ejecución', icon: '◷', capacidades: ['sis_pro.project.read'], pendiente: true },
        { route: '/sis-pro/supervision', label: 'Supervisión', icon: '◈', capacidades: ['sis_pro.project.read'], pendiente: true },
        { route: '/sis-pro/seguimiento', label: 'Seguimiento', icon: '◷', capacidades: ['sis_pro.project.read'], pendiente: true },
      ],
    },
  };

  /** Módulos de administración de la plataforma (§18.1 — se muestran siempre). */
  private administracionMenu: NavSection = {
    title: 'PLATAFORMA / ADMINISTRACIÓN',
    items: [
      { route: '/admin-usuarios', label: 'Usuarios y permisos', icon: '👤', roles: ['superadmin', 'tecnico_admin'] },
      { route: '/organizacion', label: 'Organización', icon: '🏢', roles: ['superadmin', 'tecnico_admin'] },
      { route: '/gestion', label: 'Gestiones / periodos', icon: '🗓️', roles: ['superadmin', 'tecnico_admin'] },
      { route: '/catalogos', label: 'Catálogos', icon: '📚', roles: ['superadmin', 'tecnico_admin'] },
      { route: '/normativa', label: 'Normativa', icon: '📜', roles: ['superadmin', 'tecnico_admin'] },
      { route: '/documentos', label: 'Documentos', icon: '📁', roles: ['superadmin', 'tecnico_admin'] },
      { route: '/auditoria', label: 'Auditoría', icon: '🔍', roles: ['superadmin', 'tecnico_admin'] },
      { route: '/reportes', label: 'Reportes', icon: '📈' },
      { route: '/territorio/mapa', label: 'Mapa inversiones', icon: '🗺️' },
      { route: '/workflow', label: 'Revisiones', icon: '⇄', roles: ['superadmin', 'tecnico_admin', 'jefe_ue', 'director'] },
      { route: '/workflow/observaciones', label: 'Observaciones', icon: '◈', roles: ['superadmin', 'tecnico_admin', 'jefe_ue', 'director'] },
      { route: '/workflow/aprobaciones', label: 'Aprobaciones', icon: '✓', roles: ['superadmin', 'tecnico_admin'] },
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
          items: [{ route: '/sistemas', label: 'Selección de sistemas', icon: '🏠' }],
        },
        { title: sistema.title, items },
        this.administracionMenu,
      ];
      return;
    }

    this.visibleSections = [
      {
        title: 'PRINCIPAL',
        items: [
          { route: '/sistemas', label: 'Selección de sistemas', icon: '🏠' },
          { route: '/dashboard', label: 'Dashboard', icon: '◉' },
          { route: '/notificaciones', label: 'Notificaciones', icon: '🔔' },
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

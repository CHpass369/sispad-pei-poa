import { Component, EventEmitter, Output, ChangeDetectionStrategy, ChangeDetectorRef } from '@angular/core';
import { AuthService } from '../../core/services/auth.service';
import { PermissionsService } from '../../core/services/permissions.service';

interface NavItem {
  route: string;
  label: string;
  icon: string;
  roles?: string[];
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
export class SidebarComponent {
  @Output() sidebarToggle = new EventEmitter<boolean>();

  collapsed = false;
  mobileOpen = false;

  private allSections: NavSection[] = [
    {
      title: 'PRINCIPAL',
      items: [
        { route: '/dashboard', label: 'Dashboard', icon: '◉' },
        { route: '/notificaciones', label: 'Notificaciones', icon: '⊕' },
      ],
    },
    {
      title: 'FORMULACIÓN',
      items: [
        { route: '/articulacion', label: 'Articulación PAD-PEI-POA', icon: '🔗', roles: ['superadmin', 'tecnico_admin', 'planificador'] },
        { route: '/articulador', label: 'ARTICULADOR PAD', icon: '◈', roles: ['superadmin', 'tecnico_admin', 'planificador'] },
        { route: '/poau', label: 'POAU por Unidad', icon: '◷', roles: ['superadmin', 'tecnico_admin', 'jefe_ue', 'director'] },
        { route: '/planificacion/formulacion', label: 'Formulación POA', icon: '✎', roles: ['superadmin', 'tecnico_admin', 'planificador'] },
        { route: '/indicadores', label: 'Indicadores', icon: '⊡', roles: ['superadmin', 'tecnico_admin', 'planificador'] },
      ],
    },
    {
      title: 'PRESUPUESTO',
      items: [
        { route: '/presupuesto', label: 'Presupuesto', icon: '⊞', roles: ['superadmin', 'tecnico_admin', 'planificador'] },
        { route: '/techos', label: 'Techos', icon: '⊡', roles: ['superadmin', 'tecnico_admin', 'planificador'] },
        { route: '/inversion', label: 'Proyectos Inversión', icon: '◉', roles: ['superadmin', 'tecnico_admin', 'planificador'] },
      ],
    },
    {
      title: 'SEGUIMIENTO',
      items: [
        { route: '/seguimiento', label: 'Seguimiento', icon: '◷', roles: ['superadmin', 'tecnico_admin', 'jefe_ue', 'director', 'tecnico'] },
        { route: '/modificaciones', label: 'Modificaciones', icon: '✎', roles: ['superadmin', 'tecnico_admin'] },
        { route: '/consolidacion', label: 'Consolidación', icon: '⊞', roles: ['superadmin', 'tecnico_admin'] },
      ],
    },
    {
      title: 'REVISIÓN',
      items: [
        { route: '/workflow', label: 'Revisiones', icon: '◷', roles: ['superadmin', 'tecnico_admin', 'jefe_ue', 'director'] },
        { route: '/workflow/observaciones', label: 'Observaciones', icon: '◈', roles: ['superadmin', 'tecnico_admin', 'jefe_ue', 'director'] },
        { route: '/workflow/aprobaciones', label: 'Aprobaciones', icon: '✓', roles: ['superadmin', 'tecnico_admin'] },
      ],
    },
    {
      title: 'EVALUACIÓN',
      items: [
        { route: '/evaluacion', label: 'Evaluación', icon: '◆', roles: ['superadmin', 'tecnico_admin', 'evaluador'] },
      ],
    },
    {
      title: 'ADMINISTRACIÓN',
      items: [
        { route: '/gestion', label: 'Gestión Fiscal', icon: '◷', roles: ['superadmin', 'tecnico_admin'] },
        { route: '/organizacion', label: 'Organización', icon: '◈', roles: ['superadmin', 'tecnico_admin'] },
        { route: '/catalogos', label: 'Catálogos', icon: '⊞', roles: ['superadmin', 'tecnico_admin'] },
        { route: '/admin-usuarios', label: 'Usuarios', icon: '⊕', roles: ['superadmin', 'tecnico_admin'] },
        { route: '/documentos', label: 'Documentos', icon: '📄', roles: ['superadmin', 'tecnico_admin'] },
        { route: '/normativa', label: 'Normativa', icon: '⚖', roles: ['superadmin', 'tecnico_admin'] },
        { route: '/recursos', label: 'Recursos', icon: '☰', roles: ['superadmin', 'tecnico_admin'] },
      ],
    },
    {
      title: 'REPORTES',
      items: [
        { route: '/reportes', label: 'Reportes', icon: '⊡' },
        { route: '/territorio/mapa', label: 'Mapa Inversiones', icon: '◉' },
        { route: '/auditoria', label: 'Auditoría', icon: '◈', roles: ['superadmin', 'tecnico_admin'] },
      ],
    },
  ];

  visibleSections: NavSection[] = [];

  constructor(
    public auth: AuthService,
    private permissions: PermissionsService,
    private cdr: ChangeDetectorRef,
  ) {
    this.rebuildMenu();
    this.auth.user$.subscribe(() => {
      this.rebuildMenu();
      this.cdr.markForCheck();
    });
  }

  private rebuildMenu(): void {
    this.visibleSections = this.allSections
      .map(section => ({
        ...section,
        items: section.items.filter(item =>
          !item.roles || this.permissions.hasAnyRole(item.roles),
        ),
      }))
      .filter(section => section.items.length > 0);
  }

  toggleCollapse(): void {
    this.collapsed = !this.collapsed;
    this.sidebarToggle.emit(this.collapsed);
  }

  toggleMobile(): void {
    this.mobileOpen = !this.mobileOpen;
  }
}

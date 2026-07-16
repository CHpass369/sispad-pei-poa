import { Component } from '@angular/core';
import { AuthService } from '../../core/services/auth.service';

@Component({
  standalone: false,
  selector: 'app-sidebar',
  template: `
    <aside class="sidebar">
      <div class="sidebar-header">
        <div class="logo">
          <span class="logo-icon">G</span>
          <div class="logo-text">
            <strong>SISPOA</strong>
            <small>Sacaba</small>
          </div>
        </div>
      </div>
      <nav class="sidebar-nav">
        <div class="nav-section">PRINCIPAL</div>
        <a routerLink="/dashboard" routerLinkActive="active" class="nav-item">
          <span class="nav-icon">◉</span>Dashboard
        </a>

        <div class="nav-section">FORMULACIÓN</div>
        <a routerLink="/articulador" routerLinkActive="active" class="nav-item">
          <span class="nav-icon">◈</span>ARTICULADOR PAD
        </a>
        <a routerLink="/poau" routerLinkActive="active" class="nav-item">
          <span class="nav-icon">◷</span>POAU por Unidad
        </a>
        <a routerLink="/planificacion/formulacion" routerLinkActive="active" class="nav-item">
          <span class="nav-icon">✎</span>Formulación POA
        </a>
        <a routerLink="/indicadores" routerLinkActive="active" class="nav-item">
          <span class="nav-icon">⊡</span>Indicadores
        </a>
        <a routerLink="/indicadores" routerLinkActive="active" class="nav-item">
          <span class="nav-icon">⊡</span>Indicadores
        </a>

        <div class="nav-section">PRESUPUESTO</div>
        <a routerLink="/presupuesto" routerLinkActive="active" class="nav-item">
          <span class="nav-icon">⊞</span>Presupuesto
        </a>
        <a routerLink="/techos" routerLinkActive="active" class="nav-item">
          <span class="nav-icon">⊡</span>Techos
        </a>
        <a routerLink="/inversion" routerLinkActive="active" class="nav-item">
          <span class="nav-icon">◉</span>Proyectos Inversión
        </a>

        <div class="nav-section">REVISIÓN</div>
        <a routerLink="/workflow" routerLinkActive="active" class="nav-item">
          <span class="nav-icon">◷</span>Revisiones
        </a>
        <a routerLink="/workflow/observaciones" routerLinkActive="active" class="nav-item">
          <span class="nav-icon">◈</span>Observaciones
        </a>
        <a routerLink="/workflow/aprobaciones" routerLinkActive="active" class="nav-item">
          <span class="nav-icon">✓</span>Aprobaciones
        </a>

        <div class="nav-section">ADMINISTRACIÓN</div>
        <a routerLink="/gestion" routerLinkActive="active" class="nav-item">
          <span class="nav-icon">◷</span>Gestión Fiscal
        </a>
        <a routerLink="/organizacion" routerLinkActive="active" class="nav-item">
          <span class="nav-icon">◈</span>Organización
        </a>
        <a routerLink="/catalogos" routerLinkActive="active" class="nav-item">
          <span class="nav-icon">⊞</span>Catálogos
        </a>

        <div class="nav-section">REPORTES</div>
        <a routerLink="/reportes" routerLinkActive="active" class="nav-item">
          <span class="nav-icon">⊡</span>Reportes
        </a>
        <a routerLink="/territorio/mapa" routerLinkActive="active" class="nav-item">
          <span class="nav-icon">◉</span>Mapa Inversiones
        </a>
        <a routerLink="/auditoria" routerLinkActive="active" class="nav-item">
          <span class="nav-icon">◈</span>Auditoría
        </a>
      </nav>
      <div class="sidebar-footer">
        <span class="version">v1.0.0</span>
      </div>
    </aside>
  `,
  styles: [`
    .sidebar {
      position: fixed; left: 0; top: 0; bottom: 0; width: 260px;
      background: var(--sidebar-bg); color: var(--sidebar-text);
      display: flex; flex-direction: column; z-index: 100; overflow-y: auto;
    }
    .sidebar-header { padding: 1.25rem; border-bottom: 1px solid rgba(255,255,255,0.1); }
    .logo { display: flex; align-items: center; gap: 0.75rem; }
    .logo-icon {
      width: 40px; height: 40px; background: var(--accent); color: white;
      border-radius: 8px; display: flex; align-items: center; justify-content: center;
      font-weight: 800; font-size: 1.25rem;
    }
    .logo-text strong { display: block; color: white; font-size: 1.1rem; }
    .logo-text small { color: var(--sidebar-text); font-size: 0.75rem; }
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
    .sidebar-footer { padding: 1rem 1.25rem; border-top: 1px solid rgba(255,255,255,0.1); }
    .version { font-size: 0.75rem; opacity: 0.5; }
  `]
})
export class SidebarComponent {
  constructor(public auth: AuthService) {}
}

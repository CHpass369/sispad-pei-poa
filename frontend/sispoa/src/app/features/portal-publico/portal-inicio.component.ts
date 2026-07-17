import { Component, OnInit } from '@angular/core';
import { PortalPublicoService, EstadisticasResumen } from './portal-publico.service';

@Component({
  standalone: false,
  selector: 'app-portal-inicio',
  template: `
    <div class="portal-inicio">
      <div class="hero-section">
        <div class="hero-content">
          <div class="hero-logo">
            <div class="logo-placeholder">SISPAD</div>
          </div>
          <h1>Sistema de Planificación y Presupuesto</h1>
          <p class="hero-subtitle">PEI - PAD - POA - POAU</p>
          <p class="hero-desc">Plataforma institucional para la gestión de la planificación estratégica, presupuestaria y de seguimiento.</p>
        </div>
      </div>

      <div class="stats-section" *ngIf="!cargando">
        <div class="stats-grid">
          <div class="stat-card">
            <div class="stat-icon">📋</div>
            <div class="stat-valor">{{ resumen.total_planes || 0 }}</div>
            <div class="stat-label">Planes Registrados</div>
          </div>
          <div class="stat-card">
            <div class="stat-icon">💰</div>
            <div class="stat-valor">Bs {{ resumen.total_presupuesto | number:'1.0-0' }}</div>
            <div class="stat-label">Presupuesto Total</div>
          </div>
          <div class="stat-card">
            <div class="stat-icon">📊</div>
            <div class="stat-valor">{{ resumen.total_indicadores || 0 }}</div>
            <div class="stat-label">Indicadores</div>
          </div>
          <div class="stat-card">
            <div class="stat-icon">✅</div>
            <div class="stat-valor">{{ resumen.indicadores_cumplidos || 0 }}</div>
            <div class="stat-label">Indicadores Cumplidos</div>
          </div>
        </div>
      </div>

      <div class="info-section">
        <div class="info-card">
          <h3>Planificación Estratégica</h3>
          <p>Gestión integral del Plan Estratégico Institucional (PEI), Plan de Desarrollo Sectorial (PDESA), Plan de Transversalización del Desarrollo Institucional (PTDI) y Plan de Acción (PAD).</p>
          <a routerLink="/portal/planes" class="btn btn-primary">Ver Planes</a>
        </div>
        <div class="info-card">
          <h3>Indicadores</h3>
          <p>Seguimiento y monitoreo de indicadores de desempeño institucional con metas y resultados verificables.</p>
          <a routerLink="/portal/indicadores" class="btn btn-primary">Ver Indicadores</a>
        </div>
        <div class="info-card">
          <h3>Estadísticas</h3>
          <p>Dashboards y reportes estadísticos de ejecución presupuestaria por tipo, sector y período.</p>
          <a routerLink="/portal/estadisticas" class="btn btn-primary">Ver Estadísticas</a>
        </div>
      </div>
    </div>
  `,
  styles: [`
    .hero-section { background: linear-gradient(135deg, var(--primary, #1a237e) 0%, var(--primary-dark, #0d1642) 100%); color: white; padding: 3rem 2rem; text-align: center; border-radius: 12px; margin-bottom: 2rem; }
    .hero-content { max-width: 700px; margin: 0 auto; }
    .logo-placeholder { display: inline-block; background: rgba(255,255,255,0.15); padding: 1rem 2rem; border-radius: 12px; font-size: 1.5rem; font-weight: 800; letter-spacing: 2px; margin-bottom: 1.5rem; border: 1px solid rgba(255,255,255,0.2); }
    .hero-section h1 { font-size: 1.75rem; margin-bottom: 0.5rem; }
    .hero-subtitle { font-size: 1rem; opacity: 0.9; margin-bottom: 1rem; letter-spacing: 1px; }
    .hero-desc { font-size: 0.875rem; opacity: 0.8; line-height: 1.6; }
    .stats-section { margin-bottom: 2rem; }
    .stats-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 1rem; }
    .stat-card { background: var(--surface); border: 1px solid var(--border); border-radius: 8px; padding: 1.5rem; text-align: center; }
    .stat-icon { font-size: 1.5rem; margin-bottom: 0.5rem; }
    .stat-valor { font-size: 1.5rem; font-weight: 700; color: var(--primary); }
    .stat-label { font-size: 0.8125rem; color: var(--text-secondary); margin-top: 0.25rem; }
    .info-section { display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 1rem; }
    .info-card { background: var(--surface); border: 1px solid var(--border); border-radius: 8px; padding: 1.5rem; }
    .info-card h3 { font-size: 1.125rem; margin-bottom: 0.5rem; }
    .info-card p { font-size: 0.875rem; color: var(--text-secondary); line-height: 1.5; margin-bottom: 1rem; }
    .btn { display: inline-flex; align-items: center; padding: 0.5rem 1rem; border-radius: 6px; border: none; font-size: 0.875rem; font-weight: 600; cursor: pointer; text-decoration: none; }
    .btn-primary { background: var(--primary); color: white; }
    .btn-primary:hover { background: var(--primary-dark, #303F9F); }
  `]
})
export class PortalInicioComponent implements OnInit {
  resumen: EstadisticasResumen = {};
  cargando = true;

  constructor(private portalService: PortalPublicoService) {}

  ngOnInit(): void {
    this.portalService.obtenerResumenEjecucion().subscribe({
      next: (data) => {
        this.resumen = {
          total_planes: data.total_programas,
          total_presupuesto: data.total_presupuesto,
          total_indicadores: 0,
          indicadores_cumplidos: 0,
        };
        this.cargando = false;
      },
      error: () => {
        this.cargando = false;
      },
    });
  }
}

import { Component, OnInit } from '@angular/core';
import { SisProService } from './sis-pro.service';

@Component({
  standalone: false,
  selector: 'app-sis-pro-dashboard',
  template: `
    <div class="page-header">
      <h2>SIS-PRO — Dashboard de Proyectos</h2>
      <p class="text-secondary">Sistema de Gestión del Ciclo del Proyecto (V2)</p>
    </div>
    @if (cargando) {
      <div class="loading">Cargando indicadores...</div>
    }
    @if (error) {
      <div class="alert alert-error">{{ error }}</div>
    }
    @if (!cargando) {
      <div class="stats-grid">
        <div class="card stat-card">
          <div class="stat-icon">🚧</div>
          <div class="stat-value">{{ total }}</div>
          <div class="stat-label">Proyectos</div>
        </div>
        <div class="card stat-card">
          <div class="stat-icon">📐</div>
          <div class="stat-value">{{ enPreinversion }}</div>
          <div class="stat-label">En preinversión</div>
        </div>
        <div class="card stat-card">
          <div class="stat-icon">🔨</div>
          <div class="stat-value">{{ enEjecucion }}</div>
          <div class="stat-label">En ejecución</div>
        </div>
        <div class="card stat-card">
          <div class="stat-icon">✅</div>
          <div class="stat-value">{{ cerrados }}</div>
          <div class="stat-label">Cerrados</div>
        </div>
      </div>
    }
    @if (!cargando) {
      <div class="quick-actions">
        <a routerLink="/sis-pro/proyectos" class="btn btn-primary">Cartera de proyectos</a>
      </div>
    }
    `,
  styles: [`
    .page-header { margin-bottom: 1.5rem; }
    .text-secondary { color: var(--text-secondary); font-size: 0.875rem; }
    .stats-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 1rem; margin-bottom: 2rem; }
    .card { background: var(--surface); border: 1px solid var(--border); border-radius: 8px; padding: 1.25rem; }
    .stat-card { text-align: center; }
    .stat-icon { font-size: 1.5rem; }
    .stat-value { font-size: 1.75rem; font-weight: 700; color: var(--primary); }
    .stat-label { font-size: 0.8125rem; color: var(--text-secondary); }
    .loading { text-align: center; padding: 2rem; color: var(--text-secondary); }
    .alert { padding: 0.75rem 1rem; border-radius: 6px; margin-bottom: 1rem; }
    .alert-error { background: #FFEBEE; color: var(--warn); }
    .btn { display: inline-flex; align-items: center; padding: 0.5rem 1rem; border-radius: 6px; border: none; font-size: 0.875rem; font-weight: 600; cursor: pointer; text-decoration: none; }
    .btn-primary { background: var(--primary); color: white; }
  `],
})
export class SisProDashboardComponent implements OnInit {
  cargando = true;
  error = '';
  total = 0;
  enPreinversion = 0;
  enEjecucion = 0;
  cerrados = 0;

  constructor(private service: SisProService) {}

  ngOnInit(): void {
    this.service.listarProyectos().subscribe({
      next: (data) => {
        this.total = data.count;
        this.enPreinversion = data.results.filter(p => p.fase === 'preinversion').length;
        this.enEjecucion = data.results.filter(p => ['ejecucion', 'supervision'].includes(p.fase)).length;
        this.cerrados = data.results.filter(p => ['cierre', 'evaluacion'].includes(p.fase)).length;
        this.cargando = false;
      },
      error: () => {
        this.error = 'Error al cargar los indicadores del SIS-PRO';
        this.cargando = false;
      },
    });
  }
}

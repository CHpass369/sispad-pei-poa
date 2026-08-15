import { Component, OnInit } from '@angular/core';
import { SisPeService } from './sis-pe.service';

@Component({
  standalone: false,
  selector: 'app-sis-pe-dashboard',
  template: `
    <div class="page-header">
      <h2>SIS-PE — Dashboard Estratégico</h2>
      <p class="text-secondary">Sistema de Planificación Estratégica (kernel V2)</p>
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
          <div class="stat-icon">📋</div>
          <div class="stat-value">{{ total }}</div>
          <div class="stat-label">Instrumentos</div>
        </div>
        <div class="card stat-card">
          <div class="stat-icon">✅</div>
          <div class="stat-value">{{ aprobados }}</div>
          <div class="stat-label">Aprobados</div>
        </div>
        <div class="card stat-card">
          <div class="stat-icon">✏️</div>
          <div class="stat-value">{{ en_borrador }}</div>
          <div class="stat-label">En borrador</div>
        </div>
        <div class="card stat-card">
          <div class="stat-icon">🧩</div>
          <div class="stat-value">{{ versiones }}</div>
          <div class="stat-label">Versiones</div>
        </div>
      </div>
    }
    
    @if (!cargando) {
      <div class="quick-actions">
        <a routerLink="/sis-pe/instrumentos" class="btn btn-primary">Instrumentos</a>
      </div>
    }
    `,
  styles: [`
    .page-header { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 1.5rem; flex-wrap: wrap; gap: 1rem; }
    .text-secondary { color: var(--text-secondary); font-size: 0.875rem; }
    .stats-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 1rem; margin-bottom: 2rem; }
    .card { background: var(--surface); border: 1px solid var(--border); border-radius: 8px; padding: 1.25rem; }
    .stat-card { text-align: center; }
    .stat-icon { font-size: 1.5rem; }
    .stat-value { font-size: 1.75rem; font-weight: 700; color: var(--primary); }
    .stat-label { font-size: 0.8125rem; color: var(--text-secondary); }
    .loading { text-align: center; padding: 2rem; color: var(--text-secondary); }
    .alert { padding: 0.75rem 1rem; border-radius: 6px; margin-top: 1rem; }
    .alert-error { background: #FFEBEE; color: var(--warn); }
    .btn { display: inline-flex; align-items: center; padding: 0.5rem 1rem; border-radius: 6px; border: none; font-size: 0.875rem; font-weight: 600; cursor: pointer; text-decoration: none; }
    .btn-primary { background: var(--primary); color: white; }
  `],
})
export class SisPeDashboardComponent implements OnInit {
  cargando = true;
  error = '';
  total = 0;
  aprobados = 0;
  en_borrador = 0;
  versiones = 0;

  constructor(private service: SisPeService) {}

  ngOnInit(): void {
    this.service.listarInstrumentos().subscribe({
      next: (data) => {
        this.total = data.count;
        this.aprobados = data.results.filter(i => i.estado === 'aprobado').length;
        this.en_borrador = data.results.filter(i => i.estado === 'borrador').length;
        this.versiones = data.results.reduce((acc, i) => acc + (i.versiones_count || 0), 0);
        this.cargando = false;
      },
      error: () => {
        this.error = 'Error al cargar los indicadores del SIS-PE';
        this.cargando = false;
      },
    });
  }
}

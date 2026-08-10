import { Component, OnInit } from '@angular/core';
import { SisPoaService } from './sis-poa.service';

@Component({
  standalone: false,
  selector: 'app-sis-poa-dashboard',
  template: `
    <div class="page-header">
      <h2>SIS-POA — Dashboard Operativo</h2>
      <p class="text-secondary">Sistema de Planificación Operativa Anual (V2)</p>
    </div>
    <div *ngIf="cargando" class="loading">Cargando indicadores...</div>
    <div class="alert alert-error" *ngIf="error">{{ error }}</div>
    <div class="stats-grid" *ngIf="!cargando">
      <div class="card stat-card">
        <div class="stat-icon">📋</div>
        <div class="stat-value">{{ total }}</div>
        <div class="stat-label">POAs</div>
      </div>
      <div class="card stat-card">
        <div class="stat-icon">✅</div>
        <div class="stat-value">{{ aprobados }}</div>
        <div class="stat-label">Aprobados</div>
      </div>
      <div class="card stat-card">
        <div class="stat-icon">✏️</div>
        <div class="stat-value">{{ borradores }}</div>
        <div class="stat-label">En borrador</div>
      </div>
    </div>
    <div class="quick-actions" *ngIf="!cargando">
      <a routerLink="/sis-poa/poas" class="btn btn-primary">POAs</a>
    </div>
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
export class SisPoaDashboardComponent implements OnInit {
  cargando = true;
  error = '';
  total = 0;
  aprobados = 0;
  borradores = 0;

  constructor(private service: SisPoaService) {}

  ngOnInit(): void {
    this.service.listarPoas().subscribe({
      next: (data) => {
        this.total = data.count;
        this.aprobados = data.results.filter(p => p.estado === 'aprobado').length;
        this.borradores = data.results.filter(p => p.estado === 'borrador').length;
        this.cargando = false;
      },
      error: () => {
        this.error = 'Error al cargar los indicadores del SIS-POA';
        this.cargando = false;
      },
    });
  }
}

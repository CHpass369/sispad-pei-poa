import { Component, OnInit } from '@angular/core';
import { ApiService } from '../../core/services/api.service';

@Component({
  standalone: false,
  selector: 'app-dashboard',
  template: `
    <div class="dashboard">
      <div class="page-header">
        <h2>Dashboard POA {{ gestion }}</h2>
        <p class="text-secondary">Panel de control institucional</p>
      </div>

      <!-- Stats Grid -->
      <div class="stats-grid">
        <div class="stat-card" *ngIf="data?.totales">
          <div class="stat-value">{{ data.totales.avance_porcentual }}%</div>
          <div class="stat-label">Avance formulación</div>
          <div class="progress-bar">
            <div class="progress-fill" [style.width.%]="data.totales.avance_porcentual"></div>
          </div>
        </div>
        <div class="stat-card">
          <div class="stat-value">{{ data?.unidades?.con_envio || 0 }}/{{ data?.unidades?.total || 0 }}</div>
          <div class="stat-label">Unidades que enviaron</div>
        </div>
        <div class="stat-card">
          <div class="stat-value">{{ data?.acciones?.total || 0 }}</div>
          <div class="stat-label">Acciones registradas</div>
        </div>
        <div class="stat-card">
          <div class="stat-value" [class.text-warn]="(data?.observaciones?.abiertas || 0) > 0">
            {{ data?.observaciones?.abiertas || 0 }}
          </div>
          <div class="stat-label">Observaciones abiertas</div>
        </div>
      </div>

      <!-- Totales Financieros -->
      <div class="section">
        <h3>Resumen Financiero</h3>
        <div class="finance-grid" *ngIf="data?.totales">
          <div class="finance-item">
            <span class="finance-label">Techo Municipal</span>
            <span class="finance-value">Bs {{ data.totales.techo_municipal | number:'1.2-2' }}</span>
          </div>
          <div class="finance-item">
            <span class="finance-label">Techo Distribuido</span>
            <span class="finance-value">Bs {{ data.totales.techo_distribuido | number:'1.2-2' }}</span>
          </div>
          <div class="finance-item highlight">
            <span class="finance-label">Formulado</span>
            <span class="finance-value">Bs {{ data.totales.formulado | number:'1.2-2' }}</span>
          </div>
          <div class="finance-item">
            <span class="finance-label">Saldo por formular</span>
            <span class="finance-value" [class.text-warn]="data.totales.saldo_por_formular > 0">
              Bs {{ data.totales.saldo_por_formular | number:'1.2-2' }}
            </span>
          </div>
        </div>
      </div>

      <!-- Programas -->
      <div class="section" *ngIf="data?.programas?.length">
        <h3>Programas con mayor presupuesto</h3>
        <table>
          <thead>
            <tr><th>Código</th><th>Programa</th><th>Presupuesto (Bs)</th></tr>
          </thead>
          <tbody>
            <tr *ngFor="let p of data.programas.slice(0, 10)">
              <td><strong>{{ p.codigo }}</strong></td>
              <td>{{ p.nombre }}</td>
              <td>{{ p.formulado | number:'1.2-2' }}</td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- Loading -->
      <div class="loading" *ngIf="!data && !error">
        <p>Cargando datos del dashboard...</p>
      </div>

      <!-- Error -->
      <div class="alert alert-error" *ngIf="error">
        {{ error }}
      </div>
    </div>
  `,
  styles: [`
    .page-header { margin-bottom: 1.5rem; }
    .page-header h2 { font-size: 1.5rem; margin-bottom: 0.25rem; }
    .text-secondary { color: var(--text-secondary); font-size: 0.875rem; }
    .stats-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1rem; margin-bottom: 2rem; }
    .stat-card { background: var(--surface); border: 1px solid var(--border); border-radius: 8px; padding: 1.25rem; }
    .stat-value { font-size: 1.75rem; font-weight: 800; color: var(--primary); }
    .stat-label { font-size: 0.8125rem; color: var(--text-secondary); margin-top: 0.25rem; }
    .text-warn { color: var(--warn) !important; }
    .progress-bar { height: 4px; background: var(--border); border-radius: 2px; margin-top: 0.75rem; overflow: hidden; }
    .progress-fill { height: 100%; background: var(--primary); border-radius: 2px; transition: width 0.5s; }
    .section { margin-bottom: 2rem; }
    .section h3 { font-size: 1rem; margin-bottom: 1rem; }
    .finance-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 0.75rem; }
    .finance-item { background: var(--bg); padding: 1rem; border-radius: 6px; border-left: 3px solid var(--primary); }
    .finance-item.highlight { border-left-color: var(--accent); background: #FFF8E1; }
    .finance-label { display: block; font-size: 0.75rem; color: var(--text-secondary); margin-bottom: 0.25rem; }
    .finance-value { font-size: 1.125rem; font-weight: 700; }
    table { width: 100%; border-collapse: collapse; }
    th, td { padding: 0.625rem 0.75rem; text-align: left; border-bottom: 1px solid var(--border); }
    th { font-size: 0.75rem; color: var(--text-secondary); text-transform: uppercase; }
    .loading { text-align: center; padding: 3rem; color: var(--text-secondary); }
    .alert { padding: 0.75rem 1rem; border-radius: 6px; }
    .alert-error { background: #FFEBEE; color: var(--warn); }
  `]
})
export class DashboardComponent implements OnInit {
  gestion = 2026;
  data: any = null;
  error = '';

  constructor(private api: ApiService) {}

  ngOnInit(): void {
    this.api.get<any>('/dashboard/poa/', { gestion: this.gestion }).subscribe({
      next: d => this.data = d,
      error: e => this.error = 'Error al cargar dashboard: ' + (e.message || e),
    });
  }
}

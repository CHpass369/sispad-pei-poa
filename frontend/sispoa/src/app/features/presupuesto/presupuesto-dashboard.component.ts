import { Component, OnInit } from '@angular/core';
import { ApiService } from '../../core/services/api.service';

@Component({
  standalone: false,
  selector: 'app-presupuesto-dashboard',
  template: `
    <div class="presupuesto-dashboard">
      <div class="page-header">
        <h2>Dashboard Presupuestario {{ gestion }}</h2>
        <p class="text-secondary">Resumen de ejecución presupuestaria por programa</p>
      </div>

      <!-- Loading -->
      <div class="loading" *ngIf="!data && !error">
        <p>Cargando datos presupuestarios...</p>
      </div>

      <!-- Error -->
      <div class="alert alert-error" *ngIf="error">
        {{ error }}
      </div>

      <!-- Financial Cards -->
      <div class="finance-grid" *ngIf="data">
        <div class="finance-card">
          <span class="finance-label">Techo Presupuestario</span>
          <span class="finance-value">Bs {{ data.techo | number:'1.2-2' }}</span>
        </div>
        <div class="finance-card highlight">
          <span class="finance-label">Formulado</span>
          <span class="finance-value">Bs {{ data.formulado | number:'1.2-2' }}</span>
        </div>
        <div class="finance-card" [class.text-warn]="data.saldo > 0">
          <span class="finance-label">Saldo por formular</span>
          <span class="finance-value">Bs {{ data.saldo | number:'1.2-2' }}</span>
        </div>
        <div class="finance-card">
          <span class="finance-label">% Avance</span>
          <span class="finance-value">{{ data.porcentaje_avance }}%</span>
          <div class="progress-bar">
            <div class="progress-fill" [style.width.%]="data.porcentaje_avance"></div>
          </div>
        </div>
      </div>

      <!-- Programas Table -->
      <div class="section" *ngIf="data?.programas?.length">
        <h3>Programas Presupuestarios</h3>
        <table>
          <thead>
            <tr>
              <th>Código</th>
              <th>Programa</th>
              <th>Presupuesto (Bs)</th>
              <th>Techo (Bs)</th>
              <th>% Avance</th>
            </tr>
          </thead>
          <tbody>
            <tr *ngFor="let p of data.programas">
              <td><strong>{{ p.codigo }}</strong></td>
              <td>{{ p.nombre }}</td>
              <td>{{ p.presupuesto | number:'1.2-2' }}</td>
              <td>{{ p.techo | number:'1.2-2' }}</td>
              <td>
                <span class="badge" [class.badge-ok]="p.porcentaje >= 90"
                      [class.badge-warn]="p.porcentaje > 0 && p.porcentaje < 90"
                      [class.badge-danger]="p.porcentaje === 0">
                  {{ p.porcentaje }}%
                </span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  `,
  styles: [`
    .page-header { margin-bottom: 1.5rem; }
    .page-header h2 { font-size: 1.5rem; margin-bottom: 0.25rem; }
    .text-secondary { color: var(--text-secondary); font-size: 0.875rem; }
    .finance-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1rem; margin-bottom: 2rem; }
    .finance-card { background: var(--surface); border: 1px solid var(--border); border-radius: 8px; padding: 1.25rem; }
    .finance-card.highlight { border-left: 4px solid var(--accent); background: #FFF8E1; }
    .finance-card.text-warn { border-left: 4px solid var(--warn); }
    .finance-label { display: block; font-size: 0.75rem; color: var(--text-secondary); margin-bottom: 0.25rem; text-transform: uppercase; }
    .finance-value { font-size: 1.375rem; font-weight: 700; color: var(--primary); }
    .text-warn .finance-value { color: var(--warn); }
    .progress-bar { height: 4px; background: var(--border); border-radius: 2px; margin-top: 0.75rem; overflow: hidden; }
    .progress-fill { height: 100%; background: var(--primary); border-radius: 2px; transition: width 0.5s; }
    .section { margin-bottom: 2rem; }
    .section h3 { font-size: 1rem; margin-bottom: 1rem; color: var(--text-primary); }
    table { width: 100%; border-collapse: collapse; }
    th, td { padding: 0.625rem 0.75rem; text-align: left; border-bottom: 1px solid var(--border); }
    th { font-size: 0.75rem; color: var(--text-secondary); text-transform: uppercase; }
    .badge { display: inline-block; padding: 0.125rem 0.5rem; border-radius: 999px; font-size: 0.75rem; font-weight: 600; }
    .badge-ok { background: #E8F5E9; color: #2E7D32; }
    .badge-warn { background: #FFF8E1; color: #F57F17; }
    .badge-danger { background: #FFEBEE; color: #C62828; }
    .loading { text-align: center; padding: 3rem; color: var(--text-secondary); }
    .alert { padding: 0.75rem 1rem; border-radius: 6px; }
    .alert-error { background: #FFEBEE; color: var(--warn); }
  `]
})
export class PresupuestoDashboardComponent implements OnInit {
  gestion = 2026;
  data: any = null;
  error = '';

  constructor(private api: ApiService) {}

  ngOnInit(): void {
    this.api.get<any>('/dashboard/presupuesto/', { gestion: this.gestion }).subscribe({
      next: d => this.data = d,
      error: e => this.error = 'Error al cargar datos presupuestarios: ' + (e.message || e),
    });
  }
}

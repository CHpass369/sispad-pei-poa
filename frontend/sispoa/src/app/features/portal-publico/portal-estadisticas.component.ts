import { Component, OnInit } from '@angular/core';
import { PortalPublicoService, ResumenEjecucion } from './portal-publico.service';

@Component({
  standalone: false,
  selector: 'app-portal-estadisticas',
  template: `
    <div class="page-header">
      <h2>Estadísticas Públicas</h2>
      <p class="text-secondary">Resumen ejecutivo de planificación y presupuesto</p>
    </div>

    <div class="stats-grid" *ngIf="!cargando && resumen">
      <div class="card stat-card highlight">
        <div class="stat-valor">Bs {{ resumen.total_presupuesto | number:'1.2-2' }}</div>
        <div class="stat-label">Presupuesto Total</div>
      </div>
      <div class="card stat-card">
        <div class="stat-valor">Bs {{ resumen.total_ejecutado | number:'1.2-2' }}</div>
        <div class="stat-label">Total Ejecutado</div>
      </div>
      <div class="card stat-card">
        <div class="stat-valor">{{ resumen.porcentaje_ejecucion || 0 }}%</div>
        <div class="stat-label">% Ejecución</div>
        <div class="progress-bar">
          <div class="progress-fill" [style.width.%]="resumen.porcentaje_ejecucion || 0"></div>
        </div>
      </div>
      <div class="card stat-card">
        <div class="stat-valor">{{ resumen.total_programas || 0 }}</div>
        <div class="stat-label">Programas</div>
      </div>
    </div>

    <div class="charts-row" *ngIf="!cargando && resumen">
      <div class="card chart-card">
        <h3>Ejecución por Tipo</h3>
        <div class="chart-bars">
          <div *ngFor="let item of resumen.por_tipo" class="bar-item">
            <span class="bar-label">{{ item.tipo || item.nombre }}</span>
            <div class="bar-track">
              <div class="bar-fill" [style.width.%]="item.porcentaje || 0"></div>
            </div>
            <span class="bar-value">{{ item.monto | number:'1.0-0' }} Bs</span>
          </div>
          <div *ngIf="!resumen.por_tipo || resumen.por_tipo.length === 0" class="empty-chart">Sin datos disponibles</div>
        </div>
      </div>

      <div class="card chart-card">
        <h3>Ejecución por Sector</h3>
        <div class="chart-bars">
          <div *ngFor="let item of resumen.por_sector" class="bar-item">
            <span class="bar-label">{{ item.sector || item.nombre }}</span>
            <div class="bar-track">
              <div class="bar-fill bar-fill-alt" [style.width.%]="item.porcentaje || 0"></div>
            </div>
            <span class="bar-value">{{ item.monto | number:'1.0-0' }} Bs</span>
          </div>
          <div *ngIf="!resumen.por_sector || resumen.por_sector.length === 0" class="empty-chart">Sin datos disponibles</div>
        </div>
      </div>
    </div>

    <div class="card chart-card full-width" *ngIf="!cargando && resumen && resumen.por_mes && resumen.por_mes.length > 0">
      <h3>Ejecución Mensual</h3>
      <div class="monthly-bars">
        <div *ngFor="let item of resumen.por_mes" class="month-bar">
          <div class="month-column">
            <div class="month-fill" [style.height.%]="item.porcentaje || 0"></div>
          </div>
          <span class="month-label">{{ item.mes }}</span>
        </div>
      </div>
    </div>

    <div class="loading" *ngIf="cargando">Cargando estadísticas...</div>
    <div class="alert alert-error" *ngIf="error">{{ error }}</div>
  `,
  styles: [`
    .page-header { margin-bottom: 1.5rem; }
    .page-header h2 { font-size: 1.5rem; margin-bottom: 0.25rem; }
    .text-secondary { color: var(--text-secondary); font-size: 0.875rem; }
    .card { background: var(--surface); border: 1px solid var(--border); border-radius: 8px; padding: 1.25rem; }
    .stats-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1rem; margin-bottom: 2rem; }
    .stat-card { text-align: center; }
    .stat-card.highlight { background: var(--primary, #1a237e); color: white; }
    .stat-card.highlight .stat-label { color: rgba(255,255,255,0.8); }
    .stat-valor { font-size: 1.5rem; font-weight: 700; }
    .stat-label { font-size: 0.8125rem; color: var(--text-secondary); margin-top: 0.25rem; }
    .progress-bar { height: 6px; background: rgba(0,0,0,0.1); border-radius: 3px; margin-top: 0.5rem; overflow: hidden; }
    .progress-fill { height: 100%; background: #2E7D32; border-radius: 3px; }
    .charts-row { display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; margin-bottom: 1.5rem; }
    .chart-card { margin-bottom: 1rem; }
    .chart-card.full-width { margin-bottom: 1rem; }
    .chart-card h3 { font-size: 1rem; margin-bottom: 1rem; }
    .chart-bars { display: flex; flex-direction: column; gap: 0.75rem; }
    .bar-item { display: flex; align-items: center; gap: 0.75rem; }
    .bar-label { min-width: 120px; font-size: 0.8125rem; text-align: right; }
    .bar-track { flex: 1; height: 20px; background: var(--border); border-radius: 4px; overflow: hidden; }
    .bar-fill { height: 100%; background: var(--primary); border-radius: 4px; transition: width 0.5s; }
    .bar-fill-alt { background: #2E7D32; }
    .bar-value { min-width: 100px; font-size: 0.8125rem; font-weight: 600; }
    .empty-chart { text-align: center; color: var(--text-secondary); font-size: 0.875rem; padding: 1rem; }
    .monthly-bars { display: flex; align-items: flex-end; gap: 0.5rem; height: 200px; padding-top: 1rem; }
    .month-bar { display: flex; flex-direction: column; align-items: center; flex: 1; height: 100%; }
    .month-column { flex: 1; width: 100%; max-width: 40px; background: var(--border); border-radius: 4px 4px 0 0; display: flex; flex-direction: column; justify-content: flex-end; }
    .month-fill { width: 100%; background: var(--primary); border-radius: 4px 4px 0 0; transition: height 0.5s; min-height: 2px; }
    .month-label { font-size: 0.6875rem; color: var(--text-secondary); margin-top: 0.5rem; }
    .loading { text-align: center; padding: 2rem; color: var(--text-secondary); }
    .alert { padding: 0.75rem 1rem; border-radius: 6px; margin-top: 1rem; }
    .alert-error { background: #FFEBEE; color: var(--warn); }
    @media (max-width: 768px) { .charts-row { grid-template-columns: 1fr; } }
  `]
})
export class PortalEstadisticasComponent implements OnInit {
  resumen: ResumenEjecucion | null = null;
  cargando = true;
  error = '';

  constructor(private portalService: PortalPublicoService) {}

  ngOnInit(): void {
    this.portalService.obtenerResumenEjecucion().subscribe({
      next: (data) => {
        this.resumen = data;
        this.cargando = false;
      },
      error: () => {
        this.error = 'Error al cargar estadísticas';
        this.cargando = false;
      },
    });
  }
}

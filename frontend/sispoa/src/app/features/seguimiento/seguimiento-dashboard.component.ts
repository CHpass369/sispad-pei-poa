import { Component, OnInit } from '@angular/core';
import { SeguimientoService, Semaforo, DashboardData, Alerta } from './seguimiento.service';

@Component({
  standalone: false,
  selector: 'app-seguimiento-dashboard',
  template: `
    <div class="page-header">
      <h2>Dashboard de Seguimiento</h2>
      <p class="text-secondary">Indicadores de avance físico y financiero</p>
    </div>

    <div class="indicadores-grid" *ngIf="dashboard">
      <div class="card indicador">
        <div class="indicador-label">Total Actividades</div>
        <div class="indicador-valor">{{ dashboard.total_actividades || 0 }}</div>
      </div>
      <div class="card indicador verde">
        <div class="indicador-label">En Tiempo</div>
        <div class="indicador-valor">{{ dashboard.en_tiempo || 0 }}</div>
      </div>
      <div class="card indicador amarillo">
        <div class="indicador-label">Con Riesgo</div>
        <div class="indicador-valor">{{ dashboard.con_riesgo || 0 }}</div>
      </div>
      <div class="card indicador rojo">
        <div class="indicador-label">Retrasadas</div>
        <div class="indicador-valor">{{ dashboard.retrasadas || 0 }}</div>
      </div>
      <div class="card indicador">
        <div class="indicador-label">Avance Físico Prom.</div>
        <div class="indicador-valor">{{ dashboard.avance_fisico_promedio || 0 }}%</div>
      </div>
      <div class="card indicador">
        <div class="indicador-label">Avance Financiero Prom.</div>
        <div class="indicador-valor">{{ dashboard.avance_financiero_promedio || 0 }}%</div>
      </div>
    </div>

    <div class="seccion">
      <h3>Semáforo de Actividades</h3>
      <div class="semaforo-grid" *ngIf="semaforos.length > 0">
        <div class="card semaforo-item" *ngFor="let s of semaforos"
             [class.semaforo-verde]="s.estado_semaforo === 'verde'"
             [class.semaforo-amarillo]="s.estado_semaforo === 'amarillo'"
             [class.semaforo-rojo]="s.estado_semaforo === 'rojo'">
          <div class="semaforo-dot" [ngClass]="'dot-' + s.estado_semaforo"></div>
          <div class="semaforo-info">
            <strong>{{ s.actividad_descripcion }}</strong>
            <div class="semaforo-avances">
              <span>Físico: {{ s.avance_fisico || 0 }}%</span>
              <span>Financiero: {{ s.avance_financiero || 0 }}%</span>
            </div>
          </div>
        </div>
      </div>
      <div *ngIf="semaforos.length === 0" class="empty">No hay datos de semáforo disponibles</div>
    </div>

    <div class="seccion">
      <h3>Alertas Activas ({{ alertas.length }})</h3>
      <div *ngFor="let a of alertas" class="card alerta-item">
        <span class="badge" [ngClass]="'badge-' + a.severidad">{{ a.severidad }}</span>
        <span class="alerta-mensaje">{{ a.mensaje }}</span>
        <span class="alerta-actividad">{{ a.actividad_descripcion }}</span>
      </div>
      <div *ngIf="alertas.length === 0" class="empty">No hay alertas activas</div>
    </div>

    <div class="loading" *ngIf="cargando">Cargando dashboard...</div>
  `,
  styles: [`
    .page-header { margin-bottom: 1.5rem; }
    .page-header h2 { font-size: 1.5rem; margin-bottom: 0.25rem; }
    .text-secondary { color: var(--text-secondary); font-size: 0.875rem; }
    .indicadores-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 1rem; margin-bottom: 2rem; }
    .card { background: var(--surface); border: 1px solid var(--border); border-radius: 8px; padding: 1.25rem; }
    .indicador { text-align: center; }
    .indicador-label { font-size: 0.8125rem; color: var(--text-secondary); margin-bottom: 0.5rem; }
    .indicador-valor { font-size: 1.75rem; font-weight: 700; }
    .indicador.verde .indicador-valor { color: #2E7D32; }
    .indicador.amarillo .indicador-valor { color: #F57F17; }
    .indicador.rojo .indicador-valor { color: #C62828; }
    .seccion { margin-bottom: 2rem; }
    .seccion h3 { font-size: 1.125rem; margin-bottom: 1rem; }
    .semaforo-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 1rem; }
    .semaforo-item { display: flex; align-items: center; gap: 1rem; }
    .semaforo-item.semaforo-verde { border-left: 4px solid #2E7D32; }
    .semaforo-item.semaforo-amarillo { border-left: 4px solid #F57F17; }
    .semaforo-item.semaforo-rojo { border-left: 4px solid #C62828; }
    .semaforo-dot { width: 14px; height: 14px; border-radius: 50%; flex-shrink: 0; }
    .dot-verde { background: #2E7D32; }
    .dot-amarillo { background: #F57F17; }
    .dot-rojo { background: #C62828; }
    .semaforo-info strong { font-size: 0.875rem; display: block; margin-bottom: 0.25rem; }
    .semaforo-avances { display: flex; gap: 1rem; font-size: 0.8125rem; color: var(--text-secondary); }
    .alerta-item { display: flex; align-items: center; gap: 0.75rem; padding: 0.75rem 1rem; margin-bottom: 0.5rem; }
    .alerta-mensaje { flex: 1; font-size: 0.875rem; }
    .alerta-actividad { font-size: 0.8125rem; color: var(--text-secondary); }
    .badge { display: inline-block; padding: 0.125rem 0.5rem; border-radius: 4px; font-size: 0.75rem; font-weight: 600; text-transform: uppercase; }
    .badge-alta, .badge-alto { background: #FFEBEE; color: #C62828; }
    .badge-media, .badge-medio { background: #FFF3E0; color: #E65100; }
    .badge-baja, .badge-bajo { background: #E8F5E9; color: #2E7D32; }
    .empty { text-align: center; padding: 2rem; color: var(--text-secondary); }
    .loading { text-align: center; padding: 2rem; color: var(--text-secondary); }
  `]
})
export class SeguimientoDashboardComponent implements OnInit {
  dashboard: DashboardData | null = null;
  semaforos: Semaforo[] = [];
  alertas: Alerta[] = [];
  cargando = true;

  constructor(private seguimientoService: SeguimientoService) {}

  ngOnInit(): void {
    this.cargarDashboard();
    this.cargarSemaforo();
    this.cargarAlertas();
  }

  cargarDashboard(): void {
    this.seguimientoService.obtenerDashboard().subscribe({
      next: (data) => {
        this.dashboard = data;
        this.cargando = false;
      },
      error: () => { this.cargando = false; },
    });
  }

  cargarSemaforo(): void {
    this.seguimientoService.obtenerSemaforo().subscribe({
      next: (data: any) => {
        this.semaforos = data.results || data;
      },
    });
  }

  cargarAlertas(): void {
    this.seguimientoService.listarAlertasActivas().subscribe({
      next: (data: any) => {
        this.alertas = data.results || data;
      },
    });
  }
}

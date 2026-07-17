import { Component, OnInit } from '@angular/core';
import { AuthService } from '../../core/services/auth.service';
import { ApiService } from '../../core/services/api.service';

@Component({
  standalone: false,
  selector: 'app-dashboard',
  template: `
    <div class="dashboard">
      <div class="page-header">
        <div class="header-left">
          <h2>Bienvenido, {{ userName }}</h2>
          <p class="text-secondary">{{ fechaActual | date:'EEEE d \'de\' MMMM yyyy' }}</p>
        </div>
        <div class="header-right">
          <span class="badge badge-role">{{ rolDisplay }}</span>
          <div class="notif-bell" routerLink="/notificaciones">
            🔔 <span class="notif-count" *ngIf="notifCount > 0">{{ notifCount }}</span>
          </div>
        </div>
      </div>

      <!-- SUPERADMIN / TECNICO_ADMIN -->
      <ng-container *ngIf="isSuperAdmin || isTecnicoAdmin">
        <div class="stats-grid">
          <div class="card stat-card">
            <div class="stat-icon">💰</div>
            <div class="stat-value">Bs {{ kpis?.presupuesto_total | number:'1.0-0' }}</div>
            <div class="stat-label">Presupuesto Total</div>
          </div>
          <div class="card stat-card">
            <div class="stat-icon">📊</div>
            <div class="stat-value">{{ kpis?.ejecucion_porcentaje || 0 }}%</div>
            <div class="stat-label">Ejecución Global</div>
            <div class="progress-bar">
              <div class="progress-fill" [style.width.%]="kpis?.ejecucion_porcentaje || 0"></div>
            </div>
          </div>
          <div class="card stat-card">
            <div class="stat-icon">⏳</div>
            <div class="stat-value">{{ kpis?.aprobaciones_pendientes || 0 }}</div>
            <div class="stat-label">Aprobaciones Pendientes</div>
          </div>
          <div class="card stat-card">
            <div class="stat-icon">⚠️</div>
            <div class="stat-value">{{ kpis?.alertas_count || 0 }}</div>
            <div class="stat-label">Alertas Activas</div>
          </div>
        </div>

        <div class="charts-grid">
          <div class="card chart-card">
            <h3>Ejecución por Tipo de Plan</h3>
            <div class="chart-bars">
              <div *ngFor="let item of kpis?.por_tipo" class="bar-item">
                <span class="bar-label">{{ item.tipo }}</span>
                <div class="bar-track">
                  <div class="bar-fill" [style.width.%]="item.porcentaje || 0"></div>
                </div>
                <span class="bar-value">{{ item.porcentaje || 0 }}%</span>
              </div>
              <div *ngIf="!kpis?.por_tipo || kpis.por_tipo.length === 0" class="empty-chart">Sin datos</div>
            </div>
          </div>
          <div class="card chart-card">
            <h3>Ejecución Mensual</h3>
            <div class="monthly-bars">
              <div *ngFor="let item of kpis?.por_mes" class="month-bar">
                <div class="month-column">
                  <div class="month-fill" [style.height.%]="item.porcentaje || 0"></div>
                </div>
                <span class="month-label">{{ item.mes }}</span>
              </div>
              <div *ngIf="!kpis?.por_mes || kpis.por_mes.length === 0" class="empty-chart">Sin datos</div>
            </div>
          </div>
        </div>

        <div class="card activity-card">
          <h3>Actividad Reciente</h3>
          <div class="activity-list">
            <div *ngFor="let act of kpis?.actividad_reciente" class="activity-item">
              <span class="activity-icon">📌</span>
              <div class="activity-content">
                <span class="activity-text">{{ act.descripcion }}</span>
                <span class="activity-date">{{ act.fecha | date:'dd/MM/yyyy HH:mm' }}</span>
              </div>
            </div>
            <div *ngIf="!kpis?.actividad_reciente || kpis.actividad_reciente.length === 0" class="empty-chart">Sin actividad reciente</div>
          </div>
        </div>
      </ng-container>

      <!-- PLANIFICADOR / EVALUADOR -->
      <ng-container *ngIf="isPlanificador || isEvaluador">
        <div class="stats-grid">
          <div class="card stat-card">
            <div class="stat-icon">🎯</div>
            <div class="stat-value">{{ kpis?.pei_avance || 0 }}%</div>
            <div class="stat-label">Avance PEI</div>
            <div class="progress-bar">
              <div class="progress-fill" [style.width.%]="kpis?.pei_avance || 0"></div>
            </div>
          </div>
          <div class="card stat-card">
            <div class="stat-icon">📋</div>
            <div class="stat-value">{{ kpis?.pad_avance || 0 }}%</div>
            <div class="stat-label">Avance PAD</div>
            <div class="progress-bar">
              <div class="progress-fill" [style.width.%]="kpis?.pad_avance || 0"></div>
            </div>
          </div>
          <div class="card stat-card">
            <div class="stat-icon">📊</div>
            <div class="stat-value">{{ kpis?.indicadores_ok || 0 }}/{{ kpis?.indicadores_total || 0 }}</div>
            <div class="stat-label">Indicadores en Meta</div>
          </div>
          <div class="card stat-card">
            <div class="stat-icon">📝</div>
            <div class="stat-value">{{ kpis?.evaluaciones_pendientes || 0 }}</div>
            <div class="stat-label">Evaluaciones Pendientes</div>
          </div>
        </div>

        <div class="card">
          <h3>Estado de Indicadores</h3>
          <div class="indicadores-status">
            <div *ngFor="let ind of kpis?.indicadores_estado" class="ind-item">
              <span class="ind-nombre">{{ ind.nombre }}</span>
              <div class="progress-bar progress-bar-sm">
                <div class="progress-fill" [style.width.%]="ind.avance || 0"
                     [class.fill-ok]="(ind.avance || 0) >= 80"
                     [class.fill-warn]="(ind.avance || 0) >= 40 && (ind.avance || 0) < 80"
                     [class.fill-danger]="(ind.avance || 0) < 40"></div>
              </div>
              <span class="ind-avance">{{ ind.avance || 0 }}%</span>
            </div>
            <div *ngIf="!kpis?.indicadores_estado || kpis.indicadores_estado.length === 0" class="empty-chart">Sin indicadores registrados</div>
          </div>
        </div>
      </ng-container>

      <!-- JEFE_UE / DIRECTOR -->
      <ng-container *ngIf="isJefeUe || isDirector">
        <div class="stats-grid">
          <div class="card stat-card">
            <div class="stat-icon">🏢</div>
            <div class="stat-value">{{ kpis?.unidad_ejecutada || 0 }}%</div>
            <div class="stat-label">Ejecución de la Unidad</div>
            <div class="progress-bar">
              <div class="progress-fill" [style.width.%]="kpis?.unidad_ejecutada || 0"></div>
            </div>
          </div>
          <div class="card stat-card">
            <div class="stat-icon">📋</div>
            <div class="stat-value">{{ kpis?.tareas_equipo || 0 }}</div>
            <div class="stat-label">Tareas del Equipo</div>
          </div>
          <div class="card stat-card">
            <div class="stat-icon">⚠️</div>
            <div class="stat-value">{{ kpis?.alertas_unidad || 0 }}</div>
            <div class="stat-label">Alertas de la Unidad</div>
          </div>
          <div class="card stat-card">
            <div class="stat-icon">💰</div>
            <div class="stat-value">Bs {{ kpis?.presupuesto_unidad | number:'1.0-0' }}</div>
            <div class="stat-label">Presupuesto Unidad</div>
          </div>
        </div>

        <div class="card">
          <h3>Tareas del Equipo</h3>
          <div class="task-list">
            <div *ngFor="let tarea of kpis?.tareas_lista" class="task-item">
              <span class="task-status" [ngClass]="tarea.estado === 'completado' ? 'status-done' : (tarea.estado === 'en_progreso' ? 'status-progress' : 'status-pending')">
                {{ tarea.estado === 'completado' ? '✓' : (tarea.estado === 'en_progreso' ? '◐' : '○') }}
              </span>
              <span class="task-nombre">{{ tarea.nombre }}</span>
              <span class="task-fecha">{{ tarea.fecha_limite | date:'dd/MM' }}</span>
            </div>
            <div *ngIf="!kpis?.tareas_lista || kpis.tareas_lista.length === 0" class="empty-chart">No hay tareas asignadas</div>
          </div>
        </div>
      </ng-container>

      <!-- TODOS: Quick Actions -->
      <div class="quick-actions">
        <h3>Acciones Rápidas</h3>
        <div class="actions-grid">
          <a routerLink="/planificacion" class="card action-card">
            <div class="action-icon">📝</div>
            <span>Planificación</span>
          </a>
          <a routerLink="/seguimiento" class="card action-card">
            <div class="action-icon">📊</div>
            <span>Seguimiento</span>
          </a>
          <a routerLink="/reportes" class="card action-card">
            <div class="action-icon">📈</div>
            <span>Reportes</span>
          </a>
          <a routerLink="/consolidacion" class="card action-card">
            <div class="action-icon">🔗</div>
            <span>Consolidación</span>
          </a>
        </div>
      </div>

      <!-- TODOS: Profile Card -->
      <div class="card profile-card">
        <h3>Mi Perfil</h3>
        <div class="profile-info">
          <div class="profile-avatar">{{ userName.charAt(0) }}</div>
          <div class="profile-details">
            <strong>{{ userName }}</strong>
            <span>{{ userEmail }}</span>
            <span class="badge badge-role">{{ rolDisplay }}</span>
          </div>
        </div>
      </div>

      <div class="loading" *ngIf="cargando">Cargando dashboard...</div>
      <div class="alert alert-error" *ngIf="error">{{ error }}</div>
    </div>
  `,
  styles: [`
    .page-header { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 1.5rem; flex-wrap: wrap; gap: 1rem; }
    .header-left h2 { font-size: 1.5rem; margin-bottom: 0.25rem; }
    .header-right { display: flex; align-items: center; gap: 1rem; }
    .text-secondary { color: var(--text-secondary); font-size: 0.875rem; }
    .badge { display: inline-block; padding: 0.125rem 0.5rem; border-radius: 4px; font-size: 0.75rem; font-weight: 600; }
    .badge-role { background: #E3F2FD; color: #1565C0; text-transform: uppercase; }
    .notif-bell { position: relative; cursor: pointer; font-size: 1.25rem; padding: 0.25rem; }
    .notif-count { position: absolute; top: -4px; right: -4px; background: #C62828; color: white; font-size: 0.625rem; padding: 0.125rem 0.375rem; border-radius: 10px; font-weight: 700; }
    .stats-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1rem; margin-bottom: 2rem; }
    .card { background: var(--surface); border: 1px solid var(--border); border-radius: 8px; padding: 1.25rem; }
    .stat-card { text-align: center; }
    .stat-icon { font-size: 1.5rem; margin-bottom: 0.5rem; }
    .stat-value { font-size: 1.75rem; font-weight: 700; color: var(--primary); }
    .stat-label { font-size: 0.8125rem; color: var(--text-secondary); margin-top: 0.25rem; }
    .progress-bar { height: 6px; background: var(--border); border-radius: 3px; margin-top: 0.5rem; overflow: hidden; }
    .progress-fill { height: 100%; background: var(--primary); border-radius: 3px; transition: width 0.5s; }
    .progress-bar-sm { height: 4px; margin-top: 0; }
    .fill-ok { background: #2E7D32 !important; }
    .fill-warn { background: #F57F17 !important; }
    .fill-danger { background: #C62828 !important; }
    .charts-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; margin-bottom: 1.5rem; }
    .chart-card h3, .activity-card h3, .profile-card h3, .quick-actions h3 { font-size: 1rem; margin-bottom: 1rem; }
    .chart-bars { display: flex; flex-direction: column; gap: 0.75rem; }
    .bar-item { display: flex; align-items: center; gap: 0.75rem; }
    .bar-label { min-width: 100px; font-size: 0.8125rem; text-align: right; }
    .bar-track { flex: 1; height: 20px; background: var(--border); border-radius: 4px; overflow: hidden; }
    .bar-fill { height: 100%; background: var(--primary); border-radius: 4px; }
    .bar-value { min-width: 40px; font-size: 0.8125rem; font-weight: 600; }
    .monthly-bars { display: flex; align-items: flex-end; gap: 0.5rem; height: 160px; }
    .month-bar { display: flex; flex-direction: column; align-items: center; flex: 1; height: 100%; }
    .month-column { flex: 1; width: 100%; max-width: 30px; background: var(--border); border-radius: 4px 4px 0 0; display: flex; flex-direction: column; justify-content: flex-end; }
    .month-fill { width: 100%; background: var(--primary); border-radius: 4px 4px 0 0; min-height: 2px; }
    .month-label { font-size: 0.625rem; color: var(--text-secondary); margin-top: 0.25rem; }
    .activity-card { margin-bottom: 1.5rem; }
    .activity-list { display: flex; flex-direction: column; gap: 0.75rem; }
    .activity-item { display: flex; align-items: flex-start; gap: 0.75rem; }
    .activity-icon { font-size: 1rem; }
    .activity-content { display: flex; flex-direction: column; flex: 1; }
    .activity-text { font-size: 0.875rem; }
    .activity-date { font-size: 0.75rem; color: var(--text-secondary); }
    .indicadores-status { display: flex; flex-direction: column; gap: 0.75rem; }
    .ind-item { display: flex; align-items: center; gap: 0.75rem; }
    .ind-nombre { min-width: 200px; font-size: 0.875rem; }
    .ind-avance { min-width: 40px; font-size: 0.8125rem; font-weight: 600; text-align: right; }
    .task-list { display: flex; flex-direction: column; gap: 0.5rem; }
    .task-item { display: flex; align-items: center; gap: 0.75rem; padding: 0.5rem 0; border-bottom: 1px solid var(--border); }
    .task-item:last-child { border-bottom: none; }
    .task-status { font-size: 1rem; min-width: 20px; text-align: center; }
    .status-done { color: #2E7D32; }
    .status-progress { color: #F57F17; }
    .status-pending { color: #9E9E9E; }
    .task-nombre { flex: 1; font-size: 0.875rem; }
    .task-fecha { font-size: 0.8125rem; color: var(--text-secondary); }
    .quick-actions { margin-bottom: 1.5rem; }
    .actions-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(140px, 1fr)); gap: 0.75rem; }
    .action-card { text-align: center; text-decoration: none; color: var(--text-primary); transition: transform 0.1s; padding: 1rem; }
    .action-card:hover { transform: translateY(-2px); }
    .action-icon { font-size: 1.5rem; margin-bottom: 0.5rem; }
    .action-card span { font-size: 0.8125rem; font-weight: 600; }
    .profile-card { margin-bottom: 1.5rem; }
    .profile-info { display: flex; align-items: center; gap: 1rem; }
    .profile-avatar { width: 48px; height: 48px; border-radius: 50%; background: var(--primary); color: white; display: flex; align-items: center; justify-content: center; font-size: 1.25rem; font-weight: 700; }
    .profile-details { display: flex; flex-direction: column; gap: 0.25rem; }
    .profile-details strong { font-size: 0.9375rem; }
    .profile-details span { font-size: 0.8125rem; color: var(--text-secondary); }
    .empty-chart { text-align: center; color: var(--text-secondary); font-size: 0.875rem; padding: 1rem; }
    .loading { text-align: center; padding: 2rem; color: var(--text-secondary); }
    .alert { padding: 0.75rem 1rem; border-radius: 6px; margin-top: 1rem; }
    .alert-error { background: #FFEBEE; color: var(--warn); }
    @media (max-width: 768px) {
      .charts-grid { grid-template-columns: 1fr; }
      .page-header { flex-direction: column; }
    }
  `]
})
export class DashboardComponent implements OnInit {
  kpis: any = null;
  cargando = true;
  error = '';
  notifCount = 0;
  userName = '';
  userEmail = '';
  fechaActual = new Date();

  get isSuperAdmin(): boolean { return this.auth.hasRole('superadmin'); }
  get isTecnicoAdmin(): boolean { return this.auth.hasRole('tecnico_admin'); }
  get isPlanificador(): boolean { return this.auth.hasRole('planificador'); }
  get isEvaluador(): boolean { return this.auth.hasRole('evaluador'); }
  get isJefeUe(): boolean { return this.auth.hasRole('jefe_ue'); }
  get isDirector(): boolean { return this.auth.hasRole('director'); }

  get rolDisplay(): string {
    if (this.isSuperAdmin) return 'Super Administrador';
    if (this.isTecnicoAdmin) return 'Técnico Admin';
    if (this.isPlanificador) return 'Planificador';
    if (this.isEvaluador) return 'Evaluador';
    if (this.isJefeUe) return 'Jefe de UE';
    if (this.isDirector) return 'Director';
    return 'Usuario';
  }

  constructor(
    private auth: AuthService,
    private api: ApiService,
  ) {}

  ngOnInit(): void {
    this.auth.user$.subscribe(user => {
      if (user) {
        this.userName = `${user.first_name} ${user.last_name}`.trim() || user.email;
        this.userEmail = user.email;
      }
    });
    this.cargarKpis();
    this.cargarNotificaciones();
  }

  cargarKpis(): void {
    this.cargando = true;
    this.error = '';
    this.api.get<any>('/dashboard/kpis/').subscribe({
      next: (data) => {
        this.kpis = data;
        this.cargando = false;
      },
      error: () => {
        this.kpis = {};
        this.cargando = false;
      },
    });
  }

  cargarNotificaciones(): void {
    this.api.get<any>('/notificaciones/resumen/').subscribe({
      next: (data) => {
        this.notifCount = data.no_leidas || 0;
      },
    });
  }
}

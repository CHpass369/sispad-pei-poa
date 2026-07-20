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
          <p class="text-secondary">{{ fechaActual | date:'fullDate' }}</p>
        </div>
        <div class="header-right">
          <span class="badge badge-role" *ngIf="rolLabel">{{ rolLabel }}</span>
          <div class="notif-bell" routerLink="/notificaciones">
            🔔 <span class="notif-count" *ngIf="notifCount > 0">{{ notifCount }}</span>
          </div>
        </div>
      </div>

      <div *ngIf="cargando" class="loading">Cargando dashboard...</div>
      <div class="alert alert-error" *ngIf="error">{{ error }}</div>

      <ng-container *ngIf="!cargando && kpis">
        <!-- Admin KPIs -->
        <div class="stats-grid">
          <div class="card stat-card">
            <div class="stat-icon">💰</div>
            <div class="stat-value">Bs {{ kpis.presupuesto_total | number:'1.0-0' }}</div>
            <div class="stat-label">Presupuesto Total</div>
          </div>
          <div class="card stat-card">
            <div class="stat-icon">📊</div>
            <div class="stat-value">{{ kpis.ejecucion_porcentaje || 0 }}%</div>
            <div class="stat-label">Ejecución Global</div>
          </div>
          <div class="card stat-card">
            <div class="stat-icon">⏳</div>
            <div class="stat-value">{{ kpis.aprobaciones_pendientes || 0 }}</div>
            <div class="stat-label">Aprobaciones Pendientes</div>
          </div>
          <div class="card stat-card">
            <div class="stat-icon">⚠️</div>
            <div class="stat-value">{{ kpis.alertas_count || 0 }}</div>
            <div class="stat-label">Alertas Activas</div>
          </div>
        </div>

        <!-- Quick Actions -->
        <div class="quick-actions">
          <h3>Acciones Rápidas</h3>
          <div class="actions-grid">
            <a routerLink="/planificacion" class="card action-card"><span>📝 Planificación</span></a>
            <a routerLink="/seguimiento" class="card action-card"><span>📊 Seguimiento</span></a>
            <a routerLink="/reportes" class="card action-card"><span>📈 Reportes</span></a>
            <a routerLink="/consolidacion" class="card action-card"><span>🔗 Consolidación</span></a>
          </div>
        </div>

        <!-- Profile Card -->
        <div class="card profile-card">
          <h3>Mi Perfil</h3>
          <div class="profile-info">
            <div class="profile-avatar">{{ userName.charAt(0) }}</div>
            <div class="profile-details">
              <strong>{{ userName }}</strong>
              <span>{{ userEmail }}</span>
            </div>
          </div>
        </div>
      </ng-container>
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
    .quick-actions { margin-bottom: 1.5rem; }
    .actions-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(140px, 1fr)); gap: 0.75rem; }
    .action-card { text-align: center; text-decoration: none; color: var(--text-primary); padding: 1rem; }
    .action-card:hover { background: #f5f5f5; }
    .profile-card { margin-bottom: 1.5rem; }
    .profile-info { display: flex; align-items: center; gap: 1rem; }
    .profile-avatar { width: 48px; height: 48px; border-radius: 50%; background: var(--primary); color: white; display: flex; align-items: center; justify-content: center; font-size: 1.25rem; font-weight: 700; }
    .profile-details { display: flex; flex-direction: column; gap: 0.25rem; }
    .profile-details strong { font-size: 0.9375rem; }
    .profile-details span { font-size: 0.8125rem; color: var(--text-secondary); }
    .loading { text-align: center; padding: 2rem; color: var(--text-secondary); }
    .alert { padding: 0.75rem 1rem; border-radius: 6px; margin-top: 1rem; }
    .alert-error { background: #FFEBEE; color: var(--warn); }
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
  rolLabel = '';

  constructor(
    private auth: AuthService,
    private api: ApiService,
  ) {}

  ngOnInit(): void {
    this.auth.user$.subscribe(user => {
      if (user) {
        this.userName = `${user.first_name} ${user.last_name}`.trim() || user.email;
        this.userEmail = user.email;
        this.rolLabel = user.roles_detalle?.length ? user.roles_detalle[0].nombre : 'Usuario';
      }
    });
    // Si el usuario no está cargado aún (login reciente), cargarlo
    if (!this.auth['userSubject'].value) {
      this.auth['loadUser']();
    }
    this.cargarKpis();
    this.cargarNotificaciones();
  }

  cargarKpis(): void {
    this.cargando = true;
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

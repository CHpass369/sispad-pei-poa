import { Component, OnInit } from '@angular/core';
import { NotificacionesService, Notificacion, ResumenNotificaciones } from './notificaciones.service';

@Component({
  standalone: false,
  selector: 'app-notificaciones-lista',
  template: `
    <div class="page-header">
      <h2>Notificaciones</h2>
      <p class="text-secondary">Centro de notificaciones del sistema</p>
    </div>
    
    <div class="acciones-superior">
      @if (resumen) {
        <span class="resumen-text">
          {{ resumen.no_leidas || 0 }} sin leer de {{ resumen.total || 0 }} total
        </span>
      }
      <button class="btn btn-primary" (click)="marcarTodasLeidas()"
        [disabled]="!resumen || (resumen.no_leidas || 0) === 0">
        Marcar todas como leídas
      </button>
      <button class="btn btn-outline" (click)="cargar()">Recargar</button>
    </div>
    
    @if (!cargando) {
      <div class="notificaciones-container">
        @for (n of notificaciones; track n) {
          <div class="card notificacion-item"
            [class.no-leida]="!n.leida" (click)="marcarLeida(n)">
            <div class="notificacion-header">
              <span class="badge badge-tipo" [ngClass]="'badge-' + (n.tipo || 'info')">{{ n.tipo || 'info' }}</span>
              <span class="notificacion-fecha">{{ n.fecha_creacion | date:'dd/MM/yyyy HH:mm' }}</span>
              @if (!n.leida) {
                <span class="notificacion-leida">●</span>
              }
            </div>
            <h4 class="notificacion-titulo">{{ n.titulo }}</h4>
            <p class="notificacion-mensaje">{{ n.mensaje }}</p>
            @if (n.enlace) {
              <a class="notificacion-enlace" [routerLink]="n.enlace">Ver detalle →</a>
            }
          </div>
        }
        @if (notificaciones.length === 0) {
          <div class="empty">
            No tienes notificaciones
          </div>
        }
      </div>
    }
    
    @if (cargando) {
      <div class="loading">Cargando notificaciones...</div>
    }
    @if (error) {
      <div class="alert alert-error">{{ error }}</div>
    }
    `,
  styles: [`
    .page-header { margin-bottom: 1rem; }
    .page-header h2 { font-size: 1.5rem; margin-bottom: 0.25rem; }
    .text-secondary { color: var(--text-secondary); font-size: 0.875rem; }
    .acciones-superior { display: flex; gap: 1rem; margin-bottom: 1.5rem; align-items: center; }
    .resumen-text { font-size: 0.875rem; color: var(--text-secondary); flex: 1; }
    .notificaciones-container { display: flex; flex-direction: column; gap: 0.75rem; }
    .notificacion-item { cursor: pointer; transition: transform 0.1s; padding: 1rem 1.25rem; }
    .notificacion-item:hover { transform: translateX(4px); }
    .notificacion-item.no-leida { border-left: 3px solid var(--primary); background: var(--primary-bg, #E8EAF6); }
    .notificacion-header { display: flex; align-items: center; gap: 0.5rem; margin-bottom: 0.5rem; }
    .notificacion-fecha { font-size: 0.75rem; color: var(--text-secondary); margin-left: auto; }
    .notificacion-leida { color: var(--primary); font-size: 1.25rem; line-height: 1; }
    .notificacion-titulo { font-size: 0.9375rem; margin-bottom: 0.375rem; }
    .notificacion-mensaje { font-size: 0.8125rem; color: var(--text-secondary); line-height: 1.4; margin-bottom: 0.5rem; }
    .notificacion-enlace { font-size: 0.8125rem; color: var(--primary); text-decoration: none; font-weight: 600; }
    .notificacion-enlace:hover { text-decoration: underline; }
    .badge { display: inline-block; padding: 0.125rem 0.5rem; border-radius: 4px; font-size: 0.6875rem; font-weight: 600; text-transform: uppercase; }
    .badge-info { background: var(--mdc-blue-50); color: var(--mdc-blue-800); }
    .badge-alerta, .badge-warning { background: var(--mdc-amber-50); color: #E65100; }
    .badge-error { background: var(--mdc-red-50); color: var(--mdc-red-800); }
    .badge-exito, .badge-success { background: var(--mdc-green-50); color: var(--mdc-green-800); }
    .badge-sistema { background: #F3E5F5; color: #6A1B9A; }
    .card { background: var(--surface); border: 1px solid var(--border); border-radius: 8px; }
    .btn { display: inline-flex; align-items: center; padding: 0.5rem 1rem; border-radius: 6px; border: none; font-size: 0.875rem; font-weight: 600; cursor: pointer; }
    .btn-primary { background: var(--primary); color: white; }
    .btn-primary:disabled { opacity: 0.5; cursor: not-allowed; }
    .btn-outline { background: transparent; border: 1px solid var(--border); color: var(--text-primary); }
    .btn-outline:hover { background: var(--hover, var(--neutro-fondo)); }
    .empty { text-align: center; padding: 3rem; color: var(--text-secondary); }
    .loading { text-align: center; padding: 2rem; color: var(--text-secondary); }
    .alert { padding: 0.75rem 1rem; border-radius: 6px; margin-top: 1rem; }
    .alert-error { background: var(--mdc-red-50); color: var(--warn); }
  `]
})
export class NotificacionesListaComponent implements OnInit {
  notificaciones: Notificacion[] = [];
  resumen: ResumenNotificaciones | null = null;
  cargando = true;
  error = '';

  constructor(private notificacionesService: NotificacionesService) {}

  ngOnInit(): void {
    this.cargar();
    this.cargarResumen();
  }

  cargar(): void {
    this.cargando = true;
    this.error = '';
    this.notificacionesService.listar().subscribe({
      next: (data: any) => {
        this.notificaciones = data.results || data;
        this.cargando = false;
      },
      error: () => {
        this.error = 'Error al cargar notificaciones';
        this.cargando = false;
      },
    });
  }

  cargarResumen(): void {
    this.notificacionesService.obtenerResumen().subscribe({
      next: (data) => {
        this.resumen = data;
      },
    });
  }

  marcarLeida(n: Notificacion): void {
    if (n.leida || !n.id) return;
    this.notificacionesService.marcarLeida(n.id).subscribe({
      next: () => {
        n.leida = true;
        if (this.resumen && this.resumen.no_leidas && this.resumen.no_leidas > 0) {
          this.resumen.no_leidas--;
        }
      },
    });
  }

  marcarTodasLeidas(): void {
    this.notificacionesService.marcarTodasLeidas().subscribe({
      next: () => {
        this.notificaciones.forEach(n => n.leida = true);
        if (this.resumen) this.resumen.no_leidas = 0;
      },
      error: () => {
        this.error = 'Error al marcar notificaciones';
      },
    });
  }
}

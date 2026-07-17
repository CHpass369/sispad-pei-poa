import { Component, OnInit } from '@angular/core';
import { SeguimientoService, Alerta } from './seguimiento.service';

@Component({
  standalone: false,
  selector: 'app-alertas-lista',
  template: `
    <div class="page-header">
      <h2>Alertas Activas</h2>
      <p class="text-secondary">Alertas del sistema que requieren atención</p>
    </div>

    <div class="lista" *ngIf="!cargando">
      <div class="card alerta-item" *ngFor="let a of alertas">
        <div class="alerta-header">
          <span class="badge" [ngClass]="'badge-' + a.severidad">{{ a.severidad }}</span>
          <span class="alerta-tipo">{{ a.tipo }}</span>
          <span class="alerta-fecha">{{ a.fecha_creacion | date:'dd/MM/yyyy HH:mm' }}</span>
        </div>
        <div class="alerta-body">
          <p class="alerta-mensaje">{{ a.mensaje }}</p>
          <span class="alerta-actividad" *ngIf="a.actividad_descripcion">
            Actividad: {{ a.actividad_descripcion }}
          </span>
        </div>
        <div class="alerta-actions">
          <button class="btn btn-sm btn-success" (click)="resolver(a)"
                  [disabled]="resolviendo === a.id">
            {{ resolviendo === a.id ? 'Resolviendo...' : 'Resolver' }}
          </button>
        </div>
      </div>
      <div *ngIf="alertas.length === 0" class="empty">No hay alertas activas</div>
    </div>

    <div class="loading" *ngIf="cargando">Cargando alertas...</div>
    <div class="alert alert-error" *ngIf="error">{{ error }}</div>
    <div class="alert alert-success" *ngIf="exito">{{ exito }}</div>
  `,
  styles: [`
    .page-header { margin-bottom: 1.5rem; }
    .page-header h2 { font-size: 1.5rem; margin-bottom: 0.25rem; }
    .text-secondary { color: var(--text-secondary); font-size: 0.875rem; }
    .lista { display: flex; flex-direction: column; gap: 0.75rem; }
    .alerta-item { padding: 1rem 1.25rem; }
    .alerta-header { display: flex; align-items: center; gap: 0.75rem; margin-bottom: 0.5rem; }
    .alerta-tipo { font-size: 0.8125rem; font-weight: 600; }
    .alerta-fecha { margin-left: auto; font-size: 0.75rem; color: var(--text-secondary); }
    .alerta-body { margin-bottom: 0.75rem; }
    .alerta-mensaje { font-size: 0.875rem; margin-bottom: 0.25rem; }
    .alerta-actividad { font-size: 0.8125rem; color: var(--text-secondary); }
    .alerta-actions { display: flex; justify-content: flex-end; }
    .badge { display: inline-block; padding: 0.125rem 0.5rem; border-radius: 4px; font-size: 0.75rem; font-weight: 600; text-transform: uppercase; }
    .badge-alta, .badge-alto { background: #FFEBEE; color: #C62828; }
    .badge-media, .badge-medio { background: #FFF3E0; color: #E65100; }
    .badge-baja, .badge-bajo { background: #E8F5E9; color: #2E7D32; }
    .btn { display: inline-flex; align-items: center; padding: 0.5rem 1rem; border-radius: 6px; border: none; font-size: 0.875rem; font-weight: 600; cursor: pointer; }
    .btn-sm { padding: 0.25rem 0.5rem; font-size: 0.8125rem; }
    .btn-success { background: #2E7D32; color: white; }
    .btn-success:disabled { opacity: 0.5; cursor: not-allowed; }
    .empty { text-align: center; padding: 2rem; color: var(--text-secondary); }
    .loading { text-align: center; padding: 2rem; color: var(--text-secondary); }
    .alert { padding: 0.75rem 1rem; border-radius: 6px; margin-top: 1rem; }
    .alert-error { background: #FFEBEE; color: var(--warn); }
    .alert-success { background: #E8F5E9; color: #2E7D32; }
  `]
})
export class AlertasListaComponent implements OnInit {
  alertas: Alerta[] = [];
  cargando = true;
  error = '';
  exito = '';
  resolviendo: number | null = null;

  constructor(private seguimientoService: SeguimientoService) {}

  ngOnInit(): void {
    this.cargar();
  }

  cargar(): void {
    this.cargando = true;
    this.seguimientoService.listarAlertasActivas().subscribe({
      next: (data: any) => {
        this.alertas = data.results || data;
        this.cargando = false;
      },
      error: () => {
        this.error = 'Error al cargar alertas';
        this.cargando = false;
      },
    });
  }

  resolver(alerta: Alerta): void {
    if (!confirm('¿Marcar esta alerta como resuelta?')) return;
    this.resolviendo = alerta.id!;
    this.error = '';
    this.exito = '';
    this.seguimientoService.resolverAlerta(alerta.id!).subscribe({
      next: () => {
        this.exito = 'Alerta resuelta correctamente';
        this.resolviendo = null;
        this.cargar();
      },
      error: () => {
        this.error = 'Error al resolver alerta';
        this.resolviendo = null;
      },
    });
  }
}

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
    
    @if (!cargando) {
      <div class="lista">
        @for (a of alertas; track a) {
          <div class="card alerta-item">
            <div class="alerta-header">
              <span class="badge" [ngClass]="'badge-' + a.severidad">{{ a.severidad }}</span>
              <span class="alerta-tipo">{{ a.tipo }}</span>
              <span class="alerta-fecha">{{ a.fecha_creacion | date:'dd/MM/yyyy HH:mm' }}</span>
            </div>
            <div class="alerta-body">
              <p class="alerta-mensaje">{{ a.mensaje }}</p>
              @if (a.actividad_descripcion) {
                <span class="alerta-actividad">
                  Actividad: {{ a.actividad_descripcion }}
                </span>
              }
            </div>
            <div class="alerta-actions">
              <button class="btn btn-sm btn-success" (click)="resolver(a)"
                [disabled]="resolviendo === a.id">
                {{ resolviendo === a.id ? 'Resolviendo...' : 'Resolver' }}
              </button>
            </div>
          </div>
        }
        @if (alertas.length === 0) {
          <div class="empty">No hay alertas activas</div>
        }
      </div>
    }
    
    @if (cargando) {
      <div class="loading">Cargando alertas...</div>
    }
    @if (error) {
      <div class="alert alert-error">{{ error }}</div>
    }
    @if (exito) {
      <div class="alert alert-success">{{ exito }}</div>
    }
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
    .badge-alta, .badge-alto { background: var(--mdc-red-50); color: var(--mdc-red-800); }
    .badge-media, .badge-medio { background: var(--mdc-amber-50); color: #E65100; }
    .badge-baja, .badge-bajo { background: var(--mdc-green-50); color: var(--mdc-green-800); }
    .btn { display: inline-flex; align-items: center; padding: 0.5rem 1rem; border-radius: 6px; border: none; font-size: 0.875rem; font-weight: 600; cursor: pointer; }
    .btn-sm { padding: 0.25rem 0.5rem; font-size: 0.8125rem; }
    .btn-success { background: var(--mdc-green-800); color: white; }
    .btn-success:disabled { opacity: 0.5; cursor: not-allowed; }
    .empty { text-align: center; padding: 2rem; color: var(--text-secondary); }
    .loading { text-align: center; padding: 2rem; color: var(--text-secondary); }
    .alert { padding: 0.75rem 1rem; border-radius: 6px; margin-top: 1rem; }
    .alert-error { background: var(--mdc-red-50); color: var(--warn); }
    .alert-success { background: var(--mdc-green-50); color: var(--mdc-green-800); }
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

import { Component, OnInit } from '@angular/core';
import { ActivatedRoute } from '@angular/router';
import { ModificacionesService, SolicitudModificacion } from './modificaciones.service';

@Component({
  standalone: false,
  selector: 'app-modificacion-detalle',
  template: `
    <div class="page-header" *ngIf="solicitud">
      <h2>Detalle de Modificación</h2>
      <p class="text-secondary">{{ solicitud.tipo }} — {{ solicitud.entidad }}</p>
    </div>

    <div class="info-grid" *ngIf="solicitud">
      <div class="card info-item">
        <label>Tipo</label>
        <span>{{ solicitud.tipo }}</span>
      </div>
      <div class="card info-item">
        <label>Entidad</label>
        <span>{{ solicitud.entidad }}</span>
      </div>
      <div class="card info-item">
        <label>Estado</label>
        <span class="badge" [ngClass]="'badge-' + solicitud.estado">{{ solicitud.estado }}</span>
      </div>
      <div class="card info-item">
        <label>Solicitado por</label>
        <span>{{ solicitud.solicitado_por_nombre || solicitud.solicitado_por }}</span>
      </div>
      <div class="card info-item">
        <label>Fecha Solicitud</label>
        <span>{{ solicitud.fecha_solicitud | date:'dd/MM/yyyy HH:mm' }}</span>
      </div>
      <div class="card info-item" *ngIf="solicitud.fecha_resolucion">
        <label>Fecha Resolución</label>
        <span>{{ solicitud.fecha_resolucion | date:'dd/MM/yyyy HH:mm' }}</span>
      </div>
      <div class="card info-item full-width" *ngIf="solicitud.motivo">
        <label>Motivo</label>
        <span>{{ solicitud.motivo }}</span>
      </div>
      <div class="card info-item full-width" *ngIf="solicitud.informe_tecnico">
        <label>Informe Técnico</label>
        <span>{{ solicitud.informe_tecnico }}</span>
      </div>
      <div class="card info-item full-width" *ngIf="solicitud.observaciones">
        <label>Observaciones</label>
        <span>{{ solicitud.observaciones }}</span>
      </div>
    </div>

    <div class="seccion" *ngIf="solicitud && solicitud.estado === 'pendiente'">
      <h3>Acciones de Resolución</h3>
      <div class="form-card">
        <div class="field">
          <label>Observaciones de resolución</label>
          <textarea [(ngModel)]="observacionesResolucion" class="form-control"
                    rows="3" placeholder="Ingrese observaciones..."></textarea>
        </div>
        <div class="acciones-resolucion">
          <button class="btn btn-success" (click)="aprobar()" [disabled]="procesando">
            {{ procesando ? 'Procesando...' : 'Aprobar' }}
          </button>
          <button class="btn btn-danger" (click)="rechazar()" [disabled]="procesando">
            {{ procesando ? 'Procesando...' : 'Rechazar' }}
          </button>
        </div>
      </div>
    </div>

    <div class="loading" *ngIf="cargando">Cargando detalle...</div>
    <div class="alert alert-error" *ngIf="error">{{ error }}</div>
    <div class="alert alert-success" *ngIf="exito">{{ exito }}</div>
  `,
  styles: [`
    .page-header { margin-bottom: 1.5rem; }
    .page-header h2 { font-size: 1.5rem; margin-bottom: 0.25rem; }
    .text-secondary { color: var(--text-secondary); font-size: 0.875rem; }
    .info-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1rem; margin-bottom: 2rem; }
    .card { background: var(--surface); border: 1px solid var(--border); border-radius: 8px; }
    .info-item { padding: 1rem 1.25rem; }
    .info-item label { display: block; font-size: 0.75rem; text-transform: uppercase; color: var(--text-secondary); margin-bottom: 0.375rem; }
    .info-item span { font-size: 0.9375rem; font-weight: 500; }
    .info-item.full-width { grid-column: 1 / -1; }
    .badge { display: inline-block; padding: 0.125rem 0.5rem; border-radius: 4px; font-size: 0.75rem; }
    .badge-pendiente { background: #FFF3E0; color: #E65100; }
    .badge-aprobada { background: #E8F5E9; color: #2E7D32; }
    .badge-rechazada { background: #FFEBEE; color: #C62828; }
    .badge-en_revision, .badge-en-revision { background: #E3F2FD; color: #1565C0; }
    .seccion { margin-bottom: 2rem; }
    .seccion h3 { font-size: 1.125rem; margin-bottom: 1rem; }
    .form-card { padding: 1.25rem; }
    .field { display: flex; flex-direction: column; margin-bottom: 1rem; }
    .field label { font-size: 0.8125rem; font-weight: 600; margin-bottom: 0.375rem; color: var(--text-primary); }
    .form-control { padding: 0.5rem 0.75rem; border: 1px solid var(--border); border-radius: 6px; font-size: 0.875rem; }
    .form-control:focus { outline: none; border-color: var(--primary); }
    textarea.form-control { resize: vertical; }
    .acciones-resolucion { display: flex; gap: 0.75rem; justify-content: flex-end; }
    .btn { display: inline-flex; align-items: center; padding: 0.5rem 1rem; border-radius: 6px; border: none; font-size: 0.875rem; font-weight: 600; cursor: pointer; }
    .btn-success { background: #2E7D32; color: white; }
    .btn-success:hover { background: #1B5E20; }
    .btn-success:disabled, .btn-danger:disabled { opacity: 0.5; cursor: not-allowed; }
    .btn-danger { background: #C62828; color: white; }
    .btn-danger:hover { background: #B71C1C; }
    .loading { text-align: center; padding: 2rem; color: var(--text-secondary); }
    .alert { padding: 0.75rem 1rem; border-radius: 6px; margin-top: 1rem; }
    .alert-error { background: #FFEBEE; color: var(--warn); }
    .alert-success { background: #E8F5E9; color: #2E7D32; }
  `]
})
export class ModificacionDetalleComponent implements OnInit {
  solicitud: SolicitudModificacion | null = null;
  observacionesResolucion = '';
  cargando = true;
  procesando = false;
  error = '';
  exito = '';

  constructor(
    private modificacionesService: ModificacionesService,
    private route: ActivatedRoute,
  ) {}

  ngOnInit(): void {
    const id = +this.route.snapshot.paramMap.get('id')!;
    this.cargarDetalle(id);
  }

  cargarDetalle(id: number): void {
    this.modificacionesService.obtener(id).subscribe({
      next: (data) => {
        this.solicitud = data;
        this.cargando = false;
      },
      error: () => {
        this.error = 'Error al cargar solicitud';
        this.cargando = false;
      },
    });
  }

  aprobar(): void {
    if (!this.solicitud?.id) return;
    if (!confirm('¿Aprobar esta solicitud de modificación?')) return;
    this.procesando = true;
    this.error = '';
    this.exito = '';
    this.modificacionesService.aprobar(this.solicitud.id, {
      observaciones: this.observacionesResolucion,
    }).subscribe({
      next: () => {
        this.exito = 'Solicitud aprobada correctamente';
        this.procesando = false;
        this.cargarDetalle(this.solicitud!.id!);
      },
      error: (e) => {
        this.error = e.error?.detail || 'Error al aprobar solicitud';
        this.procesando = false;
      },
    });
  }

  rechazar(): void {
    if (!this.solicitud?.id) return;
    if (!confirm('¿Rechazar esta solicitud de modificación?')) return;
    this.procesando = true;
    this.error = '';
    this.exito = '';
    this.modificacionesService.rechazar(this.solicitud.id, {
      observaciones: this.observacionesResolucion,
    }).subscribe({
      next: () => {
        this.exito = 'Solicitud rechazada';
        this.procesando = false;
        this.cargarDetalle(this.solicitud!.id!);
      },
      error: (e) => {
        this.error = e.error?.detail || 'Error al rechazar solicitud';
        this.procesando = false;
      },
    });
  }
}

import { Component } from '@angular/core';
import { Router } from '@angular/router';
import { ModificacionesService, SolicitudModificacion } from './modificaciones.service';

@Component({
  standalone: false,
  selector: 'app-modificacion-form',
  template: `
    <div class="page-header">
      <h2>Nueva Solicitud de Modificación</h2>
      <p class="text-secondary">Registrar una solicitud de modificación al plan</p>
    </div>

    <div class="form-card">
      <form (ngSubmit)="guardar()">
        <div class="form-grid">
          <div class="field">
            <label>Tipo de Modificación *</label>
            <select [(ngModel)]="solicitud.tipo" name="tipo" class="form-control" required>
              <option value="">Seleccione...</option>
              <option value="ampliacion">Ampliación</option>
              <option value="reduccion">Reducción</option>
              <option value="sustitucion">Sustitución</option>
              <option value="transferencia">Transferencia</option>
            </select>
          </div>
          <div class="field">
            <label>Entidad Afectada *</label>
            <input [(ngModel)]="solicitud.entidad" name="entidad" class="form-control"
                   placeholder="Nombre de la entidad" required>
          </div>
          <div class="field field-full">
            <label>Motivo *</label>
            <textarea [(ngModel)]="solicitud.motivo" name="motivo" class="form-control"
                      rows="3" placeholder="Describa el motivo de la modificación" required></textarea>
          </div>
          <div class="field field-full">
            <label>Informe Técnico</label>
            <textarea [(ngModel)]="solicitud.informe_tecnico" name="informe_tecnico" class="form-control"
                      rows="4" placeholder="Detalle técnico de la modificación propuesta"></textarea>
          </div>
          <div class="field field-full">
            <label>Observaciones</label>
            <textarea [(ngModel)]="solicitud.observaciones" name="observaciones" class="form-control"
                      rows="2"></textarea>
          </div>
        </div>

        <div class="form-actions">
          <button type="button" class="btn btn-outline" (click)="cancelar()">Cancelar</button>
          <button type="submit" class="btn btn-primary" [disabled]="guardando">
            {{ guardando ? 'Enviando...' : 'Enviar Solicitud' }}
          </button>
        </div>
      </form>
    </div>

    <div class="alert alert-error" *ngIf="error">{{ error }}</div>
  `,
  styles: [`
    .page-header { margin-bottom: 1rem; }
    .page-header h2 { font-size: 1.5rem; margin-bottom: 0.25rem; }
    .text-secondary { color: var(--text-secondary); font-size: 0.875rem; }
    .form-card { background: var(--surface); border: 1px solid var(--border); border-radius: 8px; padding: 1.5rem; }
    .form-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; }
    .field { display: flex; flex-direction: column; margin-bottom: 1rem; }
    .field-full { grid-column: 1 / -1; }
    .field label { font-size: 0.8125rem; font-weight: 600; margin-bottom: 0.375rem; color: var(--text-primary); }
    .form-control { padding: 0.5rem 0.75rem; border: 1px solid var(--border); border-radius: 6px; font-size: 0.875rem; }
    .form-control:focus { outline: none; border-color: var(--primary); }
    textarea.form-control { resize: vertical; }
    .form-actions { display: flex; justify-content: flex-end; gap: 0.75rem; margin-top: 1.5rem; }
    .btn { display: inline-flex; align-items: center; padding: 0.5rem 1rem; border-radius: 6px; border: none; font-size: 0.875rem; font-weight: 600; cursor: pointer; }
    .btn-primary { background: var(--primary); color: white; }
    .btn-primary:disabled { opacity: 0.5; cursor: not-allowed; }
    .btn-outline { background: transparent; border: 1px solid var(--border); color: var(--text-primary); }
    .btn-outline:hover { background: var(--hover, #f5f5f5); }
    .alert { padding: 0.75rem 1rem; border-radius: 6px; margin-top: 1rem; }
    .alert-error { background: #FFEBEE; color: var(--warn); }
  `]
})
export class ModificacionFormComponent {
  solicitud: Partial<SolicitudModificacion> = {};
  guardando = false;
  error = '';

  constructor(
    private modificacionesService: ModificacionesService,
    private router: Router,
  ) {}

  guardar(): void {
    if (!this.solicitud.tipo || !this.solicitud.entidad || !this.solicitud.motivo) {
      this.error = 'Tipo, entidad y motivo son obligatorios';
      return;
    }
    this.guardando = true;
    this.error = '';
    this.modificacionesService.crear(this.solicitud).subscribe({
      next: () => {
        this.router.navigate(['modificaciones']);
      },
      error: (e) => {
        this.error = e.error?.detail || 'Error al crear solicitud';
        this.guardando = false;
      },
    });
  }

  cancelar(): void {
    this.router.navigate(['modificaciones']);
  }
}

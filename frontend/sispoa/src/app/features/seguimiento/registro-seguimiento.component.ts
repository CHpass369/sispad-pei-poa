import { Component, OnInit } from '@angular/core';
import { SeguimientoService, ReporteSeguimiento } from './seguimiento.service';

@Component({
  standalone: false,
  selector: 'app-registro-seguimiento',
  template: `
    <div class="page-header">
      <h2>Registrar Seguimiento</h2>
      <p class="text-secondary">Registrar avance físico y financiero de actividades</p>
    </div>

    <div class="form-card">
      <form (ngSubmit)="guardar()">
        <div class="form-grid">
          <div class="field field-full">
            <label>Actividad *</label>
            <select [(ngModel)]="reporte.actividad" name="actividad" class="form-control" required>
              <option [ngValue]="undefined">Seleccione una actividad</option>
            </select>
          </div>
          <div class="field">
            <label>Avance Físico (%)</label>
            <input type="number" [(ngModel)]="reporte.avance_fisico" name="avance_fisico"
                   class="form-control" min="0" max="100" step="0.01">
          </div>
          <div class="field">
            <label>Avance Financiero (%)</label>
            <input type="number" [(ngModel)]="reporte.avance_financiero" name="avance_financiero"
                   class="form-control" min="0" max="100" step="0.01">
          </div>
          <div class="field">
            <label>Monto Ejecutado (Bs.)</label>
            <input type="number" [(ngModel)]="reporte.monto_ejecutado" name="monto_ejecutado"
                   class="form-control" min="0" step="0.01">
          </div>
          <div class="field">
            <label>Monto Programado (Bs.)</label>
            <input type="number" [(ngModel)]="reporte.monto_programado" name="monto_programado"
                   class="form-control" min="0" step="0.01">
          </div>
          <div class="field field-full">
            <label>Observaciones</label>
            <textarea [(ngModel)]="reporte.observaciones" name="observaciones"
                      class="form-control" rows="3"></textarea>
          </div>
        </div>

        <div class="form-actions">
          <button type="button" class="btn btn-outline" (click)="limpiar()">Limpiar</button>
          <button type="submit" class="btn btn-primary" [disabled]="guardando">
            {{ guardando ? 'Guardando...' : 'Registrar' }}
          </button>
        </div>
      </form>
    </div>

    <div class="alert alert-success" *ngIf="exito">{{ exito }}</div>
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
    .alert-success { background: #E8F5E9; color: #2E7D32; }
  `]
})
export class RegistroSeguimientoComponent implements OnInit {
  reporte: Partial<ReporteSeguimiento> = {};
  guardando = false;
  exito = '';
  error = '';

  constructor(private seguimientoService: SeguimientoService) {}

  ngOnInit(): void {}

  guardar(): void {
    if (!this.reporte.actividad) {
      this.error = 'Debe seleccionar una actividad';
      return;
    }
    this.guardando = true;
    this.error = '';
    this.exito = '';
    this.seguimientoService.crearReporte(this.reporte).subscribe({
      next: () => {
        this.exito = 'Seguimiento registrado correctamente';
        this.guardando = false;
        this.limpiar();
      },
      error: (e) => {
        this.error = e.error?.detail || 'Error al registrar seguimiento';
        this.guardando = false;
      },
    });
  }

  limpiar(): void {
    this.reporte = {};
  }
}

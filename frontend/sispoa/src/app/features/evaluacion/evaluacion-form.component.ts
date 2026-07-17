import { Component } from '@angular/core';
import { Router } from '@angular/router';
import { EvaluacionService, Evaluacion } from './evaluacion.service';

@Component({
  standalone: false,
  selector: 'app-evaluacion-form',
  template: `
    <div class="page-header">
      <h2>Nueva Evaluación</h2>
      <p class="text-secondary">Crear una nueva evaluación del plan</p>
    </div>

    <div class="form-card">
      <form (ngSubmit)="guardar()">
        <div class="form-grid">
          <div class="field">
            <label>Tipo de Evaluación *</label>
            <select [(ngModel)]="evaluacion.tipo" name="tipo" class="form-control" required>
              <option value="">Seleccione...</option>
              <option value="formativa">Formativa</option>
              <option value="sumativa">Sumativa</option>
              <option value="global">Global</option>
            </select>
          </div>
          <div class="field">
            <label>Periodo *</label>
            <input [(ngModel)]="evaluacion.periodo" name="periodo" class="form-control"
                   placeholder="Ej: 2026-S1" required>
          </div>
          <div class="field">
            <label>Responsable</label>
            <input [(ngModel)]="evaluacion.responsable" name="responsable" class="form-control"
                   placeholder="Nombre del responsable">
          </div>
          <div class="field">
            <label>Estado</label>
            <select [(ngModel)]="evaluacion.estado" name="estado" class="form-control">
              <option value="borrador">Borrador</option>
              <option value="en_curso">En Curso</option>
              <option value="completada">Completada</option>
            </select>
          </div>
          <div class="field field-full">
            <label>Observaciones</label>
            <textarea [(ngModel)]="evaluacion.observaciones" name="observaciones"
                      class="form-control" rows="3"></textarea>
          </div>
        </div>

        <div class="form-actions">
          <button type="button" class="btn btn-outline" (click)="cancelar()">Cancelar</button>
          <button type="submit" class="btn btn-primary" [disabled]="guardando">
            {{ guardando ? 'Guardando...' : 'Crear Evaluación' }}
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
export class EvaluacionFormComponent {
  evaluacion: Partial<Evaluacion> = {};
  guardando = false;
  error = '';

  constructor(
    private evaluacionService: EvaluacionService,
    private router: Router,
  ) {}

  guardar(): void {
    if (!this.evaluacion.tipo || !this.evaluacion.periodo) {
      this.error = 'Tipo y periodo son obligatorios';
      return;
    }
    this.guardando = true;
    this.error = '';
    this.evaluacionService.crear(this.evaluacion).subscribe({
      next: () => {
        this.router.navigate(['evaluacion']);
      },
      error: (e) => {
        this.error = e.error?.detail || 'Error al crear evaluación';
        this.guardando = false;
      },
    });
  }

  cancelar(): void {
    this.router.navigate(['evaluacion']);
  }
}

import { Component } from '@angular/core';
import { Router } from '@angular/router';
import { RecursosService, Recurso } from './recursos.service';

@Component({
  standalone: false,
  selector: 'app-recursos-form',
  template: `
    <div class="page-header">
      <h2>Nuevo Recurso</h2>
      <p class="text-secondary">Registrar o estimar un nuevo recurso</p>
    </div>

    <div class="form-card">
      <form (ngSubmit)="guardar()">
        <div class="form-grid">
          <div class="field">
            <label>Tipo de Recurso *</label>
            <select [(ngModel)]="recurso.tipo" name="tipo" class="form-control" required>
              <option value="">Seleccione...</option>
              <option value="humano">Humano</option>
              <option value="material">Material</option>
              <option value="tecnologico">Tecnológico</option>
              <option value="financiero">Financiero</option>
              <option value="infraestructura">Infraestructura</option>
            </select>
          </div>
          <div class="field">
            <label>Nombre *</label>
            <input [(ngModel)]="recurso.nombre" name="nombre" class="form-control"
                   placeholder="Nombre del recurso" required>
          </div>
          <div class="field">
            <label>Cantidad</label>
            <input type="number" [(ngModel)]="recurso.cantidad" name="cantidad" class="form-control"
                   placeholder="0" min="0">
          </div>
          <div class="field">
            <label>Unidad</label>
            <select [(ngModel)]="recurso.unidad" name="unidad" class="form-control">
              <option value="">Seleccione...</option>
              <option value="unidad">Unidad</option>
              <option value="kg">Kilogramo</option>
              <option value="lt">Litro</option>
              <option value="m2">Metro cuadrado</option>
              <option value="m3">Metro cúbico</option>
              <option value="hora">Hora</option>
              <option value="dia">Día</option>
              <option value="mes">Mes</option>
              <option value="par">Par</option>
              <option value="jornal">Jornal</option>
            </select>
          </div>
          <div class="field">
            <label>Costo Estimado (Bs.)</label>
            <input type="number" [(ngModel)]="recurso.costo_estimado" name="costo_estimado"
                   class="form-control" placeholder="0.00" min="0" step="0.01">
          </div>
          <div class="field">
            <label>Periodo</label>
            <input [(ngModel)]="recurso.periodo" name="periodo" class="form-control"
                   placeholder="Ej: 2026-S1">
          </div>
          <div class="field">
            <label>Responsable</label>
            <input [(ngModel)]="recurso.responsable" name="responsable" class="form-control"
                   placeholder="Nombre del responsable">
          </div>
          <div class="field">
            <label>Disponibilidad</label>
            <select [(ngModel)]="recurso.disponibilidad" name="disponibilidad" class="form-control">
              <option value="disponible">Disponible</option>
              <option value="asignado">Asignado</option>
              <option value="agotado">Agotado</option>
            </select>
          </div>
          <div class="field field-full">
            <label>Descripción</label>
            <textarea [(ngModel)]="recurso.descripcion" name="descripcion" class="form-control" rows="3"
                      placeholder="Descripción del recurso"></textarea>
          </div>
        </div>

        <div class="form-actions">
          <button type="button" class="btn btn-outline" (click)="cancelar()">Cancelar</button>
          <button type="submit" class="btn btn-primary" [disabled]="guardando">
            {{ guardando ? 'Guardando...' : 'Guardar Recurso' }}
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
export class RecursosFormComponent {
  recurso: Partial<Recurso> = { tipo: '', nombre: '', disponibilidad: 'disponible' };
  guardando = false;
  error = '';

  constructor(
    private recursosService: RecursosService,
    private router: Router,
  ) {}

  guardar(): void {
    if (!this.recurso.tipo || !this.recurso.nombre) {
      this.error = 'El tipo y nombre son obligatorios';
      return;
    }
    this.guardando = true;
    this.error = '';
    this.recursosService.crear(this.recurso).subscribe({
      next: () => {
        this.router.navigate(['recursos']);
      },
      error: (e) => {
        this.error = e.error?.detail || 'Error al guardar recurso';
        this.guardando = false;
      },
    });
  }

  cancelar(): void {
    this.router.navigate(['recursos']);
  }
}

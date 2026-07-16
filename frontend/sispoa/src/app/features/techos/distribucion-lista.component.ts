import { Component, OnInit } from '@angular/core';
import { ApiService } from '../../core/services/api.service';

@Component({
  standalone: false,
  selector: 'app-distribucion-lista',
  template: `
    <div class="distribucion-lista">
      <div class="page-header">
        <h2>Distribución de Techos</h2>
        <p class="text-secondary">Asignación de techos por unidad organizacional</p>
      </div>

      <!-- Loading -->
      <div class="loading" *ngIf="!items && !error && !showForm">
        <p>Cargando distribuciones...</p>
      </div>

      <!-- Error -->
      <div class="alert alert-error" *ngIf="error">
        {{ error }}
      </div>

      <!-- Save Success -->
      <div class="alert alert-success" *ngIf="successMsg">
        {{ successMsg }}
      </div>

      <!-- Table Section -->
      <div *ngIf="items">
        <div class="toolbar">
          <h3>Distribuciones registradas</h3>
          <button class="btn btn-primary" (click)="openForm()">
            + Nueva Distribución
          </button>
        </div>

        <div class="table-responsive">
          <table>
            <thead>
              <tr>
                <th>Unidad / DA / UE</th>
                <th>Monto Asignado (Bs)</th>
                <th>Gestión</th>
                <th>Acciones</th>
              </tr>
            </thead>
            <tbody>
              <tr *ngFor="let d of items">
                <td>{{ d.unidad_nombre }}</td>
                <td class="text-right">{{ d.monto | number:'1.2-2' }}</td>
                <td>{{ d.gestion }}</td>
                <td>
                  <button class="btn btn-sm btn-outline" (click)="editForm(d)">Editar</button>
                </td>
              </tr>
              <tr *ngIf="items.length === 0">
                <td colspan="4" class="empty">No hay distribuciones registradas</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- Form Section -->
      <div class="form-section" *ngIf="showForm">
        <h3>{{ editingId ? 'Editar' : 'Nueva' }} Distribución</h3>
        <form (ngSubmit)="onSubmit()" #distForm="ngForm">
          <div class="form-group">
            <label for="unidad">Unidad / DA / UE</label>
            <select id="unidad" [(ngModel)]="formData.unidad_id" name="unidad_id" required class="form-control">
              <option value="" disabled>Seleccione una unidad...</option>
              <option *ngFor="let u of unidades" [value]="u.id">{{ u.nombre }}</option>
            </select>
          </div>

          <div class="form-group">
            <label for="monto">Monto (Bs)</label>
            <input
              id="monto"
              type="number"
              step="0.01"
              [(ngModel)]="formData.monto"
              name="monto"
              required
              min="0"
              class="form-control"
              placeholder="0.00"
            />
          </div>

          <div class="form-group">
            <label for="gestionForm">Gestión</label>
            <select id="gestionForm" [(ngModel)]="formData.gestion" name="gestion" required class="form-control">
              <option *ngFor="let g of gestiones" [value]="g">{{ g }}</option>
            </select>
          </div>

          <div class="form-actions">
            <button type="submit" class="btn btn-primary" [disabled]="!distForm.form.valid">
              {{ editingId ? 'Actualizar' : 'Guardar' }}
            </button>
            <button type="button" class="btn btn-outline" (click)="cancelForm()">Cancelar</button>
          </div>

          <div class="alert alert-error" *ngIf="formError">
            {{ formError }}
          </div>
        </form>
      </div>
    </div>
  `,
  styles: [`
    .page-header { margin-bottom: 1.5rem; }
    .page-header h2 { font-size: 1.5rem; margin-bottom: 0.25rem; }
    .text-secondary { color: var(--text-secondary); font-size: 0.875rem; }
    .toolbar { display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem; }
    .toolbar h3 { font-size: 1rem; }
    .btn { padding: 0.5rem 1rem; border-radius: 6px; border: none; font-size: 0.875rem; cursor: pointer; font-weight: 500; }
    .btn-primary { background: var(--primary); color: white; }
    .btn-primary:disabled { opacity: 0.5; cursor: not-allowed; }
    .btn-outline { background: transparent; border: 1px solid var(--border); color: var(--text-primary); }
    .btn-sm { padding: 0.25rem 0.625rem; font-size: 0.75rem; }
    .table-responsive { overflow-x: auto; margin-bottom: 2rem; }
    table { width: 100%; border-collapse: collapse; }
    th, td { padding: 0.625rem 0.75rem; text-align: left; border-bottom: 1px solid var(--border); }
    th { font-size: 0.75rem; color: var(--text-secondary); text-transform: uppercase; }
    .text-right { text-align: right; font-weight: 600; }
    .empty { text-align: center; padding: 2rem; color: var(--text-secondary); }
    .form-section { background: var(--surface); border: 1px solid var(--border); border-radius: 8px; padding: 1.5rem; margin-top: 1rem; }
    .form-section h3 { font-size: 1rem; margin-bottom: 1.25rem; }
    .form-group { margin-bottom: 1rem; }
    .form-group label { display: block; font-size: 0.8125rem; font-weight: 500; margin-bottom: 0.375rem; color: var(--text-secondary); }
    .form-control { width: 100%; max-width: 400px; padding: 0.5rem 0.75rem; border: 1px solid var(--border); border-radius: 6px; font-size: 0.875rem; background: var(--bg); color: var(--text-primary); }
    .form-control:focus { outline: none; border-color: var(--primary); }
    .form-actions { display: flex; gap: 0.75rem; margin-top: 1.5rem; }
    .loading { text-align: center; padding: 3rem; color: var(--text-secondary); }
    .alert { padding: 0.75rem 1rem; border-radius: 6px; margin-top: 1rem; }
    .alert-error { background: #FFEBEE; color: var(--warn); }
    .alert-success { background: #E8F5E9; color: #2E7D32; margin-bottom: 1rem; }
  `]
})
export class DistribucionListaComponent implements OnInit {
  items: any[] | null = null;
  unidades: any[] = [];
  gestiones = [2024, 2025, 2026, 2027];
  showForm = false;
  editingId: number | null = null;

  formData = { unidad_id: '', monto: null, gestion: 2026 };
  formError = '';
  successMsg = '';
  error = '';

  constructor(private api: ApiService) {}

  ngOnInit(): void {
    this.load();
    this.loadUnidades();
  }

  private load(): void {
    this.api.get<any[]>('/distribucion-techos/').subscribe({
      next: d => this.items = d,
      error: e => this.error = 'Error al cargar distribuciones: ' + (e.message || e),
    });
  }

  private loadUnidades(): void {
    this.api.get<any[]>('/unidades-organizacionales/').subscribe({
      next: d => this.unidades = d,
    });
  }

  openForm(): void {
    this.showForm = true;
    this.editingId = null;
    this.formData = { unidad_id: '', monto: null, gestion: 2026 };
    this.formError = '';
  }

  editForm(d: any): void {
    this.showForm = true;
    this.editingId = d.id;
    this.formData = {
      unidad_id: d.unidad_id,
      monto: d.monto,
      gestion: d.gestion,
    };
    this.formError = '';
  }

  cancelForm(): void {
    this.showForm = false;
    this.editingId = null;
    this.formData = { unidad_id: '', monto: null, gestion: 2026 };
    this.formError = '';
  }

  onSubmit(): void {
    this.formError = '';
    this.successMsg = '';

    const body = {
      unidad_id: this.formData.unidad_id,
      monto: this.formData.monto,
      gestion: this.formData.gestion,
    };

    const request = this.editingId
      ? this.api.put(`/distribucion-techos/${this.editingId}/`, body)
      : this.api.post('/distribucion-techos/', body);

    request.subscribe({
      next: () => {
        this.successMsg = this.editingId
          ? 'Distribución actualizada correctamente'
          : 'Distribución creada correctamente';
        this.showForm = false;
        this.editingId = null;
        this.load();
      },
      error: e => this.formError = 'Error al guardar: ' + (e.message || e),
    });
  }
}

import { Component, OnInit } from '@angular/core';
import { ApiService } from '../../core/services/api.service';

@Component({
  standalone: false,
  selector: 'app-techo-lista',
  template: `
    <div class="techo-lista">
      <div class="page-header">
        <h2>Techos Presupuestarios</h2>
        <p class="text-secondary">Techos asignados por gestión</p>
      </div>
    
      <!-- Gestión Filter -->
      <div class="filter-bar">
        <label for="gestion">Gestión:</label>
        <select id="gestion" [ngModel]="gestion" (ngModelChange)="onGestionChange($event)" class="select-input">
          @for (g of gestiones; track g) {
            <option [value]="g">{{ g }}</option>
          }
        </select>
      </div>
    
      <!-- Loading -->
      @if (!items && !error) {
        <div class="loading">
          <p>Cargando techos...</p>
        </div>
      }
    
      <!-- Error -->
      @if (error) {
        <div class="alert alert-error">
          {{ error }}
        </div>
      }
    
      <!-- Table -->
      @if (items) {
        <div class="table-responsive">
          <table>
            <thead>
              <tr>
                <th>Código</th>
                <th>Concepto</th>
                <th>Monto Asignado (Bs)</th>
                <th>Monto Distribuido (Bs)</th>
                <th>Saldo (Bs)</th>
                <th>Estado</th>
              </tr>
            </thead>
            <tbody>
              @for (t of items; track t) {
                <tr>
                  <td><strong>{{ t.codigo }}</strong></td>
                  <td>{{ t.concepto }}</td>
                  <td class="text-right">{{ t.monto_asignado | number:'1.2-2' }}</td>
                  <td class="text-right">{{ t.monto_distribuido | number:'1.2-2' }}</td>
                  <td class="text-right" [class.text-warn]="t.saldo > 0">
                    {{ t.saldo | number:'1.2-2' }}
                  </td>
                  <td>
                    <span class="badge" [class.badge-ok]="t.saldo === 0"
                      [class.badge-warn]="t.saldo > 0">
                      {{ t.saldo === 0 ? 'Distribuido' : 'Pendiente' }}
                    </span>
                  </td>
                </tr>
              }
              @if (items.length === 0) {
                <tr>
                  <td colspan="6" class="empty">No se encontraron techos para esta gestión</td>
                </tr>
              }
            </tbody>
          </table>
        </div>
      }
    </div>
    `,
  styles: [`
    .page-header { margin-bottom: 1.5rem; }
    .page-header h2 { font-size: 1.5rem; margin-bottom: 0.25rem; }
    .text-secondary { color: var(--text-secondary); font-size: 0.875rem; }
    .filter-bar { display: flex; align-items: center; gap: 0.75rem; margin-bottom: 1.5rem; }
    .filter-bar label { font-size: 0.875rem; font-weight: 500; color: var(--text-secondary); }
    .select-input { padding: 0.5rem 0.75rem; border: 1px solid var(--border); border-radius: 6px; font-size: 0.875rem; background: var(--surface); color: var(--text-primary); }
    .select-input:focus { outline: none; border-color: var(--primary); }
    .table-responsive { overflow-x: auto; }
    table { width: 100%; border-collapse: collapse; }
    th, td { padding: 0.625rem 0.75rem; text-align: left; border-bottom: 1px solid var(--border); }
    th { font-size: 0.75rem; color: var(--text-secondary); text-transform: uppercase; }
    .text-right { text-align: right; font-weight: 600; }
    .text-warn { color: var(--warn); }
    .badge { display: inline-block; padding: 0.125rem 0.5rem; border-radius: 999px; font-size: 0.75rem; font-weight: 600; }
    .badge-ok { background: var(--mdc-green-50); color: var(--mdc-green-800); }
    .badge-warn { background: var(--mdc-amber-50); color: #F57F17; }
    .empty { text-align: center; padding: 2rem; color: var(--text-secondary); }
    .loading { text-align: center; padding: 3rem; color: var(--text-secondary); }
    .alert { padding: 0.75rem 1rem; border-radius: 6px; }
    .alert-error { background: var(--mdc-red-50); color: var(--warn); }
  `]
})
export class TechoListaComponent implements OnInit {
  gestion = 2026;
  gestiones = [2024, 2025, 2026, 2027];
  items: any[] | null = null;
  error = '';

  constructor(private api: ApiService) {}

  ngOnInit(): void {
    this.load();
  }

  onGestionChange(g: number): void {
    this.gestion = g;
    this.load();
  }

  private load(): void {
    this.items = null;
    this.error = '';
    this.api.get<any[]>('/techos/', { gestion: this.gestion }).subscribe({
      next: d => this.items = d,
      error: e => this.error = 'Error al cargar techos: ' + (e.message || e),
    });
  }
}

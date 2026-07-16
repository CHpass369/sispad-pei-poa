import { Component, OnInit } from '@angular/core';
import { ApiService } from '../../core/services/api.service';

@Component({
  standalone: false,
  selector: 'app-programa-lista',
  template: `
    <div class="programa-lista">
      <div class="page-header">
        <h2>Programas Presupuestarios</h2>
        <p class="text-secondary">Catálogo de programas con sus montos asignados</p>
      </div>

      <!-- Search -->
      <div class="search-bar">
        <input
          type="text"
          placeholder="Buscar por código o nombre..."
          (input)="onSearch($event)"
          class="search-input"
        />
      </div>

      <!-- Loading -->
      <div class="loading" *ngIf="!items && !error">
        <p>Cargando programas...</p>
      </div>

      <!-- Error -->
      <div class="alert alert-error" *ngIf="error">
        {{ error }}
      </div>

      <!-- Table -->
      <div class="table-responsive" *ngIf="items">
        <table>
          <thead>
            <tr>
              <th>Código</th>
              <th>Programa</th>
              <th>Presupuesto (Bs)</th>
              <th>Estado</th>
            </tr>
          </thead>
          <tbody>
            <tr *ngFor="let p of filteredItems">
              <td><strong>{{ p.codigo }}</strong></td>
              <td>{{ p.nombre }}</td>
              <td>{{ p.presupuesto | number:'1.2-2' }}</td>
              <td>
                <span class="badge" [class.badge-ok]="p.activo"
                      [class.badge-muted]="!p.activo">
                  {{ p.activo ? 'Activo' : 'Inactivo' }}
                </span>
              </td>
            </tr>
            <tr *ngIf="filteredItems.length === 0">
              <td colspan="4" class="empty">No se encontraron programas</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  `,
  styles: [`
    .page-header { margin-bottom: 1.5rem; }
    .page-header h2 { font-size: 1.5rem; margin-bottom: 0.25rem; }
    .text-secondary { color: var(--text-secondary); font-size: 0.875rem; }
    .search-bar { margin-bottom: 1.5rem; }
    .search-input { width: 100%; max-width: 400px; padding: 0.625rem 0.875rem; border: 1px solid var(--border); border-radius: 6px; font-size: 0.875rem; background: var(--surface); color: var(--text-primary); }
    .search-input:focus { outline: none; border-color: var(--primary); }
    .table-responsive { overflow-x: auto; }
    table { width: 100%; border-collapse: collapse; }
    th, td { padding: 0.625rem 0.75rem; text-align: left; border-bottom: 1px solid var(--border); }
    th { font-size: 0.75rem; color: var(--text-secondary); text-transform: uppercase; }
    .badge { display: inline-block; padding: 0.125rem 0.5rem; border-radius: 999px; font-size: 0.75rem; font-weight: 600; }
    .badge-ok { background: #E8F5E9; color: #2E7D32; }
    .badge-muted { background: #ECEFF1; color: #546E7A; }
    .empty { text-align: center; padding: 2rem; color: var(--text-secondary); }
    .loading { text-align: center; padding: 3rem; color: var(--text-secondary); }
    .alert { padding: 0.75rem 1rem; border-radius: 6px; }
    .alert-error { background: #FFEBEE; color: var(--warn); }
  `]
})
export class ProgramaListaComponent implements OnInit {
  items: any[] | null = null;
  filteredItems: any[] = [];
  error = '';

  constructor(private api: ApiService) {}

  ngOnInit(): void {
    this.api.get<any[]>('/programas-presupuestarios/').subscribe({
      next: d => {
        this.items = d;
        this.filteredItems = [...d];
      },
      error: e => this.error = 'Error al cargar programas: ' + (e.message || e),
    });
  }

  onSearch(event: Event): void {
    const q = (event.target as HTMLInputElement).value.toLowerCase();
    if (!this.items) return;
    this.filteredItems = this.items.filter(p =>
      p.codigo?.toLowerCase().includes(q) ||
      p.nombre?.toLowerCase().includes(q)
    );
  }
}

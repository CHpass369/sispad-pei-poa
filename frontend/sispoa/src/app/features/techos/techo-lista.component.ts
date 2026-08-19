import { Component, OnInit } from '@angular/core';
import { BudgetService, DirectiveCeiling } from '../sis-poa/budget/budget.service';

@Component({
  standalone: false,
  selector: 'app-techo-lista',
  template: `
    <div class="techo-lista">
      <div class="page-header">
        <h2>Techos Presupuestarios</h2>
        <p class="text-secondary">Techos directivos por gestión (fuente canónica DirectiveCeiling)</p>
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
                <th>Gestión</th>
                <th>Estado</th>
                <th>Monto Bruto (Bs)</th>
                <th>Gastos Obligatorios (Bs)</th>
                <th>Distribuible (Bs)</th>
                <th>Fuentes</th>
              </tr>
            </thead>
            <tbody>
              @for (t of items; track t.id) {
                <tr>
                  <td><strong>{{ t.gestion_anio }}</strong></td>
                  <td>
                    <span class="badge" [class]="badgeClass(t.estado)">
                      {{ t.estado_display }}
                    </span>
                  </td>
                  <td class="text-right">{{ montoBruto(t) | number:'1.2-2' }}</td>
                  <td class="text-right">{{ montoObligatorio(t) | number:'1.2-2' }}</td>
                  <td class="text-right">{{ montoDistribuible(t) | number:'1.2-2' }}</td>
                  <td>{{ fuentesDe(t) }}</td>
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
    
    table { width: 100%; border-collapse: collapse; }
    th, td { padding: 0.625rem 0.75rem; text-align: left; border-bottom: 1px solid var(--border); }
    th { font-size: 0.75rem; color: var(--text-secondary); text-transform: uppercase; }
    .text-right { text-align: right; font-weight: 600; }
    .badge { display: inline-block; padding: 0.125rem 0.5rem; border-radius: 999px; font-size: 0.75rem; font-weight: 600; }
    .badge-info { background: var(--mdc-blue-50); color: var(--mdc-blue-800); }
    .badge-warning { background: var(--mdc-amber-50); color: #F57F17; }
    .badge-danger { background: var(--mdc-red-50); color: var(--mdc-red-800); }
    .badge-success { background: var(--mdc-green-50); color: var(--mdc-green-800); }
    .empty { text-align: center; padding: 2rem; color: var(--text-secondary); }
    .loading { text-align: center; padding: 3rem; color: var(--text-secondary); }
    .alert { padding: 0.75rem 1rem; border-radius: 6px; }
    .alert-error { background: var(--mdc-red-50); color: var(--warn); }
  `]
})
export class TechoListaComponent implements OnInit {
  gestion = 0;
  gestiones: number[] = [];
  items: DirectiveCeiling[] | null = null;
  error = '';

  constructor(private service: BudgetService) {}

  ngOnInit(): void {
    this.cargarGestiones();
    this.load();
  }

  private cargarGestiones(): void {
    this.service.listar().subscribe({
      next: (data) => {
        this.gestiones = data.results.map(g => g.anio);
        const habilitada = data.results.find(g => g.estado === 'HABILITADA');
        this.gestion = habilitada ? habilitada.anio : (this.gestiones[0] ?? 0);
        if (this.gestion !== 0) {
          this.load();
        }
      },
      error: () => undefined,
    });
  }

  onGestionChange(g: number): void {
    this.gestion = g;
    this.load();
  }

  private load(): void {
    this.items = null;
    this.error = '';
    this.service.listarTechos().subscribe({
      next: d => this.items = d.results.filter(t => t.gestion_anio === this.gestion),
      error: e => this.error = 'Error al cargar techos: ' + (e.message || e),
    });
  }

  montoBruto(t: DirectiveCeiling): string {
    return t.composicion?.techo_bruto ?? '0.00';
  }

  montoObligatorio(t: DirectiveCeiling): string {
    return t.composicion?.gastos_obligatorios ?? '0.00';
  }

  montoDistribuible(t: DirectiveCeiling): string {
    return t.composicion?.techo_distribuible ?? '0.00';
  }

  fuentesDe(t: DirectiveCeiling): string {
    const porFuente = t.composicion?.por_fuente ?? [];
    return porFuente.length
      ? porFuente.map(f => f.fuente).join(', ')
      : 'Sin fuentes';
  }

  badgeClass(estado: string): string {
    switch (estado) {
      case 'EN_REVISION':
      case 'APROBADO':
        return 'badge-warning';
      case 'OBSERVADO':
        return 'badge-danger';
      case 'FIJADO':
        return 'badge-success';
      default:
        return 'badge-info';
    }
  }
}
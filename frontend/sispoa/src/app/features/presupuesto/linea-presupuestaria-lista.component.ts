import { Component, OnInit } from '@angular/core';
import { ApiService } from '../../core/services/api.service';

@Component({
  standalone: false,
  selector: 'app-linea-presupuestaria-lista',
  template: `
    <div class="linea-lista">
      <div class="page-header">
        <h2>Líneas Presupuestarias</h2>
        <p class="text-secondary">Detalle de líneas con llave presupuestaria completa</p>
      </div>
    
      <!-- Loading -->
      @if (!items && !error) {
        <div class="loading">
          <p>Cargando líneas presupuestarias...</p>
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
                <th>Programa</th>
                <th>Proyecto</th>
                <th>Actividad</th>
                <th>Fuente</th>
                <th>Objeto Gasto</th>
                <th>Importe (Bs)</th>
              </tr>
            </thead>
            <tbody>
              @for (l of items; track l) {
                <tr>
                  <td>{{ l.programa_codigo }} - {{ l.programa }}</td>
                  <td>{{ l.proyecto_codigo }} - {{ l.proyecto }}</td>
                  <td>{{ l.actividad_codigo }} - {{ l.actividad }}</td>
                  <td>{{ l.fuente_codigo }} - {{ l.fuente }}</td>
                  <td>{{ l.objeto_gasto_codigo }} - {{ l.objeto_gasto }}</td>
                  <td class="text-right">{{ l.importe | number:'1.2-2' }}</td>
                </tr>
              }
              @if (items.length === 0) {
                <tr>
                  <td colspan="6" class="empty">No se encontraron líneas presupuestarias</td>
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
    .table-responsive { overflow-x: auto; }
    table { width: 100%; border-collapse: collapse; font-size: 0.8125rem; }
    th, td { padding: 0.5rem 0.625rem; text-align: left; border-bottom: 1px solid var(--border); white-space: nowrap; }
    th { font-size: 0.6875rem; color: var(--text-secondary); text-transform: uppercase; }
    .text-right { text-align: right; font-weight: 600; }
    .empty { text-align: center; padding: 2rem; color: var(--text-secondary); }
    .loading { text-align: center; padding: 3rem; color: var(--text-secondary); }
    .alert { padding: 0.75rem 1rem; border-radius: 6px; }
    .alert-error { background: #FFEBEE; color: var(--warn); }
  `]
})
export class LineaPresupuestariaListaComponent implements OnInit {
  items: any[] | null = null;
  error = '';

  constructor(private api: ApiService) {}

  ngOnInit(): void {
    this.api.get<any[]>('/lineas-presupuestarias/').subscribe({
      next: d => this.items = d,
      error: e => this.error = 'Error al cargar líneas: ' + (e.message || e),
    });
  }
}

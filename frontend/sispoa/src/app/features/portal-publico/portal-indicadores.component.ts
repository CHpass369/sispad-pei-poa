import { Component, OnInit } from '@angular/core';
import { PortalPublicoService, IndicadorPublico } from './portal-publico.service';

@Component({
  standalone: false,
  selector: 'app-portal-indicadores',
  template: `
    <div class="page-header">
      <h2>Indicadores Públicos</h2>
      <p class="text-secondary">Indicadores de desempeño institucional - Vista de solo lectura</p>
    </div>

    <div class="acciones-superior">
      <div class="field">
        <input [(ngModel)]="busqueda" (keyup.enter)="cargar()" class="form-control"
               placeholder="Buscar indicadores...">
      </div>
      <select [(ngModel)]="filtroTipo" (change)="cargar()" class="form-control">
        <option value="">Todos los tipos</option>
        <option value="eficiencia">Eficiencia</option>
        <option value="efectividad">Efectividad</option>
        <option value="calidad">Calidad</option>
        <option value="productividad">Productividad</option>
      </select>
    </div>

    <div class="indicadores-grid" *ngIf="!cargando">
      <div class="card indicador-card" *ngFor="let ind of indicadoresFiltrados">
        <div class="indicador-header">
          <span class="badge badge-tipo">{{ ind.tipo || 'General' }}</span>
          <span class="indicador-avance">{{ ind.avance_porcentual || 0 }}%</span>
        </div>
        <h4 class="indicador-nombre">{{ ind.nombre }}</h4>
        <p class="indicador-desc">{{ ind.descripcion }}</p>
        <div class="indicador-meta">
          <span>Meta: {{ ind.meta }} {{ ind.unidad_medida }}</span>
          <span>Actual: {{ ind.valor_actual }} {{ ind.unidad_medida }}</span>
        </div>
        <div class="progress-bar">
          <div class="progress-fill" [style.width.%]="ind.avance_porcentual || 0"
               [class.fill-ok]="(ind.avance_porcentual || 0) >= 80"
               [class.fill-warn]="(ind.avance_porcentual || 0) >= 40 && (ind.avance_porcentual || 0) < 80"
               [class.fill-danger]="(ind.avance_porcentual || 0) < 40"></div>
        </div>
        <div class="indicador-fuente" *ngIf="ind.fuente">Fuente: {{ ind.fuente }}</div>
      </div>

      <div *ngIf="indicadoresFiltrados.length === 0" class="empty">No se encontraron indicadores</div>
    </div>

    <div class="loading" *ngIf="cargando">Cargando indicadores...</div>
    <div class="alert alert-error" *ngIf="error">{{ error }}</div>
  `,
  styles: [`
    .page-header { margin-bottom: 1rem; }
    .page-header h2 { font-size: 1.5rem; margin-bottom: 0.25rem; }
    .text-secondary { color: var(--text-secondary); font-size: 0.875rem; }
    .acciones-superior { display: flex; gap: 1rem; margin-bottom: 1.5rem; align-items: center; }
    .acciones-superior .field { flex: 1; }
    .form-control { padding: 0.5rem 0.75rem; border: 1px solid var(--border); border-radius: 6px; font-size: 0.875rem; }
    .indicadores-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 1rem; }
    .card { background: var(--surface); border: 1px solid var(--border); border-radius: 8px; padding: 1.25rem; }
    .indicador-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.75rem; }
    .indicador-avance { font-size: 1.25rem; font-weight: 700; color: var(--primary); }
    .indicador-nombre { font-size: 1rem; margin-bottom: 0.5rem; }
    .indicador-desc { font-size: 0.8125rem; color: var(--text-secondary); line-height: 1.4; margin-bottom: 0.75rem; }
    .indicador-meta { display: flex; justify-content: space-between; font-size: 0.8125rem; margin-bottom: 0.75rem; color: var(--text-secondary); }
    .progress-bar { height: 8px; background: var(--border); border-radius: 4px; overflow: hidden; margin-bottom: 0.5rem; }
    .progress-fill { height: 100%; border-radius: 4px; transition: width 0.5s; }
    .fill-ok { background: #2E7D32; }
    .fill-warn { background: #F57F17; }
    .fill-danger { background: #C62828; }
    .indicador-fuente { font-size: 0.75rem; color: var(--text-secondary); font-style: italic; }
    .badge { display: inline-block; padding: 0.125rem 0.5rem; border-radius: 4px; font-size: 0.6875rem; font-weight: 600; }
    .badge-tipo { background: #E3F2FD; color: #1565C0; text-transform: uppercase; }
    .empty { text-align: center; padding: 2rem; color: var(--text-secondary); grid-column: 1 / -1; }
    .loading { text-align: center; padding: 2rem; color: var(--text-secondary); }
    .alert { padding: 0.75rem 1rem; border-radius: 6px; margin-top: 1rem; }
    .alert-error { background: #FFEBEE; color: var(--warn); }
  `]
})
export class PortalIndicadoresComponent implements OnInit {
  indicadores: IndicadorPublico[] = [];
  busqueda = '';
  filtroTipo = '';
  cargando = true;
  error = '';

  get indicadoresFiltrados(): IndicadorPublico[] {
    let lista = this.indicadores;
    if (this.busqueda) {
      const term = this.busqueda.toLowerCase();
      lista = lista.filter(i => i.nombre?.toLowerCase().includes(term) || i.descripcion?.toLowerCase().includes(term));
    }
    if (this.filtroTipo) {
      lista = lista.filter(i => i.tipo === this.filtroTipo);
    }
    return lista;
  }

  constructor(private portalService: PortalPublicoService) {}

  ngOnInit(): void {
    this.cargar();
  }

  cargar(): void {
    this.cargando = true;
    this.error = '';
    this.portalService.listarIndicadores().subscribe({
      next: (data: any) => {
        this.indicadores = data.results || data;
        this.cargando = false;
      },
      error: () => {
        this.error = 'Error al cargar indicadores';
        this.cargando = false;
      },
    });
  }
}

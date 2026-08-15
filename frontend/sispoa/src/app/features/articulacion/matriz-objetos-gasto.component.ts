import { Component, OnInit } from '@angular/core';
import { ApiService } from '../../core/services/api.service';
import {
  ARTICULATION_MANAGEMENT,
  buildReportUrl,
  mapM5Rows,
} from './matrices-contracts';

@Component({
  selector: 'app-matriz-objetos-gasto',
  standalone: false,
  template: `
    <div class="matriz-page">
      <div class="page-header">
        <h2>Matriz 5 — Objetos de Gasto</h2>
        <p class="text-secondary">
          Asignaciones de objetos de gasto por actividad: código, grupo, fuente, organismo y monto
        </p>
      </div>
    
      <div class="card filtros-card">
        <div class="filtros">
          <div class="field">
            <label>Buscar</label>
            <input [(ngModel)]="filtroTexto" class="form-control" placeholder="Código o descripción..."
              (input)="aplicarFiltros()">
            </div>
            <div class="field">
              <label>Grupo de gasto</label>
              <select [(ngModel)]="filtroGrupo" class="form-control" (change)="aplicarFiltros()">
                <option value="">Todos</option>
                @for (g of grupos; track g) {
                  <option [value]="g">{{ g }}</option>
                }
              </select>
            </div>
            <div class="field">
              <label>Gestión</label>
              <select [(ngModel)]="filtroGestion" class="form-control" (change)="aplicarFiltros()">
                <option value="">Todas</option>
                @for (g of gestiones; track g) {
                  <option [value]="g">{{ g }}</option>
                }
              </select>
            </div>
            <div class="field">
              <label>&nbsp;</label>
              <span class="badge badge-info">Mostrando {{ filtrados.length }} de {{ asignaciones.length }} registros</span>
            </div>
            <div class="field export-field">
              <label>&nbsp;</label>
              <a routerLink="./nuevo" class="btn btn-sm btn-primary">+ Nueva</a>
            </div>
            <div class="field export-field">
              <label>&nbsp;</label>
              <button class="btn btn-sm btn-outline-success" (click)="exportarXLSX()">
                ⬇ Exportar XLSX
              </button>
            </div>
          </div>
        </div>
    
        <div class="card table-card">
          <div class="table-scroll">
            <table class="matriz-table">
              <thead>
                <tr>
                  <th>Código Asignación</th>
                  <th>Actividad</th>
                  <th>Código Objeto Gasto</th>
                  <th>Descripción Objeto</th>
                  <th>Grupo Gasto</th>
                  <th>Tipo Gasto</th>
                  <th>FTE</th>
                  <th>ORG</th>
                  <th>Cat. Programática</th>
                  <th>DA</th>
                  <th>UE</th>
                  <th>Monto Programado</th>
                  <th>Monto Vigente</th>
                  <th>Justificación</th>
                </tr>
              </thead>
              <tbody>
                @for (item of filtrados; track item) {
                  <tr>
                    <td><span class="codigo">{{ item.codigo_asignacion }}</span></td>
                    <td class="cell-desc">{{ item.actividad_nombre || '—' }}</td>
                    <td><span class="codigo">{{ item.cod_objeto_gasto }}</span></td>
                    <td class="cell-desc">{{ item.descripcion_objeto }}</td>
                    <td><span class="badge badge-info">{{ item.grupo_gasto }}</span></td>
                    <td>{{ item.tipo_gasto || '—' }}</td>
                    <td>{{ item.fuente_financiamiento || '—' }}</td>
                    <td>{{ item.organismo_financiador || '—' }}</td>
                    <td class="cell-desc">{{ item.categoria_programatica || '—' }}</td>
                    <td>{{ item.da || '—' }}</td>
                    <td>{{ item.ue || '—' }}</td>
                    <td class="num">{{ item.monto_programado | number:'1.2-2' }}</td>
                    <td class="num"><strong>{{ item.monto_vigente | number:'1.2-2' }}</strong></td>
                    <td class="cell-desc">{{ item.justificacion || '—' }}</td>
                  </tr>
                }
                @if (cargando) {
                  <tr>
                    <td colspan="14" class="empty-cell">Cargando datos...</td>
                  </tr>
                }
                @if (!cargando && filtrados.length === 0) {
                  <tr>
                    <td colspan="14" class="empty-cell">No se encontraron asignaciones de objetos de gasto</td>
                  </tr>
                }
              </tbody>
            </table>
          </div>
        </div>
      </div>
    `,
  styles: [`
    .matriz-page { padding-bottom: 2rem; }
    .page-header { margin-bottom: 1rem; }
    .page-header h2 { font-size: 1.25rem; color: var(--primary); margin-bottom: 0.25rem; }
    .text-secondary { color: var(--text-secondary); font-size: 0.8125rem; }

    .filtros-card { padding: 1rem; margin-bottom: 1rem; }
    .filtros { display: flex; gap: 1rem; align-items: flex-end; flex-wrap: wrap; }
    .filtros .field { min-width: 150px; }
    .filtros .field label { display: block; font-size: 0.6875rem; font-weight: 600; color: var(--text-secondary); margin-bottom: 0.25rem; }

    .table-scroll { overflow-x: auto; }
    .table-card { padding: 0; overflow: hidden; }

    .matriz-table { width: 100%; border-collapse: collapse; font-size: 0.75rem; }
    .matriz-table th {
      background: var(--primary);
      color: white;
      padding: 0.5rem 0.5rem;
      text-align: left;
      font-size: 0.625rem;
      text-transform: uppercase;
      letter-spacing: 0.04em;
      white-space: nowrap;
    }
    .matriz-table td {
      padding: 0.375rem 0.5rem;
      border-bottom: 1px solid var(--border);
      vertical-align: top;
    }
    .matriz-table tbody tr:hover td { background: #F0F7F3; }
    .matriz-table tbody tr:nth-child(even) td { background: #FAFCFA; }
    .matriz-table tbody tr:nth-child(even):hover td { background: #F0F7F3; }

    .codigo { font-family: 'Courier New', monospace; font-weight: 700; font-size: 0.6875rem; color: var(--primary-dark); white-space: nowrap; }
    .cell-desc { max-width: 180px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
    .num { text-align: right; font-family: 'Courier New', monospace; font-size: 0.6875rem; }
    .empty-cell { text-align: center; color: var(--text-secondary); padding: 2rem; font-size: 0.875rem; }
    .badge { font-size: 0.6875rem; }
    .export-field { margin-left: auto; }
    .btn-outline-success { border: 1px solid var(--primary); color: var(--primary); background: transparent; padding: 0.375rem 0.75rem; border-radius: 4px; cursor: pointer; font-size: 0.75rem; }
    .btn-outline-success:hover { background: var(--primary); color: white; }
  `],
})
export class MatrizObjetosGastoComponent implements OnInit {
  cargando = true;
  asignaciones: any[] = [];
  filtrados: any[] = [];
  gestiones: number[] = [];
  grupos: string[] = [];

  filtroTexto = '';
  filtroGrupo = '';
  filtroGestion = '';

  constructor(private api: ApiService) {}

  ngOnInit(): void {
    this.cargarDatos();
  }

  private cargarDatos(): void {
    this.cargando = true;
    this.api.get<any>(
      '/articulacion/matrices/m5_objetos_gasto/',
      { gestion: ARTICULATION_MANAGEMENT },
    ).subscribe({
      next: (response) => {
        const rows = mapM5Rows(response);
        this.asignaciones = rows;
        this.gestiones = [...new Set<number>(
          rows.map((row: any) => row.gestion).filter(Boolean),
        )].sort();
        this.grupos = [...new Set<string>(
          rows.map((row: any) => row.grupo_gasto).filter(Boolean),
        )].sort();
        this.aplicarFiltros();
        this.cargando = false;
      },
      error: () => { this.cargando = false; },
    });
  }

  aplicarFiltros(): void {
    let items = this.asignaciones;
    if (this.filtroTexto.trim()) {
      const q = this.filtroTexto.trim().toLowerCase();
      items = items.filter(i =>
        i.codigo_asignacion?.toLowerCase().includes(q) ||
        i.descripcion_objeto?.toLowerCase().includes(q) ||
        i.cod_objeto_gasto?.toLowerCase().includes(q)
      );
    }
    if (this.filtroGrupo) {
      items = items.filter(i => i.grupo_gasto === this.filtroGrupo);
    }
    if (this.filtroGestion) {
      items = items.filter(i => i.gestion === Number(this.filtroGestion));
    }
    this.filtrados = items;
  }

  exportarXLSX(): void {
    window.open(
      buildReportUrl(
        '/reportes/articulacion_objetos_gasto/',
        this.filtroGestion || ARTICULATION_MANAGEMENT,
      ),
      '_blank',
    );
  }
}

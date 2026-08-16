import { Component, OnInit } from '@angular/core';
import { ApiService } from '../../core/services/api.service';
import {
  ARTICULATION_MANAGEMENT,
  buildReportUrl,
  mapM1Rows,
} from './matrices-contracts';

@Component({
  selector: 'app-matriz-pad-pei',
  standalone: false,
  template: `
    <div class="matriz-page">
      <div class="page-header">
        <h2>Matriz 1 — Articulación PAD → PEI</h2>
        <p class="text-secondary">
          Vinculación de resultados y productos del PAD con resultados y productos del PEI
        </p>
      </div>
    
      <div class="card filtros-card">
        <div class="filtros">
          <div class="field">
            <label>Buscar por código</label>
            <input [(ngModel)]="filtroCodigo" class="form-control" placeholder="Código..."
              (input)="aplicarFiltros()">
            </div>
            <div class="field">
              <label>Estado</label>
              <select [(ngModel)]="filtroEstado" class="form-control" (change)="aplicarFiltros()">
                <option value="">Todos</option>
                <option value="REFERENCIAL">Referencial</option>
                <option value="VALIDADO">Validado</option>
                <option value="APROBADO">Aprobado</option>
              </select>
            </div>
            <div class="field">
              <label>&nbsp;</label>
              <span class="badge badge-info">Mostrando {{ filtrados.length }} de {{ articulaciones.length }} registros</span>
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
                  <th>Código Resultado PAD</th>
                  <th>Resultado PAD</th>
                  <th>Código Producto PAD</th>
                  <th>Producto PAD</th>
                  <th>Código Resultado PEI</th>
                  <th>Resultado PEI</th>
                  <th>Código Producto PEI</th>
                  <th>Producto PEI</th>
                  <th>Estado</th>
                </tr>
              </thead>
              <tbody>
                @for (item of filtrados; track item) {
                  <tr>
                    <td><span class="codigo">{{ item.codigo_resultado_pad }}</span></td>
                    <td class="cell-desc">{{ item.resultado_pad }}</td>
                    <td><span class="codigo">{{ item.codigo_producto_pad }}</span></td>
                    <td class="cell-desc">{{ item.producto_pad }}</td>
                    <td><span class="codigo">{{ item.codigo_resultado_pei }}</span></td>
                    <td class="cell-desc">{{ item.resultado_pei }}</td>
                    <td><span class="codigo">{{ item.codigo_producto_pei }}</span></td>
                    <td class="cell-desc">{{ item.producto_pei }}</td>
                    <td>
                      <span class="badge" [class.badge-success]="item.estado==='APROBADO'"
                        [class.badge-warning]="item.estado==='VALIDADO'"
                        [class.badge-info]="item.estado==='REFERENCIAL'">
                        {{ item.estado }}
                      </span>
                    </td>
                  </tr>
                }
                @if (cargando) {
                  <tr>
                    <td colspan="9" class="empty-cell">Cargando datos...</td>
                  </tr>
                }
                @if (!cargando && filtrados.length === 0) {
                  <tr>
                    <td colspan="9" class="empty-cell">No se encontraron registros de articulación PAD-PEI</td>
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
    .filtros .field { min-width: 180px; }
    .filtros .field label { display: block; font-size: 0.6875rem; font-weight: 600; color: var(--text-secondary); margin-bottom: 0.25rem; }

    .table-scroll { overflow-x: auto; }
    .table-card { padding: 0; overflow: hidden; }

    .matriz-table { width: 100%; border-collapse: collapse; font-size: 0.8125rem; }
    .matriz-table th {
      background: var(--primary);
      color: white;
      padding: 0.625rem 0.75rem;
      text-align: left;
      font-size: 0.6875rem;
      text-transform: uppercase;
      letter-spacing: 0.04em;
      white-space: nowrap;
    }
    .matriz-table td {
      padding: 0.5rem 0.75rem;
      border-bottom: 1px solid var(--border);
      vertical-align: top;
    }
    .matriz-table tbody tr:hover td { background: var(--mdc-hover); }
    .matriz-table tbody tr:nth-child(even) td { background: #FAFCFA; }
    .matriz-table tbody tr:nth-child(even):hover td { background: var(--mdc-hover); }

    .codigo {
      font-family: 'Courier New', monospace;
      font-weight: 700;
      font-size: 0.75rem;
      color: var(--primary-dark);
      white-space: nowrap;
    }
    .cell-desc { max-width: 240px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
    .empty-cell { text-align: center; color: var(--text-secondary); padding: 2rem; font-size: 0.875rem; }
    .badge { font-size: 0.6875rem; }
    .export-field { margin-left: auto; }
    .btn-outline-success { border: 1px solid var(--primary); color: var(--primary); background: transparent; padding: 0.375rem 0.75rem; border-radius: 4px; cursor: pointer; font-size: 0.75rem; }
    .btn-outline-success:hover { background: var(--primary); color: white; }
  `],
})
export class MatrizPADPEIComponent implements OnInit {
  cargando = true;
  articulaciones: any[] = [];
  filtrados: any[] = [];

  filtroCodigo = '';
  filtroEstado = '';

  constructor(private api: ApiService) {}

  ngOnInit(): void {
    this.cargarDatos();
  }

  private cargarDatos(): void {
    this.cargando = true;
    this.api.get<any>(
      '/articulacion/matrices/m1_pad_pei/',
      { gestion: ARTICULATION_MANAGEMENT },
    ).subscribe({
      next: (response) => {
        this.articulaciones = mapM1Rows(response);
        this.aplicarFiltros();
        this.cargando = false;
      },
      error: () => { this.cargando = false; },
    });
  }

  aplicarFiltros(): void {
    let items = this.articulaciones;
    if (this.filtroCodigo.trim()) {
      const q = this.filtroCodigo.trim().toLowerCase();
      items = items.filter(i =>
        i.codigo_producto_pad.toLowerCase().includes(q) ||
        i.codigo_producto_pei.toLowerCase().includes(q) ||
        i.codigo_resultado_pad.toLowerCase().includes(q) ||
        i.codigo_resultado_pei.toLowerCase().includes(q)
      );
    }
    if (this.filtroEstado) {
      items = items.filter(i => i.estado === this.filtroEstado);
    }
    this.filtrados = items;
  }

  exportarXLSX(): void {
    window.open(buildReportUrl('/reportes/articulacion_matriz_pad_pei/'), '_blank');
  }
}

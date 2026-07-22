import { Component, OnInit } from '@angular/core';
import { ApiService } from '../../core/services/api.service';
import { environment } from '../../../environments/environment';

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
              <tr *ngFor="let item of filtrados">
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
              <tr *ngIf="cargando">
                <td colspan="9" class="empty-cell">Cargando datos...</td>
              </tr>
              <tr *ngIf="!cargando && filtrados.length === 0">
                <td colspan="9" class="empty-cell">No se encontraron registros de articulación PAD-PEI</td>
              </tr>
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
    .matriz-table tbody tr:hover td { background: #F0F7F3; }
    .matriz-table tbody tr:nth-child(even) td { background: #FAFCFA; }
    .matriz-table tbody tr:nth-child(even):hover td { background: #F0F7F3; }

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

  resultadosPad: Map<string, any> = new Map();
  productosPad: Map<string, any> = new Map();
  resultadosPei: Map<string, any> = new Map();
  productosPei: Map<string, any> = new Map();

  filtroCodigo = '';
  filtroEstado = '';

  constructor(private api: ApiService) {}

  ngOnInit(): void {
    this.cargarDatos();
  }

  private cargarDatos(): void {
    this.cargando = true;
    Promise.all([
      this.fetchList('/articulacion/resultados-pad/'),
      this.fetchList('/articulacion/productos-pad/'),
      this.fetchList('/articulacion/resultados-pei/'),
      this.fetchList('/articulacion/productos-pei/'),
      this.fetchList('/articulacion/articulaciones-pad-pei/'),
    ]).then(([resPad, prodPad, resPei, prodPei, arts]) => {
      this.resultadosPad = this.buildMap(resPad, 'id');
      this.productosPad = this.buildMap(prodPad, 'id');
      this.resultadosPei = this.buildMap(resPei, 'id');
      this.productosPei = this.buildMap(prodPei, 'id');

      this.articulaciones = arts.map((a: any) => this.ensamblarFila(a));
      this.aplicarFiltros();
      this.cargando = false;
    }).catch(() => {
      this.cargando = false;
    });
  }

  private fetchList(path: string): Promise<any[]> {
    return new Promise((resolve) => {
      this.api.get<any>(path).subscribe({
        next: (r) => resolve(r.results || r || []),
        error: () => resolve([]),
      });
    });
  }

  private buildMap(list: any[], key: string): Map<string, any> {
    const m = new Map<string, any>();
    list.forEach((item: any) => m.set(item[key], item));
    return m;
  }

  private ensamblarFila(a: any): any {
    const prodPad = this.productosPad.get(a.producto_pad);
    const prodPei = this.productosPei.get(a.producto_pei);
    const resPad = prodPad ? this.resultadosPad.get(prodPad.resultado_pad) : null;
    const resPei = prodPei ? this.resultadosPei.get(prodPei.resultado_pei) : null;

    return {
      codigo_resultado_pad: resPad?.codigo_resultado || '—',
      resultado_pad: resPad?.denominacion || '—',
      codigo_producto_pad: prodPad?.codigo_producto || '—',
      producto_pad: prodPad?.denominacion || '—',
      codigo_resultado_pei: resPei?.codigo_resultado || '—',
      resultado_pei: resPei?.denominacion || '—',
      codigo_producto_pei: prodPei?.codigo_producto || '—',
      producto_pei: prodPei?.denominacion || '—',
      estado: a.estado || 'REFERENCIAL',
      tipo_contribucion: a.tipo_contribucion,
      ponderacion: a.ponderacion,
    };
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
    const url = `${environment.apiUrl}/api/v1/reportes/articulacion_matriz_pad_pei/?gestion=2026`;
    window.open(url, '_blank');
  }
}

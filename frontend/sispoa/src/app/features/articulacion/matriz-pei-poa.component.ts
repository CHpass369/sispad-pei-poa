import { Component, OnInit } from '@angular/core';
import { ApiService } from '../../core/services/api.service';

@Component({
  selector: 'app-matriz-pei-poa',
  standalone: false,
  template: `
    <div class="matriz-page">
      <div class="page-header">
        <h2>Matriz 2 — Articulación PEI → POA</h2>
        <p class="text-secondary">
          Acciones del POA articuladas con productos del PEI, indicadores, metas y presupuesto
        </p>
      </div>

      <div class="card filtros-card">
        <div class="filtros">
          <div class="field">
            <label>Buscar</label>
            <input [(ngModel)]="filtroTexto" class="form-control" placeholder="Código o denominación..."
                   (input)="aplicarFiltros()">
          </div>
          <div class="field">
            <label>Estado</label>
            <select [(ngModel)]="filtroEstado" class="form-control" (change)="aplicarFiltros()">
              <option value="">Todos</option>
              <option value="REFERENCIAL">Referencial</option>
              <option value="VALIDADO">Validado</option>
              <option value="APROBADO">Aprobado</option>
              <option value="EJECUCION">En Ejecución</option>
              <option value="FINALIZADO">Finalizado</option>
            </select>
          </div>
          <div class="field">
            <label>Gestión</label>
            <select [(ngModel)]="filtroGestion" class="form-control" (change)="aplicarFiltros()">
              <option value="">Todas</option>
              <option *ngFor="let g of gestiones" [value]="g">{{ g }}</option>
            </select>
          </div>
          <div class="field">
            <label>&nbsp;</label>
            <span class="badge badge-info">{{ filtrados.length }} registros</span>
          </div>
        </div>
      </div>

      <div class="card table-card">
        <div class="table-scroll">
          <table class="matriz-table">
            <thead>
              <tr>
                <th>Código Acción POA</th>
                <th>Acción POA</th>
                <th>Producto PEI</th>
                <th>Indicador</th>
                <th>Unidad</th>
                <th>Meta Gestión</th>
                <th>Presupuesto Programado</th>
                <th>FF</th>
                <th>Estado</th>
              </tr>
            </thead>
            <tbody>
              <tr *ngFor="let item of filtrados">
                <td><span class="codigo">{{ item.codigo_accion }}</span></td>
                <td class="cell-desc">{{ item.denominacion }}</td>
                <td class="cell-desc">{{ item.producto_pei_nombre || '—' }}</td>
                <td class="cell-desc">{{ item.indicador || '—' }}</td>
                <td>{{ item.unidad_medida || '—' }}</td>
                <td class="num">{{ item.meta_gestion != null ? item.meta_gestion : '—' }}</td>
                <td class="num">{{ item.presupuesto_programado != null ? (item.presupuesto_programado | number:'1.0-2') : '—' }}</td>
                <td>{{ item.fuente_financiamiento || '—' }}</td>
                <td>
                  <span class="badge" [class.badge-success]="item.estado==='APROBADO'||item.estado==='FINALIZADO'"
                        [class.badge-warning]="item.estado==='VALIDADO'||item.estado==='EJECUCION'"
                        [class.badge-info]="item.estado==='REFERENCIAL'">
                    {{ item.estado }}
                  </span>
                </td>
              </tr>
              <tr *ngIf="cargando">
                <td colspan="9" class="empty-cell">Cargando datos...</td>
              </tr>
              <tr *ngIf="!cargando && filtrados.length === 0">
                <td colspan="9" class="empty-cell">No se encontraron acciones POA</td>
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
    .filtros .field { min-width: 160px; }
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
    .cell-desc { max-width: 260px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
    .num { text-align: right; font-family: 'Courier New', monospace; font-size: 0.75rem; }
    .empty-cell { text-align: center; color: var(--text-secondary); padding: 2rem; font-size: 0.875rem; }
    .badge { font-size: 0.6875rem; }
  `],
})
export class MatrizPEIPOAComponent implements OnInit {
  cargando = true;
  acciones: any[] = [];
  filtrados: any[] = [];
  gestiones: number[] = [];

  filtroTexto = '';
  filtroEstado = '';
  filtroGestion = '';

  constructor(private api: ApiService) {}

  ngOnInit(): void {
    this.cargarDatos();
  }

  cargarDatos(): void {
    this.cargando = true;
    this.api.get<any>('/articulacion/acciones-poa/').subscribe({
      next: (r) => {
        const items = r.results || r || [];
        // Cargar productos PEI para nombres
        this.api.get<any>('/articulacion/productos-pei/').subscribe({
          next: (rProd) => {
            const prods = this.buildMap(rProd.results || rProd || [], 'id');
            this.acciones = items.map((a: any) => ({
              ...a,
              producto_pei_nombre: prods.get(a.producto_pei)?.denominacion || '—',
            }));
            this.gestiones = [...new Set(items.map((a: any) => a.gestion).filter(Boolean))] as number[];
            this.aplicarFiltros();
            this.cargando = false;
          },
          error: () => {
            this.acciones = items;
            this.gestiones = [...new Set(items.map((a: any) => a.gestion).filter(Boolean))] as number[];
            this.aplicarFiltros();
            this.cargando = false;
          },
        });
      },
      error: () => { this.cargando = false; },
    });
  }

  private buildMap(list: any[], key: string): Map<string, any> {
    const m = new Map<string, any>();
    list.forEach((item: any) => m.set(item[key], item));
    return m;
  }

  aplicarFiltros(): void {
    let items = this.acciones;
    if (this.filtroTexto.trim()) {
      const q = this.filtroTexto.trim().toLowerCase();
      items = items.filter(i =>
        i.codigo_accion?.toLowerCase().includes(q) ||
        i.denominacion?.toLowerCase().includes(q)
      );
    }
    if (this.filtroEstado) {
      items = items.filter(i => i.estado === this.filtroEstado);
    }
    if (this.filtroGestion) {
      items = items.filter(i => i.gestion === Number(this.filtroGestion));
    }
    this.filtrados = items;
  }
}

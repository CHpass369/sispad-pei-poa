import { Component, OnInit } from '@angular/core';
import { ApiService } from '../../core/services/api.service';
import { environment } from '../../../environments/environment';

@Component({
  selector: 'app-matriz-presupuesto-seguimiento',
  standalone: false,
  template: `
    <div class="matriz-page">
      <div class="page-header">
        <h2>Matriz 4 — Presupuesto y Seguimiento</h2>
        <p class="text-secondary">
          Seguimiento presupuestario con ejecución financiera, física e indicadores de eficacia
        </p>
      </div>

      <div class="card filtros-card">
        <div class="filtros">
          <div class="field">
            <label>Buscar (ID cadena)</label>
            <input [(ngModel)]="filtroTexto" class="form-control" placeholder="ID cadena..."
                   (input)="aplicarFiltros()">
          </div>
          <div class="field">
            <label>Gestión</label>
            <select [(ngModel)]="filtroGestion" class="form-control" (change)="aplicarFiltros()">
              <option value="">Todas</option>
              <option *ngFor="let g of gestiones" [value]="g">{{ g }}</option>
            </select>
          </div>
          <div class="field">
            <label>Estado</label>
            <select [(ngModel)]="filtroEstado" class="form-control" (change)="aplicarFiltros()">
              <option value="">Todos</option>
              <option value="REFERENCIAL">Referencial</option>
              <option value="EJECUTADO">Ejecutado</option>
            </select>
          </div>
          <div class="field">
            <label>&nbsp;</label>
            <span class="badge badge-info">Mostrando {{ filtrados.length }} de {{ seguimientos.length }} registros</span>
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
                <th>ID Cadena</th>
                <th>Acción POA</th>
                <th>Operación</th>
                <th>Actividad</th>
                <th>Cat. Programática</th>
                <th>DA</th>
                <th>UE</th>
                <th>Programa</th>
                <th>Presup. Inicial</th>
                <th>Modificaciones</th>
                <th>Presup. Vigente</th>
                <th>Ejec. Financiera</th>
                <th>% Ejec. Fin.</th>
                <th>Meta Física</th>
                <th>Ejec. Física</th>
                <th>% Ejec. Fís.</th>
                <th>Eficacia</th>
              </tr>
            </thead>
            <tbody>
              <tr *ngFor="let item of filtrados">
                <td><span class="codigo">{{ item.id_cadena }}</span></td>
                <td class="cell-desc">{{ item.accion_poa_nombre || '—' }}</td>
                <td class="cell-desc">{{ item.operacion_nombre || '—' }}</td>
                <td class="cell-desc">{{ item.actividad_nombre || '—' }}</td>
                <td>{{ item.categoria_programatica || '—' }}</td>
                <td>{{ item.da || '—' }}</td>
                <td>{{ item.ue || '—' }}</td>
                <td class="cell-desc">{{ item.programa || '—' }}</td>
                <td class="num">{{ item.presupuesto_inicial | number:'1.2-2' }}</td>
                <td class="num">{{ item.modificaciones | number:'1.2-2' }}</td>
                <td class="num"><strong>{{ item.presupuesto_vigente | number:'1.2-2' }}</strong></td>
                <td class="num">{{ item.ejecutado_total | number:'1.2-2' }}</td>
                <td class="num">
                  <span [class.text-success]="item.porcentaje_ejecucion_financiera >= 80"
                        [class.text-warning]="item.porcentaje_ejecucion_financiera >= 50 && item.porcentaje_ejecucion_financiera < 80"
                        [class.text-danger]="item.porcentaje_ejecucion_financiera < 50">
                    {{ item.porcentaje_ejecucion_financiera != null ? (item.porcentaje_ejecucion_financiera + '%') : '—' }}
                  </span>
                </td>
                <td class="num">{{ item.meta_fisica != null ? item.meta_fisica : '—' }}</td>
                <td class="num">{{ item.ejecucion_fisica != null ? item.ejecucion_fisica : '—' }}</td>
                <td class="num">{{ item.porcentaje_ejecucion_fisica != null ? (item.porcentaje_ejecucion_fisica + '%') : '—' }}</td>
                <td class="num">
                  <span [class.text-success]="item.eficacia >= 80"
                        [class.text-warning]="item.eficacia >= 50 && item.eficacia < 80"
                        [class.text-danger]="item.eficacia < 50">
                    {{ item.eficacia != null ? (item.eficacia + '%') : '—' }}
                  </span>
                </td>
              </tr>
              <tr *ngIf="cargando">
                <td colspan="17" class="empty-cell">Cargando datos...</td>
              </tr>
              <tr *ngIf="!cargando && filtrados.length === 0">
                <td colspan="17" class="empty-cell">No se encontraron registros de seguimiento</td>
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
    .cell-desc { max-width: 160px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
    .num { text-align: right; font-family: 'Courier New', monospace; font-size: 0.6875rem; }
    .text-success { color: #2E7D32; font-weight: 600; }
    .text-warning { color: #F57F17; font-weight: 600; }
    .text-danger { color: #C62828; font-weight: 600; }
    .empty-cell { text-align: center; color: var(--text-secondary); padding: 2rem; font-size: 0.875rem; }
    .badge { font-size: 0.6875rem; }
    .export-field { margin-left: auto; }
    .btn-outline-success { border: 1px solid var(--primary); color: var(--primary); background: transparent; padding: 0.375rem 0.75rem; border-radius: 4px; cursor: pointer; font-size: 0.75rem; }
    .btn-outline-success:hover { background: var(--primary); color: white; }
  `],
})
export class MatrizPresupuestoSeguimientoComponent implements OnInit {
  cargando = true;
  seguimientos: any[] = [];
  filtrados: any[] = [];
  gestiones: number[] = [];

  filtroTexto = '';
  filtroGestion = '';
  filtroEstado = '';

  constructor(private api: ApiService) {}

  ngOnInit(): void {
    this.cargarDatos();
  }

  private cargarDatos(): void {
    this.cargando = true;
    Promise.all([
      this.fetchList('/articulacion/seguimientos/'),
      this.fetchList('/articulacion/acciones-poa/'),
      this.fetchList('/articulacion/operaciones/'),
      this.fetchList('/articulacion/actividades/'),
    ]).then(([segs, accs, ops, acts]) => {
      const accMap = this.buildMap(accs, 'id');
      const opMap = this.buildMap(ops, 'id');
      const actMap = this.buildMap(acts, 'id');

      this.seguimientos = segs.map((s: any) => ({
        ...s,
        accion_poa_nombre: accMap.get(s.accion_poa)?.denominacion || '—',
        operacion_nombre: opMap.get(s.operacion)?.denominacion || '—',
        actividad_nombre: actMap.get(s.actividad)?.denominacion || '—',
      }));

      this.gestiones = [...new Set(segs.map((s: any) => s.gestion).filter(Boolean))].sort();
      this.aplicarFiltros();
      this.cargando = false;
    }).catch(() => { this.cargando = false; });
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
    (list || []).forEach((item: any) => m.set(item[key], item));
    return m;
  }

  aplicarFiltros(): void {
    let items = this.seguimientos;
    if (this.filtroTexto.trim()) {
      const q = this.filtroTexto.trim().toLowerCase();
      items = items.filter(i => i.id_cadena?.toLowerCase().includes(q));
    }
    if (this.filtroGestion) {
      items = items.filter(i => i.gestion === Number(this.filtroGestion));
    }
    if (this.filtroEstado) {
      items = items.filter(i => i.estado === this.filtroEstado);
    }
    this.filtrados = items;
  }

  exportarXLSX(): void {
    const url = `${environment.apiUrl}/api/v1/reportes/articulacion_matriz_pei_poa/?gestion=${this.filtroGestion || new Date().getFullYear()}`;
    window.open(url, '_blank');
  }
}

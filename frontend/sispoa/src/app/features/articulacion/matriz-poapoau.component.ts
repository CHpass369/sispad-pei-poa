import { Component, OnInit } from '@angular/core';
import { ApiService } from '../../core/services/api.service';
import { environment } from '../../../environments/environment';

interface OperacionExpandida {
  data: any;
  expandida: boolean;
  actividades: ActividadExpandida[];
}

interface ActividadExpandida {
  data: any;
  expandida: boolean;
  tareas: any[];
}

@Component({
  selector: 'app-matriz-poapoau',
  standalone: false,
  template: `
    <div class="matriz-page">
      <div class="page-header">
        <h2>Matriz 3 — Articulación POA → POAU</h2>
        <p class="text-secondary">
          Despliegue jerárquico: Operación → Actividad → Tarea con programación mensual
        </p>
      </div>

      <div class="card filtros-card">
        <div class="filtros">
          <div class="field">
            <label>Buscar</label>
            <input [(ngModel)]="filtro" class="form-control" placeholder="Código o denominación..."
                   (input)="aplicarFiltro()">
          </div>
          <div class="field">
            <label>Estado</label>
            <select [(ngModel)]="filtroEstado" class="form-control" (change)="aplicarFiltro()">
              <option value="">Todos</option>
              <option value="REFERENCIAL">Referencial</option>
              <option value="ENVIADO">Enviado</option>
              <option value="APROBADO">Aprobado</option>
              <option value="OBSERVADO">Observado</option>
            </select>
          </div>
          <div class="field">
            <label>&nbsp;</label>
            <span class="badge badge-info">{{ stats.ops }} ops · {{ stats.acts }} acts · {{ stats.tars }} tars</span>
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
                <th style="width:30px"></th>
                <th>Código</th>
                <th>Denominación</th>
                <th>Tipo</th>
                <th>Responsable</th>
                <th>Meta Anual</th>
                <th>Unidad</th>
                <th>Inicio</th>
                <th>Fin</th>
                <th>Estado</th>
              </tr>
            </thead>
            <tbody>
              <ng-container *ngFor="let op of operacionesFiltradas">
                <tr class="fila-op" (click)="op.expandida = !op.expandida">
                  <td class="toggle-cell">
                    <span class="toggle-icon" [class.expandido]="op.expandida">▶</span>
                  </td>
                  <td><span class="codigo">{{ op.data.codigo_operacion }}</span></td>
                  <td class="cell-desc"><strong>{{ op.data.denominacion }}</strong></td>
                  <td>{{ op.data.tipo_operacion || '—' }}</td>
                  <td>{{ op.data.responsable || '—' }}</td>
                  <td class="num">{{ op.data.meta_anual != null ? op.data.meta_anual : '—' }}</td>
                  <td>{{ op.data.unidad_medida || '—' }}</td>
                  <td>{{ op.data.fecha_inicio || '—' }}</td>
                  <td>{{ op.data.fecha_fin || '—' }}</td>
                  <td>
                    <span class="badge"
                          [class.badge-info]="op.data.estado==='REFERENCIAL'"
                          [class.badge-warning]="op.data.estado==='ENVIADO'"
                          [class.badge-success]="op.data.estado==='APROBADO'"
                          [class.badge-danger]="op.data.estado==='OBSERVADO'">{{ op.data.estado }}</span>
                  </td>
                </tr>
                <ng-container *ngIf="op.expandida">
                  <tr *ngFor="let act of op.actividades" class="fila-act">
                    <td></td>
                    <td class="act-td" colspan="9">
                      <div class="jerarquia-wrapper">
                        <div class="act-header" (click)="act.expandida = !act.expandida">
                          <span class="toggle-icon sub" [class.expandido]="act.expandida">▶</span>
                          <span class="codigo-sub">{{ act.data.codigo_actividad }}</span>
                          <span class="act-nombre"><strong>{{ act.data.denominacion }}</strong></span>
                          <span class="act-meta">Meta: {{ act.data.meta_anual || '—' }} {{ act.data.unidad_medida || '' }}</span>
                          <span class="badge badge-info" *ngIf="act.data.estado==='REFERENCIAL'">{{ act.data.estado }}</span>
                          <span class="badge badge-success" *ngIf="act.data.estado!=='REFERENCIAL'">{{ act.data.estado }}</span>
                        </div>
                        <div *ngIf="act.expandida && act.tareas.length > 0" class="tareas-list">
                          <div *ngFor="let t of act.tareas" class="tarea-item">
                            <span class="codigo-tar">{{ t.codigo_tarea }}</span>
                            <span class="tar-nombre">{{ t.denominacion }}</span>
                            <span class="tar-resp">{{ t.responsable || '—' }}</span>
                            <span class="tar-fechas">{{ t.fecha_inicio || '—' }} → {{ t.fecha_fin || '—' }}</span>
                            <span *ngIf="t.metas != null" class="tar-meta">Meta: {{ t.metas }}</span>
                            <span class="badge badge-info" *ngIf="t.estado==='REFERENCIAL'">{{ t.estado }}</span>
                            <span class="badge badge-success" *ngIf="t.estado!=='REFERENCIAL'">{{ t.estado }}</span>
                          </div>
                          <div *ngIf="act.tareas.length === 0" class="tarea-item empty">Sin tareas</div>
                        </div>
                        <div *ngIf="act.expandida && act.tareas.length === 0" class="tareas-list">
                          <div class="tarea-item empty">Sin tareas registradas</div>
                        </div>
                      </div>
                    </td>
                  </tr>
                </ng-container>
              </ng-container>
              <tr *ngIf="cargando">
                <td colspan="10" class="empty-cell">Cargando datos...</td>
              </tr>
              <tr *ngIf="!cargando && operacionesFiltradas.length === 0">
                <td colspan="10" class="empty-cell">No se encontraron operaciones</td>
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
    .matriz-table td { padding: 0.5rem 0.75rem; border-bottom: 1px solid var(--border); vertical-align: top; }
    .matriz-table tbody tr:hover td { background: #F0F7F3; }

    .fila-op { cursor: pointer; }
    .fila-op td { background: #E8F5E9; font-weight: 500; border-bottom: 2px solid #C8E6C9; }
    .fila-op:hover td { background: #C8E6C9; }

    .fila-act td { padding: 0; }
    .jerarquia-wrapper { padding: 0.5rem 1rem 0.5rem 1.5rem; background: #FAFCFA; }
    .act-header { display: flex; align-items: center; gap: 0.625rem; cursor: pointer; padding: 0.375rem 0; }
    .act-header:hover { background: #F0F7F3; border-radius: 4px; }
    .act-nombre { flex: 1; font-size: 0.8125rem; }
    .act-meta { font-size: 0.75rem; color: var(--text-secondary); margin-right: auto; }
    .codigo-sub { font-family: 'Courier New', monospace; font-weight: 600; font-size: 0.75rem; color: var(--primary-dark); }

    .tareas-list { margin-left: 1.75rem; border-left: 2px solid var(--border); padding-left: 0.75rem; }
    .tarea-item {
      display: flex; align-items: center; gap: 0.625rem;
      padding: 0.375rem 0.5rem; font-size: 0.75rem;
      border-bottom: 1px solid var(--border);
    }
    .tarea-item:last-child { border-bottom: none; }
    .tarea-item:hover { background: #F5F7F5; border-radius: 4px; }
    .tarea-item.empty { color: var(--text-secondary); font-style: italic; }
    .codigo-tar { font-family: 'Courier New', monospace; font-weight: 600; font-size: 0.6875rem; color: #388E3C; min-width: 90px; }
    .tar-nombre { flex: 1; }
    .tar-resp { font-size: 0.6875rem; color: var(--text-secondary); min-width: 100px; }
    .tar-fechas { font-size: 0.6875rem; color: var(--text-secondary); min-width: 130px; }
    .tar-meta { font-size: 0.6875rem; color: var(--primary-dark); }

    .toggle-cell { text-align: center; }
    .toggle-icon { display: inline-block; transition: transform 0.15s; font-size: 0.625rem; color: var(--primary); }
    .toggle-icon.expandido { transform: rotate(90deg); }
    .toggle-icon.sub { font-size: 0.5rem; }

    .codigo { font-family: 'Courier New', monospace; font-weight: 700; font-size: 0.75rem; color: var(--primary-dark); white-space: nowrap; }
    .cell-desc { max-width: 240px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
    .num { text-align: right; font-family: 'Courier New', monospace; font-size: 0.75rem; }
    .empty-cell { text-align: center; color: var(--text-secondary); padding: 2rem; font-size: 0.875rem; }
    .badge { font-size: 0.6875rem; }
    .export-field { margin-left: auto; }
    .btn-outline-success { border: 1px solid var(--primary); color: var(--primary); background: transparent; padding: 0.375rem 0.75rem; border-radius: 4px; cursor: pointer; font-size: 0.75rem; }
    .btn-outline-success:hover { background: var(--primary); color: white; }
  `],
})
export class MatrizPOAPOAUComponent implements OnInit {
  cargando = true;
  operaciones: OperacionExpandida[] = [];
  operacionesFiltradas: OperacionExpandida[] = [];
  filtro = '';
  filtroEstado = '';
  stats = { ops: 0, acts: 0, tars: 0 };

  constructor(private api: ApiService) {}

  ngOnInit(): void {
    this.cargarDatos();
  }

  cargarDatos(): void {
    this.cargando = true;
    Promise.all([
      this.fetchList('/articulacion/operaciones/'),
      this.fetchList('/articulacion/actividades/'),
      this.fetchList('/articulacion/tareas/'),
    ]).then(([ops, acts, tars]) => {
      const actMap = new Map<string, any[]>();
      acts.forEach((a: any) => {
        const key = a.operacion;
        if (!actMap.has(key)) actMap.set(key, []);
        actMap.get(key)!.push(a);
      });

      const tarMap = new Map<string, any[]>();
      tars.forEach((t: any) => {
        const key = t.actividad;
        if (!tarMap.has(key)) tarMap.set(key, []);
        tarMap.get(key)!.push(t);
      });

      this.operaciones = ops.map((op: any) => {
        const actsOfOp = actMap.get(op.id) || [];
        return {
          data: op,
          expandida: false,
          actividades: actsOfOp.map((act: any) => ({
            data: act,
            expandida: false,
            tareas: tarMap.get(act.id) || [],
          })),
        };
      });

      this.stats = {
        ops: this.operaciones.length,
        acts: acts.length,
        tars: tars.length,
      };
      this.aplicarFiltro();
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

  aplicarFiltro(): void {
    let items = this.operaciones;
    if (this.filtro.trim()) {
      const q = this.filtro.trim().toLowerCase();
      items = items.filter(op =>
        op.data.codigo_operacion?.toLowerCase().includes(q) ||
        op.data.denominacion?.toLowerCase().includes(q)
      );
    }
    if (this.filtroEstado) {
      items = items.filter(op => op.data.estado === this.filtroEstado);
    }
    this.operacionesFiltradas = items;
  }

  exportarXLSX(): void {
    const url = `${environment.apiUrl}/api/v1/reportes/articulacion_matriz_pei_poa/?gestion=2026`;
    window.open(url, '_blank');
  }
}

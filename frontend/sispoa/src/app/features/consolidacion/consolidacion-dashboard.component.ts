import { Component, OnInit } from '@angular/core';
import { ConsolidacionService, ConsolidacionUE } from './consolidacion.service';

@Component({
  standalone: false,
  selector: 'app-consolidacion-dashboard',
  template: `
    <div class="page-header">
      <h2>Consolidación de Planificación</h2>
      <p class="text-secondary">Estado de consolidación por Unidad Ejecutora</p>
    </div>

    <div class="acciones-superior">
      <div class="field">
        <input [(ngModel)]="busqueda" (keyup.enter)="cargar()" class="form-control"
               placeholder="Buscar por nombre de UE...">
      </div>
      <button class="btn btn-outline" (click)="cargar()">Recargar</button>
    </div>

    <div class="resumen-grid" *ngIf="!cargando && consolidaciones.length > 0">
      <div class="card resumen-item">
        <div class="resumen-valor">{{ consolidaciones.length }}</div>
        <div class="resumen-label">Total UEs</div>
      </div>
      <div class="card resumen-item verde">
        <div class="resumen-valor">{{ uesCompletas }}</div>
        <div class="resumen-label">Completas</div>
      </div>
      <div class="card resumen-item amarillo">
        <div class="resumen-valor">{{ uesEnCurso }}</div>
        <div class="resumen-label">En Curso</div>
      </div>
      <div class="card resumen-item rojo">
        <div class="resumen-valor">{{ uesPendientes }}</div>
        <div class="resumen-label">Pendientes</div>
      </div>
    </div>

    <div class="table-container" *ngIf="!cargando">
      <table class="data-table">
        <thead>
          <tr>
            <th>Unidad Ejecutora</th>
            <th>PEI</th>
            <th>PAD</th>
            <th>POA</th>
            <th>POAU</th>
            <th>Estado General</th>
            <th>Acciones</th>
          </tr>
        </thead>
        <tbody>
          <tr *ngFor="let c of consolidacionesFiltradas">
            <td><strong>{{ c.ue_nombre }}</strong></td>
            <td>
              <div class="progress-cell">
                <div class="progress-bar">
                  <div class="progress-fill" [style.width.%]="c.pei_porcentaje"
                       [class.fill-ok]="c.pei_porcentaje >= 80"
                       [class.fill-warn]="c.pei_porcentaje >= 40 && c.pei_porcentaje < 80"
                       [class.fill-danger]="c.pei_porcentaje < 40"></div>
                </div>
                <span class="progress-text">{{ c.pei_porcentaje }}%</span>
              </div>
            </td>
            <td>
              <div class="progress-cell">
                <div class="progress-bar">
                  <div class="progress-fill" [style.width.%]="c.pad_porcentaje"
                       [class.fill-ok]="c.pad_porcentaje >= 80"
                       [class.fill-warn]="c.pad_porcentaje >= 40 && c.pad_porcentaje < 80"
                       [class.fill-danger]="c.pad_porcentaje < 40"></div>
                </div>
                <span class="progress-text">{{ c.pad_porcentaje }}%</span>
              </div>
            </td>
            <td>
              <div class="progress-cell">
                <div class="progress-bar">
                  <div class="progress-fill" [style.width.%]="c.poa_porcentaje"
                       [class.fill-ok]="c.poa_porcentaje >= 80"
                       [class.fill-warn]="c.poa_porcentaje >= 40 && c.poa_porcentaje < 80"
                       [class.fill-danger]="c.poa_porcentaje < 40"></div>
                </div>
                <span class="progress-text">{{ c.poa_porcentaje }}%</span>
              </div>
            </td>
            <td>
              <div class="progress-cell">
                <div class="progress-bar">
                  <div class="progress-fill" [style.width.%]="c.poau_porcentaje"
                       [class.fill-ok]="c.poau_porcentaje >= 80"
                       [class.fill-warn]="c.poau_porcentaje >= 40 && c.poau_porcentaje < 80"
                       [class.fill-danger]="c.poau_porcentaje < 40"></div>
                </div>
                <span class="progress-text">{{ c.poau_porcentaje }}%</span>
              </div>
            </td>
            <td>
              <span class="badge" [ngClass]="'badge-' + c.estado_general">{{ c.estado_general }}</span>
            </td>
            <td>
              <button class="btn btn-sm btn-outline" (click)="verDetalle(c)">Ver Detalle</button>
            </td>
          </tr>
        </tbody>
      </table>
      <div *ngIf="consolidacionesFiltradas.length === 0" class="empty">No se encontraron unidades ejecutoras</div>
    </div>

    <div class="loading" *ngIf="cargando">Cargando consolidación...</div>
    <div class="alert alert-error" *ngIf="error">{{ error }}</div>
  `,
  styles: [`
    .page-header { margin-bottom: 1rem; }
    .page-header h2 { font-size: 1.5rem; margin-bottom: 0.25rem; }
    .text-secondary { color: var(--text-secondary); font-size: 0.875rem; }
    .acciones-superior { display: flex; gap: 1rem; margin-bottom: 1.5rem; align-items: center; }
    .acciones-superior .field { flex: 1; }
    .resumen-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(160px, 1fr)); gap: 1rem; margin-bottom: 2rem; }
    .card { background: var(--surface); border: 1px solid var(--border); border-radius: 8px; padding: 1.25rem; }
    .resumen-item { text-align: center; }
    .resumen-valor { font-size: 1.75rem; font-weight: 700; }
    .resumen-label { font-size: 0.8125rem; color: var(--text-secondary); margin-top: 0.25rem; }
    .resumen-item.verde .resumen-valor { color: #2E7D32; }
    .resumen-item.amarillo .resumen-valor { color: #F57F17; }
    .resumen-item.rojo .resumen-valor { color: #C62828; }
    .table-container { overflow-x: auto; }
    .data-table { width: 100%; border-collapse: collapse; background: var(--surface); border-radius: 8px; overflow: hidden; }
    .data-table th { background: var(--background, #f5f5f5); padding: 0.75rem 1rem; text-align: left; font-size: 0.75rem; text-transform: uppercase; color: var(--text-secondary); }
    .data-table td { padding: 0.75rem 1rem; border-top: 1px solid var(--border); font-size: 0.875rem; }
    .data-table tr:hover td { background: var(--hover, #fafafa); }
    .progress-cell { display: flex; align-items: center; gap: 0.5rem; min-width: 120px; }
    .progress-bar { flex: 1; height: 8px; background: var(--border); border-radius: 4px; overflow: hidden; }
    .progress-fill { height: 100%; border-radius: 4px; transition: width 0.5s; }
    .fill-ok { background: #2E7D32; }
    .fill-warn { background: #F57F17; }
    .fill-danger { background: #C62828; }
    .progress-text { font-size: 0.8125rem; font-weight: 600; min-width: 40px; }
    .badge { display: inline-block; padding: 0.125rem 0.5rem; border-radius: 4px; font-size: 0.75rem; font-weight: 600; text-transform: uppercase; }
    .badge-completo { background: #E8F5E9; color: #2E7D32; }
    .badge-en_curso, .badge-en-curso { background: #FFF3E0; color: #E65100; }
    .badge-pendiente { background: #FFEBEE; color: #C62828; }
    .badge-borrador { background: #F5F5F5; color: #616161; }
    .badge-aprobado { background: #E8F5E9; color: #2E7D32; }
    .btn { display: inline-flex; align-items: center; padding: 0.5rem 1rem; border-radius: 6px; border: none; font-size: 0.875rem; font-weight: 600; cursor: pointer; }
    .btn-outline { background: transparent; border: 1px solid var(--border); color: var(--text-primary); }
    .btn-outline:hover { background: var(--hover, #f5f5f5); }
    .btn-sm { padding: 0.25rem 0.5rem; font-size: 0.8125rem; }
    .empty { text-align: center; padding: 2rem; color: var(--text-secondary); }
    .loading { text-align: center; padding: 2rem; color: var(--text-secondary); }
    .alert { padding: 0.75rem 1rem; border-radius: 6px; margin-top: 1rem; }
    .alert-error { background: #FFEBEE; color: var(--warn); }
  `]
})
export class ConsolidacionDashboardComponent implements OnInit {
  consolidaciones: ConsolidacionUE[] = [];
  busqueda = '';
  cargando = true;
  error = '';

  get consolidacionesFiltradas(): ConsolidacionUE[] {
    if (!this.busqueda) return this.consolidaciones;
    const term = this.busqueda.toLowerCase();
    return this.consolidaciones.filter(c => c.ue_nombre?.toLowerCase().includes(term));
  }

  get uesCompletas(): number {
    return this.consolidaciones.filter(c => c.estado_general === 'completo' || c.estado_general === 'aprobado').length;
  }

  get uesEnCurso(): number {
    return this.consolidaciones.filter(c => c.estado_general === 'en_curso' || c.estado_general === 'en-curso').length;
  }

  get uesPendientes(): number {
    return this.consolidaciones.filter(c => c.estado_general === 'pendiente' || c.estado_general === 'borrador').length;
  }

  constructor(private consolidacionService: ConsolidacionService) {}

  ngOnInit(): void {
    this.cargar();
  }

  cargar(): void {
    this.cargando = true;
    this.error = '';
    const params: Record<string, string | number | boolean> = {};
    if (this.busqueda) params.search = this.busqueda;

    this.consolidacionService.listarPoau(params).subscribe({
      next: (data: any) => {
        const poauList = data.results || data;
        const ueMap = new Map<number, ConsolidacionUE>();

        poauList.forEach((p: any) => {
          const ueId = p.unidad_ejecutora || 0;
          const ueNombre = p.unidad_ejecutora_nombre || `UE ${ueId}`;
          if (!ueMap.has(ueId)) {
            ueMap.set(ueId, {
              ue_id: ueId,
              ue_nombre: ueNombre,
              pei_porcentaje: 0,
              pad_porcentaje: 0,
              poa_porcentaje: 0,
              poau_porcentaje: p.avance_porcentual || 0,
              estado_general: p.estado || 'borrador',
            });
          } else {
            const existing = ueMap.get(ueId)!;
            existing.poau_porcentaje = Math.max(existing.poau_porcentaje, p.avance_porcentual || 0);
          }
        });

        this.consolidaciones = Array.from(ueMap.values());
        this.cargando = false;
      },
      error: () => {
        this.error = 'Error al cargar consolidación';
        this.cargando = false;
      },
    });
  }

  verDetalle(c: ConsolidacionUE): void {
    window.location.href = `/consolidacion/${c.ue_id}`;
  }
}

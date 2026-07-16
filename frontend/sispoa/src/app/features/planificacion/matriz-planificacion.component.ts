import { Component, OnInit } from '@angular/core';
import { ApiService } from '../../core/services/api.service';

@Component({
  standalone: false,
  selector: 'app-matriz-planificacion',
  template: `
    <div class="matriz-page">
      <div class="page-header">
        <h2>Matriz de Planificación Estratégica</h2>
        <p class="text-secondary">Articulación PDES → PTDI → PEI → POA</p>
        <div class="filtros">
          <label>Secretaría:</label>
          <select [(ngModel)]="filtroSec" (change)="filtrar()" class="form-control filtro-select">
            <option value="">Todas</option>
            <option *ngFor="let s of secretarias" [value]="s.sigla">{{ s.nombre }}</option>
          </select>
          <label>Programa:</label>
          <input [(ngModel)]="filtroProg" (keyup.enter)="filtrar()" class="form-control" 
                 placeholder="Filtrar por código...">
          <label>Buscar:</label>
          <input [(ngModel)]="filtroTexto" (keyup.enter)="filtrar()" class="form-control" 
                 placeholder="Acción o indicador...">
        </div>
      </div>

      <div class="card">
        <div class="table-wrapper">
          <table class="matriz-table">
            <thead>
              <tr>
                <th>AMP</th>
                <th>Acción de Mediano Plazo (PEI)</th>
                <th>ACP</th>
                <th>Acción de Corto Plazo (POA)</th>
                <th>Indicador</th>
                <th>Fórmula</th>
                <th>Línea Base</th>
                <th>Meta 2025</th>
                <th>Unidad</th>
                <th>Categoría Programática</th>
                <th>Secretaría</th>
              </tr>
            </thead>
            <tbody>
              <ng-container *ngFor="let amp of ampsFiltrados">
                <tr *ngFor="let acp of amp.acciones; let i = index" class="artic-row">
                  <td *ngIf="i === 0" [attr.rowspan]="amp.acciones.length" class="amp-cell">
                    <strong>{{ amp.codigo_amp }}</strong>
                  </td>
                  <td *ngIf="i === 0" [attr.rowspan]="amp.acciones.length" class="amp-desc">
                    {{ amp.nombre }}
                    <div class="producto" *ngIf="amp.producto">Producto: {{ amp.producto }}</div>
                    <div class="programa-link" *ngIf="amp.programa"><small>{{ amp.programa }}</small></div>
                  </td>
                  <td><strong>{{ acp.codigo }}</strong></td>
                  <td>{{ acp.nombre }}</td>
                  <td>{{ acp.indicador || '—' }}</td>
                  <td class="formula-cell">{{ acp.formula || '—' }}</td>
                  <td>{{ acp.linea_base || '—' }}</td>
                  <td>{{ acp.meta_2025 || '—' }}</td>
                  <td>{{ acp.unidad_medida || '—' }}</td>
                  <td><code>{{ acp.cat_prog || '—' }}</code></td>
                  <td><span class="badge badge-info">{{ acp.secretaria || '—' }}</span></td>
                </tr>
              </ng-container>
              <tr *ngIf="ampsFiltrados.length === 0">
                <td colspan="11" class="empty">No se encontraron acciones</td>
              </tr>
            </tbody>
          </table>
        </div>
        <div class="table-footer" *ngIf="amps.length > 0">
          Mostrando {{ ampsFiltrados.length }} de {{ amps.length }} acciones de mediano plazo
        </div>
      </div>
    </div>
  `,
  styles: [`
    .matriz-page { padding-bottom: 2rem; }
    .page-header { margin-bottom: 1rem; }
    .page-header h2 { font-size: 1.25rem; }
    .filtros { display: flex; gap: 0.75rem; margin-top: 0.75rem; flex-wrap: wrap; }
    .filtros label { font-size: 0.75rem; color: var(--text-secondary); align-self: center; }
    .filtro-select { width: auto; min-width: 150px; padding: 0.375rem 0.5rem; }
    .filtros input { width: auto; min-width: 200px; padding: 0.375rem 0.5rem; }
    .table-wrapper { overflow-x: auto; }
    .matriz-table { width: 100%; border-collapse: collapse; font-size: 0.8125rem; }
    .matriz-table th { 
      background: var(--primary); color: white; padding: 0.5rem 0.625rem;
      text-align: left; font-weight: 600; font-size: 0.6875rem;
      text-transform: uppercase; letter-spacing: 0.03em;
      white-space: nowrap; position: sticky; top: 0; z-index: 1;
    }
    .matriz-table td { padding: 0.5rem 0.625rem; border-bottom: 1px solid var(--border); vertical-align: top; }
    .matriz-table tbody tr:hover { background: #F0F7F3; }
    .amp-cell { background: var(--bg); font-size: 0.8125rem; vertical-align: middle !important; }
    .amp-desc { background: var(--bg); font-size: 0.8125rem; }
    .producto { font-size: 0.75rem; color: var(--text-secondary); margin-top: 0.25rem; }
    .programa-link { margin-top: 0.25rem; }
    .programa-link small { color: var(--primary); }
    .formula-cell { font-family: 'Courier New', monospace; font-size: 0.75rem; max-width: 200px; overflow: hidden; text-overflow: ellipsis; }
    code { font-size: 0.75rem; background: #E8F5E9; padding: 0.125rem 0.375rem; border-radius: 3px; }
    .empty { text-align: center; padding: 2rem; color: var(--text-secondary); }
    .table-footer { padding: 0.75rem; font-size: 0.75rem; color: var(--text-secondary); }
  `]
})
export class MatrizPlanificacionComponent implements OnInit {
  amps: any[] = [];
  ampsFiltrados: any[] = [];
  secretarias: any[] = [];
  filtroSec = '';
  filtroProg = '';
  filtroTexto = '';

  constructor(private api: ApiService) {}

  ngOnInit(): void {
    this.cargarSecretarias();
    this.cargarArticulacion();
  }

  cargarSecretarias(): void {
    this.api.get<any>('/unidades/', { gestion: 2026, activo: true }).subscribe({
      next: (r: any) => this.secretarias = (r.results || r).filter((u: any) => u.sigla),
    });
  }

  cargarArticulacion(): void {
    // Cargar AMPs con sus ACPs desde la API
    this.api.get<any>('/acciones-mediano-plazo/').subscribe({
      next: (amps: any) => {
        const lista = amps.results || amps;
        this.amps = lista.map((amp: any) => ({
          id: amp.id,
          codigo_amp: amp.codigo,
          nombre: amp.nombre,
          producto: '',
          programa: '',
          acciones: [{
            codigo: 'ACP-' + (amp.codigo || '').replace('AMP-', ''),
            nombre: amp.nombre?.substring(0, 80) || '',
            indicador: '',
            formula: '',
            linea_base: '',
            meta_2025: '',
            unidad_medida: '',
            cat_prog: '',
            secretaria: amp.responsable_nombre || '',
          }]
        }));
        // Cargar ACPs reales
        this.api.get<any>('/acciones-corto-plazo/', { gestion: 2026 }).subscribe({
          next: (acps: any) => {
            const acpList = acps.results || acps;
            // Mapear ACPs a sus AMPs
            for (const amp of this.amps) {
              const relacionadas = acpList.filter((a: any) => 
                a.accion_mediano_plazo === amp.id
              );
              if (relacionadas.length > 0) {
                amp.acciones = relacionadas.map((a: any) => ({
                  codigo: a.codigo,
                  nombre: a.nombre,
                  indicador: '',
                  formula: '',
                  linea_base: '',
                  meta_2025: '',
                  unidad_medida: '',
                  cat_prog: '',
                  secretaria: '',
                }));
              }
            }
            this.filtrar();
          }
        });
      }
    });
  }

  filtrar(): void {
    this.ampsFiltrados = this.amps.filter(amp => {
      if (this.filtroSec) {
        const secMatch = amp.acciones.some((a: any) => 
          a.secretaria?.toUpperCase().includes(this.filtroSec.toUpperCase())
        );
        if (!secMatch) return false;
      }
      if (this.filtroProg) {
        const progMatch = amp.acciones.some((a: any) =>
          (a.cat_prog || '').includes(this.filtroProg)
        );
        if (!progMatch) return false;
      }
      if (this.filtroTexto) {
        const txt = this.filtroTexto.toLowerCase();
        const txtMatch = amp.nombre.toLowerCase().includes(txt) ||
          amp.acciones.some((a: any) => 
            a.nombre?.toLowerCase().includes(txt) || 
            a.indicador?.toLowerCase().includes(txt)
          );
        if (!txtMatch) return false;
      }
      return true;
    });
  }
}

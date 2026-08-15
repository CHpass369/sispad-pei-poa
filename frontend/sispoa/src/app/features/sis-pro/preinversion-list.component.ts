import { Component, OnInit } from '@angular/core';
import { PermissionsService } from '../../core/services/permissions.service';
import { PreinversionService, ProyectoPreinversion } from './preinversion.service';

@Component({
  standalone: false,
  selector: 'app-preinversion-list',
  template: `
    <div class="page-header">
      <h2>Preinversión — Expediente RM 115</h2>
      <p class="text-secondary">ITCP · TDR · EDTP — banco de proyectos viables (SISPRE)</p>
    </div>
    @if (error) {
      <div class="alert alert-error">{{ error }}</div>
    }
    @if (mensaje) {
      <div class="alert alert-success">{{ mensaje }}</div>
    }
    
    <div class="toolbar">
      <label>Gestión
        <input type="number" [(ngModel)]="filtro.gestion" (change)="cargar()" class="input" />
      </label>
      <label>Tipología
        <select [(ngModel)]="filtro.tipologia_rm115" (change)="cargar()" class="input">
          <option value="">Todas</option>
          <option value="I">I — Empresarial Productivo</option>
          <option value="II">II — Apoyo Productivo</option>
          <option value="III">III — Desarrollo Social</option>
          <option value="IV">IV — Fortalecimiento Institucional</option>
          <option value="V">V — Investigación y Tecnología</option>
        </select>
      </label>
      <label>Habilitados POA
        <select [(ngModel)]="filtro.habilitado_poa" (change)="cargar()" class="input">
          <option [ngValue]="undefined">Todos</option>
          <option [ngValue]="true">Sí</option>
          <option [ngValue]="false">No</option>
        </select>
      </label>
      <a class="btn btn-sm btn-inventario" routerLink="/sis-pro/preinversion/inventario">📚 Inventario documental</a>
    </div>
    
    @if (cargando) {
      <div class="loading">Cargando expedientes...</div>
    }
    @if (!cargando) {
      <table class="data-table">
        <thead>
          <tr>
            <th>Código</th><th>Proyecto</th><th>Tipología</th><th>Estado</th>
            <th>Madurez</th><th>POA</th><th></th>
          </tr>
        </thead>
        <tbody>
          @for (p of proyectos; track p) {
            <tr>
              <td>{{ p.codigo_interno }}</td>
              <td>{{ p.nombre }}</td>
              <td><span class="badge">{{ p.tipologia_rm115 || '—' }}</span></td>
              <td><span class="badge estado">{{ service.etiquetaEstadoExpediente(p.estado_preinversion) }}</span></td>
              <td>
                <div class="madurez">
                  <div class="barra"><div class="relleno" [style.width.%]="madurezNum(p)"></div></div>
                  {{ p.puntaje_madurez }}%
                </div>
              </td>
              <td>{{ p.habilitado_poa ? '✅' : '—' }}</td>
              <td>
                <a class="btn btn-sm" [routerLink]="['/sis-pro/preinversion', p.id, 'wizard']">Wizard</a>
                <a class="btn btn-sm" [routerLink]="['/sis-pro/preinversion', p.id]">Expediente</a>
              </td>
            </tr>
          }
        </tbody>
      </table>
    }
    @if (!cargando && proyectos.length === 0) {
      <div class="empty">No hay proyectos en preinversión</div>
    }
    `,
  styles: [`
    .page-header { margin-bottom: 1.5rem; }
    .text-secondary { color: var(--text-secondary); font-size: 0.875rem; }
    .toolbar { display: flex; gap: 1rem; align-items: flex-end; margin-bottom: 1.25rem; flex-wrap: wrap; }
    .toolbar label { display: flex; flex-direction: column; gap: 0.25rem; font-size: 0.75rem; color: var(--text-secondary); }
    .input { padding: 0.5rem; border: 1px solid var(--border); border-radius: 6px; font-size: 0.875rem; }
    .data-table { width: 100%; border-collapse: collapse; background: var(--surface); border: 1px solid var(--border); border-radius: 8px; }
    .data-table th, .data-table td { padding: 0.625rem 0.75rem; text-align: left; border-bottom: 1px solid var(--border); font-size: 0.8125rem; }
    .badge { display: inline-block; padding: 0.125rem 0.5rem; border-radius: 4px; font-size: 0.6875rem; font-weight: 600; background: #E3F2FD; color: #1565C0; }
    .estado { background: #F3E5F5; color: #6A1B9A; }
    .madurez { display: flex; align-items: center; gap: 0.375rem; font-size: 0.75rem; }
    .barra { width: 70px; height: 6px; background: #E0E0E0; border-radius: 3px; overflow: hidden; }
    .relleno { height: 100%; background: var(--primary); }
    .btn { display: inline-flex; align-items: center; padding: 0.5rem 0.875rem; border-radius: 6px; border: none; font-size: 0.8125rem; font-weight: 600; cursor: pointer; text-decoration: none; }
    .btn-sm { background: #E3F2FD; color: #1565C0; }
    .btn-inventario { background: #EDE7F6; color: #4527A0; margin-left: auto; }
    .loading { text-align: center; padding: 2rem; color: var(--text-secondary); }
    .empty { text-align: center; padding: 2rem; color: var(--text-secondary); }
    .alert { padding: 0.75rem 1rem; border-radius: 6px; margin-bottom: 1rem; }
    .alert-error { background: #FFEBEE; color: var(--warn); }
    .alert-success { background: #E8F5E9; color: #2E7D32; }
  `],
})
export class PreinversionListComponent implements OnInit {
  cargando = true;
  error = '';
  mensaje = '';
  proyectos: ProyectoPreinversion[] = [];
  filtro: { gestion?: number; tipologia_rm115?: string; habilitado_poa?: boolean } = {};

  constructor(
    public service: PreinversionService,
    private permissions: PermissionsService,
  ) {}

  get puedeValidar(): boolean {
    return this.permissions.hasAnyCapability(['sis_pro.preinvestment.validate']);
  }

  ngOnInit(): void {
    this.cargar();
  }

  cargar(): void {
    this.cargando = true;
    this.error = '';
    const params: Record<string, string | number | boolean> = {};
    if (this.filtro.gestion) params['gestion'] = this.filtro.gestion;
    if (this.filtro.tipologia_rm115) params['tipologia_rm115'] = this.filtro.tipologia_rm115;
    if (this.filtro.habilitado_poa !== undefined) params['habilitado_poa'] = this.filtro.habilitado_poa;
    this.service.listarProyectos(params).subscribe({
      next: (data) => { this.proyectos = data.results; this.cargando = false; },
      error: () => { this.error = 'Error al cargar los expedientes'; this.cargando = false; },
    });
  }

  madurezNum(p: ProyectoPreinversion): number {
    return Math.min(100, Number(p.puntaje_madurez) || 0);
  }
}

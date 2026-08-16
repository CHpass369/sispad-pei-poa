import { Component, OnInit } from '@angular/core';
import { PermissionsService } from '../../core/services/permissions.service';
import { PoaV2, SisPoaService } from './sis-poa.service';

@Component({
  standalone: false,
  selector: 'app-sis-poa-list',
  template: `
    <div class="page-header">
      <h2>POAs Institucionales</h2>
      <p class="text-secondary">SIS-POA V2 — jerarquía canónica</p>
    </div>
    @if (error) {
      <div class="alert alert-error">{{ error }}</div>
    }
    @if (mensaje) {
      <div class="alert alert-success">{{ mensaje }}</div>
    }
    
    @if (puedeFormular) {
      <form (ngSubmit)="crear()" class="form-inline">
        <input [(ngModel)]="form.gestion" name="gestion" type="number" placeholder="Gestión" required class="input" />
        <input [(ngModel)]="form.codigo" name="codigo" placeholder="Código" required class="input" />
        <input [(ngModel)]="form.nombre" name="nombre" placeholder="Nombre" required class="input" />
        <button type="submit" class="btn btn-primary">+ Crear POA</button>
      </form>
    }
    
    @if (cargando) {
      <div class="loading">Cargando POAs...</div>
    }
    @if (!cargando) {
      <table class="data-table">
        <thead>
          <tr><th>Código</th><th>Nombre</th><th>Gestión</th><th>Estado</th><th>PEI</th><th></th></tr>
        </thead>
        <tbody>
          @for (poa of poas; track poa) {
            <tr>
              <td>{{ poa.codigo }}</td>
              <td>{{ poa.nombre }}</td>
              <td>{{ poa.gestion }}</td>
              <td><span class="badge">{{ poa.estado }}</span></td>
              <td>{{ poa.version_pei ? '✓' : '—' }}</td>
              <td><a class="btn btn-sm" [routerLink]="['/sis-poa/poas', poa.id]">Detalle</a></td>
            </tr>
          }
        </tbody>
      </table>
    }
    @if (!cargando && poas.length === 0) {
      <div class="empty">No hay POAs registrados</div>
    }
    `,
  styles: [`
    .page-header { margin-bottom: 1.5rem; }
    .text-secondary { color: var(--text-secondary); font-size: 0.875rem; }
    .form-inline { display: flex; gap: 0.5rem; margin-bottom: 1.5rem; flex-wrap: wrap; }
    .input { padding: 0.5rem; border: 1px solid var(--border); border-radius: 6px; font-size: 0.875rem; }
    .btn { display: inline-flex; align-items: center; padding: 0.5rem 0.875rem; border-radius: 6px; border: none; font-size: 0.8125rem; font-weight: 600; cursor: pointer; text-decoration: none; }
    .btn-primary { background: var(--primary); color: white; }
    .btn-sm { background: var(--mdc-blue-50); color: var(--mdc-blue-800); }
    .data-table { width: 100%; border-collapse: collapse; background: var(--surface); border: 1px solid var(--border); border-radius: 8px; }
    .data-table th, .data-table td { padding: 0.625rem 0.75rem; text-align: left; border-bottom: 1px solid var(--border); font-size: 0.8125rem; }
    .badge { display: inline-block; padding: 0.125rem 0.5rem; border-radius: 4px; font-size: 0.6875rem; font-weight: 600; background: var(--mdc-blue-50); color: var(--mdc-blue-800); }
    .loading { text-align: center; padding: 2rem; color: var(--text-secondary); }
    .empty { text-align: center; padding: 2rem; color: var(--text-secondary); }
    .alert { padding: 0.75rem 1rem; border-radius: 6px; margin-bottom: 1rem; }
    .alert-error { background: var(--mdc-red-50); color: var(--warn); }
    .alert-success { background: var(--mdc-green-50); color: var(--mdc-green-800); }
  `],
})
export class SisPoaListComponent implements OnInit {
  cargando = true;
  error = '';
  mensaje = '';
  poas: PoaV2[] = [];
  form: { gestion: number | null; codigo: string; nombre: string } = {
    gestion: null, codigo: '', nombre: '',
  };

  constructor(
    private service: SisPoaService,
    private permissions: PermissionsService,
  ) {}

  get puedeFormular(): boolean {
    return this.permissions.hasAnyCapability(['sis_poa.formulate', 'sis_poa.poau.edit']);
  }

  ngOnInit(): void {
    this.service.listarPoas().subscribe({
      next: (data) => { this.poas = data.results; this.cargando = false; },
      error: () => { this.error = 'Error al cargar POAs'; this.cargando = false; },
    });
  }

  crear(): void {
    const { gestion, codigo, nombre } = this.form;
    if (!gestion || !codigo || !nombre) {
      this.error = 'Gestión, código y nombre son requeridos';
      return;
    }
    this.error = '';
    this.service.crearPoa({ gestion, codigo, nombre } as Partial<PoaV2>).subscribe({
      next: () => {
        this.mensaje = 'POA creado (vincula una versión de PEI para aprobarlo)';
        this.form = { gestion: null, codigo: '', nombre: '' };
        this.cargando = true;
        this.service.listarPoas().subscribe({
          next: (data) => { this.poas = data.results; this.cargando = false; },
          error: () => { this.error = 'Error al recargar'; this.cargando = false; },
        });
      },
      error: (err) => {
        this.error = err.error?.error?.version_pei?.[0] || 'Error al crear el POA';
      },
    });
  }
}

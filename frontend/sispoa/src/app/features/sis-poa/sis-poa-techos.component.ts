import { Component, OnInit } from '@angular/core';
import { PermissionsService } from '../../core/services/permissions.service';
import { environment } from '../../../environments/environment';
import { SisPoaService, TechoV2 } from './sis-poa.service';
import { HttpClient } from '@angular/common/http';

interface FuenteV1 {
  id: string;
  codigo: string;
  denominacion: string;
}

@Component({
  standalone: false,
  selector: 'app-sis-poa-techos',
  template: `
    <div class="page-header">
      <h2>Techos Presupuestarios</h2>
      <p class="text-secondary">Límites de programación por gestión y fuente</p>
    </div>
    @if (error) {
      <div class="alert alert-error">{{ error }}</div>
    }
    @if (mensaje) {
      <div class="alert alert-success">{{ mensaje }}</div>
    }
    
    @if (puedeGestionar) {
      <form (ngSubmit)="crear()" class="card form-inline">
        <div class="campo">
          <label>Gestión</label>
          <input [(ngModel)]="form.gestion" name="g" type="number" required class="input" />
        </div>
        <div class="campo">
          <label>Monto total</label>
          <input [(ngModel)]="form.monto_total" name="m" type="number" required class="input" />
        </div>
        <div class="campo">
          <label>Fuente</label>
          <select [(ngModel)]="form.fuente" name="f" required class="input">
            @for (fuente of fuentes; track fuente) {
              <option [value]="fuente.id">{{ fuente.codigo }} — {{ fuente.denominacion }}</option>
            }
          </select>
        </div>
        <div class="campo">
          <label>&nbsp;</label>
          <button type="submit" class="btn btn-primary">+ Techo</button>
        </div>
      </form>
    }
    
    @if (cargando) {
      <div class="loading">Cargando techos...</div>
    }
    @if (!cargando) {
      <table class="data-table">
        <thead>
          <tr><th>Gestión</th><th>Fuente</th><th>Monto</th><th>Estado</th><th></th></tr>
        </thead>
        <tbody>
          @for (techo of techos; track techo) {
            <tr>
              <td>{{ techo.gestion }}</td>
              <td>{{ techo.fuente_codigo }} — {{ techo.fuente_nombre }}</td>
              <td>Bs {{ techo.monto_total }}</td>
              <td><span class="badge">{{ techo.activo ? 'activo' : 'inactivo' }}</span></td>
              <td>
                @if (puedeGestionar) {
                  <button class="btn btn-sm" (click)="eliminar(techo)">Eliminar</button>
                }
              </td>
            </tr>
          }
        </tbody>
      </table>
    }
    @if (!cargando && techos.length === 0) {
      <div class="empty">Sin techos registrados</div>
    }
    `,
  styles: [`
    .page-header { margin-bottom: 1.5rem; }
    .text-secondary { color: var(--text-secondary); font-size: 0.875rem; }
    .card { background: var(--surface); border: 1px solid var(--border); border-radius: 8px; padding: 1.25rem; margin-bottom: 1rem; }
    .form-inline { display: flex; gap: 1rem; flex-wrap: wrap; }
    .campo label { display: block; font-size: 0.75rem; font-weight: 600; margin-bottom: 0.375rem; }
    .input { padding: 0.5rem; border: 1px solid var(--border); border-radius: 6px; font-size: 0.875rem; min-width: 160px; }
    .btn { display: inline-flex; align-items: center; padding: 0.5rem 0.875rem; border-radius: 6px; border: none; font-size: 0.8125rem; font-weight: 600; cursor: pointer; }
    .btn-primary { background: var(--primary); color: white; }
    .btn-sm { background: #FFEBEE; color: #C62828; }
    .data-table { width: 100%; border-collapse: collapse; background: var(--surface); border: 1px solid var(--border); border-radius: 8px; }
    .data-table th, .data-table td { padding: 0.625rem 0.75rem; text-align: left; border-bottom: 1px solid var(--border); font-size: 0.8125rem; }
    .badge { display: inline-block; padding: 0.125rem 0.5rem; border-radius: 4px; font-size: 0.6875rem; font-weight: 600; background: #E3F2FD; color: #1565C0; }
    .loading { text-align: center; padding: 2rem; color: var(--text-secondary); }
    .empty { text-align: center; padding: 2rem; color: var(--text-secondary); }
    .alert { padding: 0.75rem 1rem; border-radius: 6px; margin-bottom: 1rem; }
    .alert-error { background: #FFEBEE; color: var(--warn); }
    .alert-success { background: #E8F5E9; color: #2E7D32; }
  `],
})
export class SisPoaTechosComponent implements OnInit {
  techos: TechoV2[] = [];
  fuentes: FuenteV1[] = [];
  cargando = true;
  error = '';
  mensaje = '';
  form: { gestion: number | null; monto_total: number | null; fuente: string } = {
    gestion: null, monto_total: null, fuente: '',
  };

  constructor(
    private service: SisPoaService,
    private http: HttpClient,
    private permissions: PermissionsService,
  ) {}

  get puedeGestionar(): boolean {
    return this.permissions.hasAnyCapability(['sis_poa.budget.manage', 'sis_poa.formulate']);
  }

  ngOnInit(): void {
    this.cargar();
    this.http.get<{ results: FuenteV1[] }>(`${environment.apiUrl}/fuentes/`).subscribe({
      next: (data) => { this.fuentes = data.results ?? []; },
      error: () => undefined,
    });
  }

  cargar(): void {
    this.cargando = true;
    this.service.listarTechos().subscribe({
      next: (data) => { this.techos = data.results; this.cargando = false; },
      error: () => { this.error = 'Error al cargar techos'; this.cargando = false; },
    });
  }

  crear(): void {
    const { gestion, monto_total, fuente } = this.form;
    if (!gestion || !monto_total || !fuente) {
      this.error = 'Gestión, monto y fuente son requeridos';
      return;
    }
    this.error = '';
    this.service.crearTecho({
      gestion, monto_total: String(monto_total), fuente,
    } as Partial<TechoV2>).subscribe({
      next: () => {
        this.mensaje = 'Techo registrado';
        this.form = { gestion: null, monto_total: null, fuente: '' };
        this.cargar();
      },
      error: () => { this.error = 'Error al crear el techo'; },
    });
  }

  eliminar(techo: TechoV2): void {
    if (!confirm(`¿Eliminar el techo de ${techo.gestion} (${techo.fuente_codigo})?`)) return;
    this.service.eliminarTecho(techo.id).subscribe({
      next: () => { this.mensaje = 'Techo eliminado'; this.cargar(); },
      error: () => { this.error = 'Error al eliminar el techo'; },
    });
  }
}

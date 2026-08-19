import { Component, OnInit } from '@angular/core';
import { PermissionsService } from '../../core/services/permissions.service';
import {
  BudgetService,
  DetalleCatalogo,
  DirectiveCeiling,
  FiscalYear,
} from './budget/budget.service';

const ORIGENES = [
  { codigo: 'SIGEP', nombre: 'SIGEP' },
  { codigo: 'MUNICIPAL', nombre: 'Recursos propios municipales' },
  { codigo: 'SALDO', nombre: 'Saldo de caja y bancos' },
  { codigo: 'OTRO', nombre: 'Otros' },
];

@Component({
  standalone: false,
  selector: 'app-sis-poa-techos',
  template: `
    <div class="page-header">
      <h2>Techos Presupuestarios</h2>
      <p class="text-secondary">Límites de programación por gestión (DirectiveCeiling)</p>
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
          <select [(ngModel)]="form.gestion" name="g" required class="input">
            <option value="" disabled>Seleccione...</option>
            @for (gf of gestiones; track gf) {
              <option [value]="gf.id">{{ gf.anio }}</option>
            }
          </select>
        </div>
        <div class="campo">
          <label>Origen</label>
          <select [(ngModel)]="form.origen" name="o" class="input">
            @for (o of origenes; track o) {
              <option [value]="o.codigo">{{ o.nombre }}</option>
            }
          </select>
        </div>
        <div class="campo">
          <label>Monto (Bs)</label>
          <input [(ngModel)]="form.monto" name="m" type="number" min="0" step="0.01" class="input" />
        </div>
        <div class="campo">
          <label>Fuente</label>
          <select [(ngModel)]="form.fuente" name="f" class="input">
            <option value="">Sin fuente</option>
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
          <tr><th>Gestión</th><th>Estado</th><th>Monto Bruto (Bs)</th><th>Fuentes</th><th></th></tr>
        </thead>
        <tbody>
          @for (techo of techos; track techo.id) {
            <tr>
              <td>{{ techo.gestion_anio }}</td>
              <td><span class="badge">{{ techo.estado_display }}</span></td>
              <td>Bs {{ montoBruto(techo) }}</td>
              <td>{{ fuentesDe(techo) }}</td>
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
    .input { padding: 0.5rem; border: 1px solid var(--border); border-radius: 6px; font-size: 0.875rem; min-width: 160px; background: var(--surface); color: var(--text-primary); }
    .btn { display: inline-flex; align-items: center; padding: 0.5rem 0.875rem; border-radius: 6px; border: none; font-size: 0.8125rem; font-weight: 600; cursor: pointer; }
    .btn-primary { background: var(--primary); color: white; }
    .btn-sm { background: var(--mdc-red-50); color: var(--mdc-red-800); }
    .data-table { width: 100%; border-collapse: collapse; background: var(--surface); border: 1px solid var(--border); border-radius: 8px; }
    .data-table th, 
    .badge { display: inline-block; padding: 0.125rem 0.5rem; border-radius: 4px; font-size: 0.6875rem; font-weight: 600; background: var(--mdc-blue-50); color: var(--mdc-blue-800); }
    .loading { text-align: center; padding: 2rem; color: var(--text-secondary); }
    .empty { text-align: center; padding: 2rem; color: var(--text-secondary); }
    .alert { padding: 0.75rem 1rem; border-radius: 6px; margin-bottom: 1rem; }
    .alert-error { background: var(--mdc-red-50); color: var(--warn); }
    .alert-success { background: var(--mdc-green-50); color: var(--mdc-green-800); }
  `],
})
export class SisPoaTechosComponent implements OnInit {
  techos: DirectiveCeiling[] = [];
  gestiones: FiscalYear[] = [];
  fuentes: DetalleCatalogo[] = [];
  cargando = true;
  error = '';
  mensaje = '';
  form: { gestion: string | null; origen: string; monto: number | null; fuente: string | null } = {
    gestion: null, origen: 'SIGEP', monto: null, fuente: null,
  };

  readonly origenes = ORIGENES;

  constructor(
    private service: BudgetService,
    private permissions: PermissionsService,
  ) {}

  get puedeGestionar(): boolean {
    return this.permissions.hasAnyCapability(['sis_poa.budget.manage', 'sis_poa.formulate']);
  }

  ngOnInit(): void {
    this.cargar();
    this.cargarGestiones();
    this.cargarFuentes();
  }

  private cargarGestiones(): void {
    this.service.listar().subscribe({
      next: (data) => { this.gestiones = data.results; },
      error: () => undefined,
    });
  }

  private cargarFuentes(): void {
    this.service.opcionesCatalogo().subscribe({
      next: (data) => { this.fuentes = data.fuentes ?? []; },
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
    const { gestion, origen, monto, fuente } = this.form;
    if (!gestion) {
      this.error = 'La gestión es requerida';
      return;
    }
    this.error = '';
    this.service.crearTecho({ gestion }).subscribe({
      next: (techo) => {
        const version = techo.version?.id;
        if (monto !== null && monto !== undefined && version) {
          this.service.crearRecurso({
            version,
            origen,
            concepto: 'Carga inicial',
            monto,
            fuente: fuente ?? undefined,
          }).subscribe({
            next: () => {
              this.mensaje = 'Techo y recurso registrados';
              this.resetForm();
              this.cargar();
            },
            error: () => { this.error = 'Techo creado, pero falló el recurso inicial'; },
          });
          return;
        }
        this.mensaje = 'Techo registrado';
        this.resetForm();
        this.cargar();
      },
      error: () => { this.error = 'No se pudo crear el techo (la gestión debe estar habilitada)'; },
    });
  }

  eliminar(techo: DirectiveCeiling): void {
    if (!confirm(`¿Eliminar el techo directivo de la gestión ${techo.gestion_anio}?`)) return;
    this.service.eliminarTecho(techo.id).subscribe({
      next: () => { this.mensaje = 'Techo eliminado'; this.cargar(); },
      error: () => { this.error = 'Error al eliminar el techo'; },
    });
  }

  private resetForm(): void {
    this.form = { gestion: null, origen: 'SIGEP', monto: null, fuente: null };
  }

  montoBruto(techo: DirectiveCeiling): string {
    return techo.composicion?.techo_bruto ?? '0.00';
  }

  fuentesDe(techo: DirectiveCeiling): string {
    const porFuente = techo.composicion?.por_fuente ?? [];
    return porFuente.length
      ? porFuente.map(f => f.fuente).join(', ')
      : 'Sin fuentes';
  }
}
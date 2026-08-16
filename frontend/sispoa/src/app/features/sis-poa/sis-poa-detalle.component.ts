import { Component, OnInit } from '@angular/core';
import { ActivatedRoute } from '@angular/router';
import { PermissionsService } from '../../core/services/permissions.service';
import {
  AccionPoaV2, ResumenPresupuesto, SisPoaService, ValidacionTecho,
} from './sis-poa.service';

@Component({
  standalone: false,
  selector: 'app-sis-poa-detalle',
  template: `
    <div class="page-header">
      <h2>POA {{ poa?.codigo }}</h2>
      <p class="text-secondary">{{ poa?.nombre }} — gestión {{ poa?.gestion }}</p>
    </div>
    @if (cargando) {
      <div class="loading">Cargando POA...</div>
    }
    @if (error) {
      <div class="alert alert-error">{{ error }}</div>
    }
    
    @if (resumen && !cargando) {
      <div class="card">
        <h3>Presupuesto</h3>
        <div class="info-grid">
          <div><strong>Financiero programado:</strong> Bs {{ resumen.financiera.programado }}</div>
          <div><strong>Financiero ejecutado:</strong> Bs {{ resumen.financiera.ejecutado }}</div>
          <div><strong>Físico:</strong> {{ resumen.fisica.programado }} / {{ resumen.fisica.ejecutado }}</div>
          <div><strong>Actividades:</strong> {{ resumen.actividades }}</div>
        </div>
        <div class="actions">
          <button class="btn btn-sm" (click)="verificarTecho()">Validar techo</button>
        </div>
        @if (techo) {
          <div class="techo {{ techo.excede ? 'excede' : 'ok' }}">
            {{ techo.mensaje }} (techo: Bs {{ techo.techo }} | formulado: Bs {{ techo.formulado }})
          </div>
        }
      </div>
    }
    
    @if (!cargando && poa) {
      <div class="card">
        <h3>Acciones de corto plazo</h3>
        @if (puedeFormular) {
          <form (ngSubmit)="crearAccion()" class="form-inline">
            <input [(ngModel)]="accionForm.codigo" name="ac" placeholder="Código" required class="input" />
            <input [(ngModel)]="accionForm.nombre" name="an" placeholder="Nombre" required class="input" />
            <button type="submit" class="btn btn-primary">+ Acción</button>
          </form>
        }
        <table class="data-table">
          <thead><tr><th>Código</th><th>Nombre</th><th>Nodo PEI</th><th>Estado</th></tr></thead>
          <tbody>
            @for (accion of acciones; track accion) {
              <tr>
                <td>{{ accion.codigo }}</td>
                <td>{{ accion.nombre }}</td>
                <td>{{ accion.nodo_pei_codigo || '—' }}</td>
                <td><span class="badge">{{ accion.estado }}</span></td>
              </tr>
            }
          </tbody>
        </table>
        @if (acciones.length === 0) {
          <div class="empty">Sin acciones registradas</div>
        }
      </div>
    }
    `,
  styles: [`
    .page-header { margin-bottom: 1.5rem; }
    .text-secondary { color: var(--text-secondary); font-size: 0.875rem; }
    .card { background: var(--surface); border: 1px solid var(--border); border-radius: 8px; padding: 1.25rem; margin-bottom: 1rem; }
    .card h3 { margin-top: 0; font-size: 1rem; }
    .info-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 0.75rem; font-size: 0.875rem; }
    .actions { margin-top: 1rem; }
    .btn { display: inline-flex; align-items: center; padding: 0.5rem 0.875rem; border-radius: 6px; border: none; font-size: 0.8125rem; font-weight: 600; cursor: pointer; }
    .btn-sm { background: var(--mdc-blue-50); color: var(--mdc-blue-800); }
    .btn-primary { background: var(--primary); color: white; }
    .form-inline { display: flex; gap: 0.5rem; margin-bottom: 1rem; flex-wrap: wrap; }
    .input { padding: 0.5rem; border: 1px solid var(--border); border-radius: 6px; font-size: 0.875rem; }
    .data-table { width: 100%; border-collapse: collapse; }
    .data-table th, .data-table td { padding: 0.5rem 0.625rem; text-align: left; border-bottom: 1px solid var(--border); font-size: 0.8125rem; }
    .badge { display: inline-block; padding: 0.125rem 0.5rem; border-radius: 4px; font-size: 0.6875rem; font-weight: 600; background: var(--mdc-blue-50); color: var(--mdc-blue-800); }
    .techo { margin-top: 0.75rem; padding: 0.5rem 0.75rem; border-radius: 6px; font-size: 0.8125rem; }
    .techo.ok { background: var(--mdc-green-50); color: var(--mdc-green-800); }
    .techo.excede { background: var(--mdc-red-50); color: var(--mdc-red-800); }
    .loading { text-align: center; padding: 2rem; color: var(--text-secondary); }
    .empty { text-align: center; padding: 1rem; color: var(--text-secondary); }
    .alert { padding: 0.75rem 1rem; border-radius: 6px; margin-bottom: 1rem; }
    .alert-error { background: var(--mdc-red-50); color: var(--warn); }
  `],
})
export class SisPoaDetalleComponent implements OnInit {
  poa: any = null;
  resumen: ResumenPresupuesto | null = null;
  acciones: AccionPoaV2[] = [];
  techo: ValidacionTecho | null = null;
  cargando = true;
  error = '';
  accionForm: { codigo: string; nombre: string } = { codigo: '', nombre: '' };

  constructor(
    private route: ActivatedRoute,
    private service: SisPoaService,
    private permissions: PermissionsService,
  ) {}

  get puedeFormular(): boolean {
    return this.permissions.hasAnyCapability(['sis_poa.formulate', 'sis_poa.poau.edit']);
  }

  ngOnInit(): void {
    const id = this.route.snapshot.paramMap.get('id')!;
    this.service.obtenerPoa(id).subscribe({
      next: (poa) => {
        this.poa = poa;
        this.service.resumenPresupuesto(id).subscribe({
          next: (r) => { this.resumen = r; this.cargando = false; },
          error: () => { this.cargando = false; },
        });
        this.service.accionesDePoa(id).subscribe({
          next: (a) => { this.acciones = a; },
          error: () => undefined,
        });
      },
      error: () => { this.error = 'Error al cargar el POA'; this.cargando = false; },
    });
  }

  verificarTecho(): void {
    if (!this.poa) return;
    this.service.validarTecho(this.poa.id).subscribe({
      next: (t) => { this.techo = t; },
      error: () => { this.error = 'Error al validar techo'; },
    });
  }

  crearAccion(): void {
    if (!this.poa) return;
    const { codigo, nombre } = this.accionForm;
    if (!codigo || !nombre) return;
    this.service.crearAccion(this.poa.id, codigo, nombre).subscribe({
      next: () => {
        this.accionForm = { codigo: '', nombre: '' };
        this.service.accionesDePoa(this.poa.id).subscribe({
          next: (a) => { this.acciones = a; },
          error: () => undefined,
        });
      },
      error: () => { this.error = 'Error al crear la acción'; },
    });
  }
}

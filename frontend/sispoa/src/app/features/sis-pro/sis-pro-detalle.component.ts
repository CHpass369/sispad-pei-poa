import { Component, OnInit } from '@angular/core';
import { ActivatedRoute } from '@angular/router';
import { PermissionsService } from '../../core/services/permissions.service';
import {
  CadenaPaso, CondicionV2, DocumentoV2, PresupuestoProyecto, ProyectoV2, SisProService,
} from './sis-pro.service';

@Component({
  standalone: false,
  selector: 'app-sis-pro-detalle',
  template: `
    <div class="page-header">
      <h2>{{ proyecto?.codigo_interno }} — {{ proyecto?.nombre }}</h2>
      @if (proyecto) {
        <p class="text-secondary">Fase: <span class="badge">{{ proyecto.fase }}</span></p>
      }
    </div>
    @if (cargando) {
      <div class="loading">Cargando proyecto...</div>
    }
    @if (error) {
      <div class="alert alert-error">{{ error }}</div>
    }
    
    @if (presupuesto && !cargando) {
      <div class="card">
        <h3>Presupuesto</h3>
        <div class="info-grid">
          <div><strong>Costo total:</strong> Bs {{ presupuesto.costo_total }}</div>
          <div><strong>Ejecutado:</strong> Bs {{ presupuesto.ejecucion_acumulada }}</div>
          <div><strong>Saldo:</strong> Bs {{ presupuesto.saldo }}</div>
        </div>
      </div>
    }
    
    @if (cadena.length && !cargando) {
      <div class="card">
        <h3>Cadena ascendente</h3>
        <div class="cadena">
          @for (paso of cadena; track paso; let i = $index) {
            <span class="paso">
              <span class="tipo">{{ paso.tipo }}</span> {{ paso.codigo }}
              @if (i < cadena.length - 1) {
                <span class="flecha">→</span>
              }
            </span>
          }
        </div>
      </div>
    }
    
    @if (!cargando && proyecto) {
      <div class="card">
        <h3>Condiciones previas</h3>
        @if (puedeEditar) {
          <form (ngSubmit)="crearCondicion()" class="form-inline">
            <input [(ngModel)]="condicionForm" name="cd" placeholder="Descripción" required class="input" />
            <button type="submit" class="btn btn-primary">+ Condición</button>
          </form>
        }
        <ul class="lista">
          @for (c of condiciones; track c) {
            <li>{{ c.cumplida ? '✅' : '⬜' }} {{ c.descripcion }}</li>
          }
        </ul>
      </div>
    }
    
    @if (!cargando && proyecto) {
      <div class="card">
        <h3>Documentos técnicos</h3>
        @if (puedeEditar) {
          <form (ngSubmit)="crearDocumento()" class="form-inline">
            <select [(ngModel)]="docTipo" name="dt" class="input">
              <option value="itcp">ITCP</option>
              <option value="edtp">EDTP</option>
              <option value="expediente">Expediente</option>
              <option value="otro">Otro</option>
            </select>
            <input [(ngModel)]="docNombre" name="dn" placeholder="Nombre" required class="input" />
            <button type="submit" class="btn btn-primary">+ Documento</button>
          </form>
        }
        <ul class="lista">
          @for (d of documentos; track d) {
            <li>{{ d.tipo }} — {{ d.nombre }} ({{ d.estado }})</li>
          }
        </ul>
      </div>
    }
    `,
  styles: [`
    .page-header { margin-bottom: 1.5rem; }
    .text-secondary { color: var(--text-secondary); font-size: 0.875rem; }
    .card { background: var(--surface); border: 1px solid var(--border); border-radius: 8px; padding: 1.25rem; margin-bottom: 1rem; }
    .card h3 { margin-top: 0; font-size: 1rem; }
    .info-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 0.75rem; font-size: 0.875rem; }
    .cadena { display: flex; flex-wrap: wrap; gap: 0.5rem; align-items: center; font-size: 0.8125rem; }
    .paso { display: inline-flex; align-items: center; gap: 0.25rem; }
    .tipo { font-size: 0.6875rem; background: var(--mdc-grey-50); padding: 0.125rem 0.375rem; border-radius: 4px; color: var(--text-secondary); }
    .flecha { color: var(--text-secondary); }
    .badge { display: inline-block; padding: 0.125rem 0.5rem; border-radius: 4px; font-size: 0.6875rem; font-weight: 600; background: var(--mdc-blue-50); color: var(--mdc-blue-800); }
    .form-inline { display: flex; gap: 0.5rem; margin-bottom: 1rem; flex-wrap: wrap; }
    .input { padding: 0.5rem; border: 1px solid var(--border); border-radius: 6px; font-size: 0.875rem; }
    .btn { display: inline-flex; align-items: center; padding: 0.5rem 0.875rem; border-radius: 6px; border: none; font-size: 0.8125rem; font-weight: 600; cursor: pointer; }
    .btn-primary { background: var(--primary); color: white; }
    .lista { list-style: none; margin: 0; padding: 0; font-size: 0.8125rem; }
    .lista li { padding: 0.375rem 0; border-bottom: 1px solid var(--border); }
    .loading { text-align: center; padding: 2rem; color: var(--text-secondary); }
    .alert { padding: 0.75rem 1rem; border-radius: 6px; margin-bottom: 1rem; }
    .alert-error { background: var(--mdc-red-50); color: var(--warn); }
  `],
})
export class SisProDetalleComponent implements OnInit {
  proyecto: ProyectoV2 | null = null;
  presupuesto: PresupuestoProyecto | null = null;
  cadena: CadenaPaso[] = [];
  condiciones: CondicionV2[] = [];
  documentos: DocumentoV2[] = [];
  cargando = true;
  error = '';
  condicionForm = '';
  docTipo = 'itcp';
  docNombre = '';

  constructor(
    private route: ActivatedRoute,
    private service: SisProService,
    private permissions: PermissionsService,
  ) {}

  get puedeEditar(): boolean {
    return this.permissions.hasAnyCapability(['sis_pro.project.create', 'sis_pro.project.edit']);
  }

  ngOnInit(): void {
    const id = this.route.snapshot.paramMap.get('id')!;
    this.service.obtenerProyecto(id).subscribe({
      next: (proyecto) => {
        this.proyecto = proyecto;
        this.service.presupuesto(id).subscribe({
          next: (p) => { this.presupuesto = p; this.cargando = false; },
          error: () => { this.cargando = false; },
        });
        this.service.cadena(id).subscribe({
          next: (c) => { this.cadena = c; },
          error: () => undefined,
        });
        this.service.condiciones(id).subscribe({
          next: (c) => { this.condiciones = c; },
          error: () => undefined,
        });
        this.service.documentos(id).subscribe({
          next: (d) => { this.documentos = d; },
          error: () => undefined,
        });
      },
      error: () => { this.error = 'Error al cargar el proyecto'; this.cargando = false; },
    });
  }

  crearCondicion(): void {
    if (!this.proyecto || !this.condicionForm.trim()) return;
    this.service.crearCondicion(this.proyecto.id, this.condicionForm.trim()).subscribe({
      next: () => {
        this.condicionForm = '';
        this.service.condiciones(this.proyecto!.id).subscribe({
          next: (c) => { this.condiciones = c; },
          error: () => undefined,
        });
      },
      error: () => { this.error = 'Error al crear la condición'; },
    });
  }

  crearDocumento(): void {
    if (!this.proyecto || !this.docNombre.trim()) return;
    this.service.crearDocumento(this.proyecto.id, this.docTipo, this.docNombre.trim()).subscribe({
      next: () => {
        this.docNombre = '';
        this.service.documentos(this.proyecto!.id).subscribe({
          next: (d) => { this.documentos = d; },
          error: () => undefined,
        });
      },
      error: () => { this.error = 'Error al crear el documento'; },
    });
  }
}

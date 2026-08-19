import { Component, OnInit } from '@angular/core';
import { PoaV2, ProgramacionFila, SisPoaService, ValidacionTecho } from './sis-poa.service';

@Component({
  standalone: false,
  selector: 'app-sis-poa-presupuesto',
  template: `
    <div class="page-header">
      <h2>Presupuesto del POA</h2>
      <p class="text-secondary">Programación físico-financiera por actividad y validación de techos</p>
    </div>
    @if (error) {
      <div class="alert alert-error">{{ error }}</div>
    }
    
    <div class="card">
      <label>POA</label>
      <select [(ngModel)]="poaSeleccionado" (ngModelChange)="cargar()" class="input">
        @for (poa of poas; track poa) {
          <option [value]="poa.id">{{ poa.codigo }} — {{ poa.nombre }}</option>
        }
      </select>
    </div>
    
    @if (cargando) {
      <div class="loading">Cargando programaciones...</div>
    }
    
    @if (!cargando && filas.length) {
      <table class="data-table">
        <thead>
          <tr>
            <th>Actividad</th><th>Año</th><th>Tipo</th>
            <th>Programado</th><th>Ejecutado</th>
          </tr>
        </thead>
        <tbody>
          @for (fila of filas; track fila) {
            <tr>
              <td>{{ fila.actividad_codigo }} — {{ fila.actividad_nombre }}</td>
              <td>{{ fila.anio }}</td>
              <td>{{ fila.tipo === 'financiera' ? 'Financiera' : 'Física' }}</td>
              <td>Bs {{ fila.programado }}</td>
              <td>Bs {{ fila.ejecutado }}</td>
            </tr>
          }
        </tbody>
      </table>
      <div class="card resumen">
        <h3>Resumen financiero</h3>
        <div class="info-grid">
          <div><strong>Programado:</strong> Bs {{ totalProgramado }}</div>
          <div><strong>Ejecutado:</strong> Bs {{ totalEjecutado }}</div>
          <div><strong>Avance:</strong> {{ avance }}%</div>
        </div>
        <div class="actions">
          <button class="btn btn-sm" (click)="validarTecho()">Validar contra techo</button>
        </div>
        @if (techo) {
          <div class="techo {{ techo.excede ? 'excede' : 'ok' }}">
            {{ techo.mensaje }} — techo: Bs {{ techo.techo }} | formulado: Bs {{ techo.formulado }}
          </div>
        }
      </div>
    }
    @if (!cargando && poas.length && filas.length === 0) {
      <div class="empty">
        Sin programaciones para este POA
      </div>
    }
    `,
  styles: [`
    .page-header { margin-bottom: 1.5rem; }
    .text-secondary { color: var(--text-secondary); font-size: 0.875rem; }
    .card { background: var(--surface); border: 1px solid var(--border); border-radius: 8px; padding: 1.25rem; margin-bottom: 1rem; }
    .card label { display: block; font-size: 0.75rem; font-weight: 600; margin-bottom: 0.375rem; }
    .input { padding: 0.5rem; border: 1px solid var(--border); border-radius: 6px; font-size: 0.875rem; width: 100%; max-width: 480px; }
    .data-table { width: 100%; border-collapse: collapse; background: var(--surface); border: 1px solid var(--border); border-radius: 8px; margin-bottom: 1rem; }
    .data-table th, 
    .info-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(160px, 1fr)); gap: 0.75rem; font-size: 0.875rem; }
    .actions { margin-top: 1rem; }
    .btn { display: inline-flex; align-items: center; padding: 0.5rem 0.875rem; border-radius: 6px; border: none; font-size: 0.8125rem; font-weight: 600; cursor: pointer; }
    .btn-sm { background: var(--mdc-blue-50); color: var(--mdc-blue-800); }
    .techo { margin-top: 0.75rem; padding: 0.5rem 0.75rem; border-radius: 6px; font-size: 0.8125rem; }
    .techo.ok { background: var(--mdc-green-50); color: var(--mdc-green-800); }
    .techo.excede { background: var(--mdc-red-50); color: var(--mdc-red-800); }
    .loading { text-align: center; padding: 2rem; color: var(--text-secondary); }
    .empty { text-align: center; padding: 2rem; color: var(--text-secondary); }
    .alert { padding: 0.75rem 1rem; border-radius: 6px; margin-bottom: 1rem; }
    .alert-error { background: var(--mdc-red-50); color: var(--warn); }
  `],
})
export class SisPoaPresupuestoComponent implements OnInit {
  poas: PoaV2[] = [];
  poaSeleccionado = '';
  filas: ProgramacionFila[] = [];
  techo: ValidacionTecho | null = null;
  cargando = true;
  error = '';

  constructor(private service: SisPoaService) {}

  ngOnInit(): void {
    this.service.listarPoas().subscribe({
      next: (data) => {
        this.poas = data.results;
        if (this.poas.length) {
          this.poaSeleccionado = this.poas[0].id;
          this.cargar();
        } else {
          this.cargando = false;
        }
      },
      error: () => { this.error = 'Error al cargar POAs'; this.cargando = false; },
    });
  }

  cargar(): void {
    if (!this.poaSeleccionado) return;
    this.cargando = true;
    this.techo = null;
    this.service.programacionesDePoa(this.poaSeleccionado).subscribe({
      next: (data) => { this.filas = data.filas; this.cargando = false; },
      error: () => { this.error = 'Error al cargar programaciones'; this.cargando = false; },
    });
  }

  get totalProgramado(): number {
    return this.filas
      .filter(f => f.tipo === 'financiera')
      .reduce((acc, f) => acc + Number(f.programado), 0);
  }

  get totalEjecutado(): number {
    return this.filas
      .filter(f => f.tipo === 'financiera')
      .reduce((acc, f) => acc + Number(f.ejecutado), 0);
  }

  get avance(): number {
    return this.totalProgramado ? Math.round((this.totalEjecutado / this.totalProgramado) * 100) : 0;
  }

  validarTecho(): void {
    if (!this.poaSeleccionado) return;
    this.service.validarTecho(this.poaSeleccionado).subscribe({
      next: (t) => { this.techo = t; },
      error: () => { this.error = 'Error al validar techo'; },
    });
  }
}

import { Component } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { environment } from '../../../environments/environment';

interface TipoReporte {
  id: string;
  label: string;
  formatos: string[];
  endpoint: string;
}

@Component({
  standalone: false,
  selector: 'app-reportes',
  template: `
    <div class="reportes">
      <div class="page-header">
        <h2>Reportes</h2>
        <p class="text-secondary">Generación de reportes del POA</p>
      </div>

      <div class="reportes-grid">
        <!-- Tipo de Reporte -->
        <div class="card">
          <h3>Tipo de Reporte</h3>
          <div class="opciones">
            <label class="opcion" *ngFor="let t of tipos" [class.selected]="tipoSeleccionado === t.id">
              <input
                type="radio"
                name="tipo"
                [value]="t.id"
                [(ngModel)]="tipoSeleccionado"
                (change)="onTipoChange()"
              />
              <span class="opcion-label">{{ t.label }}</span>
            </label>
          </div>
        </div>

        <!-- Formato -->
        <div class="card">
          <h3>Formato</h3>
          <div class="opciones">
            <label
              class="opcion"
              *ngFor="let f of formatosDisponibles"
              [class.selected]="formatoSeleccionado === f"
            >
              <input
                type="radio"
                name="formato"
                [value]="f"
                [(ngModel)]="formatoSeleccionado"
              />
              <span class="opcion-label">{{ f.toUpperCase() }}</span>
            </label>
          </div>
          <p class="text-secondary hint" *ngIf="formatosDisponibles.length === 0">
            Seleccione un tipo de reporte primero
          </p>
        </div>

        <!-- Preview / Download -->
        <div class="card card-action">
          <h3>Descargar</h3>
          <p class="text-secondary">
            {{ tipoSeleccionado ? (tipoLabel) : 'Seleccione un tipo de reporte' }}
            {{ formatoSeleccionado ? ('- Formato ' + formatoSeleccionado.toUpperCase()) : '' }}
          </p>

          <button
            class="btn btn-primary btn-download"
            [disabled]="!tipoSeleccionado || !formatoSeleccionado || descargando"
            (click)="descargar()"
          >
            <span *ngIf="!descargando">Descargar</span>
            <span *ngIf="descargando">Descargando...</span>
          </button>

          <div class="alert alert-error" *ngIf="error">
            {{ error }}
          </div>

          <div class="alert alert-success" *ngIf="successMsg">
            {{ successMsg }}
          </div>
        </div>
      </div>
    </div>
  `,
  styles: [`
    .page-header { margin-bottom: 1.5rem; }
    .page-header h2 { font-size: 1.5rem; margin-bottom: 0.25rem; }
    .text-secondary { color: var(--text-secondary); font-size: 0.875rem; }
    .hint { margin-top: 0.75rem; font-style: italic; }
    .reportes-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 1.25rem; }
    .card { background: var(--surface); border: 1px solid var(--border); border-radius: 8px; padding: 1.25rem; }
    .card h3 { font-size: 0.9375rem; margin-bottom: 1rem; color: var(--text-primary); }
    .card-action { display: flex; flex-direction: column; }
    .opciones { display: flex; flex-direction: column; gap: 0.5rem; }
    .opcion { display: flex; align-items: center; gap: 0.5rem; padding: 0.5rem 0.75rem; border: 1px solid var(--border); border-radius: 6px; cursor: pointer; transition: all 0.15s; }
    .opcion:hover { border-color: var(--primary); background: #F5F5FF; }
    .opcion.selected { border-color: var(--primary); background: #EDE7F6; }
    .opcion input[type="radio"] { accent-color: var(--primary); }
    .opcion-label { font-size: 0.875rem; font-weight: 500; }
    .btn { display: inline-flex; align-items: center; justify-content: center; padding: 0.625rem 1.5rem; border-radius: 6px; border: none; font-size: 0.875rem; font-weight: 600; cursor: pointer; transition: background 0.15s; }
    .btn-primary { background: var(--primary); color: white; }
    .btn-primary:hover:not(:disabled) { background: var(--primary-dark, #303F9F); }
    .btn-primary:disabled { opacity: 0.5; cursor: not-allowed; }
    .btn-download { margin-top: 1rem; align-self: flex-start; }
    .alert { padding: 0.75rem 1rem; border-radius: 6px; margin-top: 1rem; }
    .alert-error { background: #FFEBEE; color: var(--warn); }
    .alert-success { background: #E8F5E9; color: #2E7D32; }
  `]
})
export class ReportesComponent {
  tipos: TipoReporte[] = [
    { id: 'poa_unidad', label: 'POA por Unidad', formatos: ['xlsx', 'pdf'], endpoint: '/reportes/poa_unidad/' },
    { id: 'consolidado', label: 'Consolidado', formatos: ['xlsx', 'csv', 'pdf'], endpoint: '/reportes/consolidado/' },
    { id: 'proyectos', label: 'Proyectos', formatos: ['xlsx', 'pdf'], endpoint: '/reportes/proyectos/' },
    { id: 'observaciones', label: 'Observaciones', formatos: ['xlsx', 'csv', 'pdf'], endpoint: '/reportes/observaciones/' },
    { id: 'mapa', label: 'Mapa', formatos: ['pdf'], endpoint: '/reportes/mapa/' },
    { id: 'acta_aprobacion', label: 'Acta de aprobación', formatos: ['pdf'], endpoint: '/reportes/acta_aprobacion/' },
    { id: 'auxiliar_pluri', label: 'Auxiliar Pluri', formatos: ['xlsx'], endpoint: '/reportes/auxiliar_pluri/' },
    { id: 'evaluacion_cuadro1', label: 'Evaluación — Cuadro N°1', formatos: ['xlsx'], endpoint: '/reportes/evaluacion_cuadro1/' },
    { id: 'evaluacion_cuadro2', label: 'Evaluación — Cuadro N°2', formatos: ['xlsx'], endpoint: '/reportes/evaluacion_cuadro2/' },
    { id: 'evaluacion_cuadro3', label: 'Evaluación — Cuadro N°3', formatos: ['xlsx'], endpoint: '/reportes/evaluacion_cuadro3/' },
  ];

  tipoSeleccionado = '';
  formatoSeleccionado = '';
  formatosDisponibles: string[] = [];

  descargando = false;
  error = '';
  successMsg = '';

  constructor(private http: HttpClient) {}

  get tipoLabel(): string {
    const t = this.tipos.find(t => t.id === this.tipoSeleccionado);
    return t ? t.label : '';
  }

  onTipoChange(): void {
    const t = this.tipos.find(t => t.id === this.tipoSeleccionado);
    this.formatosDisponibles = t ? t.formatos : [];
    this.formatoSeleccionado = this.formatosDisponibles.length === 1 ? this.formatosDisponibles[0] : '';
    this.error = '';
    this.successMsg = '';
  }

  descargar(): void {
    const tipo = this.tipos.find(t => t.id === this.tipoSeleccionado);
    if (!tipo || !this.formatoSeleccionado) return;

    this.descargando = true;
    this.error = '';
    this.successMsg = '';

    const url = `${environment.apiUrl}${tipo.endpoint}`;
    let params = new HttpParams().set('formato', this.formatoSeleccionado);
    params = params.set('gestion', '2026');

    this.http.get(url, { params, responseType: 'blob' }).subscribe({
      next: blob => {
        const filename = `${tipo.id}-${this.formatoSeleccionado}.${this.formatoSeleccionado}`;
        const link = document.createElement('a');
        link.href = URL.createObjectURL(blob);
        link.download = filename;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        URL.revokeObjectURL(link.href);

        this.successMsg = `Descarga iniciada: ${filename}`;
        this.descargando = false;
      },
      error: e => {
        this.error = 'Error al descargar: ' + (e.message || e);
        this.descargando = false;
      },
    });
  }
}

import { Component, OnInit } from '@angular/core';
import { ActivatedRoute } from '@angular/router';
import { EvaluacionService, Evaluacion, ResultadoEvaluacion } from './evaluacion.service';

@Component({
  standalone: false,
  selector: 'app-evaluacion-detalle',
  template: `
    @if (evaluacion) {
      <div class="page-header">
        <h2>Detalle de Evaluación</h2>
        <p class="text-secondary">{{ evaluacion.tipo }} — {{ evaluacion.periodo }}</p>
      </div>
    }
    
    @if (evaluacion) {
      <div class="info-grid">
        <div class="card info-item">
          <label>Tipo</label>
          <span>{{ evaluacion.tipo }}</span>
        </div>
        <div class="card info-item">
          <label>Periodo</label>
          <span>{{ evaluacion.periodo }}</span>
        </div>
        <div class="card info-item">
          <label>Responsable</label>
          <span>{{ evaluacion.responsable_nombre || evaluacion.responsable }}</span>
        </div>
        <div class="card info-item">
          <label>Estado</label>
          <span class="badge" [ngClass]="'badge-' + evaluacion.estado">{{ evaluacion.estado }}</span>
        </div>
        @if (evaluacion.observaciones) {
          <div class="card info-item full-width">
            <label>Observaciones</label>
            <span>{{ evaluacion.observaciones }}</span>
          </div>
        }
      </div>
    }
    
    @if (resultados.length > 0) {
      <div class="seccion">
        <h3>Resultados por POAU / Unidad</h3>
        <div class="table-container">
          <table class="data-table">
            <thead>
              <tr>
                <th>POAU</th>
                <th>Unidad</th>
                <th>Criterio</th>
                <th>Puntaje</th>
                <th>Máximo</th>
                <th>Observaciones</th>
              </tr>
            </thead>
            <tbody>
              @for (r of resultados; track r) {
                <tr>
                  <td>{{ r.poau }}</td>
                  <td>{{ r.unidad }}</td>
                  <td>{{ r.criterio }}</td>
                  <td>{{ r.puntaje }}</td>
                  <td>{{ r.max_puntaje }}</td>
                  <td>{{ r.observaciones }}</td>
                </tr>
              }
            </tbody>
          </table>
        </div>
      </div>
    }
    
    @if (resultados.length > 0) {
      <div class="seccion">
        <h3>Resumen de Calificaciones</h3>
        <div class="resumen-grid">
          @for (r of resumenPorPoau; track r) {
            <div class="card resumen-item">
              <strong>{{ r.poau }}</strong>
              <span class="resumen-puntaje">{{ r.puntaje_total }} / {{ r.max_total }}</span>
              <span class="resumen-porcentaje">{{ r.porcentaje }}%</span>
            </div>
          }
        </div>
      </div>
    }
    
    @if (cargando) {
      <div class="loading">Cargando detalle...</div>
    }
    @if (error) {
      <div class="alert alert-error">{{ error }}</div>
    }
    `,
  styles: [`
    .page-header { margin-bottom: 1.5rem; }
    .page-header h2 { font-size: 1.5rem; margin-bottom: 0.25rem; }
    .text-secondary { color: var(--text-secondary); font-size: 0.875rem; }
    .info-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1rem; margin-bottom: 2rem; }
    .info-item { padding: 1rem 1.25rem; }
    .info-item label { display: block; font-size: 0.75rem; text-transform: uppercase; color: var(--text-secondary); margin-bottom: 0.375rem; }
    .info-item span { font-size: 0.9375rem; font-weight: 500; }
    .info-item.full-width { grid-column: 1 / -1; }
    .badge { display: inline-block; padding: 0.125rem 0.5rem; border-radius: 4px; font-size: 0.75rem; }
    .badge-borrador { background: var(--mdc-grey-50); color: #616161; }
    .badge-en_curso, .badge-en-curso { background: var(--mdc-blue-50); color: var(--mdc-blue-800); }
    .badge-completada, .badge-finalizada { background: var(--mdc-green-50); color: var(--mdc-green-800); }
    .seccion { margin-bottom: 2rem; }
    .seccion h3 { font-size: 1.125rem; margin-bottom: 1rem; }
    .card { background: var(--surface); border: 1px solid var(--border); border-radius: 8px; }
    .table-container { overflow-x: auto; }
    .data-table { width: 100%; border-collapse: collapse; background: var(--surface); border-radius: 8px; overflow: hidden; }
    .data-table th { background: var(--background, #f5f5f5); padding: 0.75rem 1rem; text-align: left; font-size: 0.75rem; text-transform: uppercase; color: var(--text-secondary); }
    .data-table td { padding: 0.75rem 1rem; border-top: 1px solid var(--border); font-size: 0.875rem; }
    .data-table tr:hover td { background: var(--hover, #fafafa); }
    .resumen-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1rem; }
    .resumen-item { display: flex; flex-direction: column; align-items: center; padding: 1.25rem; text-align: center; }
    .resumen-puntaje { font-size: 1.25rem; font-weight: 700; margin-top: 0.5rem; }
    .resumen-porcentaje { font-size: 0.875rem; color: var(--primary); margin-top: 0.25rem; }
    .loading { text-align: center; padding: 2rem; color: var(--text-secondary); }
    .alert { padding: 0.75rem 1rem; border-radius: 6px; margin-top: 1rem; }
    .alert-error { background: var(--mdc-red-50); color: var(--warn); }
  `]
})
export class EvaluacionDetalleComponent implements OnInit {
  evaluacion: Evaluacion | null = null;
  resultados: ResultadoEvaluacion[] = [];
  resumenPorPoau: { poau: string; puntaje_total: number; max_total: number; porcentaje: number }[] = [];
  cargando = true;
  error = '';

  constructor(
    private evaluacionService: EvaluacionService,
    private route: ActivatedRoute,
  ) {}

  ngOnInit(): void {
    const id = +this.route.snapshot.paramMap.get('id')!;
    this.cargarDetalle(id);
    this.cargarResultados(id);
  }

  cargarDetalle(id: number): void {
    this.evaluacionService.obtener(id).subscribe({
      next: (data) => {
        this.evaluacion = data;
        this.cargando = false;
      },
      error: () => {
        this.error = 'Error al cargar evaluación';
        this.cargando = false;
      },
    });
  }

  cargarResultados(id: number): void {
    this.evaluacionService.resultados(id).subscribe({
      next: (data: any) => {
        this.resultados = data.results || data;
        this.calcularResumen();
      },
    });
  }

  calcularResumen(): void {
    const agrupado: Record<string, { puntaje_total: number; max_total: number }> = {};
    for (const r of this.resultados) {
      const key = r.poau || 'Sin POAU';
      if (!agrupado[key]) agrupado[key] = { puntaje_total: 0, max_total: 0 };
      agrupado[key].puntaje_total += r.puntaje || 0;
      agrupado[key].max_total += r.max_puntaje || 0;
    }
    this.resumenPorPoau = Object.entries(agrupado).map(([poau, val]) => ({
      poau,
      puntaje_total: val.puntaje_total,
      max_total: val.max_total,
      porcentaje: val.max_total > 0 ? Math.round((val.puntaje_total / val.max_total) * 100) : 0,
    }));
  }
}

import { Component, OnInit } from '@angular/core';
import { ActivatedRoute } from '@angular/router';
import { NormativaService, Normativa, ReglaNormativa } from './normativa.service';

@Component({
  standalone: false,
  selector: 'app-normativa-detalle',
  template: `
    <div class="page-header" *ngIf="normativa">
      <h2>{{ normativa.titulo }}</h2>
      <p class="text-secondary">Detalle del documento normativo</p>
    </div>

    <div class="info-grid" *ngIf="normativa">
      <div class="card info-item">
        <label>Tipo</label>
        <span class="badge badge-info">{{ normativa.tipo }}</span>
      </div>
      <div class="card info-item">
        <label>Estado</label>
        <span class="badge" [ngClass]="'badge-' + normativa.estado">{{ normativa.estado }}</span>
      </div>
      <div class="card info-item">
        <label>Versión</label>
        <span>{{ normativa.version || '-' }}</span>
      </div>
      <div class="card info-item">
        <label>Fecha Vigencia</label>
        <span>{{ normativa.fecha_vigencia | date:'dd/MM/yyyy' }}</span>
      </div>
      <div class="card info-item full-width" *ngIf="normativa.descripcion">
        <label>Descripción</label>
        <span>{{ normativa.descripcion }}</span>
      </div>
    </div>

    <div class="seccion" *ngIf="normativa?.contenido">
      <h3>Contenido</h3>
      <div class="card contenido-card">
        <p class="contenido-texto">{{ normativa.contenido }}</p>
      </div>
    </div>

    <div class="seccion" *ngIf="historialVersiones.length > 0">
      <h3>Historial de Versiones</h3>
      <div class="table-container">
        <table class="data-table">
          <thead>
            <tr>
              <th>Versión</th>
              <th>Fecha</th>
              <th>Estado</th>
            </tr>
          </thead>
          <tbody>
            <tr *ngFor="let v of historialVersiones">
              <td>{{ v.version }}</td>
              <td>{{ v.fecha_creacion | date:'dd/MM/yyyy' }}</td>
              <td>
                <span class="badge" [ngClass]="'badge-' + v.estado">{{ v.estado }}</span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <div class="seccion" *ngIf="reglas.length > 0">
      <h3>Reglas Asociadas</h3>
      <div class="table-container">
        <table class="data-table">
          <thead>
            <tr>
              <th>Orden</th>
              <th>Regla</th>
              <th>Descripción</th>
            </tr>
          </thead>
          <tbody>
            <tr *ngFor="let r of reglas">
              <td>{{ r.orden }}</td>
              <td>{{ r.regla }}</td>
              <td>{{ r.descripcion }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <div class="loading" *ngIf="cargando">Cargando detalle...</div>
    <div class="alert alert-error" *ngIf="error">{{ error }}</div>
  `,
  styles: [`
    .page-header { margin-bottom: 1.5rem; }
    .page-header h2 { font-size: 1.5rem; margin-bottom: 0.25rem; }
    .text-secondary { color: var(--text-secondary); font-size: 0.875rem; }
    .info-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1rem; margin-bottom: 2rem; }
    .card { background: var(--surface); border: 1px solid var(--border); border-radius: 8px; }
    .info-item { padding: 1rem 1.25rem; }
    .info-item label { display: block; font-size: 0.75rem; text-transform: uppercase; color: var(--text-secondary); margin-bottom: 0.375rem; }
    .info-item span { font-size: 0.9375rem; font-weight: 500; }
    .info-item.full-width { grid-column: 1 / -1; }
    .badge { display: inline-block; padding: 0.125rem 0.5rem; border-radius: 4px; font-size: 0.75rem; }
    .badge-info { background: #E3F2FD; color: #1565C0; }
    .badge-borrador { background: #F5F5F5; color: #616161; }
    .badge-vigente { background: #E8F5E9; color: #2E7D32; }
    .badge-obsoleta { background: #FFEBEE; color: #C62828; }
    .seccion { margin-bottom: 2rem; }
    .seccion h3 { font-size: 1.125rem; margin-bottom: 1rem; }
    .contenido-card { padding: 1.5rem; }
    .contenido-texto { line-height: 1.7; white-space: pre-wrap; font-size: 0.9375rem; }
    .table-container { overflow-x: auto; }
    .data-table { width: 100%; border-collapse: collapse; background: var(--surface); border-radius: 8px; overflow: hidden; }
    .data-table th { background: var(--background, #f5f5f5); padding: 0.75rem 1rem; text-align: left; font-size: 0.75rem; text-transform: uppercase; color: var(--text-secondary); }
    .data-table td { padding: 0.75rem 1rem; border-top: 1px solid var(--border); font-size: 0.875rem; }
    .data-table tr:hover td { background: var(--hover, #fafafa); }
    .loading { text-align: center; padding: 2rem; color: var(--text-secondary); }
    .alert { padding: 0.75rem 1rem; border-radius: 6px; margin-top: 1rem; }
    .alert-error { background: #FFEBEE; color: var(--warn); }
  `]
})
export class NormativaDetalleComponent implements OnInit {
  normativa: Normativa | null = null;
  reglas: ReglaNormativa[] = [];
  historialVersiones: Normativa[] = [];
  cargando = true;
  error = '';

  constructor(
    private normativaService: NormativaService,
    private route: ActivatedRoute,
  ) {}

  ngOnInit(): void {
    const id = +this.route.snapshot.paramMap.get('id')!;
    this.cargarDetalle(id);
    this.cargarReglas(id);
  }

  cargarDetalle(id: number): void {
    this.normativaService.obtener(id).subscribe({
      next: (data) => {
        this.normativa = data;
        this.cargando = false;
      },
      error: () => {
        this.error = 'Error al cargar normativa';
        this.cargando = false;
      },
    });
  }

  cargarReglas(id: number): void {
    this.normativaService.listarReglas(id).subscribe({
      next: (data: any) => {
        this.reglas = data.results || data;
      },
      error: () => {},
    });
  }
}

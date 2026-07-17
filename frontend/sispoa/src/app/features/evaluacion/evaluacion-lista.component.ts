import { Component, OnInit } from '@angular/core';
import { Router } from '@angular/router';
import { EvaluacionService, Evaluacion } from './evaluacion.service';

@Component({
  standalone: false,
  selector: 'app-evaluacion-lista',
  template: `
    <div class="page-header">
      <h2>Evaluaciones</h2>
      <p class="text-secondary">Gestión de evaluaciones del plan</p>
    </div>

    <div class="acciones-superior">
      <div class="field">
        <input [(ngModel)]="busqueda" (keyup.enter)="cargar()" class="form-control"
               placeholder="Buscar evaluaciones...">
      </div>
      <button class="btn btn-primary" (click)="nueva()">+ Nueva Evaluación</button>
      <button class="btn btn-outline" (click)="generar()">Generar Evaluación</button>
    </div>

    <div class="table-container" *ngIf="!cargando">
      <table class="data-table">
        <thead>
          <tr>
            <th>Tipo</th>
            <th>Periodo</th>
            <th>Responsable</th>
            <th>Estado</th>
            <th>Fecha Creación</th>
            <th>Acciones</th>
          </tr>
        </thead>
        <tbody>
          <tr *ngFor="let e of evaluaciones">
            <td>{{ e.tipo }}</td>
            <td>{{ e.periodo }}</td>
            <td>{{ e.responsable_nombre || e.responsable }}</td>
            <td>
              <span class="badge" [ngClass]="'badge-' + e.estado">{{ e.estado }}</span>
            </td>
            <td>{{ e.fecha_creacion | date:'dd/MM/yyyy' }}</td>
            <td>
              <button class="btn btn-sm btn-outline" (click)="verDetalle(e)">Ver Detalle</button>
            </td>
          </tr>
        </tbody>
      </table>
      <div *ngIf="evaluaciones.length === 0" class="empty">No hay evaluaciones registradas</div>
    </div>

    <div class="loading" *ngIf="cargando">Cargando evaluaciones...</div>
    <div class="alert alert-error" *ngIf="error">{{ error }}</div>
  `,
  styles: [`
    .page-header { margin-bottom: 1rem; }
    .page-header h2 { font-size: 1.5rem; margin-bottom: 0.25rem; }
    .text-secondary { color: var(--text-secondary); font-size: 0.875rem; }
    .acciones-superior { display: flex; gap: 1rem; margin-bottom: 1.5rem; align-items: center; }
    .acciones-superior .field { flex: 1; }
    .table-container { overflow-x: auto; }
    .data-table { width: 100%; border-collapse: collapse; background: var(--surface); border-radius: 8px; overflow: hidden; }
    .data-table th { background: var(--background, #f5f5f5); padding: 0.75rem 1rem; text-align: left; font-size: 0.75rem; text-transform: uppercase; color: var(--text-secondary); }
    .data-table td { padding: 0.75rem 1rem; border-top: 1px solid var(--border); font-size: 0.875rem; }
    .data-table tr:hover td { background: var(--hover, #fafafa); }
    .badge { display: inline-block; padding: 0.125rem 0.5rem; border-radius: 4px; font-size: 0.75rem; }
    .badge-borrador { background: #F5F5F5; color: #616161; }
    .badge-en_curso, .badge-en-curso { background: #E3F2FD; color: #1565C0; }
    .badge-completada, .badge-finalizada { background: #E8F5E9; color: #2E7D32; }
    .badge-aprobada { background: #E8F5E9; color: #2E7D32; }
    .badge-cancelada { background: #FFEBEE; color: #C62828; }
    .btn { display: inline-flex; align-items: center; padding: 0.5rem 1rem; border-radius: 6px; border: none; font-size: 0.875rem; font-weight: 600; cursor: pointer; }
    .btn-primary { background: var(--primary); color: white; }
    .btn-primary:hover { background: var(--primary-dark, #303F9F); }
    .btn-sm { padding: 0.25rem 0.5rem; font-size: 0.8125rem; }
    .btn-outline { background: transparent; border: 1px solid var(--border); color: var(--text-primary); }
    .btn-outline:hover { background: var(--hover, #f5f5f5); }
    .empty { text-align: center; padding: 2rem; color: var(--text-secondary); }
    .loading { text-align: center; padding: 2rem; color: var(--text-secondary); }
    .alert { padding: 0.75rem 1rem; border-radius: 6px; margin-top: 1rem; }
    .alert-error { background: #FFEBEE; color: var(--warn); }
  `]
})
export class EvaluacionListaComponent implements OnInit {
  evaluaciones: Evaluacion[] = [];
  busqueda = '';
  cargando = true;
  error = '';

  constructor(
    private evaluacionService: EvaluacionService,
    private router: Router,
  ) {}

  ngOnInit(): void {
    this.cargar();
  }

  cargar(): void {
    this.cargando = true;
    this.error = '';
    const params: any = {};
    if (this.busqueda) params.search = this.busqueda;
    this.evaluacionService.listar(params).subscribe({
      next: (data: any) => {
        this.evaluaciones = data.results || data;
        this.cargando = false;
      },
      error: () => {
        this.error = 'Error al cargar evaluaciones';
        this.cargando = false;
      },
    });
  }

  nueva(): void {
    this.router.navigate(['evaluacion/nueva']);
  }

  verDetalle(e: Evaluacion): void {
    this.router.navigate(['evaluacion', e.id]);
  }

  generar(): void {
    this.evaluacionService.generar().subscribe({
      next: () => this.cargar(),
      error: (e) => {
        this.error = e.error?.detail || 'Error al generar evaluación';
      },
    });
  }
}

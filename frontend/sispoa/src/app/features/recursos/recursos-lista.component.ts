import { Component, OnInit } from '@angular/core';
import { Router } from '@angular/router';
import { RecursosService, Recurso } from './recursos.service';

@Component({
  standalone: false,
  selector: 'app-recursos-lista',
  template: `
    <div class="page-header">
      <h2>Recursos</h2>
      <p class="text-secondary">Gestión y estimación de recursos del plan</p>
    </div>

    <div class="summary-cards">
      <div class="card summary-item">
        <span class="summary-value">{{ totalRecursos }}</span>
        <span class="summary-label">Total Recursos</span>
      </div>
      <div class="card summary-item">
        <span class="summary-value">{{ recursosAsignados }}</span>
        <span class="summary-label">Asignados</span>
      </div>
      <div class="card summary-item">
        <span class="summary-value">{{ recursosDisponibles }}</span>
        <span class="summary-label">Disponibles</span>
      </div>
      <div class="card summary-item">
        <span class="summary-value">{{ costoTotal | number:'1.2-2' }}</span>
        <span class="summary-label">Costo Estimado (Bs.)</span>
      </div>
    </div>

    <div class="acciones-superior">
      <div class="field">
        <input [(ngModel)]="busqueda" (keyup.enter)="cargar()" class="form-control"
               placeholder="Buscar por nombre o tipo...">
      </div>
      <button class="btn btn-primary" (click)="nuevo()">+ Nuevo Recurso</button>
    </div>

    <div class="table-container" *ngIf="!cargando">
      <table class="data-table">
        <thead>
          <tr>
            <th>Tipo</th>
            <th>Nombre</th>
            <th>Cantidad</th>
            <th>Unidad</th>
            <th>Disponibilidad</th>
            <th>Asignado A</th>
            <th>Costo Est.</th>
            <th>Acciones</th>
          </tr>
        </thead>
        <tbody>
          <tr *ngFor="let r of recursos">
            <td>
              <span class="badge badge-info">{{ r.tipo }}</span>
            </td>
            <td>{{ r.nombre }}</td>
            <td>{{ r.cantidad }}</td>
            <td>{{ r.unidad }}</td>
            <td>
              <span class="badge" [ngClass]="r.disponibilidad === 'disponible' ? 'badge-success' : r.disponibilidad === 'asignado' ? 'badge-warning' : 'badge-danger'">
                {{ r.disponibilidad }}
              </span>
            </td>
            <td>{{ r.asignado_nombre || r.asignado_a || '-' }}</td>
            <td>{{ r.costo_estimado | number:'1.2-2' }}</td>
            <td>
              <button class="btn btn-sm btn-outline" (click)="verDetalle(r)">Ver</button>
            </td>
          </tr>
        </tbody>
      </table>
      <div *ngIf="recursos.length === 0" class="empty">No se encontraron recursos</div>
    </div>

    <div class="loading" *ngIf="cargando">Cargando recursos...</div>
    <div class="alert alert-error" *ngIf="error">{{ error }}</div>
  `,
  styles: [`
    .page-header { margin-bottom: 1rem; }
    .page-header h2 { font-size: 1.5rem; margin-bottom: 0.25rem; }
    .text-secondary { color: var(--text-secondary); font-size: 0.875rem; }
    .summary-cards { display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 1rem; margin-bottom: 1.5rem; }
    .card { background: var(--surface); border: 1px solid var(--border); border-radius: 8px; }
    .summary-item { display: flex; flex-direction: column; align-items: center; padding: 1.25rem; text-align: center; }
    .summary-value { font-size: 1.75rem; font-weight: 700; color: var(--primary); }
    .summary-label { font-size: 0.75rem; color: var(--text-secondary); text-transform: uppercase; margin-top: 0.25rem; }
    .acciones-superior { display: flex; gap: 1rem; margin-bottom: 1.5rem; align-items: center; }
    .acciones-superior .field { flex: 1; }
    .table-container { overflow-x: auto; }
    .data-table { width: 100%; border-collapse: collapse; background: var(--surface); border-radius: 8px; overflow: hidden; }
    .data-table th { background: var(--background, #f5f5f5); padding: 0.75rem 1rem; text-align: left; font-size: 0.75rem; text-transform: uppercase; color: var(--text-secondary); }
    .data-table td { padding: 0.75rem 1rem; border-top: 1px solid var(--border); font-size: 0.875rem; }
    .data-table tr:hover td { background: var(--hover, #fafafa); }
    .badge { display: inline-block; padding: 0.125rem 0.5rem; border-radius: 4px; font-size: 0.75rem; }
    .badge-info { background: #E3F2FD; color: #1565C0; }
    .badge-success { background: #E8F5E9; color: #2E7D32; }
    .badge-warning { background: #FFF3E0; color: #E65100; }
    .badge-danger { background: #FFEBEE; color: #C62828; }
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
export class RecursosListaComponent implements OnInit {
  recursos: Recurso[] = [];
  busqueda = '';
  cargando = true;
  error = '';

  totalRecursos = 0;
  recursosAsignados = 0;
  recursosDisponibles = 0;
  costoTotal = 0;

  constructor(
    private recursosService: RecursosService,
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
    this.recursosService.listar(params).subscribe({
      next: (data: any) => {
        this.recursos = data.results || data;
        this.calcularResumen();
        this.cargando = false;
      },
      error: () => {
        this.error = 'Error al cargar recursos';
        this.cargando = false;
      },
    });
  }

  calcularResumen(): void {
    this.totalRecursos = this.recursos.length;
    this.recursosAsignados = this.recursos.filter(r => r.disponibilidad === 'asignado').length;
    this.recursosDisponibles = this.recursos.filter(r => r.disponibilidad === 'disponible').length;
    this.costoTotal = this.recursos.reduce((sum, r) => sum + (r.costo_estimado || 0), 0);
  }

  nuevo(): void {
    this.router.navigate(['recursos/nuevo']);
  }

  verDetalle(r: Recurso): void {
    this.router.navigate(['recursos', r.id]);
  }
}

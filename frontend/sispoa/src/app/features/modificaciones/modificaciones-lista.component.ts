import { Component, OnInit } from '@angular/core';
import { Router } from '@angular/router';
import { ModificacionesService, SolicitudModificacion } from './modificaciones.service';

@Component({
  standalone: false,
  selector: 'app-modificaciones-lista',
  template: `
    <div class="page-header">
      <h2>Solicitudes de Modificación</h2>
      <p class="text-secondary">Gestión de modificaciones al plan</p>
    </div>

    <div class="acciones-superior">
      <div class="field">
        <input [(ngModel)]="busqueda" (keyup.enter)="cargar()" class="form-control"
               placeholder="Buscar solicitudes...">
      </div>
      <button class="btn btn-primary" (click)="nueva()">+ Nueva Solicitud</button>
    </div>

    <div class="table-container" *ngIf="!cargando">
      <table class="data-table">
        <thead>
          <tr>
            <th>Tipo</th>
            <th>Entidad</th>
            <th>Solicitado por</th>
            <th>Estado</th>
            <th>Fecha</th>
            <th>Acciones</th>
          </tr>
        </thead>
        <tbody>
          <tr *ngFor="let s of solicitudes">
            <td>{{ s.tipo }}</td>
            <td>{{ s.entidad }}</td>
            <td>{{ s.solicitado_por_nombre || s.solicitado_por }}</td>
            <td>
              <span class="badge" [ngClass]="'badge-' + s.estado">{{ s.estado }}</span>
            </td>
            <td>{{ s.fecha_solicitud | date:'dd/MM/yyyy' }}</td>
            <td>
              <button class="btn btn-sm btn-outline" (click)="verDetalle(s)">Ver Detalle</button>
            </td>
          </tr>
        </tbody>
      </table>
      <div *ngIf="solicitudes.length === 0" class="empty">No hay solicitudes de modificación</div>
    </div>

    <div class="loading" *ngIf="cargando">Cargando solicitudes...</div>
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
    .badge-pendiente { background: #FFF3E0; color: #E65100; }
    .badge-aprobada { background: #E8F5E9; color: #2E7D32; }
    .badge-rechazada { background: #FFEBEE; color: #C62828; }
    .badge-en_revision, .badge-en-revision { background: #E3F2FD; color: #1565C0; }
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
export class ModificacionesListaComponent implements OnInit {
  solicitudes: SolicitudModificacion[] = [];
  busqueda = '';
  cargando = true;
  error = '';

  constructor(
    private modificacionesService: ModificacionesService,
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
    this.modificacionesService.listar(params).subscribe({
      next: (data: any) => {
        this.solicitudes = data.results || data;
        this.cargando = false;
      },
      error: () => {
        this.error = 'Error al cargar solicitudes';
        this.cargando = false;
      },
    });
  }

  nueva(): void {
    this.router.navigate(['modificaciones/nueva']);
  }

  verDetalle(s: SolicitudModificacion): void {
    this.router.navigate(['modificaciones', s.id]);
  }
}

import { Component, OnInit } from '@angular/core';
import { Router } from '@angular/router';
import { NormativaService, Normativa } from './normativa.service';

@Component({
  standalone: false,
  selector: 'app-normativa-lista',
  template: `
    <div class="page-header">
      <h2>Normativa</h2>
      <p class="text-secondary">Gestión de documentos normativos del sistema</p>
    </div>
    
    <div class="acciones-superior">
      <div class="field">
        <input [(ngModel)]="busqueda" (keyup.enter)="cargar()" class="form-control"
          placeholder="Buscar por título o descripción...">
        </div>
        <select [(ngModel)]="filtroEstado" (change)="cargar()" class="form-control filtro-select">
          <option value="">Todos los estados</option>
          <option value="borrador">Borrador</option>
          <option value="vigente">Vigente</option>
          <option value="obsoleta">Obsoleta</option>
        </select>
        <select [(ngModel)]="filtroTipo" (change)="cargar()" class="form-control filtro-select">
          <option value="">Todos los tipos</option>
          <option value="ley">Ley</option>
          <option value="decreto">Decreto</option>
          <option value="resolucion">Resolución</option>
          <option value="acuerdo">Acuerdo</option>
          <option value="norma_interna">Norma Interna</option>
        </select>
      </div>
    
      @if (!cargando) {
        <div class="table-container">
          <table class="data-table">
            <thead>
              <tr>
                <th>Título</th>
                <th>Tipo</th>
                <th>Estado</th>
                <th>Versión</th>
                <th>Fecha Vigencia</th>
                <th>Acciones</th>
              </tr>
            </thead>
            <tbody>
              @for (n of normativas; track n) {
                <tr>
                  <td>{{ n.titulo }}</td>
                  <td>
                    <span class="badge badge-info">{{ n.tipo }}</span>
                  </td>
                  <td>
                    <span class="badge" [ngClass]="'badge-' + n.estado">{{ n.estado }}</span>
                  </td>
                  <td>{{ n.version || '-' }}</td>
                  <td>{{ n.fecha_vigencia | date:'dd/MM/yyyy' }}</td>
                  <td>
                    <button class="btn btn-sm btn-outline" (click)="verDetalle(n)">Ver Detalle</button>
                  </td>
                </tr>
              }
            </tbody>
          </table>
          @if (normativas.length === 0) {
            <div class="empty">No se encontraron documentos normativos</div>
          }
        </div>
      }
    
      @if (cargando) {
        <div class="loading">Cargando normativa...</div>
      }
      @if (error) {
        <div class="alert alert-error">{{ error }}</div>
      }
    `,
  styles: [`
    .page-header { margin-bottom: 1rem; }
    .page-header h2 { font-size: 1.5rem; margin-bottom: 0.25rem; }
    .text-secondary { color: var(--text-secondary); font-size: 0.875rem; }
    .acciones-superior { display: flex; gap: 1rem; margin-bottom: 1.5rem; align-items: center; }
    .acciones-superior .field { flex: 1; }
    .filtro-select { width: auto; min-width: 160px; }
    
    .data-table { width: 100%; border-collapse: collapse; background: var(--surface); border-radius: 8px; overflow: hidden; }

    .data-table tr:hover td { background: var(--hover, #fafafa); }
    .badge { display: inline-block; padding: 0.125rem 0.5rem; border-radius: 4px; font-size: 0.75rem; }
    .badge-info { background: var(--mdc-blue-50); color: var(--mdc-blue-800); }
    .badge-borrador { background: var(--mdc-grey-50); color: #616161; }
    .badge-vigente { background: var(--mdc-green-50); color: var(--mdc-green-800); }
    .badge-obsoleta { background: var(--mdc-red-50); color: var(--mdc-red-800); }
    .btn { display: inline-flex; align-items: center; padding: 0.5rem 1rem; border-radius: 6px; border: none; font-size: 0.875rem; font-weight: 600; cursor: pointer; }
    .btn-sm { padding: 0.25rem 0.5rem; font-size: 0.8125rem; }
    .btn-outline { background: transparent; border: 1px solid var(--border); color: var(--text-primary); }
    .btn-outline:hover { background: var(--hover, var(--neutro-fondo)); }
    .empty { text-align: center; padding: 2rem; color: var(--text-secondary); }
    .loading { text-align: center; padding: 2rem; color: var(--text-secondary); }
    .alert { padding: 0.75rem 1rem; border-radius: 6px; margin-top: 1rem; }
    .alert-error { background: var(--mdc-red-50); color: var(--warn); }
  `]
})
export class NormativaListaComponent implements OnInit {
  normativas: Normativa[] = [];
  busqueda = '';
  filtroEstado = '';
  filtroTipo = '';
  cargando = true;
  error = '';

  constructor(
    private normativaService: NormativaService,
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
    if (this.filtroEstado) params.estado = this.filtroEstado;
    if (this.filtroTipo) params.tipo = this.filtroTipo;
    this.normativaService.listar(params).subscribe({
      next: (data: any) => {
        this.normativas = data.results || data;
        this.cargando = false;
      },
      error: () => {
        this.error = 'Error al cargar normativa';
        this.cargando = false;
      },
    });
  }

  verDetalle(n: Normativa): void {
    this.router.navigate(['normativa', n.id]);
  }
}

import { Component, OnInit } from '@angular/core';
import { Router } from '@angular/router';
import { DocumentosService, Documento } from './documentos.service';

@Component({
  standalone: false,
  selector: 'app-documentos-lista',
  template: `
    <div class="page-header">
      <h2>Documentos</h2>
      <p class="text-secondary">Gestión de documentos del sistema</p>
    </div>

    <div class="acciones-superior">
      <div class="field">
        <input [(ngModel)]="busqueda" (keyup.enter)="cargar()" class="form-control"
               placeholder="Buscar por nombre o descripción...">
      </div>
      <select [(ngModel)]="filtroTipo" (change)="cargar()" class="form-control filtro-select">
        <option value="">Todos los tipos</option>
        <option value="pdf">PDF</option>
        <option value="xlsx">Excel</option>
        <option value="docx">Word</option>
        <option value="imagen">Imagen</option>
        <option value="otro">Otro</option>
      </select>
      <button class="btn btn-primary" (click)="subir()">+ Subir Documento</button>
    </div>

    <div class="table-container" *ngIf="!cargando">
      <table class="data-table">
        <thead>
          <tr>
            <th>Nombre</th>
            <th>Tipo</th>
            <th>Entidad Asociada</th>
            <th>Tamaño</th>
            <th>Fecha Subida</th>
            <th>Subido Por</th>
            <th>Acciones</th>
          </tr>
        </thead>
        <tbody>
          <tr *ngFor="let d of documentos">
            <td>{{ d.nombre }}</td>
            <td>
              <span class="badge badge-info">{{ d.tipo }}</span>
            </td>
            <td>{{ d.entidad_descripcion || '-' }}</td>
            <td>{{ formatTamano(d.tamano) }}</td>
            <td>{{ d.fecha_subida | date:'dd/MM/yyyy HH:mm' }}</td>
            <td>{{ d.subido_por }}</td>
            <td>
              <button class="btn btn-sm btn-outline" (click)="verDetalle(d)">Ver Detalle</button>
            </td>
          </tr>
        </tbody>
      </table>
      <div *ngIf="documentos.length === 0" class="empty">No se encontraron documentos</div>
    </div>

    <div class="loading" *ngIf="cargando">Cargando documentos...</div>
    <div class="alert alert-error" *ngIf="error">{{ error }}</div>
  `,
  styles: [`
    .page-header { margin-bottom: 1rem; }
    .page-header h2 { font-size: 1.5rem; margin-bottom: 0.25rem; }
    .text-secondary { color: var(--text-secondary); font-size: 0.875rem; }
    .acciones-superior { display: flex; gap: 1rem; margin-bottom: 1.5rem; align-items: center; }
    .acciones-superior .field { flex: 1; }
    .filtro-select { width: auto; min-width: 160px; }
    .table-container { overflow-x: auto; }
    .data-table { width: 100%; border-collapse: collapse; background: var(--surface); border-radius: 8px; overflow: hidden; }
    .data-table th { background: var(--background, #f5f5f5); padding: 0.75rem 1rem; text-align: left; font-size: 0.75rem; text-transform: uppercase; color: var(--text-secondary); }
    .data-table td { padding: 0.75rem 1rem; border-top: 1px solid var(--border); font-size: 0.875rem; }
    .data-table tr:hover td { background: var(--hover, #fafafa); }
    .badge { display: inline-block; padding: 0.125rem 0.5rem; border-radius: 4px; font-size: 0.75rem; }
    .badge-info { background: #E3F2FD; color: #1565C0; }
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
export class DocumentosListaComponent implements OnInit {
  documentos: Documento[] = [];
  busqueda = '';
  filtroTipo = '';
  cargando = true;
  error = '';

  constructor(
    private documentosService: DocumentosService,
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
    if (this.filtroTipo) params.tipo = this.filtroTipo;
    this.documentosService.listar(params).subscribe({
      next: (data: any) => {
        this.documentos = data.results || data;
        this.cargando = false;
      },
      error: () => {
        this.error = 'Error al cargar documentos';
        this.cargando = false;
      },
    });
  }

  subir(): void {
    this.router.navigate(['documentos/subir']);
  }

  verDetalle(d: Documento): void {
    this.router.navigate(['documentos', d.id]);
  }

  formatTamano(bytes?: number): string {
    if (!bytes) return '-';
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1048576) return (bytes / 1024).toFixed(1) + ' KB';
    return (bytes / 1048576).toFixed(1) + ' MB';
  }
}

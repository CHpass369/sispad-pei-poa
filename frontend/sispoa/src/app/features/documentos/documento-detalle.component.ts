import { Component, OnInit } from '@angular/core';
import { ActivatedRoute, Router } from '@angular/router';
import { DocumentosService, Documento } from './documentos.service';

@Component({
  standalone: false,
  selector: 'app-documento-detalle',
  template: `
    <div class="page-header" *ngIf="documento">
      <h2>{{ documento.nombre }}</h2>
      <p class="text-secondary">Detalle del documento</p>
    </div>

    <div class="detalle-layout" *ngIf="documento">
      <div class="preview-panel card">
        <div class="preview-content" *ngIf="esImagen()">
          <img [src]="documento.archivo_url || documento.archivo" alt="{{ documento.nombre }}">
        </div>
        <div class="preview-content preview-icon" *ngIf="!esImagen()">
          <span class="file-icon">{{ iconoArchivo() }}</span>
          <span class="file-type">{{ documento.tipo }}</span>
        </div>
      </div>

      <div class="info-panel">
        <div class="card info-card">
          <h3>Metadatos</h3>
          <div class="info-row">
            <label>Nombre</label>
            <span>{{ documento.nombre }}</span>
          </div>
          <div class="info-row">
            <label>Tipo</label>
            <span class="badge badge-info">{{ documento.tipo }}</span>
          </div>
          <div class="info-row">
            <label>Entidad Asociada</label>
            <span>{{ documento.entidad_descripcion || '-' }}</span>
          </div>
          <div class="info-row">
            <label>Tamaño</label>
            <span>{{ formatTamano(documento.tamano) }}</span>
          </div>
          <div class="info-row">
            <label>Fecha Subida</label>
            <span>{{ documento.fecha_subida | date:'dd/MM/yyyy HH:mm' }}</span>
          </div>
          <div class="info-row">
            <label>Subido Por</label>
            <span>{{ documento.subido_por }}</span>
          </div>
          <div class="info-row" *ngIf="documento.descripcion">
            <label>Descripción</label>
            <span>{{ documento.descripcion }}</span>
          </div>
          <div class="info-row" *ngIf="documento.tags">
            <label>Etiquetas</label>
            <span>{{ documento.tags }}</span>
          </div>
        </div>

        <div class="acciones-panel">
          <button class="btn btn-primary" (click)="descargar()">⬇ Descargar</button>
          <button class="btn btn-danger" (click)="eliminar()">✕ Eliminar</button>
        </div>
      </div>
    </div>

    <div class="loading" *ngIf="cargando">Cargando detalle...</div>
    <div class="alert alert-error" *ngIf="error">{{ error }}</div>
  `,
  styles: [`
    .page-header { margin-bottom: 1.5rem; }
    .page-header h2 { font-size: 1.5rem; margin-bottom: 0.25rem; }
    .text-secondary { color: var(--text-secondary); font-size: 0.875rem; }
    .detalle-layout { display: grid; grid-template-columns: 1fr 1fr; gap: 1.5rem; }
    .card { background: var(--surface); border: 1px solid var(--border); border-radius: 8px; }
    .preview-panel { padding: 1.5rem; display: flex; align-items: center; justify-content: center; min-height: 300px; }
    .preview-content { text-align: center; }
    .preview-content img { max-width: 100%; max-height: 400px; border-radius: 4px; }
    .preview-icon { display: flex; flex-direction: column; align-items: center; gap: 0.75rem; }
    .file-icon { font-size: 4rem; color: var(--text-secondary); }
    .file-type { font-size: 1rem; color: var(--text-secondary); text-transform: uppercase; }
    .info-card { padding: 1.5rem; }
    .info-card h3 { font-size: 1rem; margin-bottom: 1rem; }
    .info-row { display: flex; justify-content: space-between; padding: 0.625rem 0; border-bottom: 1px solid var(--border); }
    .info-row:last-child { border-bottom: none; }
    .info-row label { font-size: 0.8125rem; color: var(--text-secondary); font-weight: 500; }
    .info-row span { font-size: 0.875rem; font-weight: 500; }
    .badge { display: inline-block; padding: 0.125rem 0.5rem; border-radius: 4px; font-size: 0.75rem; }
    .badge-info { background: #E3F2FD; color: #1565C0; }
    .acciones-panel { display: flex; gap: 0.75rem; margin-top: 1rem; }
    .btn { display: inline-flex; align-items: center; padding: 0.5rem 1rem; border-radius: 6px; border: none; font-size: 0.875rem; font-weight: 600; cursor: pointer; }
    .btn-primary { background: var(--primary); color: white; }
    .btn-primary:hover { background: var(--primary-dark, #303F9F); }
    .btn-danger { background: #C62828; color: white; }
    .btn-danger:hover { background: #B71C1C; }
    .loading { text-align: center; padding: 2rem; color: var(--text-secondary); }
    .alert { padding: 0.75rem 1rem; border-radius: 6px; margin-top: 1rem; }
    .alert-error { background: #FFEBEE; color: var(--warn); }

    @media (max-width: 768px) {
      .detalle-layout { grid-template-columns: 1fr; }
    }
  `]
})
export class DocumentoDetalleComponent implements OnInit {
  documento: Documento | null = null;
  cargando = true;
  error = '';

  private tiposImagen = ['png', 'jpg', 'jpeg', 'gif', 'bmp', 'webp', 'svg'];

  constructor(
    private documentosService: DocumentosService,
    private route: ActivatedRoute,
    private router: Router,
  ) {}

  ngOnInit(): void {
    const id = +this.route.snapshot.paramMap.get('id')!;
    this.cargarDetalle(id);
  }

  cargarDetalle(id: number): void {
    this.documentosService.obtener(id).subscribe({
      next: (data) => {
        this.documento = data;
        this.cargando = false;
      },
      error: () => {
        this.error = 'Error al cargar documento';
        this.cargando = false;
      },
    });
  }

  esImagen(): boolean {
    if (!this.documento) return false;
    const ext = this.documento.tipo?.toLowerCase() || '';
    return this.tiposImagen.includes(ext);
  }

  iconoArchivo(): string {
    const tipo = this.documento?.tipo?.toLowerCase() || '';
    if (tipo === 'pdf') return '📄';
    if (tipo === 'xlsx' || tipo === 'xls') return '📊';
    if (tipo === 'docx' || tipo === 'doc') return '📝';
    return '📁';
  }

  formatTamano(bytes?: number): string {
    if (!bytes) return '-';
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1048576) return (bytes / 1024).toFixed(1) + ' KB';
    return (bytes / 1048576).toFixed(1) + ' MB';
  }

  descargar(): void {
    if (this.documento?.archivo_url || this.documento?.archivo) {
      const url = this.documento.archivo_url || this.documento.archivo;
      window.open(url, '_blank');
    }
  }

  eliminar(): void {
    if (!this.documento?.id) return;
    if (!confirm('¿Está seguro de eliminar este documento?')) return;
    this.documentosService.eliminar(this.documento.id).subscribe({
      next: () => this.router.navigate(['documentos']),
      error: () => {
        this.error = 'Error al eliminar documento';
      },
    });
  }
}

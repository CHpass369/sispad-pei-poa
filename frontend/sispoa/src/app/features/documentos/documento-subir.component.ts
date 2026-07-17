import { Component } from '@angular/core';
import { Router } from '@angular/router';
import { DocumentosService } from './documentos.service';

@Component({
  standalone: false,
  selector: 'app-documento-subir',
  template: `
    <div class="page-header">
      <h2>Subir Documento</h2>
      <p class="text-secondary">Adjuntar un nuevo documento al sistema</p>
    </div>

    <div class="form-card">
      <form (ngSubmit)="subir()">
        <div class="upload-zone"
             [class.upload-zone-active]="dragActive"
             (dragover)="onDragOver($event)"
             (dragleave)="onDragLeave($event)"
             (drop)="onDrop($event)"
             (click)="fileInput.click()">
          <input #fileInput type="file" (change)="onFileSelect($event)" hidden>
          <div class="upload-icon">⬆</div>
          <p *ngIf="!archivoSeleccionado">Arrastra un archivo aquí o haz clic para seleccionar</p>
          <p *ngIf="archivoSeleccionado" class="upload-file-name">{{ archivoSeleccionado.name }}</p>
          <span class="text-secondary">Tamaño máximo: 25 MB</span>
        </div>

        <div class="form-grid">
          <div class="field">
            <label>Tipo de Entidad *</label>
            <select [(ngModel)]="entidadTipo" name="entidadTipo" class="form-control" required>
              <option value="">Seleccione...</option>
              <option value="POA">POA</option>
              <option value="POAU">POAU</option>
              <option value="Actividad">Actividad</option>
              <option value="Proyecto">Proyecto de Inversión</option>
              <option value="Indicador">Indicador</option>
              <option value="Normativa">Normativa</option>
              <option value="Otro">Otro</option>
            </select>
          </div>
          <div class="field">
            <label>ID de Entidad</label>
            <input type="number" [(ngModel)]="entidadId" name="entidadId" class="form-control"
                   placeholder="Número de identificación">
          </div>
          <div class="field field-full">
            <label>Descripción</label>
            <textarea [(ngModel)]="descripcion" name="descripcion" class="form-control" rows="3"
                      placeholder="Descripción breve del documento"></textarea>
          </div>
          <div class="field field-full">
            <label>Etiquetas</label>
            <input [(ngModel)]="tags" name="tags" class="form-control"
                   placeholder="Etiquetas separadas por coma">
          </div>
        </div>

        <div class="upload-progress" *ngIf="subiendo">
          <div class="progress-bar">
            <div class="progress-fill" [style.width.%]="progreso"></div>
          </div>
          <span class="text-secondary">Subiendo... {{ progreso }}%</span>
        </div>

        <div class="form-actions">
          <button type="button" class="btn btn-outline" (click)="cancelar()">Cancelar</button>
          <button type="submit" class="btn btn-primary" [disabled]="!archivoSeleccionado || subiendo">
            {{ subiendo ? 'Subiendo...' : 'Subir Documento' }}
          </button>
        </div>
      </form>
    </div>

    <div class="alert alert-error" *ngIf="error">{{ error }}</div>
  `,
  styles: [`
    .page-header { margin-bottom: 1rem; }
    .page-header h2 { font-size: 1.5rem; margin-bottom: 0.25rem; }
    .text-secondary { color: var(--text-secondary); font-size: 0.875rem; }
    .form-card { background: var(--surface); border: 1px solid var(--border); border-radius: 8px; padding: 1.5rem; }
    .upload-zone {
      border: 2px dashed var(--border); border-radius: 8px; padding: 2.5rem;
      text-align: center; cursor: pointer; transition: all 0.2s; margin-bottom: 1.5rem;
    }
    .upload-zone:hover, .upload-zone-active { border-color: var(--primary); background: rgba(63, 81, 181, 0.04); }
    .upload-icon { font-size: 2rem; margin-bottom: 0.5rem; color: var(--text-secondary); }
    .upload-file-name { font-weight: 600; color: var(--primary); margin-bottom: 0.25rem; }
    .form-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; }
    .field { display: flex; flex-direction: column; margin-bottom: 1rem; }
    .field-full { grid-column: 1 / -1; }
    .field label { font-size: 0.8125rem; font-weight: 600; margin-bottom: 0.375rem; color: var(--text-primary); }
    .form-control { padding: 0.5rem 0.75rem; border: 1px solid var(--border); border-radius: 6px; font-size: 0.875rem; }
    .form-control:focus { outline: none; border-color: var(--primary); }
    textarea.form-control { resize: vertical; }
    .upload-progress { margin: 1rem 0; }
    .progress-bar { height: 6px; background: var(--border); border-radius: 3px; overflow: hidden; margin-bottom: 0.375rem; }
    .progress-fill { height: 100%; background: var(--primary); transition: width 0.3s; }
    .form-actions { display: flex; justify-content: flex-end; gap: 0.75rem; margin-top: 1.5rem; }
    .btn { display: inline-flex; align-items: center; padding: 0.5rem 1rem; border-radius: 6px; border: none; font-size: 0.875rem; font-weight: 600; cursor: pointer; }
    .btn-primary { background: var(--primary); color: white; }
    .btn-primary:disabled { opacity: 0.5; cursor: not-allowed; }
    .btn-outline { background: transparent; border: 1px solid var(--border); color: var(--text-primary); }
    .btn-outline:hover { background: var(--hover, #f5f5f5); }
    .alert { padding: 0.75rem 1rem; border-radius: 6px; margin-top: 1rem; }
    .alert-error { background: #FFEBEE; color: var(--warn); }
  `]
})
export class DocumentoSubirComponent {
  archivoSeleccionado: File | null = null;
  entidadTipo = '';
  entidadId: number | null = null;
  descripcion = '';
  tags = '';
  dragActive = false;
  subiendo = false;
  progreso = 0;
  error = '';

  constructor(
    private documentosService: DocumentosService,
    private router: Router,
  ) {}

  onDragOver(event: DragEvent): void {
    event.preventDefault();
    this.dragActive = true;
  }

  onDragLeave(event: DragEvent): void {
    event.preventDefault();
    this.dragActive = false;
  }

  onDrop(event: DragEvent): void {
    event.preventDefault();
    this.dragActive = false;
    const files = event.dataTransfer?.files;
    if (files && files.length > 0) {
      this.archivoSeleccionado = files[0];
    }
  }

  onFileSelect(event: Event): void {
    const input = event.target as HTMLInputElement;
    if (input.files && input.files.length > 0) {
      this.archivoSeleccionado = input.files[0];
    }
  }

  subir(): void {
    if (!this.archivoSeleccionado) {
      this.error = 'Debe seleccionar un archivo';
      return;
    }
    if (!this.entidadTipo) {
      this.error = 'El tipo de entidad es obligatorio';
      return;
    }
    this.subiendo = true;
    this.error = '';
    this.progreso = 0;
    const formData = new FormData();
    formData.append('archivo', this.archivoSeleccionado);
    formData.append('nombre', this.archivoSeleccionado.name);
    formData.append('entidad_tipo', this.entidadTipo);
    if (this.entidadId) formData.append('entidad_id', String(this.entidadId));
    if (this.descripcion) formData.append('descripcion', this.descripcion);
    if (this.tags) formData.append('tags', this.tags);
    this.progreso = 50;
    this.documentosService.subir(formData).subscribe({
      next: () => {
        this.progreso = 100;
        this.router.navigate(['documentos']);
      },
      error: (e) => {
        this.error = e.error?.detail || 'Error al subir documento';
        this.subiendo = false;
        this.progreso = 0;
      },
    });
  }

  cancelar(): void {
    this.router.navigate(['documentos']);
  }
}

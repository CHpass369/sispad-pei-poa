import { Component, OnInit } from '@angular/core';
import { PermissionsService } from '../../core/services/permissions.service';
import { InstrumentoV2, MetodologiaV2, SisPeService } from './sis-pe.service';

@Component({
  standalone: false,
  selector: 'app-sis-pe-instrumentos',
  template: `
    <div class="page-header">
      <h2>Instrumentos de Planificación</h2>
      <p class="text-secondary">Kernel estratégico V2 (SIS-PE)</p>
    </div>

    <div class="alert alert-error" *ngIf="error">{{ error }}</div>
    <div class="alert alert-success" *ngIf="mensaje">{{ mensaje }}</div>

    <form *ngIf="puedeCrear" (ngSubmit)="crear()" class="form-inline">
      <input [(ngModel)]="form.codigo" name="codigo" placeholder="Código" required class="input" />
      <input [(ngModel)]="form.nombre" name="nombre" placeholder="Nombre" required class="input" />
      <input [(ngModel)]="form.periodo_inicio" name="pi" type="number" placeholder="Inicio" required class="input" />
      <input [(ngModel)]="form.periodo_fin" name="pf" type="number" placeholder="Fin" required class="input" />
      <button type="submit" class="btn btn-primary">+ Crear</button>
    </form>

    <div *ngIf="cargando" class="loading">Cargando instrumentos...</div>

    <table class="data-table" *ngIf="!cargando">
      <thead>
        <tr>
          <th>Código</th>
          <th>Nombre</th>
          <th>Tipo</th>
          <th>Período</th>
          <th>Estado</th>
          <th>Versiones</th>
          <th></th>
        </tr>
      </thead>
      <tbody>
        <tr *ngFor="let inst of instrumentos">
          <td>{{ inst.codigo }}</td>
          <td>{{ inst.nombre }}</td>
          <td>{{ inst.tipo_nombre }}</td>
          <td>{{ inst.periodo_inicio }}–{{ inst.periodo_fin }}</td>
          <td><span class="badge">{{ inst.estado }}</span></td>
          <td>{{ inst.versiones_count }}</td>
          <td>
            <button class="btn btn-sm" (click)="crearVersion(inst)" *ngIf="puedeEditar">
              + Versión
            </button>
            <a class="btn btn-sm" [routerLink]="['/sis-pe/versiones', inst.id]">Versiones</a>
          </td>
        </tr>
      </tbody>
    </table>
    <div *ngIf="!cargando && instrumentos.length === 0" class="empty">
      No hay instrumentos registrados
    </div>
  `,
  styles: [`
    .page-header { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 1.5rem; flex-wrap: wrap; gap: 1rem; }
    .text-secondary { color: var(--text-secondary); font-size: 0.875rem; }
    .form-inline { display: flex; gap: 0.5rem; margin-bottom: 1.5rem; flex-wrap: wrap; }
    .input { padding: 0.5rem; border: 1px solid var(--border); border-radius: 6px; font-size: 0.875rem; }
    .btn { display: inline-flex; align-items: center; padding: 0.5rem 0.875rem; border-radius: 6px; border: none; font-size: 0.8125rem; font-weight: 600; cursor: pointer; text-decoration: none; }
    .btn-primary { background: var(--primary); color: white; }
    .btn-sm { background: #E3F2FD; color: #1565C0; margin-right: 0.25rem; }
    .data-table { width: 100%; border-collapse: collapse; background: var(--surface); border: 1px solid var(--border); border-radius: 8px; }
    .data-table th, .data-table td { padding: 0.625rem 0.75rem; text-align: left; border-bottom: 1px solid var(--border); font-size: 0.8125rem; }
    .badge { display: inline-block; padding: 0.125rem 0.5rem; border-radius: 4px; font-size: 0.6875rem; font-weight: 600; background: #E3F2FD; color: #1565C0; }
    .loading { text-align: center; padding: 2rem; color: var(--text-secondary); }
    .empty { text-align: center; padding: 2rem; color: var(--text-secondary); }
    .alert { padding: 0.75rem 1rem; border-radius: 6px; margin-bottom: 1rem; }
    .alert-error { background: #FFEBEE; color: var(--warn); }
    .alert-success { background: #E8F5E9; color: #2E7D32; }
  `],
})
export class SisPeInstrumentosComponent implements OnInit {
  cargando = true;
  error = '';
  mensaje = '';
  instrumentos: InstrumentoV2[] = [];
  metodologias: MetodologiaV2[] = [];
  form: { codigo: string; nombre: string; periodo_inicio: number | null; periodo_fin: number | null } = {
    codigo: '', nombre: '', periodo_inicio: null, periodo_fin: null,
  };

  constructor(
    private service: SisPeService,
    private permissions: PermissionsService,
  ) {}

  get puedeCrear(): boolean {
    return this.permissions.hasAnyCapability(['sis_pe.instrumento.create']);
  }

  get puedeEditar(): boolean {
    return this.permissions.hasAnyCapability(['sis_pe.pad.edit', 'sis_pe.pei.edit']);
  }

  ngOnInit(): void {
    this.cargar();
    this.service.listarMetodologias().subscribe({
      next: (d) => { this.metodologias = d.results; },
      error: () => undefined,
    });
  }

  cargar(): void {
    this.cargando = true;
    this.service.listarInstrumentos().subscribe({
      next: (data) => {
        this.instrumentos = data.results;
        this.cargando = false;
      },
      error: () => {
        this.error = 'Error al cargar instrumentos';
        this.cargando = false;
      },
    });
  }

  crear(): void {
    const { codigo, nombre, periodo_inicio, periodo_fin } = this.form;
    if (!codigo || !nombre || !periodo_inicio || !periodo_fin) {
      this.error = 'Código, nombre y período son requeridos';
      return;
    }
    this.error = '';
    this.service.crearInstrumento({
      codigo, nombre, periodo_inicio, periodo_fin,
    } as Partial<InstrumentoV2>).subscribe({
      next: () => {
        this.mensaje = 'Instrumento creado';
        this.form = { codigo: '', nombre: '', periodo_inicio: null, periodo_fin: null };
        this.cargar();
      },
      error: () => { this.error = 'Error al crear el instrumento'; },
    });
  }

  crearVersion(inst: InstrumentoV2): void {
    if (!this.metodologias.length) {
      this.error = 'No hay metodologías disponibles';
      return;
    }
    this.service.crearVersion(inst.id, this.metodologias[0].id).subscribe({
      next: () => {
        this.mensaje = `Versión creada para ${inst.codigo}`;
        this.cargar();
      },
      error: () => { this.error = 'Error al crear la versión'; },
    });
  }
}

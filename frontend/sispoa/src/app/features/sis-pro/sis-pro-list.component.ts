import { Component, OnInit } from '@angular/core';
import { PermissionsService } from '../../core/services/permissions.service';
import { ProyectoV2, SisProService } from './sis-pro.service';

@Component({
  standalone: false,
  selector: 'app-sis-pro-list',
  template: `
    <div class="page-header">
      <h2>Cartera de Proyectos</h2>
      <p class="text-secondary">SIS-PRO V2 — ciclo del proyecto</p>
    </div>
    @if (error) {
      <div class="alert alert-error">{{ error }}</div>
    }
    @if (mensaje) {
      <div class="alert alert-success">{{ mensaje }}</div>
    }
    
    @if (puedeCrear) {
      <form (ngSubmit)="crear()" class="form-inline">
        <input [(ngModel)]="form.codigo_interno" name="ci" placeholder="Código interno" required class="input" />
        <input [(ngModel)]="form.nombre" name="n" placeholder="Nombre" required class="input" />
        <input [(ngModel)]="form.gestion" name="g" type="number" placeholder="Gestión" required class="input" />
        <input [(ngModel)]="form.costo_total" name="ct" type="number" placeholder="Costo total" class="input" />
        <button type="submit" class="btn btn-primary">+ Proyecto</button>
      </form>
    }
    
    @if (cargando) {
      <div class="loading">Cargando proyectos...</div>
    }
    @if (!cargando) {
      <table class="data-table">
        <thead>
          <tr><th>Código</th><th>Nombre</th><th>Gestión</th><th>Fase</th><th>Costo</th><th>Saldo</th><th></th></tr>
        </thead>
        <tbody>
          @for (proy of proyectos; track proy) {
            <tr>
              <td>{{ proy.codigo_interno }}</td>
              <td>{{ proy.nombre }}</td>
              <td>{{ proy.gestion }}</td>
              <td><span class="badge">{{ proy.fase }}</span></td>
              <td>Bs {{ proy.costo_total }}</td>
              <td>
                @if (puedeValidar && proy.fase !== 'evaluacion') {
                  <button class="btn btn-sm" (click)="avanzar(proy)">
                    ➜ avanzar fase
                  </button>
                }
                <a class="btn btn-sm" [routerLink]="['/sis-pro/proyectos', proy.id]">Detalle</a>
              </td>
            </tr>
          }
        </tbody>
      </table>
    }
    @if (!cargando && proyectos.length === 0) {
      <div class="empty">No hay proyectos registrados</div>
    }
    `,
  styles: [`
    .page-header { margin-bottom: 1.5rem; }
    .text-secondary { color: var(--text-secondary); font-size: 0.875rem; }
    .form-inline { display: flex; gap: 0.5rem; margin-bottom: 1.5rem; flex-wrap: wrap; }
    .input { padding: 0.5rem; border: 1px solid var(--border); border-radius: 6px; font-size: 0.875rem; }
    .btn { display: inline-flex; align-items: center; padding: 0.5rem 0.875rem; border-radius: 6px; border: none; font-size: 0.8125rem; font-weight: 600; cursor: pointer; text-decoration: none; }
    .btn-primary { background: var(--primary); color: white; }
    .btn-sm { background: var(--mdc-blue-50); color: var(--mdc-blue-800); margin-right: 0.25rem; }
    .data-table { width: 100%; border-collapse: collapse; background: var(--surface); border: 1px solid var(--border); border-radius: 8px; }
    .data-table th, 
    .badge { display: inline-block; padding: 0.125rem 0.5rem; border-radius: 4px; font-size: 0.6875rem; font-weight: 600; background: var(--mdc-blue-50); color: var(--mdc-blue-800); }
    .loading { text-align: center; padding: 2rem; color: var(--text-secondary); }
    .empty { text-align: center; padding: 2rem; color: var(--text-secondary); }
    .alert { padding: 0.75rem 1rem; border-radius: 6px; margin-bottom: 1rem; }
    .alert-error { background: var(--mdc-red-50); color: var(--warn); }
    .alert-success { background: var(--mdc-green-50); color: var(--mdc-green-800); }
  `],
})
export class SisProListComponent implements OnInit {
  cargando = true;
  error = '';
  mensaje = '';
  proyectos: ProyectoV2[] = [];
  form: { codigo_interno: string; nombre: string; gestion: number | null; costo_total: number | null } = {
    codigo_interno: '', nombre: '', gestion: null, costo_total: null,
  };

  constructor(
    private service: SisProService,
    private permissions: PermissionsService,
  ) {}

  get puedeCrear(): boolean {
    return this.permissions.hasAnyCapability(['sis_pro.project.create', 'sis_pro.project.edit']);
  }

  get puedeValidar(): boolean {
    return this.permissions.hasAnyCapability(['sis_pro.preinvestment.validate']);
  }

  ngOnInit(): void {
    this.service.listarProyectos().subscribe({
      next: (data) => { this.proyectos = data.results; this.cargando = false; },
      error: () => { this.error = 'Error al cargar proyectos'; this.cargando = false; },
    });
  }

  crear(): void {
    const { codigo_interno, nombre, gestion, costo_total } = this.form;
    if (!codigo_interno || !nombre || !gestion) {
      this.error = 'Código, nombre y gestión son requeridos';
      return;
    }
    this.error = '';
    this.service.crearProyecto({
      codigo_interno, nombre, gestion,
      costo_total: costo_total ? String(costo_total) : '0',
    } as Partial<ProyectoV2>).subscribe({
      next: () => {
        this.mensaje = 'Proyecto creado';
        this.form = { codigo_interno: '', nombre: '', gestion: null, costo_total: null };
        this.cargando = true;
        this.service.listarProyectos().subscribe({
          next: (data) => { this.proyectos = data.results; this.cargando = false; },
          error: () => { this.error = 'Error al recargar'; this.cargando = false; },
        });
      },
      error: () => { this.error = 'Error al crear el proyecto'; },
    });
  }

  avanzar(proyecto: ProyectoV2): void {
    this.service.avanzarFase(proyecto.id).subscribe({
      next: (actualizado) => {
        this.mensaje = `${proyecto.codigo_interno} → fase ${actualizado.fase}`;
        this.cargando = true;
        this.service.listarProyectos().subscribe({
          next: (data) => { this.proyectos = data.results; this.cargando = false; },
          error: () => { this.error = 'Error al recargar'; this.cargando = false; },
        });
      },
      error: () => { this.error = 'Error al avanzar de fase'; },
    });
  }
}

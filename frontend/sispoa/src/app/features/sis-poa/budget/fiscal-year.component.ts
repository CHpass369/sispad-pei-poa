import { Component, OnInit } from '@angular/core';
import { PermissionsService } from '../../../core/services/permissions.service';
import { BudgetService, FiscalYear } from './budget.service';

const ESTADOS_ABIERTOS = ['preparacion', 'CONFIGURACION'];
const ESTADOS_TERMINALES = ['CERRADA', 'cerrada', 'archivada', 'VIGENTE'];

@Component({
  standalone: false,
  selector: 'app-fiscal-year',
  templateUrl: './fiscal-year.component.html',
  styles: [`
    .page-header { margin-bottom: 1.5rem; }
    .text-secondary { color: var(--text-secondary); font-size: 0.875rem; }
    .form-inline { display: flex; gap: 1rem; flex-wrap: wrap; align-items: flex-end; }
    .campo label { display: block; font-size: 0.75rem; font-weight: 600; margin-bottom: 0.375rem; }
    .input { padding: 0.5rem; border: 1px solid var(--border); border-radius: 6px; font-size: 0.875rem; min-width: 160px; }
    .btn-sm { background: var(--surface); border: 1px solid var(--border); }
    .btn-sm:hover { border-color: var(--primary); color: var(--primary); }
    .btn-danger { background: #FFEBEE; color: #C62828; }
    .btn-danger:hover { background: #FFCDD2; }
    .data-table { width: 100%; border-collapse: collapse; background: var(--surface); border: 1px solid var(--border); border-radius: 8px; }
    .data-table th, .data-table td { padding: 0.625rem 0.75rem; text-align: left; border-bottom: 1px solid var(--border); font-size: 0.8125rem; }
    .loading { text-align: center; padding: 2rem; color: var(--text-secondary); }
    .empty { text-align: center; padding: 2rem; color: var(--text-secondary); }
    .acciones { display: flex; gap: 0.5rem; }
  `],
})
export class FiscalYearComponent implements OnInit {
  gestiones: FiscalYear[] = [];
  cargando = true;
  error = '';
  mensaje = '';
  form: { anio: number | null; heredar_de: number | null } = {
    anio: null,
    heredar_de: null,
  };

  constructor(
    private service: BudgetService,
    private permissions: PermissionsService,
  ) {}

  get puedeGestionar(): boolean {
    return this.permissions.hasAnyCapability(['sis_poa.budget.manage']);
  }

  ngOnInit(): void {
    this.cargar();
  }

  cargar(): void {
    this.cargando = true;
    this.service.listar().subscribe({
      next: (data) => {
        this.gestiones = data.results;
        this.cargando = false;
      },
      error: () => {
        this.error = 'Error al cargar las gestiones fiscales';
        this.cargando = false;
      },
    });
  }

  crear(): void {
    if (!this.form.anio) {
      this.error = 'El año de gestión es obligatorio';
      return;
    }
    this.error = '';
    this.service.crear({
      anio: this.form.anio,
      heredar_de: this.form.heredar_de,
    }).subscribe({
      next: () => {
        this.mensaje = `Gestión ${this.form.anio} creada`;
        this.form = { anio: null, heredar_de: null };
        this.cargar();
      },
      error: () => {
        this.error = 'No se pudo crear la gestión (el año podría ya existir)';
      },
    });
  }

  habilitar(gestion: FiscalYear): void {
    this.error = '';
    this.service.habilitar(gestion.id).subscribe({
      next: () => {
        this.mensaje = `Gestión ${gestion.anio} habilitada`;
        this.cargar();
      },
      error: () => {
        this.error = `No se pudo habilitar la gestión ${gestion.anio}`;
      },
    });
  }

  cerrar(gestion: FiscalYear): void {
    if (!confirm(`¿Cerrar la gestión ${gestion.anio}?`)) return;
    this.error = '';
    this.service.cerrar(gestion.id).subscribe({
      next: () => {
        this.mensaje = `Gestión ${gestion.anio} cerrada`;
        this.cargar();
      },
      error: () => {
        this.error = `No se pudo cerrar la gestión ${gestion.anio}`;
      },
    });
  }

  puedeHabilitar(gestion: FiscalYear): boolean {
    return (
      this.puedeGestionar &&
      ESTADOS_ABIERTOS.includes(gestion.estado)
    );
  }

  puedeCerrar(gestion: FiscalYear): boolean {
    return this.puedeGestionar && !ESTADOS_TERMINALES.includes(gestion.estado);
  }

  badgeClass(gestion: FiscalYear): string {
    switch (gestion.estado) {
      case 'HABILITADA':
      case 'abierta':
        return 'badge-success';
      case 'EN_FORMULACION':
      case 'formulacion':
      case 'revision':
      case 'consolidacion':
      case 'aprobacion':
        return 'badge-warning';
      case 'CERRADA':
      case 'cerrada':
      case 'archivada':
        return 'badge-danger';
      default:
        return 'badge-info';
    }
  }
}

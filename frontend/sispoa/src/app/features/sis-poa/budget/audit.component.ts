import { Component, OnInit } from '@angular/core';
import {
  ACCIONES_AUDITORIA,
  AuditEvent,
  AuditFilter,
  BudgetService,
  ENTIDADES_AUDITORIA,
  FiscalYear,
} from './budget.service';

@Component({
  standalone: false,
  selector: 'app-budget-audit',
  templateUrl: './audit.component.html',
  styles: [`
    .page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 1.5rem; flex-wrap: wrap; gap: 0.75rem; }
    .page-header h2 { margin: 0; }
    .filtros { display: grid; grid-template-columns: repeat(auto-fit, minmax(160px, 1fr)); gap: 0.75rem; margin-bottom: 1.25rem; align-items: end; }
    .campo label { display: block; font-size: 0.75rem; font-weight: 600; margin-bottom: 0.375rem; }
    .input { padding: 0.5rem; border: 1px solid var(--border); border-radius: 6px; font-size: 0.875rem; min-width: 120px; width: 100%; box-sizing: border-box; }
    .data-table { width: 100%; border-collapse: collapse; background: var(--surface); border: 1px solid var(--border); border-radius: 8px; }
    .data-table th, 
    
    .fila-seleccionable { cursor: pointer; }
    .fila-seleccionable:hover { background: #F4F8FD; }
    .fila-seleccionada { background: #E3F0FD !important; }
    .detalle { margin-top: 1rem; background: var(--surface); border: 1px solid var(--border); border-radius: 8px; padding: 1rem; }
    .detalle-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 0.5rem 1rem; margin: 0.75rem 0; font-size: 0.8125rem; }
    .detalle-grid b { font-size: 0.6875rem; text-transform: uppercase; color: var(--text-secondary); display: block; }
    pre.json { background: #263238; color: #ECEFF1; border-radius: 6px; padding: 0.75rem; font-size: 0.75rem; overflow: auto; max-height: 320px; white-space: pre-wrap; word-break: break-word; }
    .badge { display: inline-block; padding: 0.1875rem 0.5rem; border-radius: 999px; font-size: 0.6875rem; font-weight: 600; }
    .badge-crear { background: var(--mdc-green-50); color: var(--mdc-green-800); }
    .badge-modificar { background: var(--mdc-blue-50); color: var(--mdc-blue-800); }
    .badge-anular { background: var(--mdc-red-50); color: var(--mdc-red-800); }
    .badge-aprobar { background: #F3E5F5; color: #6A1B9A; }
    .badge-enviar { background: var(--mdc-amber-50); color: #E65100; }
    .badge-cerrar { background: #ECEFF1; color: #455A64; }
    .acciones { display: flex; gap: 0.375rem; }
    .alert-error { background: var(--mdc-red-50); color: var(--mdc-red-800); border-radius: 6px; padding: 0.625rem 0.875rem; margin: 0.75rem 0; font-size: 0.875rem; }
    .loading, .empty { text-align: center; padding: 2rem; color: var(--text-secondary); }
    .paginado { display: flex; justify-content: flex-end; align-items: center; gap: 0.75rem; margin-top: 0.75rem; font-size: 0.8125rem; }
    .btn:disabled { opacity: 0.5; cursor: not-allowed; }
  `],
})
export class AuditComponent implements OnInit {
  gestiones: FiscalYear[] = [];
  filtros: AuditFilter = {};
  eventos: AuditEvent[] = [];
  total = 0;
  seleccionado: AuditEvent | null = null;

  cargando = false;
  error = '';
  pagina = 1;
  paginaSize = 25;

  entidades = ENTIDADES_AUDITORIA;
  acciones = ACCIONES_AUDITORIA;

  constructor(private service: BudgetService) {}

  ngOnInit(): void {
    this.service.listar().subscribe({
      next: (data) => {
        this.gestiones = data.results;
        if (this.gestiones.length > 0 && !this.filtros.gestion) {
          this.filtros.gestion = this.gestiones[0].id;
        }
        this.buscar();
      },
      error: () => {
        this.cargando = false;
        this.error = 'No se pudieron cargar las gestiones.';
      },
    });
  }

  buscar(): void {
    this.pagina = 1;
    this.cargar();
  }

  limpiar(): void {
    this.filtros = {};
    this.buscar();
  }

  cargar(): void {
    this.cargando = true;
    this.error = '';
    this.seleccionado = null;
    this.service
      .listarAuditoria({ ...this.filtros, page: this.pagina })
      .subscribe({
        next: (data) => {
          this.eventos = data.results;
          this.total = data.count;
          this.cargando = false;
        },
        error: () => {
          this.cargando = false;
          this.error = 'No se pudo consultar el registro de auditoría.';
        },
      });
  }

  paginaAnterior(): void {
    if (this.pagina > 1) {
      this.pagina -= 1;
      this.cargar();
    }
  }

  paginaSiguiente(): void {
    if (this.pagina * this.paginaSize < this.total) {
      this.pagina += 1;
      this.cargar();
    }
  }

  get totalPaginas(): number {
    return Math.max(1, Math.ceil(this.total / this.paginaSize));
  }

  seleccionar(evento: AuditEvent): void {
    this.seleccionado =
      this.seleccionado?.id === evento.id ? null : evento;
  }

  jsonLegible(datos: Record<string, unknown> | null): string {
    if (!datos) {
      return '—';
    }
    try {
      return JSON.stringify(datos, null, 2);
    } catch {
      return String(datos);
    }
  }

  badgeClase(accion: string): string {
    const base = 'badge badge-';
    switch (accion) {
      case 'crear':
      case 'importar':
        return base + 'crear';
      case 'modificar':
      case 'enviar':
      case 'devolver':
        return base + 'modificar';
      case 'anular':
        return base + 'anular';
      case 'aprobar':
        return base + 'aprobar';
      default:
        return base + 'cerrar';
    }
  }
}

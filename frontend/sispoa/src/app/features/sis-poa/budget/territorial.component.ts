import { Component, OnInit } from '@angular/core';
import {
  ApiErrorResponse,
  BudgetService,
  CatalogoOpciones,
  FiscalYear,
  DistribucionTerritorial,
  TerritorialRow,
} from './budget.service';

/** Métodos de reparto: controla qué columna editable se muestra. */
export const METODOS: { valor: string; etiqueta: string; usaPoblacion: boolean; usaPorcentaje: boolean; usaMonto: boolean }[] = [
  { valor: 'MANUAL', etiqueta: 'Manual', usaPoblacion: false, usaPorcentaje: false, usaMonto: true },
  { valor: 'MONTO_FIJO', etiqueta: 'Monto fijo', usaPoblacion: false, usaPorcentaje: false, usaMonto: true },
  { valor: 'PORCENTAJE', etiqueta: 'Porcentaje', usaPoblacion: false, usaPorcentaje: true, usaMonto: false },
  { valor: 'POBLACION', etiqueta: 'Población', usaPoblacion: true, usaPorcentaje: false, usaMonto: false },
  { valor: 'FORMULA', etiqueta: 'Fórmula', usaPoblacion: false, usaPorcentaje: false, usaMonto: true },
];

@Component({
  standalone: false,
  selector: 'app-territorial',
  templateUrl: './territorial.component.html',
  styles: [`
    .page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 1.5rem; flex-wrap: wrap; gap: 0.75rem; }
    .page-header h2 { margin: 0; }
    .seccion { margin-top: 1.5rem; }
    .seccion h3 { font-size: 0.9375rem; margin-bottom: 0.75rem; }
    .form-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 0.75rem; }
    .campo label { display: block; font-size: 0.75rem; font-weight: 600; margin-bottom: 0.375rem; }
    .input { padding: 0.5rem; border: 1px solid var(--border); border-radius: 6px; font-size: 0.875rem; min-width: 140px; width: 100%; box-sizing: border-box; }
    .data-table { width: 100%; border-collapse: collapse; background: var(--surface); border: 1px solid var(--border); border-radius: 8px; }
    .data-table th, 
    
    .monto-celda { text-align: right; white-space: nowrap; }
    .acciones { display: flex; gap: 0.375rem; flex-wrap: wrap; }
    .btn-sm { background: var(--surface); border: 1px solid var(--border); }
    .btn-sm:hover { border-color: var(--primary); color: var(--primary); }
    .alert-error { background: var(--mdc-red-50); color: var(--mdc-red-800); border-radius: 6px; padding: 0.625rem 0.875rem; margin: 0.75rem 0; font-size: 0.875rem; }
    .alert-success { background: var(--mdc-green-50); color: var(--mdc-green-800); border-radius: 6px; padding: 0.625rem 0.875rem; margin: 0.75rem 0; font-size: 0.875rem; }
    .loading, .empty { text-align: center; padding: 2rem; color: var(--text-secondary); }
    .total-badge { display: inline-block; border-radius: 999px; padding: 0.25rem 0.625rem; font-size: 0.75rem; font-weight: 700; }
    .total-badge.ok { background: var(--mdc-green-50); color: var(--mdc-green-800); }
    .total-badge.bad { background: var(--mdc-red-50); color: var(--mdc-red-800); }
    .fila-distribucion { display: flex; align-items: center; justify-content: space-between; padding: 0.5rem 0.75rem; border: 1px solid var(--border); border-radius: 8px; margin-bottom: 0.375rem; cursor: pointer; font-size: 0.8125rem; }
    .fila-distribucion:hover { border-color: var(--primary); }
    .fila-distribucion.seleccionada { border-color: var(--primary); background: #F4F8FD; }
  `],
})
export class TerritorialComponent implements OnInit {
  gestiones: FiscalYear[] = [];
  gestionSeleccionada: string | null = null;
  opciones: CatalogoOpciones | null = null;
  lista: DistribucionTerritorial[] = [];
  actual: DistribucionTerritorial | null = null;
  metodos = METODOS;

  formulario = {
    fuente: null as string | null,
    organismo: null as string | null,
    metodo: 'POBLACION',
    bolsa_total: null as number | null,
    observaciones: '',
  };
  filas: TerritorialRow[] = [];

  cargando = false;
  guardando = false;
  error = '';
  mensaje = '';

  constructor(private service: BudgetService) {}

  ngOnInit(): void {
    this.service.listar().subscribe({
      next: (data) => {
        this.gestiones = data.results;
        if (this.gestiones.length > 0) {
          this.seleccionarGestion(this.gestiones[0].id);
        } else {
          this.cargando = false;
        }
      },
      error: () => {
        this.error = 'Error al cargar las gestiones fiscales';
        this.cargando = false;
      },
    });
  }

  seleccionarGestion(id: string): void {
    this.gestionSeleccionada = id;
    this.error = '';
    this.mensaje = '';
    this.actual = null;
    this.cargarDatos();
  }

  cargarDatos(): void {
    if (!this.gestionSeleccionada) return;
    this.cargando = true;
    this.service.opcionesCatalogo().subscribe({
      next: (o) => { this.opciones = o; },
      error: () => { /* no bloquea */ },
    });
    this.service.listarTerritoriales({ gestion: this.gestionSeleccionada }).subscribe({
      next: (r) => {
        this.lista = r.results;
        this.cargando = false;
      },
      error: () => {
        this.error = 'Error al cargar las distribuciones territoriales';
        this.cargando = false;
      },
    });
  }

  // -- Formulario ------------------------------------------------------------

  metodoActual(): { usaPoblacion: boolean; usaPorcentaje: boolean; usaMonto: boolean } {
    return this.metodos.find((m) => m.valor === this.formulario.metodo) ?? this.metodos[0];
  }

  nuevaDistribucion(): void {
    this.actual = null;
    this.error = '';
    this.mensaje = '';
    this.formulario = {
      fuente: null, organismo: null, metodo: 'POBLACION',
      bolsa_total: null, observaciones: '',
    };
    this.filas = [];
  }

  seleccionar(d: DistribucionTerritorial): void {
    this.actual = d;
    this.error = '';
    this.mensaje = '';
    this.formulario = {
      fuente: d.fuente,
      organismo: d.organismo,
      metodo: d.metodo,
      bolsa_total: parseFloat(d.bolsa_total),
      observaciones: d.observaciones,
    };
    this.filas = d.asignaciones.map((a) => ({
      distrito: a.distrito,
      poblacion: a.poblacion,
      porcentaje: a.porcentaje ? parseFloat(a.porcentaje) : null,
      monto: parseFloat(a.monto_calculado || '0') || null,
    }));
  }

  agregarFila(): void {
    this.filas.push({ distrito: '', poblacion: null, porcentaje: null, monto: null });
  }

  quitarFila(i: number): void {
    this.filas.splice(i, 1);
  }

  /** Nombre del distrito seleccionado en la fila (para mostrar en la tabla). */
  nombreDistrito(d: string | undefined): string {
    if (!d) return '—';
    const distrito = this.opciones?.distritos.find((x) => x.id === d);
    return distrito ? `${distrito.codigo} — ${distrito.nombre}` : d;
  }

  totalEntradas(): number {
    return this.filas.reduce((acc, f) => acc + (f.monto ? Number(f.monto) : 0), 0);
  }

  sumaAsignada(): number {
    if (!this.actual) return 0;
    return this.actual.asignaciones.reduce((acc, a) => acc + parseFloat(a.monto_final || '0'), 0);
  }

  diferencia(): number {
    if (!this.actual) return 0;
    return parseFloat(this.actual.bolsa_total) - this.sumaAsignada();
  }

  coincide(): boolean {
    if (!this.actual || !this.actual.bolsa_total) return false;
    return Math.abs(this.diferencia()) < 0.005;
  }

  /** Monto de la fila según la asignación calculada (por distrito). */
  montoAsignacion(f: TerritorialRow, campo: 'monto_calculado' | 'ajuste' | 'monto_final'): string {
    const a = this.actual?.asignaciones.find((x) => x.distrito === f.distrito);
    return a ? a[campo] : '0.00';
  }

  bloquearEdicion(): boolean {
    return this.actual?.estado === 'APLICADA';
  }

  // -- Operaciones -----------------------------------------------------------

  guardar(): void {
    if (!this.gestionSeleccionada || !this.formulario.fuente ||
        this.formulario.bolsa_total === null || this.formulario.bolsa_total <= 0) {
      this.error = 'Gestión, fuente y bolsa total (mayor a 0) son obligatorias';
      return;
    }
    const distritos = this.filas.filter((f) => f.distrito);
    if (distritos.length === 0) {
      this.error = 'Debe cargar al menos un distrito';
      return;
    }
    this.error = '';
    this.guardando = true;
    this.service.crearTerritorial({
      gestion: this.gestionSeleccionada,
      fuente: this.formulario.fuente,
      organismo: this.formulario.organismo || null,
      metodo: this.formulario.metodo,
      bolsa_total: this.formulario.bolsa_total,
      observaciones: this.formulario.observaciones,
      distritos,
    }).subscribe({
      next: (d) => {
        this.guardando = false;
        this.mensaje = 'Distribución territorial creada';
        this.cargarDatos();
        this.seleccionar(d);
      },
      error: (err) => {
        this.guardando = false;
        this.error = this.mensajeError(err);
      },
    });
  }

  calcular(): void {
    if (!this.actual) {
      this.error = 'Primero guarde la distribución territorial';
      return;
    }
    const distritos = this.filas.filter((f) => f.distrito);
    if (distritos.length === 0) {
      this.error = 'Debe cargar al menos un distrito';
      return;
    }
    this.error = '';
    this.guardando = true;
    this.service.calcularTerritorial(this.actual.id, distritos).subscribe({
      next: (d) => {
        this.guardando = false;
        this.mensaje = 'Reparto calculado';
        this.actual = d;
        this.cargarDatos();
      },
      error: (err) => {
        this.guardando = false;
        this.error = this.mensajeError(err);
      },
    });
  }

  aplicar(): void {
    if (!this.actual) return;
    if (!window.confirm('¿Aplicar el reparto? Se crearán reservas DISTRITALES por distrito.')) return;
    this.error = '';
    this.guardando = true;
    this.service.aplicarTerritorial(this.actual.id).subscribe({
      next: (d) => {
        this.guardando = false;
        this.mensaje = 'Reparto aplicado (reservas DISTRITALES creadas)';
        this.actual = d;
        this.cargarDatos();
      },
      error: (err) => {
        this.guardando = false;
        this.error = this.mensajeError(err);
      },
    });
  }

  liberar(): void {
    if (!this.actual) return;
    if (!window.confirm('¿Liberar el reparto? Las reservas DISTRITALES volverán al disponible.')) return;
    this.error = '';
    this.guardando = true;
    this.service.liberarTerritorial(this.actual.id).subscribe({
      next: (d) => {
        this.guardando = false;
        this.mensaje = 'Reparto liberado (reservas LIBERADAS)';
        this.actual = d;
        this.cargarDatos();
      },
      error: (err) => {
        this.guardando = false;
        this.error = this.mensajeError(err);
      },
    });
  }

  // -- Helpers ---------------------------------------------------------------

  mensajeError(err: { error?: ApiErrorResponse }): string {
    const body = err?.error;
    const detail = body?.error && typeof body.error === 'object' && 'detail' in body.error
      ? (body.error as { detail?: string | string[] }).detail
      : undefined;
    if (Array.isArray(detail)) return detail.join(', ');
    if (detail) return detail;
    if (body?.code === 'BUDGET_EXCEEDED' && body.details) {
      return `Presupuesto insuficiente: solicitado ${body.details.requested}, disponible ${body.details.available}.`;
    }
    return 'Error de la operación';
  }

  badgeClass(estado: string): string {
    switch (estado) {
      case 'APLICADA': return 'badge-success';
      case 'CALCULADA': return 'badge-warning';
      default: return 'badge-info';
    }
  }
}

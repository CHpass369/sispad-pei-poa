import { ChangeDetectorRef, Component, OnDestroy, OnInit } from '@angular/core';
import { HttpErrorResponse } from '@angular/common/http';
import { Observable, Subject, finalize, takeUntil, TimeoutError, timeout } from 'rxjs';
import { AuthService } from '../../../core/services/auth.service';
import { Usuario } from '../../../core/models/usuario.model';
import { PermissionsService } from '../../../core/services/permissions.service';
import { GestionHabilitadaService } from '../../../core/services/gestion-habilitada.service';
import { BudgetService, FiscalYear } from './budget.service';

/** Estados en los que la gestión está disponible para formular su POA. */
const ESTADOS_EN_CURSO = ['HABILITADA', 'abierta', 'EN_FORMULACION', 'formulacion'];

export type AccionGestion = 'habilitar' | 'reabrir' | 'cerrar' | 'eliminar';

export interface ConfiguracionAccion {
  titulo: string;
  etiqueta: string;
  descripcion: (gestion: FiscalYear) => string;
  requiereMotivo: boolean;
  peligro: boolean;
}

const ACCIONES: Record<AccionGestion, ConfiguracionAccion> = {
  habilitar: {
    titulo: 'Habilitar gestión',
    etiqueta: 'Habilitar',
    descripcion: (g) =>
      `La gestión ${g.anio} queda abierta para fijar el techo directivo, ` +
      'distribuir el presupuesto y formular los POA.',
    requiereMotivo: false,
    peligro: false,
  },
  reabrir: {
    titulo: 'Reabrir gestión',
    etiqueta: 'Reabrir',
    descripcion: (g) =>
      `La gestión ${g.anio} volverá al estado Habilitada y su techo, ` +
      'distribución y POA podrán editarse otra vez.',
    requiereMotivo: true,
    peligro: false,
  },
  cerrar: {
    titulo: 'Cerrar gestión',
    etiqueta: 'Cerrar',
    descripcion: (g) =>
      `La gestión ${g.anio} deja de aceptar cambios en techo, distribución ` +
      'y POA. Se puede revertir con Reabrir.',
    requiereMotivo: false,
    peligro: true,
  },
  eliminar: {
    titulo: 'Eliminar gestión',
    etiqueta: 'Eliminar',
    descripcion: (g) =>
      `La gestión ${g.anio} se borra del sistema. Solo procede si no tiene ` +
      'ningún registro asociado; la acción no se puede deshacer.',
    requiereMotivo: false,
    peligro: true,
  },
};

@Component({
  standalone: false,
  selector: 'app-fiscal-year',
  templateUrl: './fiscal-year.component.html',
  styles: [`
    .page-header { margin-bottom: 1.5rem; }
    .text-secondary { color: var(--text-secondary); font-size: 0.875rem; }
    .campo label { display: block; font-size: 0.75rem; font-weight: 600; margin-bottom: 0.375rem; }
    .input { width: 100%; padding: 0.5rem; border: 1px solid var(--border); border-radius: 6px; font-size: 0.875rem; background: var(--surface); color: var(--text); }
    .input[readonly] { background: var(--primary-bg); color: var(--text-secondary); }
    textarea.input { min-height: 5rem; resize: vertical; font-family: inherit; }
    .btn-sm { background: var(--surface); border: 1px solid var(--border); }
    .btn-sm:hover { border-color: var(--primary); color: var(--primary); }
    .btn-danger { background: var(--mdc-red-50); color: var(--mdc-red-800); }
    .btn-danger:hover { background: var(--pip-gold-soft); }
    .data-table { width: 100%; border-collapse: collapse; background: var(--surface); border: 1px solid var(--border); border-radius: 8px; }
    .data-table th,
    .loading { text-align: center; padding: 2rem; color: var(--text-secondary); }
    .empty { text-align: center; padding: 2rem; color: var(--text-secondary); }
    .acciones { display: flex; gap: 0.5rem; flex-wrap: wrap; }
    .barra-superior { display: flex; align-items: center; justify-content: space-between; gap: 1rem; flex-wrap: wrap; margin-bottom: 1rem; }
    .resumen-ciclo { display: flex; align-items: center; gap: 0.5rem; padding: 0.5rem 0.875rem; border: 1px solid var(--border); border-left: 3px solid var(--primary); border-radius: 6px; background: var(--surface); font-size: 0.875rem; }
    .resumen-ciclo strong { color: var(--primary-dark); }
    .documento-enlace { color: var(--primary); text-decoration: underline; }
    .modal-overlay { position: fixed; inset: 0; z-index: 1000; display: flex; align-items: center; justify-content: center; padding: 1rem; background: rgba(19, 32, 25, 0.52); backdrop-filter: blur(5px); }
    .modal { width: min(100%, 680px); max-height: calc(100vh - 2rem); overflow-y: auto; padding: 1.5rem; border: 1px solid var(--border); border-radius: var(--radius); background: var(--surface); box-shadow: var(--shadow); }
    .confirmation-modal { width: min(100%, 480px); text-align: center; }
    .confirmation-check { display: flex; align-items: center; justify-content: center; width: 4rem; height: 4rem; margin: 0 auto 1rem; border: 3px solid var(--primary); border-radius: 50%; color: var(--primary); font-size: 2rem; font-weight: 700; line-height: 1; }
    .confirmation-check.peligro { border-color: var(--mdc-red-800); color: var(--mdc-red-800); }
    .confirmation-modal h3 { color: var(--primary-dark); font-size: 1.1rem; }
    .confirmation-message { margin-top: 0.75rem; color: var(--text-secondary); }
    .confirmation-actions { justify-content: center; }
    .confirmation-modal .campo { margin-top: 1.25rem; text-align: left; }
    .modal-header { display: flex; align-items: center; justify-content: space-between; gap: 1rem; margin-bottom: 1.25rem; }
    .modal-header h3 { color: var(--primary-dark); font-size: 1.1rem; }
    .modal-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 1rem; }
    .campo-completo { grid-column: 1 / -1; }
    .campo small { display: block; margin-top: 0.35rem; color: var(--text-secondary); font-size: 0.75rem; }
    .modal-acciones { display: flex; justify-content: flex-end; gap: 0.75rem; margin-top: 1.5rem; }
    .modal-error { margin-top: 1rem; }
    @media (max-width: 640px) { .modal-grid { grid-template-columns: 1fr; } .campo-completo { grid-column: auto; } }
  `],
})
export class FiscalYearComponent implements OnInit, OnDestroy {
  gestiones: FiscalYear[] = [];
  cargando = true;
  error = '';
  mensaje = '';
  modalAbierto = false;
  confirmacionAbierta = false;
  anioCreado: number | null = null;
  creando = false;
  archivo: File | null = null;
  fechaCargado = new Date();
  usuarioActual: Usuario | null = null;
  form: { anio: number | null; heredar_de: number | null } = {
    anio: null,
    heredar_de: null,
  };

  /** Acción del ciclo esperando confirmación en el modal. */
  accionPendiente: { tipo: AccionGestion; gestion: FiscalYear } | null = null;
  motivo = '';
  ejecutando = false;

  private readonly destroy$ = new Subject<void>();

  constructor(
    private service: BudgetService,
    private auth: AuthService,
    private permissions: PermissionsService,
    private cdr: ChangeDetectorRef,
    private gestionActiva: GestionHabilitadaService,
  ) {}

  get puedeGestionar(): boolean {
    return this.permissions.hasAnyCapability(['sis_poa.budget.manage']);
  }

  /**
   * Reabrir y eliminar son actos de gobernanza: revierten o borran un acto
   * formal del ciclo. Quedan en manos de la jefatura de POA y de
   * administración, que son quienes tienen esta capacidad.
   */
  get puedeGobernarGestion(): boolean {
    return this.permissions.hasAnyCapability(['sis_poa.budget.reopen']);
  }

  /** Gestión sobre la que hoy se formula, para orientar antes de operar. */
  get gestionEnCurso(): FiscalYear | null {
    return this.gestiones.find(g => ESTADOS_EN_CURSO.includes(g.estado)) ?? null;
  }

  ngOnInit(): void {
    this.auth.user$.pipe(takeUntil(this.destroy$)).subscribe(user => {
      this.usuarioActual = user;
      this.cdr.markForCheck();
    });
    this.cargar();
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
  }

  cargar(): void {
    this.cargando = true;
    this.error = '';
    this.cdr.markForCheck();
    this.service.listar().pipe(
      timeout(10_000),
      finalize(() => {
        this.cargando = false;
        this.cdr.markForCheck();
      }),
    ).subscribe({
      next: (data) => {
        this.gestiones = Array.isArray(data?.results) ? data.results : [];
        this.cdr.markForCheck();
      },
      error: (error: unknown) => {
        this.error = this.mensajeErrorCarga(error);
        this.cdr.markForCheck();
      },
    });
  }

  private mensajeErrorCarga(error: unknown): string {
    if (error instanceof TimeoutError) {
      return 'La solicitud tardó demasiado. Verifique la conexión e intente nuevamente.';
    }

    const status = error instanceof HttpErrorResponse
      ? error.status
      : error && typeof error === 'object' && 'status' in error
        ? error.status
        : undefined;

    if (status === 401) {
      return 'La sesión expiró o no es válida. Inicie sesión nuevamente para cargar las gestiones fiscales.';
    }

    return 'No se pudieron cargar las gestiones fiscales. Intente nuevamente.';
  }

  abrirModal(): void {
    this.modalAbierto = true;
    this.fechaCargado = new Date();
    this.error = '';
    this.cdr.markForCheck();
  }

  cancelar(): void {
    this.modalAbierto = false;
    this.creando = false;
    this.archivo = null;
    this.form = { anio: null, heredar_de: null };
    this.error = '';
    this.cdr.markForCheck();
  }

  cerrarConfirmacion(): void {
    this.confirmacionAbierta = false;
    this.anioCreado = null;
    this.cdr.markForCheck();
  }

  seleccionarArchivo(event: Event): void {
    const input = event.target as HTMLInputElement;
    this.archivo = input.files?.item(0) ?? null;
  }

  get archivoNombre(): string {
    return this.archivo?.name ?? 'Ningún archivo seleccionado';
  }

  get fechaInicioProgramada(): string {
    return this.formatearFechaAnual(this.form.anio, 1, 1);
  }

  get fechaCierreProgramada(): string {
    return this.formatearFechaAnual(this.form.anio, 12, 31);
  }

  get usuarioCargado(): string {
    if (!this.usuarioActual) return 'Cargando usuario...';
    const nombre = `${this.usuarioActual.first_name} ${this.usuarioActual.last_name}`.trim();
    return nombre || this.usuarioActual.email;
  }

  crear(): void {
    if (!this.form.anio) {
      this.error = 'El año de gestión es obligatorio';
      return;
    }
    if (this.gestiones.some(gestion => gestion.anio === this.form.anio)) {
      this.error = `Ya existe una gestión para el año ${this.form.anio}. Seleccione otro año.`;
      return;
    }
    if (!this.archivo) {
      this.error = 'El documento de habilitación es obligatorio';
      return;
    }

    const anio = this.form.anio;
    this.error = '';
    this.creando = true;
    this.cdr.markForCheck();
    this.service.crear({
      anio,
      heredar_de: this.form.heredar_de,
      documento_habilitacion: this.archivo,
    }).pipe(
      timeout(15_000),
      finalize(() => {
        this.creando = false;
        this.cdr.markForCheck();
      }),
    ).subscribe({
      next: (gestionCreada) => {
        this.mensaje = '';
        this.cancelar();
        this.anioCreado = gestionCreada?.anio ?? anio;
        this.confirmacionAbierta = true;
        this.cdr.markForCheck();
        this.cargar();
      },
      error: (error: unknown) => {
        this.error = this.mensajeErrorCreacion(error);
        this.cdr.markForCheck();
      },
    });
  }

  private mensajeErrorCreacion(error: unknown): string {
    if (error instanceof TimeoutError) {
      return 'La creación tardó demasiado. Verifique la conexión e intente nuevamente.';
    }
    return this.detalleDelError(error)
      ?? 'No se pudo crear la gestión. Verifique los datos e intente nuevamente.';
  }

  /** Mensaje que ya trae el backend, sin el prefijo del interceptor. */
  private detalleDelError(error: unknown): string | null {
    if (error && typeof error === 'object' && 'message' in error) {
      const message = (error as { message?: unknown }).message;
      if (typeof message === 'string' && message.trim()) {
        return message.replace(/^detail:\s*/i, '').trim();
      }
    }
    return null;
  }

  private formatearFechaAnual(anio: number | null, mes: number, dia: number): string {
    if (!anio) return '—';
    return `${String(dia).padStart(2, '0')}/${String(mes).padStart(2, '0')}/${anio}`;
  }

  // -- Acciones del ciclo ----------------------------------------------------

  pedirConfirmacion(tipo: AccionGestion, gestion: FiscalYear): void {
    this.accionPendiente = { tipo, gestion };
    this.motivo = '';
    this.error = '';
    this.mensaje = '';
    this.cdr.markForCheck();
  }

  cancelarAccion(): void {
    this.accionPendiente = null;
    this.motivo = '';
    this.ejecutando = false;
    this.cdr.markForCheck();
  }

  get accionActual(): ConfiguracionAccion | null {
    return this.accionPendiente ? ACCIONES[this.accionPendiente.tipo] : null;
  }

  get confirmacionDeshabilitada(): boolean {
    const accion = this.accionActual;
    if (!accion) return true;
    return this.ejecutando || (accion.requiereMotivo && !this.motivo.trim());
  }

  confirmarAccion(): void {
    const pendiente = this.accionPendiente;
    if (!pendiente || this.confirmacionDeshabilitada) return;

    const { tipo, gestion } = pendiente;
    this.error = '';
    this.ejecutando = true;
    this.cdr.markForCheck();

    this.peticionDeAccion(tipo, gestion).pipe(
      timeout(15_000),
      finalize(() => {
        this.ejecutando = false;
        this.cdr.markForCheck();
      }),
    ).subscribe({
      next: () => {
        this.mensaje = this.mensajeExito(tipo, gestion);
        this.accionPendiente = null;
        this.motivo = '';
        this.cdr.markForCheck();
        this.refrescarCandado();
        this.cargar();
      },
      error: (error: unknown) => {
        this.error = this.mensajeErrorAccion(tipo, gestion, error);
        this.cdr.markForCheck();
      },
    });
  }

  /**
   * Vuelve a leer el candado tras habilitar, reabrir, cerrar o eliminar.
   *
   * Las cuatro acciones lo mueven. Sin esto el resto de la plataforma
   * --sidebar, encabezado y cada módulo de SIS-POA-- sigue operando sobre la
   * gestión anterior hasta que alguien recargue el navegador.
   */
  private refrescarCandado(): void {
    this.gestionActiva.refrescar().subscribe({
      next: () => this.cdr.markForCheck(),
      error: () => undefined,
    });
  }

  private peticionDeAccion(tipo: AccionGestion, gestion: FiscalYear): Observable<unknown> {
    switch (tipo) {
      case 'habilitar':
        return this.service.habilitar(gestion.id);
      case 'reabrir':
        return this.service.reabrir(gestion.id, this.motivo.trim());
      case 'cerrar':
        return this.service.cerrar(gestion.id);
      case 'eliminar':
        return this.service.eliminar(gestion.id);
    }
  }

  private mensajeExito(tipo: AccionGestion, gestion: FiscalYear): string {
    switch (tipo) {
      case 'habilitar':
        return `Gestión ${gestion.anio} habilitada`;
      case 'reabrir':
        return `Gestión ${gestion.anio} reabierta`;
      case 'cerrar':
        return `Gestión ${gestion.anio} cerrada`;
      case 'eliminar':
        return `Gestión ${gestion.anio} eliminada`;
    }
  }

  private mensajeErrorAccion(
    tipo: AccionGestion, gestion: FiscalYear, error: unknown,
  ): string {
    if (error instanceof TimeoutError) {
      return 'La operación tardó demasiado. Verifique la conexión e intente nuevamente.';
    }
    // El backend explica por qué no procede (estado inválido, dependencias);
    // ese motivo vale más que un texto genérico.
    return this.detalleDelError(error)
      ?? `No se pudo ${ACCIONES[tipo].etiqueta.toLowerCase()} la gestión ${gestion.anio}.`;
  }

  puedeHabilitar(gestion: FiscalYear): boolean {
    return this.puedeGestionar && gestion.puede_habilitar === true;
  }

  puedeReabrir(gestion: FiscalYear): boolean {
    return this.puedeGobernarGestion && gestion.puede_reabrir === true;
  }

  puedeCerrar(gestion: FiscalYear): boolean {
    return this.puedeGestionar && gestion.puede_cerrar === true;
  }

  puedeEliminar(gestion: FiscalYear): boolean {
    return this.puedeGobernarGestion && gestion.puede_eliminar === true;
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

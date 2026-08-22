import { ChangeDetectorRef, Component, OnDestroy, OnInit } from '@angular/core';
import { HttpErrorResponse } from '@angular/common/http';
import { Subject, finalize, takeUntil, TimeoutError, timeout } from 'rxjs';
import { AuthService } from '../../../core/services/auth.service';
import { Usuario } from '../../../core/models/usuario.model';
import { PermissionsService } from '../../../core/services/permissions.service';
import { GestionHabilitadaService } from '../../../core/services/gestion-habilitada.service';
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
    .campo label { display: block; font-size: 0.75rem; font-weight: 600; margin-bottom: 0.375rem; }
    .input { width: 100%; padding: 0.5rem; border: 1px solid var(--border); border-radius: 6px; font-size: 0.875rem; background: var(--surface); color: var(--text); }
    .input[readonly] { background: var(--primary-bg); color: var(--text-secondary); }
    .btn-sm { background: var(--surface); border: 1px solid var(--border); }
    .btn-sm:hover { border-color: var(--primary); color: var(--primary); }
    .btn-danger { background: var(--mdc-red-50); color: var(--mdc-red-800); }
    .btn-danger:hover { background: var(--pip-gold-soft); }
    .data-table { width: 100%; border-collapse: collapse; background: var(--surface); border: 1px solid var(--border); border-radius: 8px; }
    .data-table th, 
    .loading { text-align: center; padding: 2rem; color: var(--text-secondary); }
    .empty { text-align: center; padding: 2rem; color: var(--text-secondary); }
    .acciones { display: flex; gap: 0.5rem; }
    .modal-overlay { position: fixed; inset: 0; z-index: 1000; display: flex; align-items: center; justify-content: center; padding: 1rem; background: rgba(19, 32, 25, 0.52); backdrop-filter: blur(5px); }
    .modal { width: min(100%, 680px); max-height: calc(100vh - 2rem); overflow-y: auto; padding: 1.5rem; border: 1px solid var(--border); border-radius: var(--radius); background: var(--surface); box-shadow: var(--shadow); }
    .confirmation-modal { width: min(100%, 420px); text-align: center; }
    .confirmation-check { display: flex; align-items: center; justify-content: center; width: 4rem; height: 4rem; margin: 0 auto 1rem; border: 3px solid var(--primary); border-radius: 50%; color: var(--primary); font-size: 2rem; font-weight: 700; line-height: 1; }
    .confirmation-modal h3 { color: var(--primary-dark); font-size: 1.1rem; }
    .confirmation-message { margin-top: 0.75rem; color: var(--text-secondary); }
    .confirmation-actions { justify-content: center; }
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

    if (error && typeof error === 'object' && 'message' in error) {
      const message = error.message;
      if (typeof message === 'string' && message.trim()) {
        return message;
      }
    }

    return 'No se pudo crear la gestión. Verifique los datos e intente nuevamente.';
  }

  private formatearFechaAnual(anio: number | null, mes: number, dia: number): string {
    if (!anio) return '—';
    return `${String(dia).padStart(2, '0')}/${String(mes).padStart(2, '0')}/${anio}`;
  }

  habilitar(gestion: FiscalYear): void {
    this.error = '';
    this.cdr.markForCheck();
    this.service.habilitar(gestion.id).subscribe({
      next: () => {
        this.mensaje = `Gestión ${gestion.anio} habilitada`;
        this.cdr.markForCheck();
        this.refrescarCandado();
        this.cargar();
      },
      error: () => {
        this.error = `No se pudo habilitar la gestión ${gestion.anio}`;
        this.cdr.markForCheck();
      },
    });
  }

  cerrar(gestion: FiscalYear): void {
    if (!confirm(`¿Cerrar la gestión ${gestion.anio}?`)) return;
    this.error = '';
    this.cdr.markForCheck();
    this.service.cerrar(gestion.id).subscribe({
      next: () => {
        this.mensaje = `Gestión ${gestion.anio} cerrada`;
        this.cdr.markForCheck();
        this.refrescarCandado();
        this.cargar();
      },
      error: () => {
        this.error = `No se pudo cerrar la gestión ${gestion.anio}`;
        this.cdr.markForCheck();
      },
    });
  }

  /**
   * Vuelve a leer el candado tras habilitar o cerrar.
   *
   * Sin esto el resto de la plataforma —sidebar, encabezado y cada módulo de
   * SIS-POA— sigue operando sobre la gestión anterior hasta que alguien
   * recargue el navegador.
   */
  private refrescarCandado(): void {
    this.gestionActiva.refrescar().subscribe({
      next: () => this.cdr.markForCheck(),
      error: () => undefined,
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

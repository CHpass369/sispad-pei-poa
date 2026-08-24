import { Component, OnInit } from '@angular/core';
import {
  Apertura,
  ApiErrorResponse,
  BudgetService,
  CatalogoOpciones,
  DistributionSummary,
  DistribucionVersion,
  ExpenseObject,
  CategoriaProgramaticaTecho,
  Reserva,
  ResumenApertura,
  ValidacionDistribucion,
} from './budget.service';
import { GestionHabilitadaService } from '../../../core/services/gestion-habilitada.service';

@Component({
  standalone: false,
  selector: 'app-distribution',
  templateUrl: './distribution.component.html',
  styles: [`
    .page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 1.5rem; flex-wrap: wrap; gap: 0.75rem; }
    .page-header h2 { margin: 0; }
    .cards-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 0.75rem; margin-bottom: 1.25rem; }
    .card-resumen { background: var(--surface); border: 1px solid var(--border); border-radius: 10px; padding: 0.875rem 1.125rem; }
    .card-resumen .etiqueta { font-size: 0.6875rem; text-transform: uppercase; letter-spacing: 0.05em; color: var(--text-secondary); }
    .card-resumen .valor { font-size: 1.125rem; font-weight: 700; margin-top: 0.25rem; }
    .card-resumen.destacada { border-color: var(--primary); background: #F4F8FD; }
    .card-resumen.resalta { border-color: var(--mdc-green-800); background: #F1F8F2; }
    .seccion { margin-top: 1.5rem; }
    .seccion h3 { font-size: 0.9375rem; margin-bottom: 0.75rem; }
    .data-table { width: 100%; border-collapse: collapse; background: var(--surface); border: 1px solid var(--border); border-radius: 8px; }
    .data-table th, 
    
    .monto-celda { text-align: right; white-space: nowrap; }
    .form-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 0.75rem; }
    .campo label { display: block; font-size: 0.75rem; font-weight: 600; margin-bottom: 0.375rem; }
    .input { padding: 0.5rem; border: 1px solid var(--border); border-radius: 6px; font-size: 0.875rem; min-width: 140px; width: 100%; box-sizing: border-box; }
    .fuentes-filas { margin-top: 0.75rem; }
    .fila-fuente { display: flex; gap: 0.5rem; align-items: flex-end; margin-bottom: 0.5rem; flex-wrap: wrap; }
    .btn-sm { background: var(--surface); border: 1px solid var(--border); }
    .btn-sm:hover { border-color: var(--primary); color: var(--primary); }
    .btn-danger { background: var(--mdc-red-50); color: var(--mdc-red-800); }
    .btn-danger:hover { background: #FFCDD2; }
    .btn-success { background: var(--mdc-green-800); color: white; }
    .btn-success:hover { background: var(--ok-tinta); }
    .btn-success:disabled { opacity: 0.5; cursor: not-allowed; }
    .acciones { display: flex; gap: 0.375rem; flex-wrap: wrap; }
    .alert-error { background: var(--mdc-red-50); color: var(--mdc-red-800); border-radius: 6px; padding: 0.625rem 0.875rem; margin: 0.75rem 0; font-size: 0.875rem; }
    .alert-success { background: var(--mdc-green-50); color: var(--mdc-green-800); border-radius: 6px; padding: 0.625rem 0.875rem; margin: 0.75rem 0; font-size: 0.875rem; }
    .loading, .empty { text-align: center; padding: 2rem; color: var(--text-secondary); }
    .tooltip-wrap { position: relative; display: inline-block; }
    .tooltip-wrap .tooltip-text { visibility: hidden; background: #333; color: #fff; text-align: center; border-radius: 4px; padding: 0.25rem 0.5rem; position: absolute; bottom: 125%; left: 50%; transform: translateX(-50%); white-space: nowrap; font-size: 0.75rem; z-index: 10; }
    .tooltip-wrap:hover .tooltip-text { visibility: visible; }
    .fila-seleccionable { cursor: pointer; }
    .fila-seleccionable:hover { background: #F4F8FD; }
    .fila-seleccionada { background: #E3F0FD !important; }
  `],
})
export class DistributionComponent implements OnInit {
  gestionSeleccionada: string | null = null;
  resumen: DistributionSummary | null = null;
  aperturas: Apertura[] = [];
  reservas: Reserva[] = [];
  versiones: DistribucionVersion[] = [];
  categorias: CategoriaProgramaticaTecho[] = [];
  opciones: CatalogoOpciones | null = null;

  cargando = false;
  guardando = false;
  error = '';
  mensaje = '';
  mostrarFormulario = false;
  editando: Apertura | null = null;

  nueva = {
    denominacion: '',
    categoria: null as number | null,
    distrito: null as string | null,
    da: null as string | null,
    ue: null as string | null,
    unidad_organizacional: null as string | null,
    proyecto_codigo: '',
    codigo_sisin: '',
    actividad_codigo: '',
    orden: 0,
  };
  filasFuentes: { fuente: string; organismo: string; monto: number | null }[] = [];
  formReserva = {
    fuente: null as string | null,
    organismo: null as string | null,
    tipo: 'OTRA',
    monto: null as number | null,
    motivo: '',
  };

  // -- Fijación de la distribución (Fase 7) ---------------------------------
  validacion: ValidacionDistribucion | null = null;
  observacionTexto = '';

  // -- Objetos del gasto por apertura (Fase 9) ------------------------------
  aperturaSeleccionada: Apertura | null = null;
  objetosGasto: ExpenseObject[] = [];
  resumenApertura: ResumenApertura | null = null;
  formObjeto = { objeto_gasto: null as string | null, monto: null as number | null };
  editandoObjeto: ExpenseObject | null = null;
  errorObjetos = '';
  guardandoObjeto = false;

  constructor(private service: BudgetService,
              private gestionActiva: GestionHabilitadaService) {}

  ngOnInit(): void {
    // Sin selector de gestión: SIS-POA opera sobre la habilitada y sobre
    // ninguna otra (ADR-007). El guard ya garantizó que existe.
    const habilitada = this.gestionActiva.gestion();
    if (!habilitada) {
      this.error = 'No hay una gestión fiscal habilitada.';
      this.cargando = false;
      return;
    }
    this.seleccionarGestion(habilitada.id);
  }

  /** Año de la gestión habilitada, para el encabezado. */
  get gestionAnio(): number | null {
    return this.gestionActiva.anio();
  }

  seleccionarGestion(id: string): void {
    this.gestionSeleccionada = id;
    this.cargarDatos();
  }

  cargarDatos(): void {
    if (!this.gestionSeleccionada) return;
    this.cargando = true;
    this.error = '';
    this.validacion = null;
    this.aperturaSeleccionada = null;
    this.objetosGasto = [];
    this.resumenApertura = null;
    this.editandoObjeto = null;
    this.errorObjetos = '';
    const gestion = this.gestionSeleccionada;
    this.service.resumenDistribucion(gestion).subscribe({
      next: (r) => { this.resumen = r; this.cargando = false; },
      error: () => { this.error = 'Error al cargar el resumen de distribución'; this.cargando = false; },
    });
    this.service.listarAperturas({ gestion }).subscribe({
      next: (r) => { this.aperturas = r.results; },
      error: () => { /* el resumen muestra el error principal */ },
    });
    this.service.listarReservas({ gestion }).subscribe({
      next: (r) => { this.reservas = r.results; },
      error: () => { /* no bloquea */ },
    });
    this.service.listarVersionesDistribucion(gestion).subscribe({
      next: (r) => { this.versiones = r; },
      error: () => { /* no bloquea */ },
    });
    this.service.listarCategorias({ gestion: Number(gestion) }).subscribe({
      next: (r) => { this.categorias = r.results; },
      error: () => { /* no bloquea */ },
    });
    this.service.opcionesCatalogo().subscribe({
      next: (o) => { this.opciones = o; },
      error: () => { /* no bloquea */ },
    });
  }

  // -- Formulario de apertura ------------------------------------------------

  abrirFormulario(): void {
    this.mostrarFormulario = true;
    this.editando = null;
    this.error = '';
    this.nueva = {
      denominacion: '', categoria: null, distrito: null, da: null,
      ue: null, unidad_organizacional: null, proyecto_codigo: '',
      codigo_sisin: '', actividad_codigo: '', orden: 0,
    };
    this.filasFuentes = [{ fuente: '', organismo: '', monto: null }];
  }

  editar(a: Apertura): void {
    this.mostrarFormulario = true;
    this.editando = a;
    this.error = '';
    this.nueva = {
      denominacion: a.denominacion,
      categoria: a.categoria,
      distrito: a.distrito,
      da: a.da,
      ue: a.ue,
      unidad_organizacional: a.unidad_organizacional,
      proyecto_codigo: a.proyecto_codigo,
      codigo_sisin: a.codigo_sisin,
      actividad_codigo: a.actividad_codigo,
      orden: a.orden,
    };
    this.filasFuentes = a.fuentes.map((f) => ({
      fuente: f.fuente ?? '',
      organismo: f.organismo ?? '',
      monto: f.monto ? parseFloat(f.monto) : null,
    }));
  }

  cerrarFormulario(): void {
    this.mostrarFormulario = false;
    this.editando = null;
  }

  agregarFilaFuente(): void {
    this.filasFuentes.push({ fuente: '', organismo: '', monto: null });
  }

  quitarFilaFuente(i: number): void {
    this.filasFuentes.splice(i, 1);
  }

  totalFormulario(): number {
    return this.filasFuentes.reduce((acc, f) => acc + (f.monto ?? 0), 0);
  }

  guardar(): void {
    if (!this.gestionSeleccionada || !this.nueva.denominacion) {
      this.error = 'La denominación es obligatoria';
      return;
    }
    const fuentes = this.filasFuentes
      .filter((f) => f.fuente && f.monto !== null && f.monto > 0)
      .map((f) => ({
        fuente: f.fuente,
        organismo: f.organismo || null,
        monto: f.monto as number,
      }));
    if (fuentes.length === 0) {
      this.error = 'Debe indicar al menos una fuente con monto mayor a 0';
      return;
    }
    this.error = '';
    this.guardando = true;
    const payload = {
      ...this.nueva,
      gestion: this.gestionSeleccionada,
      fuentes,
    };
    const operacion = this.editando
      ? this.service.actualizarApertura(this.editando.id, payload)
      : this.service.crearApertura(payload);
    operacion.subscribe({
      next: () => {
        this.guardando = false;
        this.mensaje = this.editando
          ? 'Apertura actualizada correctamente'
          : 'Apertura creada correctamente';
        this.mostrarFormulario = false;
        this.editando = null;
        this.cargarDatos();
      },
      error: (err) => {
        this.guardando = false;
        this.error = this.mensajeError(err);
      },
    });
  }

  eliminar(a: Apertura): void {
    if (!window.confirm(`¿Eliminar la apertura "${a.denominacion}"?`)) return;
    this.service.eliminarApertura(a.id).subscribe({
      next: () => {
        this.mensaje = 'Apertura eliminada';
        this.cargarDatos();
      },
      error: (err) => { this.error = this.mensajeError(err); },
    });
  }

  cerrar(a: Apertura): void {
    if (!window.confirm(`¿Cerrar la apertura "${a.denominacion}"?`)) return;
    this.service.cerrarApertura(a.id).subscribe({
      next: () => {
        this.mensaje = 'Apertura cerrada';
        this.cargarDatos();
      },
      error: (err) => { this.error = this.mensajeError(err); },
    });
  }

  // -- Reservas --------------------------------------------------------------

  guardarReserva(): void {
    if (!this.gestionSeleccionada || !this.formReserva.fuente || !this.formReserva.monto || this.formReserva.monto <= 0) {
      this.error = 'Fuente y monto (mayor a 0) son obligatorios para la reserva';
      return;
    }
    this.error = '';
    this.guardando = true;
    this.service.crearReserva({
      gestion: this.gestionSeleccionada,
      fuente: this.formReserva.fuente,
      organismo: this.formReserva.organismo || null,
      tipo: this.formReserva.tipo,
      monto: this.formReserva.monto,
      motivo: this.formReserva.motivo,
    }).subscribe({
      next: () => {
        this.guardando = false;
        this.mensaje = 'Reserva creada';
        this.formReserva = { fuente: null, organismo: null, tipo: 'OTRA', monto: null, motivo: '' };
        this.cargarDatos();
      },
      error: (err) => {
        this.guardando = false;
        this.error = this.mensajeError(err);
      },
    });
  }

  liberar(r: Reserva): void {
    if (!window.confirm(`¿Liberar la reserva de ${r.monto}?`)) return;
    this.service.liberarReserva(r.id).subscribe({
      next: () => {
        this.mensaje = 'Reserva liberada';
        this.cargarDatos();
      },
      error: (err) => { this.error = this.mensajeError(err); },
    });
  }

  // -- Fijación de la distribución (Fase 7) ---------------------------------

  /** Versión editable de mayor número (la no fijada); null si está fijada. */
  versionActiva(): DistribucionVersion | null {
    return this.versiones.find((v) => !v.inmutable) ?? null;
  }

  /** ¿La versión activa habilita la acción del ciclo (según su estado)? */
  puede(accion: string): boolean {
    const v = this.versionActiva();
    if (!v) return false;
    switch (accion) {
      case 'submit': return v.estado === 'BORRADOR';
      case 'observe': return v.estado === 'EN_REVISION';
      case 'approve': return v.estado === 'EN_REVISION';
      case 'freeze': return v.estado === 'APROBADO';
      default: return false;
    }
  }

  validar(): void {
    const v = this.versionActiva();
    if (!v) return;
    this.service.validarDistribucion(v.id).subscribe({
      next: (r) => { this.validacion = r; },
      error: (err) => { this.error = this.mensajeError(err); },
    });
  }

  enviarRevision(): void {
    const v = this.versionActiva();
    if (!v) return;
    this.service.submitDistribucion(v.id).subscribe({
      next: () => {
        this.mensaje = 'Distribución enviada a revisión';
        this.validacion = null;
        this.observacionTexto = '';
        this.cargarDatos();
      },
      error: (err) => { this.error = this.mensajeError(err); },
    });
  }

  observar(): void {
    const v = this.versionActiva();
    if (!v) return;
    if (!this.observacionTexto.trim()) {
      this.error = 'Debe indicar el motivo de la observación';
      return;
    }
    this.service.observarDistribucion(v.id, this.observacionTexto).subscribe({
      next: () => {
        this.mensaje = 'Distribución observada';
        this.validacion = null;
        this.observacionTexto = '';
        this.cargarDatos();
      },
      error: (err) => { this.error = this.mensajeError(err); },
    });
  }

  aprobar(): void {
    const v = this.versionActiva();
    if (!v) return;
    this.service.aprobarDistribucion(v.id).subscribe({
      next: () => {
        this.mensaje = 'Distribución aprobada';
        this.validacion = null;
        this.cargarDatos();
      },
      error: (err) => { this.error = this.mensajeError(err); },
    });
  }

  fijar(): void {
    const v = this.versionActiva();
    if (!v) return;
    if (!window.confirm(`¿Fijar la distribución v${v.numero}? Quedará inmutable con checksum.`)) return;
    this.service.fijarDistribucion(v.id, this.observacionTexto).subscribe({
      next: () => {
        this.mensaje = `Distribución v${v.numero} fijada (inmutable)`;
        this.validacion = null;
        this.observacionTexto = '';
        this.cargarDatos();
      },
      error: (err) => { this.error = this.mensajeError(err); },
    });
  }

  ajustar(v: DistribucionVersion): void {
    if (!window.confirm(`¿Crear la versión ${v.numero + 1} (BORRADOR) a partir de la fijada v${v.numero}?`)) return;
    this.service.ajusteDistribucion(v.id).subscribe({
      next: () => {
        this.mensaje = `Versión ${v.numero + 1} creada para el ajuste`;
        this.validacion = null;
        this.cargarDatos();
      },
      error: (err) => { this.error = this.mensajeError(err); },
    });
  }

  badgeEstadoVersion(estado: string): string {
    switch (estado) {
      case 'FIJADO':
      case 'APROBADO': return 'badge-success';
      case 'EN_REVISION': return 'badge-warning';
      case 'OBSERVADO': return 'badge-danger';
      default: return 'badge-info';
    }
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
      case 'CERRADA': return 'badge-warning';
      case 'BORRADOR': return 'badge-info';
      default: return 'badge-success';
    }
  }

  // -- Objetos del gasto por apertura (Fase 9, §90-91) ----------------------

  /** Selecciona/deselecciona una apertura y carga su panel de objetos. */
  seleccionarApertura(a: Apertura): void {
    if (this.aperturaSeleccionada?.id === a.id) {
      this.aperturaSeleccionada = null;
      this.objetosGasto = [];
      this.resumenApertura = null;
      this.editandoObjeto = null;
      this.errorObjetos = '';
      return;
    }
    this.aperturaSeleccionada = a;
    this.editandoObjeto = null;
    this.errorObjetos = '';
    this.formObjeto = { objeto_gasto: null, monto: null };
    this.service.listarObjetosGasto({ allocation: a.id }).subscribe({
      next: (r) => { this.objetosGasto = r.results; },
      error: () => { this.errorObjetos = 'Error al cargar los objetos del gasto'; },
    });
    this.service.resumenApertura(a.id).subscribe({
      next: (r) => { this.resumenApertura = r; },
      error: () => { this.errorObjetos = 'Error al cargar el resumen de la apertura'; },
    });
  }

  editarObjeto(o: ExpenseObject): void {
    this.editandoObjeto = o;
    this.formObjeto = {
      objeto_gasto: o.objeto_gasto,
      monto: o.monto ? parseFloat(o.monto) : null,
    };
    this.errorObjetos = '';
  }

  cancelarEdicionObjeto(): void {
    this.editandoObjeto = null;
    this.formObjeto = { objeto_gasto: null, monto: null };
    this.errorObjetos = '';
  }

  guardarObjeto(): void {
    if (!this.aperturaSeleccionada) return;
    const monto = this.formObjeto.monto;
    if (monto === null || monto <= 0) {
      this.errorObjetos = 'El monto debe ser mayor a 0';
      return;
    }
    if (!this.editandoObjeto && !this.formObjeto.objeto_gasto) {
      this.errorObjetos = 'Debe seleccionar un objeto del gasto';
      return;
    }
    this.errorObjetos = '';
    this.guardandoObjeto = true;
    const operacion = this.editandoObjeto
      ? this.service.actualizarObjetoGasto(this.editandoObjeto.id, monto)
      : this.service.programarObjetoGasto({
          allocation: this.aperturaSeleccionada.id,
          objeto_gasto: this.formObjeto.objeto_gasto as string,
          monto,
        });
    operacion.subscribe({
      next: () => {
        this.guardandoObjeto = false;
        this.editandoObjeto = null;
        this.formObjeto = { objeto_gasto: null, monto: null };
        this.cargarObjetosYResumen();
      },
      error: (err) => {
        this.guardandoObjeto = false;
        this.errorObjetos = this.mensajeError(err);
      },
    });
  }

  eliminarObjeto(o: ExpenseObject): void {
    if (!window.confirm(`¿Eliminar el objeto del gasto ${o.objeto_gasto_detalle?.codigo ?? ''} (${o.monto})?`)) return;
    this.service.eliminarObjetoGasto(o.id).subscribe({
      next: () => { this.cargarObjetosYResumen(); },
      error: (err) => { this.errorObjetos = this.mensajeError(err); },
    });
  }

  /** Recarga tabla de objetos + saldos del panel de la apertura. */
  private cargarObjetosYResumen(): void {
    if (!this.aperturaSeleccionada) return;
    this.errorObjetos = '';
    this.service.listarObjetosGasto({ allocation: this.aperturaSeleccionada.id }).subscribe({
      next: (r) => { this.objetosGasto = r.results; },
      error: () => { this.errorObjetos = 'Error al cargar los objetos del gasto'; },
    });
    this.service.resumenApertura(this.aperturaSeleccionada.id).subscribe({
      next: (r) => { this.resumenApertura = r; },
      error: () => { this.errorObjetos = 'Error al cargar el resumen de la apertura'; },
    });
  }
}

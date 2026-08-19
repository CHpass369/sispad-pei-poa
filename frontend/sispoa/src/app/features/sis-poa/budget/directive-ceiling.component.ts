import { Component, OnInit } from '@angular/core';
import { PermissionsService } from '../../../core/services/permissions.service';
import {
  BudgetDocument,
  BudgetService,
  CeilingResource,
  Composition,
  DirectiveCeiling,
  FiscalYear,
  MandatoryExpense,
} from './budget.service';

const ORIGENES = [
  { codigo: 'SIGEP', nombre: 'SIGEP' },
  { codigo: 'MUNICIPAL', nombre: 'Recursos propios municipales' },
  { codigo: 'SALDO', nombre: 'Saldo de caja y bancos' },
  { codigo: 'OTRO', nombre: 'Otros' },
];

const TIPOS_DOCUMENTO = [
  { codigo: 'REPORTE_SIGEP', nombre: 'Reporte SIGEP' },
  { codigo: 'NOTA_MEF', nombre: 'Nota MEF' },
  { codigo: 'RESOLUCION', nombre: 'Resolución' },
  { codigo: 'INFORME', nombre: 'Informe' },
  { codigo: 'PROYECCION_RECURSOS_PROPIOS', nombre: 'Proyección de recursos propios' },
  { codigo: 'OTRO', nombre: 'Otro' },
];

@Component({
  standalone: false,
  selector: 'app-directive-ceiling',
  templateUrl: './directive-ceiling.component.html',
  styles: [`
    .page-header { margin-bottom: 1.5rem; }
    .text-secondary { color: var(--text-secondary); font-size: 0.875rem; }
    .techo-card { background: var(--surface); border: 1px solid var(--border); border-radius: 10px; padding: 1rem 1.25rem; cursor: pointer; }
    .techo-card.seleccionada { border-color: var(--primary); box-shadow: 0 0 0 2px rgba(21, 101, 192, 0.15); }
    .composicion-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(170px, 1fr)); gap: 0.75rem; margin: 1rem 0; }
    .comp-card { background: var(--surface); border: 1px solid var(--border); border-radius: 8px; padding: 0.75rem 1rem; }
    .comp-card .etiqueta { font-size: 0.6875rem; text-transform: uppercase; letter-spacing: 0.05em; color: var(--text-secondary); }
    .comp-card .monto { font-size: 1.05rem; font-weight: 700; margin-top: 0.25rem; }
    .comp-card.destacada { border-color: var(--primary); background: #F4F8FD; }
    .comp-card.resalta { border-color: var(--mdc-green-800); background: #F1F8F2; }
    .data-table { width: 100%; border-collapse: collapse; background: var(--surface); border: 1px solid var(--border); border-radius: 8px; }
    .data-table th, 
    .form-inline { display: flex; gap: 0.75rem; flex-wrap: wrap; align-items: flex-end; }
    .campo label { display: block; font-size: 0.75rem; font-weight: 600; margin-bottom: 0.375rem; }
    .input { padding: 0.5rem; border: 1px solid var(--border); border-radius: 6px; font-size: 0.875rem; min-width: 140px; }
    .btn-sm { background: var(--surface); border: 1px solid var(--border); }
    .btn-sm:hover { border-color: var(--primary); color: var(--primary); }
    .btn-danger { background: var(--mdc-red-50); color: var(--mdc-red-800); }
    .btn-danger:hover { background: #FFCDD2; }
    .acciones { display: flex; gap: 0.5rem; flex-wrap: wrap; }
    .loading { text-align: center; padding: 2rem; color: var(--text-secondary); }
    .empty { text-align: center; padding: 2rem; color: var(--text-secondary); }
    .monto-celda { text-align: right; white-space: nowrap; }
    .seccion { margin-top: 1.5rem; }
    .seccion h3 { font-size: 0.9375rem; margin-bottom: 0.75rem; }
  `],
})
export class DirectiveCeilingComponent implements OnInit {
  techos: DirectiveCeiling[] = [];
  gestiones: FiscalYear[] = [];
  seleccionadoId: number | null = null;
  seleccion: DirectiveCeiling | null = null;
  composicion: Composition | null = null;
  recursos: CeilingResource[] = [];
  gastos: MandatoryExpense[] = [];
  documentos: BudgetDocument[] = [];
  cargando = true;
  error = '';
  mensaje = '';

  gestionNueva: string | null = null;
  formRecurso: { origen: string; concepto: string; monto: number | null } = {
    origen: 'SIGEP',
    concepto: '',
    monto: null,
  };
  formGasto: { programa: string; actividad: string; denominacion: string; monto: number | null } = {
    programa: '',
    actividad: '',
    denominacion: '',
    monto: null,
  };
  formDocumento: { tipo: string; fecha: string; archivo: File | null } = {
    tipo: 'REPORTE_SIGEP',
    fecha: '',
    archivo: null,
  };

  readonly origenes = ORIGENES;
  readonly tiposDocumento = TIPOS_DOCUMENTO;

  constructor(
    private service: BudgetService,
    private permissions: PermissionsService,
  ) {}

  get puedeGestionar(): boolean {
    return this.permissions.hasAnyCapability(['sis_poa.budget.manage']);
  }

  get puedeAprobar(): boolean {
    return this.permissions.hasAnyCapability(['sis_poa.budget.approve']);
  }

  get versionEditable(): boolean {
    const v = this.seleccion?.version;
    return !!v && !v.inmutable && v.estado !== 'FIJADO';
  }

  ngOnInit(): void {
    this.cargar();
  }

  cargar(): void {
    this.cargando = true;
    this.error = '';
    this.service.listarTechos().subscribe({
      next: (data) => {
        this.techos = data.results;
        this.cargando = false;
        if (this.techos.length > 0 && this.seleccionadoId === null) {
          this.seleccionar(this.techos[0]);
        } else if (this.seleccionadoId !== null) {
          this.refrescar();
        }
      },
      error: () => {
        this.error = 'Error al cargar los techos directivos';
        this.cargando = false;
      },
    });
    this.service.listar().subscribe({
      next: (data) => { this.gestiones = data.results; },
      error: () => { /* el error principal lo muestra listarTechos */ },
    });
  }

  seleccionar(techo: DirectiveCeiling): void {
    this.seleccionadoId = techo.id;
    this.refrescar();
  }

  refrescar(): void {
    if (this.seleccionadoId === null) return;
    this.error = '';
    this.service.obtenerTecho(this.seleccionadoId).subscribe({
      next: (techo) => {
        this.seleccion = techo;
        this.composicion = techo.composicion;
        this.recursos = techo.version?.recursos ?? [];
        this.gastos = techo.version?.gastos_obligatorios ?? [];
        this.cargarDocumentos();
      },
      error: () => {
        this.error = 'Error al cargar el detalle del techo';
      },
    });
  }

  cargarDocumentos(): void {
    if (!this.seleccion) return;
    this.service.listarDocumentos(this.seleccion.gestion).subscribe({
      next: (data) => { this.documentos = data.results; },
      error: () => { /* no bloquea el detalle */ },
    });
  }

  // -- Creación -------------------------------------------------------------

  crear(): void {
    if (!this.gestionNueva) {
      this.error = 'Seleccione una gestión para crear el techo';
      return;
    }
    this.error = '';
    this.service.crearTecho({ gestion: this.gestionNueva }).subscribe({
      next: (techo) => {
        this.mensaje = `Techo directivo creado para la gestión ${techo.gestion_anio}`;
        this.gestionNueva = null;
        this.cargar();
      },
      error: () => {
        this.error = 'No se pudo crear el techo (la gestión debe estar habilitada)';
      },
    });
  }

  // -- Acciones por estado ---------------------------------------------------

  enviar(): void {
    if (this.seleccionadoId === null) return;
    this.service.enviarRevision(this.seleccionadoId).subscribe({
      next: () => {
        this.mensaje = 'Techo enviado a revisión';
        this.refrescar();
      },
      error: () => { this.error = 'No se pudo enviar a revisión'; },
    });
  }

  observar(): void {
    if (this.seleccionadoId === null) return;
    const motivo = window.prompt('Motivo de la observación:');
    if (!motivo || !motivo.trim()) return;
    this.service.observarTecho(this.seleccionadoId, motivo.trim()).subscribe({
      next: () => {
        this.mensaje = 'Techo observado';
        this.refrescar();
      },
      error: () => { this.error = 'No se pudo observar el techo'; },
    });
  }

  aprobar(): void {
    if (this.seleccionadoId === null) return;
    this.service.aprobarTecho(this.seleccionadoId).subscribe({
      next: () => {
        this.mensaje = 'Techo aprobado';
        this.refrescar();
      },
      error: () => { this.error = 'No se pudo aprobar el techo'; },
    });
  }

  fijar(): void {
    if (this.seleccionadoId === null) return;
    this.service.fijarTecho(this.seleccionadoId).subscribe({
      next: () => {
        this.mensaje = 'Techo fijado (versión inmutable)';
        this.refrescar();
      },
      error: () => { this.error = 'No se pudo fijar el techo'; },
    });
  }

  // -- Recursos --------------------------------------------------------------

  registrarRecurso(): void {
    if (!this.seleccion?.version || !this.versionEditable) return;
    if (this.formRecurso.monto === null || this.formRecurso.monto < 0) {
      this.error = 'El monto es obligatorio y debe ser mayor o igual a 0';
      return;
    }
    this.error = '';
    this.service.crearRecurso({
      version: this.seleccion.version.id,
      origen: this.formRecurso.origen,
      concepto: this.formRecurso.concepto,
      monto: this.formRecurso.monto,
    }).subscribe({
      next: () => {
        this.mensaje = 'Recurso registrado';
        this.formRecurso = { origen: 'SIGEP', concepto: '', monto: null };
        this.refrescar();
      },
      error: () => { this.error = 'No se pudo registrar el recurso'; },
    });
  }

  eliminarRecurso(recurso: CeilingResource): void {
    if (!window.confirm(`¿Eliminar el recurso "${recurso.concepto}"?`)) return;
    this.service.eliminarRecurso(recurso.id).subscribe({
      next: () => {
        this.mensaje = 'Recurso eliminado';
        this.refrescar();
      },
      error: () => { this.error = 'No se pudo eliminar el recurso'; },
    });
  }

  // -- Gastos obligatorios ----------------------------------------------------

  registrarGasto(): void {
    if (!this.seleccion?.version || !this.versionEditable) return;
    if (this.formGasto.monto === null || this.formGasto.monto < 0) {
      this.error = 'El monto es obligatorio y debe ser mayor o igual a 0';
      return;
    }
    this.error = '';
    this.service.crearGasto({
      version: this.seleccion.version.id,
      programa: this.formGasto.programa,
      actividad: this.formGasto.actividad,
      denominacion: this.formGasto.denominacion,
      monto: this.formGasto.monto,
    }).subscribe({
      next: () => {
        this.mensaje = 'Gasto obligatorio registrado';
        this.formGasto = { programa: '', actividad: '', denominacion: '', monto: null };
        this.refrescar();
      },
      error: () => { this.error = 'No se pudo registrar el gasto obligatorio'; },
    });
  }

  eliminarGasto(gasto: MandatoryExpense): void {
    if (!window.confirm(`¿Eliminar el gasto "${gasto.denominacion}"?`)) return;
    this.service.eliminarGasto(gasto.id).subscribe({
      next: () => {
        this.mensaje = 'Gasto obligatorio eliminado';
        this.refrescar();
      },
      error: () => { this.error = 'No se pudo eliminar el gasto'; },
    });
  }

  // -- Documentos --------------------------------------------------------------

  onArchivoSeleccionado(event: Event): void {
    const input = event.target as HTMLInputElement;
    this.formDocumento.archivo = input.files?.length ? input.files[0] : null;
  }

  subirDocumento(): void {
    if (!this.seleccion) return;
    if (!this.formDocumento.archivo) {
      this.error = 'Seleccione un archivo para subir';
      return;
    }
    this.error = '';
    const fd = new FormData();
    fd.append('gestion', this.seleccion.gestion);
    fd.append('tipo', this.formDocumento.tipo);
    fd.append('archivo', this.formDocumento.archivo, this.formDocumento.archivo.name);
    if (this.formDocumento.fecha) {
      fd.append('fecha_documento', this.formDocumento.fecha);
    }
    this.service.subirDocumento(fd).subscribe({
      next: () => {
        this.mensaje = 'Documento subido';
        this.formDocumento = { tipo: 'REPORTE_SIGEP', fecha: '', archivo: null };
        this.cargarDocumentos();
      },
      error: () => { this.error = 'No se pudo subir el documento (máx 20 MB)'; },
    });
  }

  // -- Helpers de UI -----------------------------------------------------------

  esEstado(...estados: string[]): boolean {
    return !!this.seleccion && estados.includes(this.seleccion.estado);
  }

  badgeClass(estado: string): string {
    switch (estado) {
      case 'EN_REVISION':
      case 'APROBADO':
        return 'badge-warning';
      case 'OBSERVADO':
        return 'badge-danger';
      case 'FIJADO':
        return 'badge-success';
      default:
        return 'badge-info';
    }
  }

  totalPorOrigen(origen: string): string {
    if (!this.composicion) return '0.00';
    switch (origen) {
      case 'SIGEP': return this.composicion.sigep;
      case 'MUNICIPAL': return this.composicion.municipales;
      case 'SALDO': return this.composicion.saldos;
      case 'OTRO': return this.composicion.otros;
      default: return '0.00';
    }
  }
}

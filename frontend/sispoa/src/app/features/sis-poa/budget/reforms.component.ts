import { Component, OnInit } from '@angular/core';
import { Observable } from 'rxjs';
import {
  Allocation,
  ApiErrorResponse,
  BudgetService,
  CatalogoOpciones,
  FiscalYear,
  Reform,
  ReformInput,
  ReformMovementInput,
} from './budget.service';

interface FilaMovimiento {
  tipo: string;
  apertura_origen: number | null;
  apertura_destino: number | null;
  fuente: string | null;
  organismo: string | null;
  monto: number | null;
}

@Component({
  standalone: false,
  selector: 'app-reforms',
  templateUrl: './reforms.component.html',
  styles: [`
    .page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 1.5rem; flex-wrap: wrap; gap: 0.75rem; }
    .page-header h2 { margin: 0; }
    .seccion { margin-top: 1.5rem; }
    .seccion h3 { font-size: 0.9375rem; margin-bottom: 0.75rem; }
    .data-table { width: 100%; border-collapse: collapse; background: var(--surface); border: 1px solid var(--border); border-radius: 8px; }
    .data-table th, 
    
    .monto-celda { text-align: right; white-space: nowrap; }
    .form-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 0.75rem; }
    .campo label { display: block; font-size: 0.75rem; font-weight: 600; margin-bottom: 0.375rem; }
    .input { padding: 0.5rem; border: 1px solid var(--border); border-radius: 6px; font-size: 0.875rem; min-width: 140px; width: 100%; box-sizing: border-box; }
    .fila-mov { display: grid; grid-template-columns: repeat(auto-fit, minmax(140px, 1fr)); gap: 0.5rem; align-items: end; margin-bottom: 0.5rem; }
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
    .badge { display: inline-block; padding: 0.1875rem 0.5rem; border-radius: 999px; font-size: 0.6875rem; font-weight: 600; }
    .badge-borrador { background: #ECEFF1; color: #455A64; }
    .badge-revision { background: var(--mdc-amber-50); color: #E65100; }
    .badge-observada { background: var(--mdc-red-50); color: var(--mdc-red-800); }
    .badge-aprobada { background: var(--mdc-blue-50); color: var(--mdc-blue-800); }
    .badge-aplicada { background: var(--mdc-green-50); color: var(--mdc-green-800); }
    .badge-rechazada { background: #FBE9E7; color: #BF360C; }
    .fila-seleccionable { cursor: pointer; }
    .fila-seleccionable:hover { background: #F4F8FD; }
    .fila-seleccionada { background: #E3F0FD !important; }
    .detalle-saldos { display: inline-flex; gap: 0.75rem; font-size: 0.75rem; }
    .detalle-saldos .antes { color: var(--text-secondary); text-decoration: line-through; }
    .detalle-saldos .despues { color: var(--mdc-green-800); font-weight: 700; }
  `],
})
export class ReformsComponent implements OnInit {
  gestiones: FiscalYear[] = [];
  gestionSeleccionada: string | null = null;
  reforms: Reform[] = [];
  aperturas: Allocation[] = [];
  opciones: CatalogoOpciones | null = null;

  cargando = false;
  guardando = false;
  error = '';
  mensaje = '';
  mostrarFormulario = false;
  seleccionada: Reform | null = null;

  tiposReform = [
    'TRASPASO', 'INCREMENTO', 'DISMINUCION', 'NUEVA_APERTURA',
    'CIERRE_APERTURA', 'CAMBIO_FUENTE', 'AJUSTE_DISTRIBUCION',
  ];
  tiposMovimiento = [
    'TRASPASO', 'INCREMENTO', 'DISMINUCION', 'CAMBIO_FUENTE',
  ];

  nueva = {
    tipo: 'TRASPASO',
    motivo: '',
    resolucion: '',
  };
  filasMovimientos: FilaMovimiento[] = [];

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
        this.cargando = false;
        this.error = 'No se pudieron cargar las gestiones.';
      },
    });
  }

  seleccionarGestion(id: string | null): void {
    this.gestionSeleccionada = id;
    this.seleccionada = null;
    this.mostrarFormulario = false;
    this.error = '';
    this.mensaje = '';
    if (!id) { return; }
    this.cargando = true;
    this.service.listarReforms({ gestion: id }).subscribe({
      next: (data) => {
        this.reforms = data.results;
        this.cargando = false;
      },
      error: () => {
        this.cargando = false;
        this.error = 'No se pudieron cargar las reformulaciones.';
      },
    });
    this.service.listarAperturas({ gestion: id }).subscribe({
      next: (data) => { this.aperturas = data.results; },
      error: () => { /* las aperturas no bloquean la lista */ },
    });
    this.service.opcionesCatalogo().subscribe({
      next: (opciones) => { this.opciones = opciones; },
      error: () => { /* los catálogos no bloquean la lista */ },
    });
  }

  abrirFormulario(): void {
    this.error = '';
    this.mensaje = '';
    this.nueva = { tipo: 'TRASPASO', motivo: '', resolucion: '' };
    this.filasMovimientos = [this.filaVacia()];
    this.mostrarFormulario = true;
  }

  filaVacia(): FilaMovimiento {
    return {
      tipo: 'TRASPASO',
      apertura_origen: null,
      apertura_destino: null,
      fuente: null,
      organismo: null,
      monto: null,
    };
  }

  agregarMovimiento(): void {
    this.filasMovimientos.push(this.filaVacia());
  }

  quitarMovimiento(i: number): void {
    this.filasMovimientos.splice(i, 1);
    if (this.filasMovimientos.length === 0) {
      this.filasMovimientos.push(this.filaVacia());
    }
  }

  private _leerError(resp: ApiErrorResponse | { detail?: string | string[] }): string {
    const detalle = (resp as ApiErrorResponse)?.error?.detail
      ?? (resp as { detail?: string | string[] })?.detail;
    if (Array.isArray(detalle)) { return detalle.join(' · '); }
    if (typeof detalle === 'string') { return detalle; }
    const details = (resp as ApiErrorResponse)?.details;
    if (details?.requested) {
      return `BUDGET_EXCEEDED: pedido ${details.requested}, ` +
        `disponible ${details.available} ` +
        `(diferencia ${details.difference}).`;
    }
    return 'Error del servidor.';
  }

  guardarReform(): void {
    this.error = '';
    this.mensaje = '';
    const movimientos: ReformMovementInput[] = [];
    let invalido = '';
    for (let i = 0; i < this.filasMovimientos.length; i++) {
      const f = this.filasMovimientos[i];
      if (f.tipo === 'TRASPASO' && (!f.apertura_origen || !f.apertura_destino)) {
        invalido = `Movimiento ${i + 1}: el traspaso requiere origen y destino.`;
        break;
      }
      if (f.tipo === 'INCREMENTO' && !f.apertura_destino) {
        invalido = `Movimiento ${i + 1}: el incremento requiere destino.`;
        break;
      }
      if ((f.tipo === 'DISMINUCION' || f.tipo === 'CAMBIO_FUENTE') && !f.apertura_origen) {
        invalido = `Movimiento ${i + 1}: requiere apertura de origen.`;
        break;
      }
      if (!f.fuente || f.monto === null || f.monto <= 0) {
        invalido = `Movimiento ${i + 1}: indique fuente y monto mayor a 0.`;
        break;
      }
      movimientos.push({
        tipo: f.tipo,
        apertura_origen: f.apertura_origen,
        apertura_destino: f.apertura_destino,
        fuente: f.fuente,
        organismo: f.organismo,
        monto: f.monto,
      });
    }
    if (invalido) {
      this.error = invalido;
      return;
    }
    const data: ReformInput = {
      gestion: this.gestionSeleccionada!,
      tipo: this.nueva.tipo,
      motivo: this.nueva.motivo,
      resolucion: this.nueva.resolucion,
      movimientos,
    };
    this.guardando = true;
    this.service.crearReform(data).subscribe({
      next: (reform) => {
        this.guardando = false;
        this.mostrarFormulario = false;
        this.mensaje = `Reformulación ${reform.tipo_display} creada en BORRADOR.`;
        this.cargarReforms();
      },
      error: (resp) => {
        this.guardando = false;
        this.error = this._leerError(resp.error || resp);
      },
    });
  }

  private cargarReforms(): void {
    if (!this.gestionSeleccionada) { return; }
    this.service.listarReforms({ gestion: this.gestionSeleccionada }).subscribe({
      next: (data) => {
        this.reforms = data.results;
        if (this.seleccionada) {
          const actualizada = data.results.find(
            (r) => r.id === this.seleccionada!.id,
          );
          this.seleccionada = actualizada ?? null;
        }
      },
      error: () => { this.error = 'No se pudieron recargar las reformulaciones.'; },
    });
  }

  private _ejecutar(accion: (id: number) => Observable<Reform>,
                    ok: string): void {
    if (!this.seleccionada) { return; }
    const id = this.seleccionada.id;
    this.guardando = true;
    accion(id).subscribe({
      next: () => {
        this.guardando = false;
        this.mensaje = ok;
        this.error = '';
        this.cargarReforms();
      },
      error: (resp) => {
        this.guardando = false;
        this.error = this._leerError(resp.error || resp);
      },
    });
  }

  enviar(): void {
    this._ejecutar(
      (id) => this.service.submitReform(id),
      'Reformulación enviada a revisión.',
    );
  }

  revisar(): void {
    const motivo = window.prompt('Motivo de la observación:');
    if (motivo === null) { return; }
    if (!motivo.trim()) {
      this.error = 'Debe indicar el motivo de la observación.';
      return;
    }
    this._ejecutar(
      (id) => this.service.observarReform(id, motivo),
      'Reformulación observada.',
    );
  }

  aprobar(): void {
    this._ejecutar(
      (id) => this.service.aprobarReform(id),
      'Reformulación aprobada.',
    );
  }

  rechazar(): void {
    const motivo = window.prompt('Motivo del rechazo:');
    if (motivo === null) { return; }
    if (!motivo.trim()) {
      this.error = 'Debe indicar el motivo del rechazo.';
      return;
    }
    this._ejecutar(
      (id) => this.service.rechazarReform(id, motivo),
      'Reformulación rechazada.',
    );
  }

  aplicar(): void {
    if (!window.confirm(
      '¿Aplicar la reformulación? Los saldos se moverán en una sola ' +
      'transacción.',
    )) { return; }
    this._ejecutar(
      (id) => this.service.aplicarReform(id),
      'Reformulación aplicada: saldos actualizados.',
    );
  }

  verDetalle(reform: Reform): void {
    this.seleccionada = reform;
    this.error = '';
  }

  badges(): Record<string, string> {
    return {
      BORRADOR: 'badge-borrador',
      EN_REVISION: 'badge-revision',
      OBSERVADA: 'badge-observada',
      APROBADA: 'badge-aprobada',
      APLICADA: 'badge-aplicada',
      RECHAZADA: 'badge-rechazada',
    };
  }

  puedeEnviar(): boolean {
    return this.seleccionada !== null &&
      ['BORRADOR', 'OBSERVADA'].includes(this.seleccionada.estado);
  }

  puedeRevisar(): boolean {
    return this.seleccionada?.estado === 'EN_REVISION';
  }

  puedeAprobar(): boolean {
    return this.seleccionada?.estado === 'EN_REVISION';
  }

  puedeRechazar(): boolean {
    return this.seleccionada?.estado === 'EN_REVISION';
  }

  puedeAplicar(): boolean {
    return this.seleccionada?.estado === 'APROBADA';
  }

  nombreApertura(id: number | null): string {
    if (id === null) { return '—'; }
    const a = this.aperturas.find((x) => x.id === id);
    return a ? a.denominacion : `Apertura #${id}`;
  }

  nombreFuente(id: string | null): string {
    if (id === null || !this.opciones) { return '—'; }
    const f = this.opciones.fuentes.find((x) => x.id === id);
    return f ? `${f.codigo} · ${f.denominacion}` : '—';
  }
}

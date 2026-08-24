import { ChangeDetectorRef, Component, OnInit } from '@angular/core';
import { concatMap, from, toArray } from 'rxjs';
import { ApiService } from '../../core/services/api.service';
import { GestionHabilitadaService } from '../../core/services/gestion-habilitada.service';
import {
  CabeceraRecursos,
  FilaMatrizRecursos,
  Hallazgo,
  MESES,
  RequerimientoForm,
  cabeceraVacia,
  construirFilas,
  requerimientoVacio,
  tieneErrores,
  totalAnual,
  totalGeneral,
  validarMatriz,
} from './poau-recursos.model';

/**
 * Asistente de programación presupuestaria del POAU.
 *
 * Determina los requerimientos de bienes y servicios de una actividad del
 * POAU, su clasificación presupuestaria y el mes en que se necesita el pago
 * (RE-SPO, Artículo 14 inciso c).
 */
@Component({
  selector: 'app-poau-recursos-wizard',
  standalone: false,
  template: `
    <div class="rec-full">
      <div class="rec-header">
        <h1>POAU — PROGRAMACIÓN PRESUPUESTARIA</h1>
        <p>
          Requerimientos de la actividad: bien o servicio demandado, partida de gasto,
          fuente de financiamiento y mes en que se requiere el pago
        </p>
      </div>

      <div class="progress-bar-horizontal">
        <div *ngFor="let nv of pasos; let i = index" class="progress-step"
             [class.completed]="paso > i" [class.active]="paso === i" (click)="irAPaso(i)">
          <div class="step-circle">{{ paso > i ? '✓' : i + 1 }}</div>
          <div class="step-label">{{ nv }}</div>
        </div>
      </div>

      <div class="wizard-layout">
        <div class="wizard-main">

      <!-- PASO 0: ARTICULACIÓN -->
      <div *ngIf="paso === 0" class="step-content card">
        <h3>Paso 1: Actividad del POAU a presupuestar</h3>
        <p>
          Los requerimientos cuelgan de una actividad ya programada físicamente en el POAU.
          Elija la cadena y el asistente hereda su clasificación.
        </p>
        <div class="form-2col">
          <div class="field"><label>Gestión</label>
            <input [ngModel]="cabecera.gestion" name="gestion" type="number" class="form-control" readonly
                   title="La fija la habilitación de gestión fiscal"></div>
          <div class="field"><label>Acción de corto plazo</label>
            <select [(ngModel)]="accionSel" class="form-control" (change)="onAccion()">
              <option value="">Seleccione...</option>
              <option *ngFor="let a of acciones" [value]="a.id">
                {{ a.codigo_accion }} — {{ (a.denominacion || '') | slice:0:60 }}
              </option>
            </select>
          </div>
        </div>
        <div class="form-2col">
          <div class="field"><label>Operación</label>
            <select [(ngModel)]="operacionSel" class="form-control" (change)="onOperacion()"
                    [disabled]="!operacionesFiltradas.length">
              <option value="">Seleccione...</option>
              <option *ngFor="let o of operacionesFiltradas" [value]="o.id">
                {{ o.codigo_operacion }} — {{ (o.denominacion || '') | slice:0:60 }}
              </option>
            </select>
          </div>
          <div class="field"><label>Actividad</label>
            <select [(ngModel)]="actividadSel" class="form-control" (change)="onActividad()"
                    [disabled]="!actividadesFiltradas.length">
              <option value="">Seleccione...</option>
              <option *ngFor="let ac of actividadesFiltradas" [value]="ac.id">
                {{ ac.codigo_actividad }} — {{ (ac.denominacion || '') | slice:0:60 }}
              </option>
            </select>
          </div>
        </div>

        <div class="aviso-vacio" *ngIf="!cargando && !acciones.length">
          No hay acciones de corto plazo registradas. Formule primero el POA y el POAU.
          <a routerLink="/poau" class="btn btn-sm btn-primary">Ir a la formulación POAU</a>
        </div>

        <div class="heredado" *ngIf="cabecera.actividadId">
          <h4>Clasificación de la cadena</h4>
          <div class="form-2col">
            <div class="field"><label>Categoría programática</label>
              <input [(ngModel)]="cabecera.categoriaProgramatica" class="form-control"></div>
            <div class="field"><label>Denominación de la categoría</label>
              <input [(ngModel)]="cabecera.denominacionCategoria" class="form-control"></div>
          </div>
          <div class="form-3col">
            <div class="field"><label>Cargo del REACP</label>
              <input [(ngModel)]="cabecera.cargoReacp" class="form-control"></div>
            <div class="field"><label>DA — Dirección Administrativa</label>
              <input [(ngModel)]="cabecera.da" class="form-control" placeholder="Ej: 01"></div>
            <div class="field"><label>UE — Unidad Ejecutora</label>
              <input [(ngModel)]="cabecera.ue" class="form-control" placeholder="Ej: 001"></div>
          </div>
        </div>

        <div class="step-nav">
          <span></span>
          <button class="btn btn-primary" [disabled]="!cabecera.actividadId" (click)="paso = 1">
            Siguiente → Requerimientos
          </button>
        </div>
      </div>

      <!-- PASO 1: REQUERIMIENTOS -->
      <div *ngIf="paso === 1" class="step-content card">
        <h3>Paso 2: Bienes y servicios demandados</h3>
        <p>
          Para cada requerimiento: qué se necesita, con qué partida se paga, de qué fuente
          sale y en qué meses se ejecuta el gasto.
        </p>
        <div class="inline-actions">
          <button class="btn btn-accent btn-sm" (click)="agregar()">+ Agregar requerimiento</button>
          <span class="acumulado">Total programado: <strong>{{ moneda(total) }} Bs.</strong></span>
        </div>

        <div class="req-card" *ngFor="let r of requerimientos; let i = index">
          <div class="req-head">
            <span class="codigo">#{{ i + 1 }}</span>
            <span class="req-nombre">{{ r.bienServicio || 'Requerimiento sin denominar' }}</span>
            <button class="btn btn-sm btn-danger" (click)="quitar(i)">Quitar</button>
          </div>

          <div class="field"><label>Bien o servicio demandado</label>
            <input [(ngModel)]="r.bienServicio" class="form-control"
                   placeholder="Ej: Servicio de consultoría en línea"></div>

          <div class="form-3col">
            <div class="field"><label>Cod. partida de gastos</label>
              <input [(ngModel)]="r.codPartida" class="form-control" placeholder="Ej: 25200"></div>
            <div class="field"><label>Descripción de la partida</label>
              <input [(ngModel)]="r.descripcionPartida" class="form-control"></div>
            <div class="field"><label>Fecha en la que se requiere el pago</label>
              <select [(ngModel)]="r.fechaRequerimiento" class="form-control">
                <option value="">Mes estimado…</option>
                <option *ngFor="let mes of meses" [value]="mes">{{ mes | uppercase }}</option>
              </select>
            </div>
          </div>
          <div class="form-4col">
            <div class="field"><label>FTE — Fuente</label>
              <input [(ngModel)]="r.fuenteFinanciamiento" class="form-control" placeholder="Ej: 20"></div>
            <div class="field"><label>ORG — Organismo</label>
              <input [(ngModel)]="r.organismoFinanciador" class="form-control" placeholder="Ej: 230"></div>
            <div class="field"><label>Grupo de gasto</label>
              <input [(ngModel)]="r.grupoGasto" class="form-control" placeholder="Ej: 20000"></div>
            <div class="field"><label>Tipo de gasto</label>
              <input [(ngModel)]="r.tipoGasto" class="form-control" placeholder="Funcionamiento"></div>
          </div>
          <div class="form-2col">
            <div class="field"><label>Presupuesto programado gestión {{ cabecera.gestion }} (Bs.)</label>
              <input [(ngModel)]="r.presupuestoProgramado" type="number" class="form-control"></div>
            <div class="field"><label>Suma mensual (Bs.)</label>
              <input [ngModel]="totalDe(r)" class="form-control derivada" readonly></div>
          </div>

          <h5>Presupuesto programado mensual (Bs.)</h5>
          <div class="meses-grid">
            <div *ngFor="let mes of meses" class="field">
              <label>{{ mes | slice:0:3 | uppercase }}</label>
              <input [(ngModel)]="r.programacion[mes]" type="number" class="form-control">
            </div>
          </div>
          <div class="acciones-fila">
            <button class="btn btn-sm btn-heredar" (click)="repartirEnDoce(r)"
                    [disabled]="!r.presupuestoProgramado">
              ⇱ Repartir en 12 meses
            </button>
            <button class="btn btn-sm btn-heredar" (click)="cargarEnMesRequerido(r)"
                    [disabled]="!r.presupuestoProgramado || !r.fechaRequerimiento">
              ⇱ Cargar todo en {{ r.fechaRequerimiento || 'el mes requerido' }}
            </button>
          </div>

          <div class="field"><label>Medio de verificación (tipo de documento)</label>
            <input [(ngModel)]="r.medioVerificacion" class="form-control"
                   placeholder="Ej: Contrato, orden de compra, informe de conformidad"></div>
        </div>

        <div class="vacio-req" *ngIf="!requerimientos.length">
          Sin requerimientos no hay programación presupuestaria: agregue al menos uno.
        </div>

        <div class="step-nav">
          <button class="btn btn-outline" (click)="paso = 0">← Anterior</button>
          <button class="btn btn-primary" [disabled]="!requerimientos.length" (click)="paso = 2">
            Siguiente → Revisión
          </button>
        </div>
      </div>

      <!-- PASO 2: REVISIÓN -->
      <div *ngIf="paso === 2" class="step-content card">
        <h3>Paso 3: Revisión y registro</h3>
        <div class="resumen-grid">
          <div class="resumen-item"><span>Gestión</span><strong>{{ cabecera.gestion }}</strong></div>
          <div class="resumen-item"><span>Categoría programática</span><strong>{{ cabecera.categoriaProgramatica || '-' }}</strong></div>
          <div class="resumen-item"><span>DA / UE</span><strong>{{ cabecera.da || '-' }} / {{ cabecera.ue || '-' }}</strong></div>
          <div class="resumen-item"><span>Requerimientos</span><strong>{{ requerimientos.length }}</strong></div>
          <div class="resumen-item"><span>Total programado</span><strong>{{ moneda(total) }} Bs.</strong></div>
        </div>

        <div class="hallazgos" *ngIf="hallazgos.length">
          <h4>Observaciones metodológicas</h4>
          <ul>
            <li *ngFor="let h of hallazgos" [class.error]="h.severidad === 'error'"
                [class.aviso]="h.severidad === 'aviso'">
              <strong>{{ h.seccion }}:</strong> {{ h.mensaje }}
            </li>
          </ul>
        </div>

        <div class="step-nav">
          <button class="btn btn-outline" (click)="paso = 1">← Anterior</button>
          <button class="btn btn-success" [disabled]="bloqueado || guardando" (click)="guardar()">
            {{ guardando ? 'Registrando…' : '✓ Registrar programación presupuestaria' }}
          </button>
        </div>
        <div *ngIf="msg" class="msg-box" [class.error]="msgClass === 'error'"
             [class.exito]="msgClass === 'exito'">{{ msg }}</div>
      </div>

        </div>

        <app-control-metodologico [hallazgos]="hallazgos"
                                  fuente="Reglamento Específico SPO — Cuadro 4">
        </app-control-metodologico>
      </div>

      <app-poau-recursos-viewer [filas]="filas" [hallazgos]="hallazgos"
                                [gestion]="cabecera.gestion" [total]="total">
      </app-poau-recursos-viewer>
    </div>
  `,
  styles: [`
    .rec-full { max-width: var(--ancho-trabajo); margin: 0 auto; padding-bottom: 2rem; }
    .rec-header h1 { font-size: 1.35rem; color: var(--primary); }
    .rec-header p { color: var(--text-secondary); font-size: 0.8125rem; margin-bottom: 1rem; }

    .progress-bar-horizontal { display: flex; gap: 0; margin-bottom: 1.5rem; overflow-x: auto; }
    .progress-step { flex: 1; text-align: center; padding: 0.5rem 0.25rem; cursor: pointer; position: relative; min-width: 90px; }
    .progress-step::after { content: ''; position: absolute; top: 50%; right: -50%; width: 100%; height: 2px; background: var(--border); z-index: 0; }
    .progress-step:last-child::after { display: none; }
    .step-circle { width: 28px; height: 28px; border-radius: 50%; margin: 0 auto 0.25rem; display: flex; align-items: center; justify-content: center; font-weight: 700; font-size: 0.75rem; background: var(--border); color: var(--text-secondary); position: relative; z-index: 1; }
    .progress-step.active .step-circle { background: var(--primary); color: #fff; }
    .progress-step.completed .step-circle { background: var(--success); color: #fff; }
    .step-label { font-weight: 700; font-size: 0.6875rem; }

    .wizard-layout { display: grid; grid-template-columns: minmax(0, 1fr) 300px; gap: 1.25rem; align-items: start; }
    app-control-metodologico { position: sticky; top: var(--e-2); align-self: start; max-height: calc(100vh - 5rem); overflow-y: auto; }
    .wizard-main { min-width: 0; }
    @media (max-width: 1100px) { .wizard-layout { grid-template-columns: 1fr; } }

    .step-content { padding: 1.5rem; min-height: 300px; }
    .step-content h3 { font-size: 1.1rem; margin-bottom: 0.5rem; }
    .step-content h4 { font-size: 0.9rem; margin: 1rem 0 0.5rem; color: var(--text-secondary); }
    .step-content h5 { font-size: 0.8125rem; margin: 0.9rem 0 0.4rem; color: var(--primary); }
    .step-content p { color: var(--text-secondary); margin-bottom: 0.75rem; font-size: 0.8125rem; }

    .form-2col, .form-3col, .form-4col { display: grid; gap: 0.75rem; margin-bottom: 0.5rem; }
    .form-2col { grid-template-columns: repeat(auto-fit, minmax(260px, 1fr)); }
    .form-3col { grid-template-columns: repeat(auto-fit, minmax(230px, 1fr)); }
    .form-4col { grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); }
    .field { margin-bottom: 0.5rem; }
    .field label { display: block; font-size: 0.6875rem; font-weight: 500; color: var(--text-secondary); margin-bottom: 0.2rem; }
    .inline-actions { margin-bottom: 0.75rem; display: flex; align-items: center; gap: 1rem; flex-wrap: wrap; }
    .acumulado { font-size: 0.8125rem; color: var(--text-secondary); }
    .step-nav { display: flex; justify-content: space-between; margin-top: 1.25rem; padding-top: 0.75rem; border-top: 1px solid var(--border); }

    .meses-grid { display: grid; grid-template-columns: repeat(12, 1fr); gap: 0.3rem; margin-bottom: 0.5rem; }
    .meses-grid input { font-size: 0.6875rem; padding: 0.2rem 0.25rem; text-align: right; }
    .meses-grid label { font-size: 0.5625rem; text-align: center; }
    .acciones-fila { display: flex; gap: 0.5rem; flex-wrap: wrap; margin-bottom: 0.6rem; }
    .btn-heredar { background: transparent; border: 1px dashed var(--primary); color: var(--primary); border-radius: 4px; cursor: pointer; padding: 0.3rem 0.6rem; font-size: 0.6875rem; }
    .btn-heredar:hover:not([disabled]) { background: var(--ok-fondo); border-style: solid; }
    .btn-heredar[disabled] { opacity: 0.45; cursor: not-allowed; }
    .derivada { background: #F3F7F4; font-weight: 700; }

    .heredado { margin-top: 1rem; padding: 0.9rem; border: 1px solid var(--border); border-left: 4px solid var(--primary); border-radius: 6px; background: #F7FBF8; }
    .heredado h4 { margin-top: 0; }
    .aviso-vacio { margin-top: 1rem; padding: 0.9rem; background: var(--aviso-fondo); color: var(--aviso-tinta); border-radius: 6px; font-size: 0.8125rem; display: flex; align-items: center; gap: 0.75rem; flex-wrap: wrap; }

    .req-card { border: 1px solid var(--border); border-radius: 8px; padding: 1rem; margin-bottom: 1rem; }
    .req-head { display: flex; align-items: center; gap: 0.75rem; margin-bottom: 0.75rem; }
    .req-head .codigo { font-family: 'Courier New', monospace; font-weight: 800; color: var(--primary); }
    .req-nombre { flex: 1; font-size: 0.8125rem; font-weight: 600; }
    .vacio-req { padding: 1.5rem; text-align: center; color: var(--text-secondary); font-size: 0.8125rem; border: 1px dashed var(--border); border-radius: 8px; }

    .resumen-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(170px, 1fr)); gap: 0.75rem; margin-bottom: 1rem; }
    .resumen-item { padding: 0.75rem; border: 1px solid var(--border); border-radius: 6px; }
    .resumen-item span { display: block; font-size: 0.6875rem; color: var(--text-secondary); }
    .resumen-item strong { font-size: 0.8125rem; }

    .hallazgos ul { list-style: none; padding: 0; margin: 0; }
    .hallazgos li { padding: 0.4rem 0.6rem; border-radius: 6px; margin-bottom: 0.3rem; font-size: 0.75rem; }
    .hallazgos li.error { background: var(--error-fondo); color: var(--warn); }
    .hallazgos li.aviso { background: var(--aviso-fondo); color: var(--aviso-tinta); }

    .msg-box { margin-top: 0.75rem; padding: 0.5rem 0.75rem; border-radius: 6px; font-size: 0.8125rem; }
    .msg-box.error { background: var(--error-fondo); color: var(--warn); }
    .msg-box.exito { background: var(--ok-fondo); color: var(--success); }
    .btn-danger { background: transparent; border: 1px solid var(--warn); color: var(--warn); border-radius: 4px; cursor: pointer; padding: 0.2rem 0.5rem; font-size: 0.6875rem; }

    @media (max-width: 900px) { .meses-grid { grid-template-columns: repeat(4, 1fr); } .form-4col { grid-template-columns: 1fr 1fr; } }
    @media (max-width: 768px) { .form-2col, .form-3col, .form-4col { grid-template-columns: 1fr; } }
  `],
})
export class PoauRecursosWizardComponent implements OnInit {
  paso = 0;
  pasos = ['Actividad del POAU', 'Requerimientos', 'Registro'];
  meses = MESES;

  cabecera: CabeceraRecursos = cabeceraVacia();
  requerimientos: RequerimientoForm[] = [requerimientoVacio()];

  acciones: any[] = [];
  operaciones: any[] = [];
  actividades: any[] = [];
  accionSel = '';
  operacionSel = '';
  actividadSel = '';
  cargando = true;

  guardando = false;
  msg = '';
  msgClass = '';

  constructor(private api: ApiService, private cdr: ChangeDetectorRef,
              private gestionActiva: GestionHabilitadaService) {}

  ngOnInit(): void {
    // Los recursos del POAU son de la gestión habilitada (ADR-007).
    this.cabecera.gestion = this.gestionActiva.anio() ?? 0;
    this.cargar('/articulacion/acciones-poa/', v => { this.acciones = v; this.cargando = false; });
    this.cargar('/articulacion/operaciones/', v => { this.operaciones = v; });
    this.cargar('/articulacion/actividades/', v => { this.actividades = v; });
  }

  // --- Derivados ------------------------------------------------------------

  get operacionesFiltradas(): any[] {
    return this.operaciones.filter(o => o.accion_poa === this.cabecera.accionPoaId);
  }

  get actividadesFiltradas(): any[] {
    return this.actividades.filter(a => a.operacion === this.cabecera.operacionId);
  }

  get filas(): FilaMatrizRecursos[] {
    return construirFilas(this.cabecera, this.requerimientos);
  }

  get hallazgos(): Hallazgo[] {
    return validarMatriz(this.cabecera, this.requerimientos);
  }

  get bloqueado(): boolean { return tieneErrores(this.hallazgos); }
  get total(): number { return totalGeneral(this.requerimientos); }

  // --- Selección ------------------------------------------------------------

  irAPaso(p: number): void { if (p <= this.paso) this.paso = p; }

  onAccion(): void {
    const accion = this.acciones.find(a => a.id === this.accionSel);
    this.cabecera.accionPoaId = accion?.id || null;
    this.cabecera.codigoAccion = accion?.codigo_accion || '';
    this.cabecera.categoriaProgramatica = accion?.categoria_programatica || '';
    this.cabecera.cargoReacp = accion?.cargo_responsable || '';
    if (accion?.gestion) this.cabecera.gestion = accion.gestion;
    this.operacionSel = '';
    this.actividadSel = '';
    this.cabecera.operacionId = null;
    this.cabecera.actividadId = null;
  }

  onOperacion(): void {
    const operacion = this.operacionesFiltradas.find(o => o.id === this.operacionSel);
    this.cabecera.operacionId = operacion?.id || null;
    this.actividadSel = '';
    this.cabecera.actividadId = null;
  }

  onActividad(): void {
    const actividad = this.actividadesFiltradas.find(a => a.id === this.actividadSel);
    this.cabecera.actividadId = actividad?.id || null;
  }

  // --- Requerimientos -------------------------------------------------------

  agregar(): void { this.requerimientos.push(requerimientoVacio()); }
  quitar(i: number): void { this.requerimientos.splice(i, 1); }

  totalDe(r: RequerimientoForm): number { return totalAnual(r.programacion); }

  /** Reparte el presupuesto en doce cuotas, ajustando el redondeo en diciembre. */
  repartirEnDoce(r: RequerimientoForm): void {
    const monto = Number(r.presupuestoProgramado) || 0;
    if (!monto) return;
    const cuota = Math.floor((monto / 12) * 100) / 100;
    MESES.forEach(mes => { r.programacion[mes] = cuota; });
    const repartido = cuota * 12;
    r.programacion['DICIEMBRE'] = Math.round((cuota + (monto - repartido)) * 100) / 100;
  }

  /** Concentra todo el monto en el mes en que se requiere el pago. */
  cargarEnMesRequerido(r: RequerimientoForm): void {
    const monto = Number(r.presupuestoProgramado) || 0;
    if (!monto || !r.fechaRequerimiento) return;
    MESES.forEach(mes => { r.programacion[mes] = null; });
    r.programacion[r.fechaRequerimiento] = monto;
  }

  moneda(valor: number): string {
    return valor ? valor.toLocaleString('es-BO') : '0';
  }

  // --- Persistencia ---------------------------------------------------------

  guardar(): void {
    if (this.bloqueado || this.guardando) return;
    this.guardando = true;
    this.msg = 'Registrando la programación presupuestaria…';
    this.msgClass = '';

    from(this.requerimientos.map((r, i) => this.cuerpo(r, i)))
      .pipe(
        concatMap(cuerpo => this.api.post('/articulacion/asignaciones-gasto/', cuerpo)),
        toArray(),
      )
      .subscribe({
        next: () => {
          this.guardando = false;
          this.msg = `✅ Programación registrada: ${this.requerimientos.length} requerimiento(s) por ${this.moneda(this.total)} Bs.`;
          this.msgClass = 'exito';
          this.cdr.markForCheck();
        },
        error: (err: any) => {
          this.guardando = false;
          this.msg = `❌ ${this.detalleError(err)}`;
          this.msgClass = 'error';
          this.cdr.markForCheck();
        },
      });
  }

  private cuerpo(r: RequerimientoForm, indice: number): Record<string, unknown> {
    const segmentos = this.cabecera.categoriaProgramatica.split(/\s+/);
    return {
      codigo_asignacion: `${this.cabecera.codigoAccion}.G${indice + 1}`,
      gestion: Number(this.cabecera.gestion),
      accion_poa: this.cabecera.accionPoaId,
      operacion: this.cabecera.operacionId,
      actividad: this.cabecera.actividadId,
      categoria_programatica: this.cabecera.categoriaProgramatica,
      da: this.cabecera.da,
      ue: this.cabecera.ue,
      programa: segmentos[0] || '',
      proyecto_sisin: segmentos[1] || '',
      actividad_presup: segmentos[2] || '',
      cod_objeto_gasto: r.codPartida,
      descripcion_objeto: r.descripcionPartida || r.bienServicio,
      grupo_gasto: r.grupoGasto,
      tipo_gasto: r.tipoGasto,
      fuente_financiamiento: r.fuenteFinanciamiento,
      organismo_financiador: r.organismoFinanciador,
      monto_programado: totalAnual(r.programacion),
      monto_vigente: totalAnual(r.programacion),
      cargo_reacp: this.cabecera.cargoReacp,
      fecha_requerimiento: r.fechaRequerimiento,
      programacion_mensual: r.programacion,
      medio_verificacion: r.medioVerificacion,
      justificacion: r.bienServicio,
    };
  }

  private detalleError(err: any): string {
    const cuerpo = err?.error ?? err;
    if (cuerpo && typeof cuerpo === 'object') {
      const detalles = Object.entries(cuerpo).map(
        ([campo, valor]) => `${campo}: ${Array.isArray(valor) ? valor.join(', ') : valor}`,
      );
      if (detalles.length) return detalles.join(' · ');
    }
    return err?.message || 'No se pudo registrar la programación presupuestaria.';
  }

  private cargar(ruta: string, asignar: (valores: any[]) => void): void {
    this.api.get<any>(ruta).subscribe({
      next: (r: any) => { asignar(r?.results || (Array.isArray(r) ? r : [])); this.cdr.markForCheck(); },
      error: () => { asignar([]); this.cargando = false; this.cdr.markForCheck(); },
    });
  }
}

import { ChangeDetectorRef, Component, OnInit } from '@angular/core';
import { Observable, catchError, concatMap, from, map, of, switchMap, toArray } from 'rxjs';
import { ApiService } from '../../../core/services/api.service';
import {
  ANCHO_ACTIVIDAD,
  ANCHO_PROGRAMA,
  ANCHO_PROYECTO,
  CATEGORIAS_REFERENCIA,
  CategoriaProgramatica,
  categoriaProgramatica,
  etiquetaCategoria,
  normalizarSegmento,
} from './poa-catalogos';
import {
  AccionCortoPlazoForm,
  ArticulacionPeiPoa,
  FilaMatrizPoa,
  Hallazgo,
  accionVacia,
  articulacionVacia,
  codigoAccion,
  construirFilas,
  presupuestoTotal,
  tieneErrores,
  validarMatriz,
} from './poa-matriz.model';

/**
 * Asistente de formulación del POA (RE-SPO, Artículo 14).
 *
 * Parte de una acción institucional específica del PEI y programa sus acciones
 * de corto plazo para la gestión, proyectando todo sobre la matriz fusionada
 * de los Cuadros 1 y 2.
 */
@Component({
  selector: 'app-poa-wizard',
  standalone: false,
  template: `
    <div class="poa-full">
      <div class="poa-header">
        <h1>FORMULACIÓN POA — REGLAMENTO ESPECÍFICO SPO</h1>
        <p>
          Articulación POA – PEI y programación de acciones de corto plazo:
          Producto institucional del PEI → Acción de corto plazo → REACP y fechas
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

      <!-- PASO 0: ARTICULACIÓN CON EL PEI -->
      <div *ngIf="paso === 0" class="step-content card">
        <h3>Paso 1: Articulación con el PEI</h3>
        <p>
          El Artículo 13 obliga a que las acciones de corto plazo estén articuladas y
          concordantes con lo establecido en el PEI para el mismo período. Empiece por
          la acción institucional específica de origen.
        </p>
        <div class="form-2col">
          <div class="field"><label>Gestión fiscal a programar</label>
            <input [(ngModel)]="gestion" type="number" class="form-control"></div>
          <div class="field">
            <label>Acción institucional específica (producto institucional del PEI)</label>
            <select [(ngModel)]="productoSel" class="form-control" (change)="heredarDelPei()">
              <option value="">Seleccione...</option>
              <option *ngFor="let p of productosPei" [value]="p.id">
                {{ p.codigo_producto }} — {{ (p.denominacion || '') | slice:0:70 }}
              </option>
            </select>
          </div>
        </div>

        <div class="aviso-vacio" *ngIf="!cargandoPei && !productosPei.length">
          No hay productos institucionales registrados en el PEI todavía. Formule primero
          la Matriz PEI en SIS-PE: sin ella el POA no tiene de dónde colgarse.
          <a routerLink="/sis-pe/pei" class="btn btn-sm btn-primary">Ir a la Matriz PEI</a>
        </div>

        <div class="heredado" *ngIf="articulacion.productoPeiId">
          <h4>Heredado del PEI</h4>
          <div class="form-2col">
            <div class="field"><label>Código PEI</label>
              <input [(ngModel)]="articulacion.codigoPei" class="form-control" readonly></div>
            <div class="field"><label>Resultado institucional de origen</label>
              <input [ngModel]="articulacion.codigoResultadoPei" class="form-control" readonly></div>
          </div>
          <div class="field"><label>Acción institucional específica</label>
            <textarea [(ngModel)]="articulacion.accionInstitucionalEspecifica"
                      class="form-control" rows="2"></textarea></div>
          <div class="field"><label>Indicador de proceso</label>
            <input [(ngModel)]="articulacion.indicadorProceso" class="form-control"
                   placeholder="Indicador con el que se mide la acción institucional específica"></div>
        </div>

        <div class="step-nav">
          <span></span>
          <button class="btn btn-primary" [disabled]="!articulacion.productoPeiId" (click)="paso = 1">
            Siguiente → Área responsable
          </button>
        </div>
      </div>

      <!-- PASO 1: ÁREA RESPONSABLE -->
      <div *ngIf="paso === 1" class="step-content card">
        <h3>Paso 2: Área o unidad organizacional responsable</h3>
        <p>
          Es el área bajo cuya responsabilidad estará la acción institucional específica,
          y responde por cada una de las acciones de corto plazo que la componen.
        </p>
        <div class="form-2col">
          <div class="field">
            <label>Unidad organizacional del catálogo</label>
            <select [(ngModel)]="articulacion.unidadResponsableId" class="form-control"
                    (change)="onUnidadChange()">
              <option [ngValue]="null">Captura manual</option>
              <option *ngFor="let u of unidades" [ngValue]="u.id">
                {{ u.codigo ? u.codigo + ' — ' : '' }}{{ u.nombre || u.denominacion }}
              </option>
            </select>
          </div>
          <div class="field">
            <label>Área o unidad organizacional responsable</label>
            <input [(ngModel)]="articulacion.areaResponsable" class="form-control"
                   placeholder="Ej: Dirección de Infraestructura">
          </div>
        </div>
        <div class="step-nav">
          <button class="btn btn-outline" (click)="paso = 0">← Anterior</button>
          <button class="btn btn-primary" [disabled]="!articulacion.areaResponsable" (click)="paso = 2">
            Siguiente → Acciones de corto plazo
          </button>
        </div>
      </div>

      <!-- PASO 2: ACCIONES DE CORTO PLAZO -->
      <div *ngIf="paso === 2" class="step-content card">
        <h3>Paso 3: Programación de acciones de corto plazo</h3>
        <p>
          El REACP, junto a sus unidades ejecutoras, establece las fechas tomando en cuenta
          los periodos de ejecución, las prioridades, los riesgos, el presupuesto y la
          concurrencia de tareas paralelas.
        </p>
        <div class="inline-actions">
          <button class="btn btn-accent btn-sm" (click)="agregarAccion()">+ Agregar acción</button>
        </div>

        <div class="accion-card" *ngFor="let a of acciones; let i = index">
          <div class="accion-head">
            <span class="codigo">{{ codigoDeAccion(i) }}</span>
            <span class="accion-nombre">{{ a.denominacion || 'Acción sin denominar' }}</span>
            <button class="btn btn-sm btn-danger" (click)="quitarAccion(i)">Quitar</button>
          </div>

          <div class="field"><label>Acción de corto plazo gestión {{ gestion }}</label>
            <input [(ngModel)]="a.denominacion" class="form-control"
                   placeholder="Ej: Construcción de la red de alcantarillado del Distrito 4"></div>
          <div class="field"><label>Resultado esperado gestión {{ gestion }}</label>
            <textarea [(ngModel)]="a.resultadoEsperado" class="form-control" rows="2"
                      placeholder="Lo que se espera haber logrado al cierre de la gestión"></textarea></div>

          <h5>Categoría programática</h5>
          <div class="field atajo">
            <label>Combinaciones de referencia</label>
            <select class="form-control" [ngModel]="''" (ngModelChange)="aplicarCategoria(a, $event)">
              <option value="">Capturar a mano…</option>
              <option *ngFor="let c of categoriasReferencia" [ngValue]="c">{{ etiqueta(c) }}</option>
            </select>
          </div>
          <div class="form-4col">
            <div class="field"><label>Programa</label>
              <input [(ngModel)]="a.programa" class="form-control seg" maxlength="3"
                     (blur)="a.programa = segmento(a.programa, anchoPrograma)" placeholder="101"></div>
            <div class="field"><label>Proyecto</label>
              <input [(ngModel)]="a.proyecto" class="form-control seg" maxlength="1"
                     (blur)="a.proyecto = segmento(a.proyecto, anchoProyecto)" placeholder="0"></div>
            <div class="field"><label>Actividad</label>
              <input [(ngModel)]="a.actividad" class="form-control seg" maxlength="3"
                     (blur)="a.actividad = segmento(a.actividad, anchoActividad)" placeholder="023"></div>
            <div class="field"><label>Categoría programática</label>
              <input [ngModel]="categoria(a)" class="form-control seg derivada" readonly
                     placeholder="se arma sola"></div>
          </div>

          <div class="form-2col">
            <div class="field"><label>Presupuesto programado {{ gestion }} (Bs.)</label>
              <input [(ngModel)]="a.presupuestoProgramado" type="number" class="form-control"></div>
            <div class="field"><label>Cargo del REACP</label>
              <input [(ngModel)]="a.cargoReacp" class="form-control"
                     placeholder="Ej: Jefe de la Unidad de Obras Públicas"></div>
          </div>
          <div class="form-2col">
            <div class="field"><label>Fecha prevista de inicio</label>
              <input [(ngModel)]="a.fechaInicio" type="date" class="form-control"></div>
            <div class="field"><label>Fecha prevista de finalización</label>
              <input [(ngModel)]="a.fechaFin" type="date" class="form-control"></div>
          </div>
        </div>

        <div class="vacio-acciones" *ngIf="!acciones.length">
          Sin acciones de corto plazo no hay POA: agregue al menos una.
        </div>

        <div class="step-nav">
          <button class="btn btn-outline" (click)="paso = 1">← Anterior</button>
          <button class="btn btn-primary" [disabled]="!acciones.length" (click)="paso = 3">
            Siguiente → Revisión
          </button>
        </div>
      </div>

      <!-- PASO 3: REVISIÓN Y REGISTRO -->
      <div *ngIf="paso === 3" class="step-content card">
        <h3>Paso 4: Revisión y registro del POA</h3>
        <div class="resumen-grid">
          <div class="resumen-item"><span>Gestión</span><strong>{{ gestion }}</strong></div>
          <div class="resumen-item"><span>Código PEI</span><strong>{{ articulacion.codigoPei || '-' }}</strong></div>
          <div class="resumen-item"><span>Área responsable</span><strong>{{ articulacion.areaResponsable || '-' }}</strong></div>
          <div class="resumen-item"><span>Acciones de corto plazo</span><strong>{{ acciones.length }}</strong></div>
          <div class="resumen-item"><span>Presupuesto programado</span><strong>{{ moneda(total) }} Bs.</strong></div>
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
          <button class="btn btn-outline" (click)="paso = 2">← Anterior</button>
          <button class="btn btn-success" [disabled]="bloqueado || guardando" (click)="guardar()">
            {{ guardando ? 'Registrando…' : '✓ Registrar POA' }}
          </button>
        </div>
        <div *ngIf="msg" class="msg-box" [class.error]="msgClass === 'error'"
             [class.exito]="msgClass === 'exito'">{{ msg }}</div>
      </div>

        </div>

        <app-control-metodologico [hallazgos]="hallazgos"
                                  fuente="Reglamento Específico SPO — Cuadros 1 y 2">
        </app-control-metodologico>
      </div>

      <app-poa-matriz-viewer [filas]="filas" [hallazgos]="hallazgos"
                             [gestion]="gestion" [total]="total"></app-poa-matriz-viewer>
    </div>
  `,
  styles: [`
    .poa-full { max-width: 1200px; margin: 0 auto; padding-bottom: 2rem; }
    .poa-header h1 { font-size: 1.35rem; color: var(--primary); }
    .poa-header p { color: var(--text-secondary); font-size: 0.8125rem; margin-bottom: 1rem; }

    .progress-bar-horizontal { display: flex; gap: 0; margin-bottom: 1.5rem; overflow-x: auto; }
    .progress-step { flex: 1; text-align: center; padding: 0.5rem 0.25rem; cursor: pointer; position: relative; min-width: 80px; }
    .progress-step::after { content: ''; position: absolute; top: 50%; right: -50%; width: 100%; height: 2px; background: var(--border); z-index: 0; }
    .progress-step:last-child::after { display: none; }
    .step-circle { width: 28px; height: 28px; border-radius: 50%; margin: 0 auto 0.25rem; display: flex; align-items: center; justify-content: center; font-weight: 700; font-size: 0.75rem; background: var(--border); color: var(--text-secondary); position: relative; z-index: 1; }
    .progress-step.active .step-circle { background: var(--primary); color: #fff; }
    .progress-step.completed .step-circle { background: var(--success); color: #fff; }
    .step-label { font-weight: 700; font-size: 0.6875rem; }

    .wizard-layout { display: grid; grid-template-columns: minmax(0, 1fr) 300px; gap: 1.25rem; align-items: start; }
    .wizard-main { min-width: 0; }
    @media (max-width: 1100px) { .wizard-layout { grid-template-columns: 1fr; } }

    .step-content { padding: 1.5rem; min-height: 300px; }
    .step-content h3 { font-size: 1.1rem; margin-bottom: 0.5rem; }
    .step-content h4 { font-size: 0.9rem; margin: 1rem 0 0.5rem; color: var(--text-secondary); }
    .step-content p { color: var(--text-secondary); margin-bottom: 0.75rem; font-size: 0.8125rem; }

    .form-2col { display: grid; gap: 0.75rem; margin-bottom: 0.5rem; grid-template-columns: 1fr 1fr; }
    .form-4col { display: grid; gap: 0.75rem; margin-bottom: 0.5rem; grid-template-columns: repeat(4, 1fr); }
    .step-content h5 { font-size: 0.8125rem; margin: 0.9rem 0 0.4rem; color: var(--primary); }
    .atajo { max-width: 320px; }
    .seg { font-family: 'Courier New', monospace; font-weight: 700; text-align: center; letter-spacing: 0.06em; }
    .derivada { background: #F3F7F4; color: var(--primary-dark, #1B5E20); }
    .field { margin-bottom: 0.5rem; }
    .field label { display: block; font-size: 0.6875rem; font-weight: 500; color: var(--text-secondary); margin-bottom: 0.2rem; }
    .inline-actions { margin-bottom: 0.75rem; }
    .step-nav { display: flex; justify-content: space-between; margin-top: 1.25rem; padding-top: 0.75rem; border-top: 1px solid var(--border); }

    .heredado { margin-top: 1rem; padding: 0.9rem; border: 1px solid var(--border); border-left: 4px solid var(--primary); border-radius: 6px; background: #F7FBF8; }
    .heredado h4 { margin-top: 0; }
    .aviso-vacio { margin-top: 1rem; padding: 0.9rem; background: #FFF8E1; color: #8A6100; border-radius: 6px; font-size: 0.8125rem; display: flex; align-items: center; gap: 0.75rem; flex-wrap: wrap; }

    .accion-card { border: 1px solid var(--border); border-radius: 8px; padding: 1rem; margin-bottom: 1rem; }
    .accion-head { display: flex; align-items: center; gap: 0.75rem; margin-bottom: 0.75rem; }
    .accion-head .codigo { font-family: 'Courier New', monospace; font-weight: 800; color: var(--primary); }
    .accion-nombre { flex: 1; font-size: 0.8125rem; font-weight: 600; }
    .vacio-acciones { padding: 1.5rem; text-align: center; color: var(--text-secondary); font-size: 0.8125rem; border: 1px dashed var(--border); border-radius: 8px; }

    .resumen-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 0.75rem; margin-bottom: 1rem; }
    .resumen-item { padding: 0.75rem; border: 1px solid var(--border); border-radius: 6px; }
    .resumen-item span { display: block; font-size: 0.6875rem; color: var(--text-secondary); }
    .resumen-item strong { font-size: 0.8125rem; }

    .hallazgos ul { list-style: none; padding: 0; margin: 0; }
    .hallazgos li { padding: 0.4rem 0.6rem; border-radius: 6px; margin-bottom: 0.3rem; font-size: 0.75rem; }
    .hallazgos li.error { background: #FFEBEE; color: var(--warn); }
    .hallazgos li.aviso { background: #FFF8E1; color: #8A6100; }

    .msg-box { margin-top: 0.75rem; padding: 0.5rem 0.75rem; border-radius: 6px; font-size: 0.8125rem; }
    .msg-box.error { background: #FFEBEE; color: var(--warn); }
    .msg-box.exito { background: #E8F5E9; color: var(--success); }
    .btn-danger { background: transparent; border: 1px solid var(--warn); color: var(--warn); border-radius: 4px; cursor: pointer; padding: 0.2rem 0.5rem; font-size: 0.6875rem; }

    @media (max-width: 768px) { .form-2col, .form-4col { grid-template-columns: 1fr; } }
  `],
})
export class PoaWizardComponent implements OnInit {
  paso = 0;
  pasos = ['Articulación PEI', 'Área responsable', 'Acciones', 'Registro'];

  gestion = 2026;
  articulacion: ArticulacionPeiPoa = articulacionVacia();
  acciones: AccionCortoPlazoForm[] = [accionVacia()];

  productosPei: any[] = [];
  resultadosPei: any[] = [];
  unidades: any[] = [];
  productoSel = '';
  cargandoPei = true;
  /** Primer correlativo libre para esta acción institucional específica. */
  correlativoBase = 1;

  categoriasReferencia = CATEGORIAS_REFERENCIA;
  anchoPrograma = ANCHO_PROGRAMA;
  anchoProyecto = ANCHO_PROYECTO;
  anchoActividad = ANCHO_ACTIVIDAD;

  guardando = false;
  msg = '';
  msgClass = '';

  constructor(private api: ApiService, private cdr: ChangeDetectorRef) {}

  ngOnInit(): void {
    this.cargarProductosPei();
    this.cargarResultadosPei();
    this.cargarUnidades();
  }

  // --- Derivados ------------------------------------------------------------

  get filas(): FilaMatrizPoa[] {
    return construirFilas(this.articulacion, this.acciones, this.correlativoBase);
  }

  get hallazgos(): Hallazgo[] {
    return validarMatriz(this.articulacion, this.acciones, Number(this.gestion));
  }

  get bloqueado(): boolean {
    return tieneErrores(this.hallazgos);
  }

  get total(): number {
    return presupuestoTotal(this.acciones);
  }

  // --- Navegación y herencia ------------------------------------------------

  irAPaso(p: number): void {
    if (p <= this.paso) this.paso = p;
  }

  /** Los campos 1 a 3 tienen fuente PEI: se heredan del producto institucional. */
  heredarDelPei(): void {
    const producto = this.productosPei.find(p => p.id === this.productoSel);
    if (!producto) {
      this.articulacion.productoPeiId = null;
      return;
    }
    this.articulacion.productoPeiId = producto.id;
    this.articulacion.codigoPei = producto.codigo_producto || '';
    this.articulacion.accionInstitucionalEspecifica = producto.denominacion || '';

    const resultado = this.resultadosPei.find(r => r.id === producto.resultado_pei);
    this.articulacion.codigoResultadoPei = resultado?.codigo_resultado || '';
    this.articulacion.resultadoPei = resultado?.denominacion || '';

    this.cargarIndicadorProceso(producto.id);
    this.siguienteCorrelativo(producto.id).subscribe({
      next: correlativo => {
        this.correlativoBase = correlativo;
        this.cdr.markForCheck();
      },
      error: () => { this.correlativoBase = 1; },
    });
  }

  onUnidadChange(): void {
    const unidad = this.unidades.find(u => u.id === this.articulacion.unidadResponsableId);
    if (unidad) {
      this.articulacion.areaResponsable = unidad.nombre || unidad.denominacion || '';
    }
  }

  // --- Acciones -------------------------------------------------------------

  agregarAccion(): void {
    this.acciones.push(accionVacia());
  }

  quitarAccion(indice: number): void {
    this.acciones.splice(indice, 1);
  }

  codigoDeAccion(indice: number): string {
    return (
      codigoAccion(this.articulacion.codigoPei, this.correlativoBase - 1 + indice) ||
      `ACP.${indice + 1}`
    );
  }

  /**
   * El código de la acción de corto plazo es único en toda la tabla: si esta
   * acción institucional específica ya tiene acciones registradas, la
   * numeración continúa desde la última en lugar de reiniciar en 1.
   */
  private siguienteCorrelativo(productoId: string): Observable<number> {
    return this.accionesRegistradas(productoId).pipe(
      map((registradas: any[]) => {
        const prefijo = `${this.articulacion.codigoPei}.`;
        const usados = registradas
          .map((a: any) => String(a?.codigo_accion || ''))
          .filter((codigo: string) => codigo.startsWith(prefijo))
          .map((codigo: string) => Number(codigo.slice(prefijo.length).split('.')[0]))
          .filter((n: number) => Number.isFinite(n) && n > 0);
        return usados.length ? Math.max(...usados) + 1 : 1;
      }),
    );
  }

  /**
   * La API pagina de a 25 y no acepta `page_size`: hay que recorrer las
   * páginas para no subestimar el correlativo ya usado.
   */
  private accionesRegistradas(
    productoId: string,
    pagina = 1,
    acumulado: any[] = [],
  ): Observable<any[]> {
    return this.api
      .get<any>('/articulacion/acciones-poa/', { producto_pei: productoId, page: pagina })
      .pipe(
        switchMap((r: any) => {
          const lote = r?.results || (Array.isArray(r) ? r : []);
          const total = [...acumulado, ...lote];
          return r?.next ? this.accionesRegistradas(productoId, pagina + 1, total) : of(total);
        }),
        catchError(() => of(acumulado)),
      );
  }

  moneda(valor: number): string {
    return valor ? valor.toLocaleString('es-BO') : '0';
  }

  /** La categoría programática se deriva: nunca se captura directamente. */
  categoria(accion: AccionCortoPlazoForm): string {
    return categoriaProgramatica(accion);
  }

  etiqueta(categoria: CategoriaProgramatica): string {
    return etiquetaCategoria(categoria);
  }

  segmento(valor: string, ancho: number): string {
    return normalizarSegmento(valor, ancho);
  }

  aplicarCategoria(
    accion: AccionCortoPlazoForm,
    categoria: CategoriaProgramatica | '',
  ): void {
    if (!categoria) return;
    accion.programa = categoria.programa;
    accion.proyecto = categoria.proyecto;
    accion.actividad = categoria.actividad;
  }

  // --- Persistencia ---------------------------------------------------------

  guardar(): void {
    if (this.bloqueado || this.guardando) return;
    this.guardando = true;
    this.msg = 'Registrando el POA…';
    this.msgClass = '';

    const productoId = this.articulacion.productoPeiId;
    (productoId ? this.siguienteCorrelativo(productoId) : of(this.correlativoBase))
      .pipe(
        switchMap(correlativo => {
          this.correlativoBase = correlativo;
          return from(
            this.acciones.map((accion, indice) => this.cuerpoAccion(accion, indice)),
          ).pipe(
            concatMap(cuerpo => this.api.post('/articulacion/acciones-poa/', cuerpo)),
            toArray(),
          );
        }),
      )
      .subscribe({
        next: () => {
          this.guardando = false;
          this.msg = `✅ POA registrado: ${this.acciones.length} acción(es) de corto plazo articuladas a ${this.articulacion.codigoPei}.`;
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

  private cuerpoAccion(
    accion: AccionCortoPlazoForm,
    indice: number,
  ): Record<string, unknown> {
    return {
      codigo_accion: accion.codigo || this.codigoDeAccion(indice),
      denominacion: accion.denominacion,
      resultado_esperado: accion.resultadoEsperado,
      producto_pei: this.articulacion.productoPeiId,
      gestion: Number(this.gestion),
      indicador: this.articulacion.indicadorProceso,
      cargo_responsable: accion.cargoReacp,
      fecha_inicio: accion.fechaInicio || null,
      fecha_fin: accion.fechaFin || null,
      programa: normalizarSegmento(accion.programa, ANCHO_PROGRAMA),
      proyecto_sisin: normalizarSegmento(accion.proyecto, ANCHO_PROYECTO),
      actividad_presupuestaria: normalizarSegmento(accion.actividad, ANCHO_ACTIVIDAD),
      categoria_programatica: categoriaProgramatica(accion),
      presupuesto_programado: accion.presupuestoProgramado,
      unidad_responsable: this.articulacion.unidadResponsableId,
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
    return err?.message || 'No se pudo registrar el POA.';
  }

  // --- Carga de catálogos ---------------------------------------------------

  private cargarProductosPei(): void {
    this.api.get<any>('/articulacion/productos-pei/').subscribe({
      next: (r: any) => {
        this.productosPei = r.results || r || [];
        this.cargandoPei = false;
        this.cdr.markForCheck();
      },
      error: () => {
        this.productosPei = [];
        this.cargandoPei = false;
        this.cdr.markForCheck();
      },
    });
  }

  private cargarResultadosPei(): void {
    this.api.get<any>('/articulacion/resultados-pei/').subscribe({
      next: (r: any) => { this.resultadosPei = r.results || r || [];         this.cdr.markForCheck();
      },
      error: () => { this.resultadosPei = [];         this.cdr.markForCheck();
      },
    });
  }

  private cargarUnidades(): void {
    this.api.get<any>('/organizacion/unidades/').subscribe({
      next: (r: any) => { this.unidades = r.results || r || [];         this.cdr.markForCheck();
      },
      error: () => { this.unidades = [];         this.cdr.markForCheck();
      },
    });
  }

  /** El indicador de proceso sale del indicador registrado para el producto PEI. */
  private cargarIndicadorProceso(productoId: string): void {
    this.api.get<any>('/articulacion/indicadores/', { producto_pei: productoId }).subscribe({
      next: (r: any) => {
        const lista = r.results || r || [];
        if (lista.length && !this.articulacion.indicadorProceso) {
          this.articulacion.indicadorProceso = lista[0].indicador || '';
          this.cdr.markForCheck();
        }
      },
      error: () => { /* el indicador se puede capturar a mano */ },
    });
  }
}

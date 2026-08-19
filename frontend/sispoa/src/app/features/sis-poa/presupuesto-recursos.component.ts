import { ChangeDetectorRef, Component, OnInit } from '@angular/core';
import { finalize, forkJoin } from 'rxjs';
import { HttpClient } from '@angular/common/http';
import { BudgetService, FilaRecurso, PresupuestoRecursos } from './budget/budget.service';

/**
 * Presupuesto General de Recursos de la gestión.
 *
 * Es el techo directivo: se fija después de habilitar el año fiscal y es la
 * base sobre la que después se programan los gastos por fuente de
 * financiamiento y organismo financiador. Reproduce el reporte oficial —
 * rubros agrupadores con sus componentes y el corte corriente/inversión— y
 * monta encima el circuito de revisión que el backend ya implementa:
 * borrador → en revisión → aprobado → fijado.
 */
@Component({
  selector: 'app-presupuesto-recursos',
  standalone: false,
  template: `
    <div class="recursos lienzo lienzo-datos">
      <div class="encabezado-pantalla">
        <div>
          <h2>Presupuesto General de Recursos</h2>
          <p class="sub">
            Techo directivo de la gestión {{ datos?.gestion || '—' }}. Sobre estos montos
            y sus fuentes de financiamiento se programa después el gasto.
          </p>
        </div>
        <div class="encabezado-acciones">
          <span class="pastilla-estado" [ngClass]="claseEstado()">{{ etiquetaEstado() }}</span>
          <button class="btn btn-outline btn-sm" (click)="cargar()" [disabled]="cargando">
            Actualizar
          </button>
          <button class="btn btn-primary btn-sm" *ngIf="datos?.editable && !editando"
                  (click)="entrarAEdicion()">Editar montos</button>
          <button class="btn btn-outline btn-sm" *ngIf="editando"
                  (click)="cancelarEdicion()" [disabled]="guardando">Cancelar</button>
          <button class="btn btn-accent btn-sm" *ngIf="editando"
                  (click)="guardar()" [disabled]="guardando || !hayCambios()">
            {{ guardando ? 'Guardando…' : 'Guardar cambios (' + cantidadCambios() + ')' }}
          </button>
        </div>
      </div>

      <div class="msg-box error" *ngIf="error">{{ error }}</div>

      <div class="sin-datos" *ngIf="cargando">
        <div class="esqueleto" style="width:280px"></div>
        <span>Cargando el presupuesto de recursos…</span>
      </div>

      <ng-container *ngIf="!cargando && datos">
        <div class="tabla-caja">
          <table class="tabla tabla-compacta">
            <thead>
              <tr>
                <th rowspan="2" class="col-descripcion">Descripción</th>
                <th rowspan="2">FF/OF</th>
                <th rowspan="2" class="num">Total</th>
                <th rowspan="2" class="num">%</th>
                <th colspan="4" class="grupo-distribucion">Distribución de recursos</th>
                <th rowspan="2" class="col-acciones" *ngIf="editando">Acciones</th>
              </tr>
              <tr>
                <th class="num">Gastos corrientes</th>
                <th class="num">%</th>
                <th class="num">Gastos de inversión</th>
                <th class="num">%</th>
                <th class="col-acciones" *ngIf="editando"></th>
              </tr>
            </thead>
            <tbody>
              <ng-container *ngFor="let rubro of datos.rubros">
                <tr class="fila-rubro">
                  <td class="col-descripcion"><strong>{{ rubro.concepto }}</strong></td>
                  <td class="cod">
                    <span *ngIf="!editando">{{ rubro.ff_of || '—' }}</span>
                    <div class="par-clasificador" *ngIf="editando">
                      <select class="celda-sel" [value]="valor(rubro, 'fuente')"
                              (change)="editar(rubro, 'fuente', $event)"
                              title="Fuente de financiamiento">
                        <option value="">FF</option>
                        <option *ngFor="let f of fuentes" [value]="f.id">{{ f.codigo }}</option>
                      </select>
                      <select class="celda-sel" [value]="valor(rubro, 'organismo')"
                              (change)="editar(rubro, 'organismo', $event)"
                              title="Organismo financiador">
                        <option value="">OF</option>
                        <option *ngFor="let o of organismos" [value]="o.id">{{ o.codigo }}</option>
                      </select>
                    </div>
                  </td>
                  <td class="num">
                    <strong *ngIf="!editando">{{ moneda(rubro.monto) }}</strong>
                    <input *ngIf="editando" class="celda-num" type="number" step="0.01"
                           [value]="valor(rubro, 'monto')"
                           (input)="editar(rubro, 'monto', $event)">
                  </td>
                  <td class="num">{{ porcentaje(rubro.porcentaje) }}</td>
                  <td class="num">
                    <span *ngIf="!editando">{{ moneda(rubro.monto_corriente) }}</span>
                    <input *ngIf="editando" class="celda-num" type="number" step="0.01"
                           [value]="valor(rubro, 'monto_corriente')"
                           (input)="editar(rubro, 'monto_corriente', $event)">
                  </td>
                  <td class="num">{{ porcentajeVivo(rubro, 'corriente') }}</td>
                  <td class="num">
                    <span *ngIf="!editando">{{ moneda(rubro.monto_inversion) }}</span>
                    <input *ngIf="editando" class="celda-num" type="number" step="0.01"
                           [value]="valor(rubro, 'monto_inversion')"
                           (input)="editar(rubro, 'monto_inversion', $event)">
                  </td>
                  <td class="num">{{ porcentajeVivo(rubro, 'inversion') }}</td>
                  <td class="col-acciones" *ngIf="editando">
                    <button class="icono-fila" title="Agregar componente a este rubro"
                            (click)="agregarFila(rubro)">+</button>
                    <button class="icono-fila borrar" title="Eliminar este rubro y sus componentes"
                            (click)="pedirBorrado(rubro)">🗑</button>
                  </td>
                </tr>
                <tr class="fila-aviso" *ngIf="editando && descuadre(rubro) as aviso">
                  <td colspan="8">⚠ {{ aviso }}</td>
                </tr>
                <tr class="fila-componente" *ngFor="let c of rubro.componentes">
                  <td class="col-descripcion sangria">{{ c.concepto }}</td>
                  <td class="cod">
                    <span *ngIf="!editando">{{ c.ff_of || '—' }}</span>
                    <div class="par-clasificador" *ngIf="editando">
                      <select class="celda-sel" [value]="valor(c, 'fuente')"
                              (change)="editar(c, 'fuente', $event)">
                        <option value="">FF</option>
                        <option *ngFor="let f of fuentes" [value]="f.id">{{ f.codigo }}</option>
                      </select>
                      <select class="celda-sel" [value]="valor(c, 'organismo')"
                              (change)="editar(c, 'organismo', $event)">
                        <option value="">OF</option>
                        <option *ngFor="let o of organismos" [value]="o.id">{{ o.codigo }}</option>
                      </select>
                    </div>
                  </td>
                  <td class="num">
                    <span *ngIf="!editando">{{ moneda(c.monto) }}</span>
                    <input *ngIf="editando" class="celda-num" type="number" step="0.01"
                           [value]="valor(c, 'monto')"
                           (input)="editar(c, 'monto', $event)">
                  </td>
                  <td class="num">{{ porcentaje(c.porcentaje) }}</td>
                  <td class="num" colspan="4"></td>
                  <td class="col-acciones" *ngIf="editando">
                    <button class="icono-fila borrar" title="Eliminar este componente"
                            (click)="pedirBorrado(c)">🗑</button>
                  </td>
                </tr>
              </ng-container>

              <tr *ngIf="!datos.rubros.length">
                <td colspan="8">
                  <div class="sin-datos">
                    <span class="sin-datos-icono">▤</span>
                    <strong>Todavía no hay recursos registrados</strong>
                    <span>Habilite la gestión fiscal y registre los rubros del techo directivo.</span>
                  </div>
                </td>
              </tr>
            </tbody>
            <tfoot *ngIf="datos.rubros.length">
              <tr class="fila-total">
                <td class="col-descripcion">TOTAL RECURSOS</td>
                <td></td>
                <td class="num">{{ moneda(datos.total.monto) }}</td>
                <td class="num">{{ porcentaje(datos.total.porcentaje) }}</td>
                <td class="num">{{ moneda(datos.total.monto_corriente) }}</td>
                <td class="num">{{ porcentaje(datos.total.porcentaje_corriente) }}</td>
                <td class="num">{{ moneda(datos.total.monto_inversion) }}</td>
                <td class="num">{{ porcentaje(datos.total.porcentaje_inversion) }}</td>
              </tr>
            </tfoot>
          </table>
        </div>

        <div class="acciones-tabla" *ngIf="editando">
          <button class="btn btn-accent btn-sm" (click)="agregarFila(null)">
            + Agregar rubro
          </button>
          <span class="sub">
            Un rubro por fuente y organismo. Si el ministerio habilita una fuente
            nueva, se agrega una fila con su FF/OF.
          </span>
        </div>

        <div class="resumen-fuente" *ngIf="datos.por_fuente?.length">
          <h3>Resumen por fuente y organismo financiador</h3>
          <p class="sub">Se calcula solo a partir de los rubros de arriba.</p>
          <div class="tabla-caja">
            <table class="tabla tabla-compacta">
              <thead>
                <tr>
                  <th>FF/OF</th><th>Fuente de financiamiento</th>
                  <th>Organismo financiador</th><th class="num">Monto</th><th class="num">%</th>
                </tr>
              </thead>
              <tbody>
                <tr *ngFor="let f of datos.por_fuente">
                  <td class="cod">{{ f.ff_of }}</td>
                  <td>{{ f.fuente }}</td>
                  <td>{{ f.organismo }}</td>
                  <td class="num">{{ moneda(f.monto) }}</td>
                  <td class="num">{{ porcentaje(f.porcentaje) }}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        <div class="modal-fondo" *ngIf="porBorrar" (click)="porBorrar = null">
          <div class="modal" (click)="$event.stopPropagation()">
            <h3>¿Eliminar esta fila?</h3>
            <p>
              <strong>{{ porBorrar.concepto || 'Sin denominación' }}</strong> por
              {{ moneda(porBorrar.monto) }} Bs.
            </p>
            <p class="advertencia" *ngIf="porBorrar.componentes?.length">
              Se eliminarán también sus {{ porBorrar.componentes?.length }} componente(s).
            </p>
            <div class="modal-acciones">
              <button class="btn btn-outline" (click)="porBorrar = null">Cancelar</button>
              <button class="btn btn-peligro" (click)="confirmarBorrado()" [disabled]="guardando">
                {{ guardando ? 'Eliminando…' : 'Sí, eliminar' }}
              </button>
            </div>
          </div>
        </div>

        <div class="circuito">
          <p class="sub" *ngIf="datos.editable">
            El presupuesto está abierto a edición. Al enviarlo a revisión queda bloqueado
            hasta que la jefatura lo apruebe u observe.
          </p>
          <p class="sub" *ngIf="!datos.editable">
            El presupuesto ya no admite cambios en este estado.
          </p>
          <div class="encabezado-acciones">
            <button class="btn btn-primary btn-sm" *ngIf="datos.editable"
                    (click)="enviarARevision()" [disabled]="ocupado">
              Enviar a revisión
            </button>
            <button class="btn btn-outline btn-sm" *ngIf="datos.estado === 'EN_REVISION'"
                    (click)="observar()" [disabled]="ocupado">
              Observar
            </button>
            <button class="btn btn-primary btn-sm" *ngIf="datos.estado === 'EN_REVISION'"
                    (click)="aprobar()" [disabled]="ocupado">
              Aprobar
            </button>
            <button class="btn btn-accent btn-sm" *ngIf="datos.estado === 'APROBADO'"
                    (click)="fijar()" [disabled]="ocupado">
              Fijar presupuesto
            </button>
          </div>
        </div>
      </ng-container>
    </div>
  `,
  styles: [`
    .col-descripcion { min-width: 320px; max-width: 460px; }
    .sangria { padding-left: 2rem !important; color: var(--text-secondary); }
    .grupo-distribucion { text-align: center !important; background: var(--pip-green-100) !important; }
    .fila-rubro td { background: var(--surface); }
    .fila-componente td { font-size: 0.6875rem; }
    .fila-total td {
      background: var(--primary); color: #fff; font-weight: 700;
      position: sticky; bottom: 0;
    }
    .pastilla-estado {
      font-size: 0.6875rem; font-weight: 700; padding: 0.2rem 0.7rem; border-radius: 999px;
      text-transform: uppercase; letter-spacing: 0.05em;
    }
    .e-borrador { background: var(--neutro-fondo); color: var(--neutro-tinta); }
    .e-revision { background: var(--info-fondo); color: var(--info-tinta); }
    .e-observado { background: var(--aviso-fondo); color: var(--aviso-tinta); }
    .e-aprobado, .e-fijado { background: var(--ok-fondo); color: var(--ok-tinta); }
    .circuito {
      margin-top: var(--e-3); padding: var(--e-3); background: var(--surface);
      border: 1px solid var(--border); border-radius: var(--radius);
      display: flex; justify-content: space-between; align-items: center;
      gap: var(--e-3); flex-wrap: wrap;
    }
    .celda-num {
      width: 100%; max-width: 130px; text-align: right; padding: 0.15rem 0.35rem;
      border: 1px solid var(--border); border-radius: 4px; background: var(--surface);
      font-family: var(--font-mono); font-size: 0.6875rem;
      font-variant-numeric: tabular-nums; color: var(--text);
    }
    .celda-num:focus {
      outline: 2px solid var(--pip-green-500); outline-offset: -1px;
      border-color: var(--pip-green-500);
    }
    .fila-aviso td {
      background: var(--aviso-fondo); color: var(--aviso-tinta);
      font-size: 0.6875rem; padding: 0.35rem 0.8rem;
    }
    .par-clasificador { display: flex; gap: 0.2rem; }
    .celda-sel {
      border: 1px solid var(--border); border-radius: 4px; background: var(--surface);
      font-family: var(--font-mono); font-size: 0.625rem; padding: 0.1rem 0.2rem;
      color: var(--text); max-width: 62px;
    }
    .col-acciones { width: 74px; text-align: center; white-space: nowrap; }
    .icono-fila {
      width: 24px; height: 24px; border-radius: 4px; border: 1px solid var(--border);
      background: transparent; color: var(--text-secondary); cursor: pointer;
      font-size: 0.75rem; line-height: 1; margin: 0 1px;
    }
    .icono-fila:hover { border-color: var(--primary); color: var(--primary); background: var(--realce); }
    .icono-fila.borrar:hover { border-color: var(--error-tinta); color: var(--error-tinta); background: var(--error-fondo); }
    .acciones-tabla {
      margin-top: var(--e-2); display: flex; align-items: center; gap: var(--e-2); flex-wrap: wrap;
    }
    .resumen-fuente { margin-top: var(--e-4); }
    .resumen-fuente h3 { font-size: 1rem; margin-bottom: 0.15rem; }
    .modal-fondo {
      position: fixed; inset: 0; background: rgba(0,0,0,.45); display: flex;
      align-items: center; justify-content: center; z-index: 1000; padding: 1rem;
    }
    .modal {
      background: var(--surface); border-radius: var(--radius); padding: 1.5rem;
      max-width: 440px; width: 100%; box-shadow: 0 10px 40px rgba(0,0,0,.25);
    }
    .modal h3 { margin: 0 0 0.6rem; font-size: 1rem; }
    .modal p { font-size: 0.8125rem; color: var(--text-secondary); margin: 0 0 0.5rem; }
    .modal .advertencia { color: var(--error-tinta); font-weight: 600; }
    .modal-acciones { display: flex; justify-content: flex-end; gap: 0.5rem; margin-top: 1rem; }
    .btn-peligro {
      background: var(--error-tinta); color: #fff; border: none; border-radius: var(--r-sm);
      padding: 0.5rem 1rem; cursor: pointer; font-size: 0.8125rem; font-weight: 600;
    }
    .msg-box.error { background: var(--error-fondo); color: var(--error-tinta); padding: 0.7rem 0.9rem; border-radius: var(--radius); margin-bottom: var(--e-2); }
  `],
})
export class PresupuestoRecursosComponent implements OnInit {
  datos: PresupuestoRecursos | null = null;
  cargando = true;
  ocupado = false;
  error = '';
  private techoId: number | null = null;
  private versionId: number | null = null;

  editando = false;
  guardando = false;
  /** Cambios sin guardar, por id de fila. Nada se escribe hasta confirmar. */
  private pendientes = new Map<number, Record<string, number | string | null>>();

  /** Clasificadores oficiales disponibles para asignar a cada rubro. */
  fuentes: { id: number; codigo: string; denominacion: string }[] = [];
  organismos: { id: number; codigo: string; denominacion: string }[] = [];
  porBorrar: FilaRecurso | null = null;

  constructor(
    private servicio: BudgetService,
    private http: HttpClient,
    private cdr: ChangeDetectorRef,
  ) {}

  ngOnInit(): void {
    this.cargar();
    this.cargarClasificadores();
  }

  /**
   * Fuentes de financiamiento y organismos financiadores del clasificador
   * presupuestario. Sin esto no se puede cambiar el FF/OF de un rubro, que
   * era la limitacion real: venian fijos desde la carga inicial.
   */
  private cargarClasificadores(): void {
    this.http.get<any>('/api/v1/fuentes/?page_size=100').subscribe({
      next: r => { this.fuentes = r?.results ?? r ?? []; this.cdr.markForCheck(); },
      error: () => { this.fuentes = []; },
    });
    this.http.get<any>('/api/v1/organismos/?page_size=100').subscribe({
      next: r => { this.organismos = r?.results ?? r ?? []; this.cdr.markForCheck(); },
      error: () => { this.organismos = []; },
    });
  }



  cargar(): void {
    this.cargando = true;
    this.error = '';
    this.servicio.listarTechos().subscribe({
      next: (r: any) => {
        const techos = r?.results || r || [];
        if (!techos.length) {
          this.cargando = false;
          this.error = 'No hay un techo directivo para la gestión activa. '
            + 'Habilite primero la gestión fiscal.';
          this.cdr.markForCheck();
          return;
        }
        this.techoId = techos[0].id;
        this.cargarTabla();
      },
      error: () => {
        this.cargando = false;
        this.error = 'No se pudo consultar el techo directivo.';
        this.cdr.markForCheck();
      },
    });
  }

  private cargarTabla(): void {
    if (this.techoId === null) { return; }
    this.servicio.presupuestoRecursos(this.techoId)
      .pipe(finalize(() => { this.cargando = false; this.cdr.markForCheck(); }))
      .subscribe({
        next: d => {
          this.datos = d;
          this.versionId = d.version_id ?? this.versionId;
          this.cdr.markForCheck();
        },
        error: () => {
          this.error = 'No se pudo cargar el presupuesto de recursos.';
          this.cdr.markForCheck();
        },
      });
  }

  // --- Edición --------------------------------------------------------------

  entrarAEdicion(): void { this.editando = true; this.pendientes.clear(); }

  cancelarEdicion(): void {
    this.editando = false;
    this.pendientes.clear();
    this.error = '';
    this.cargarTabla();
  }

  hayCambios(): boolean { return this.pendientes.size > 0; }
  cantidadCambios(): number { return this.pendientes.size; }

  /** El valor en pantalla: lo tecleado si hay algo pendiente, si no lo guardado. */
  valor(fila: FilaRecurso, campo: string): string {
    const pendiente = this.pendientes.get(fila.id);
    if (pendiente && campo in pendiente) {
      const v = pendiente[campo];
      return v === null ? '' : String(v);
    }
    const guardado = (fila as any)[campo];
    return guardado === null || guardado === undefined ? '' : String(Number(guardado));
  }

  editar(fila: FilaRecurso, campo: string, evento: Event): void {
    const bruto = (evento.target as HTMLInputElement | HTMLSelectElement).value;
    const actual = this.pendientes.get(fila.id) ?? {};
    if (campo === 'fuente' || campo === 'organismo') {
      // Son claves foraneas: viajan como id, no como numero de monto.
      actual[campo] = bruto === '' ? null : Number(bruto);
    } else {
      const numero = bruto === '' ? null : Number(bruto);
      actual[campo] = Number.isNaN(numero as number) ? null : numero;
    }
    this.pendientes.set(fila.id, actual);
  }

  private numero(fila: FilaRecurso, campo: string): number {
    const v = this.valor(fila, campo);
    return v === '' ? 0 : Number(v);
  }

  /** Porcentaje recalculado mientras se escribe, sin esperar al servidor. */
  porcentajeVivo(fila: FilaRecurso, cual: 'corriente' | 'inversion'): string {
    if (!this.editando) {
      return this.porcentaje(
        cual === 'corriente' ? fila.porcentaje_corriente : fila.porcentaje_inversion);
    }
    const total = this.numero(fila, 'monto');
    if (!total) { return '—'; }
    const parte = this.numero(fila, `monto_${cual}`);
    return `${((parte * 100) / total).toFixed(2)}%`;
  }

  /**
   * El backend rechaza el guardado si no cuadra; avisar antes evita que la
   * persona descubra el error recién al confirmar toda la tabla.
   */
  descuadre(rubro: FilaRecurso): string | null {
    if (!this.editando) { return null; }
    const total = this.numero(rubro, 'monto');
    const suma = this.numero(rubro, 'monto_corriente') + this.numero(rubro, 'monto_inversion');
    if (Math.abs(suma - total) > 0.005) {
      return `Corriente e inversión suman ${suma.toLocaleString('es-BO')}, `
        + `y el rubro es de ${total.toLocaleString('es-BO')}.`;
    }
    const hijos = (rubro.componentes || []).reduce((n, c) => n + this.numero(c, 'monto'), 0);
    if (rubro.componentes?.length && Math.abs(hijos - total) > 0.005) {
      return `Los componentes suman ${hijos.toLocaleString('es-BO')}, `
        + `y el rubro es de ${total.toLocaleString('es-BO')}.`;
    }
    return null;
  }

  /**
   * Alta de una fila. Si el ministerio habilita una fuente nueva, se agrega un
   * rubro con su FF/OF; si un rubro se abre en partes, se agrega un componente.
   */
  agregarFila(padre: FilaRecurso | null): void {
    if (this.versionId === null || this.guardando) { return; }
    this.guardando = true;
    this.error = '';
    const cuerpo: Record<string, unknown> = {
      version: this.versionId,
      origen: 'SIGEP',
      concepto: padre ? 'Nuevo componente' : 'Nuevo rubro',
      monto: 0,
      orden: 99,
    };
    if (padre) {
      cuerpo['padre'] = padre.id;
    } else {
      // Solo el rubro agrupador lleva el corte corriente/inversion.
      cuerpo['monto_corriente'] = 0;
      cuerpo['monto_inversion'] = 0;
    }
    this.servicio.crearRecurso(cuerpo as any)
      .pipe(finalize(() => { this.guardando = false; this.cdr.markForCheck(); }))
      .subscribe({
        next: () => this.cargarTabla(),
        error: (e: any) => {
          this.error = e?.error?.detail || 'No se pudo agregar la fila.';
          this.cdr.markForCheck();
        },
      });
  }

  pedirBorrado(fila: FilaRecurso): void { this.porBorrar = fila; }

  confirmarBorrado(): void {
    const fila = this.porBorrar;
    if (!fila || this.guardando) { return; }
    this.guardando = true;
    this.error = '';
    this.servicio.eliminarRecurso(fila.id)
      .pipe(finalize(() => { this.guardando = false; this.cdr.markForCheck(); }))
      .subscribe({
        next: () => {
          this.pendientes.delete(fila.id);
          this.porBorrar = null;
          this.cargarTabla();
        },
        error: (e: any) => {
          this.error = e?.error?.detail || 'No se pudo eliminar la fila.';
          this.porBorrar = null;
          this.cdr.markForCheck();
        },
      });
  }

  guardar(): void {
    if (!this.hayCambios() || this.guardando) { return; }
    const conDescuadre = (this.datos?.rubros || []).filter(r => this.descuadre(r));
    if (conDescuadre.length) {
      this.error = `Corrija el descuadre en ${conDescuadre.length} rubro(s) antes de guardar.`;
      return;
    }
    this.guardando = true;
    this.error = '';

    const envios = [...this.pendientes.entries()].map(
      ([id, campos]) => this.servicio.actualizarRecurso(id, campos));

    forkJoin(envios)
      .pipe(finalize(() => { this.guardando = false; this.cdr.markForCheck(); }))
      .subscribe({
        next: () => {
          this.pendientes.clear();
          this.editando = false;
          this.cargarTabla();
        },
        error: (e: any) => {
          const detalle = e?.error?.detail || e?.error?.non_field_errors?.[0];
          this.error = detalle || 'No se pudieron guardar los cambios.';
          this.cdr.markForCheck();
        },
      });
  }

  // --- Presentación ---------------------------------------------------------

  /** Sin valor no hay cifra: la planilla original mostraba #DIV/0!. */
  moneda(valor: string | null): string {
    if (valor === null || valor === undefined || valor === '') { return '—'; }
    return Number(valor).toLocaleString('es-BO', { minimumFractionDigits: 2 });
  }

  porcentaje(valor: string | null): string {
    if (valor === null || valor === undefined) { return '—'; }
    return `${Number(valor).toFixed(2)}%`;
  }

  etiquetaEstado(): string {
    const mapa: Record<string, string> = {
      BORRADOR: 'Borrador', EN_REVISION: 'En revisión', OBSERVADO: 'Observado',
      APROBADO: 'Aprobado', FIJADO: 'Fijado',
    };
    return mapa[this.datos?.estado || ''] || '—';
  }

  claseEstado(): string {
    const mapa: Record<string, string> = {
      BORRADOR: 'e-borrador', EN_REVISION: 'e-revision', OBSERVADO: 'e-observado',
      APROBADO: 'e-aprobado', FIJADO: 'e-fijado',
    };
    return mapa[this.datos?.estado || ''] || 'e-borrador';
  }

  // --- Circuito de revisión -------------------------------------------------

  private transicion(llamada: any, exito: string): void {
    this.ocupado = true;
    this.error = '';
    llamada.pipe(finalize(() => { this.ocupado = false; this.cdr.markForCheck(); }))
      .subscribe({
        next: () => { this.cargarTabla(); },
        error: (e: any) => {
          this.error = e?.error?.error?.detail?.[0] || `No se pudo ${exito}.`;
          this.cdr.markForCheck();
        },
      });
  }

  enviarARevision(): void {
    if (this.techoId === null) { return; }
    this.transicion(this.servicio.enviarRevision(this.techoId), 'enviar a revisión');
  }

  observar(): void {
    const motivo = window.prompt('Indique qué debe corregirse antes de aprobar:');
    if (!motivo?.trim() || this.techoId === null) { return; }
    this.transicion(this.servicio.observarTecho(this.techoId, motivo.trim()), 'observar');
  }

  aprobar(): void {
    if (this.techoId === null) { return; }
    this.transicion(this.servicio.aprobarTecho(this.techoId), 'aprobar');
  }

  fijar(): void {
    if (this.techoId === null) { return; }
    this.transicion(this.servicio.fijarTecho(this.techoId), 'fijar el presupuesto');
  }
}

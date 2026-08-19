import { ChangeDetectorRef, Component, OnInit } from '@angular/core';
import { finalize, forkJoin } from 'rxjs';
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
              </tr>
              <tr>
                <th class="num">Gastos corrientes</th>
                <th class="num">%</th>
                <th class="num">Gastos de inversión</th>
                <th class="num">%</th>
              </tr>
            </thead>
            <tbody>
              <ng-container *ngFor="let rubro of datos.rubros">
                <tr class="fila-rubro">
                  <td class="col-descripcion"><strong>{{ rubro.concepto }}</strong></td>
                  <td class="cod">{{ rubro.ff_of || '—' }}</td>
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
                </tr>
                <tr class="fila-aviso" *ngIf="editando && descuadre(rubro) as aviso">
                  <td colspan="8">⚠ {{ aviso }}</td>
                </tr>
                <tr class="fila-componente" *ngFor="let c of rubro.componentes">
                  <td class="col-descripcion sangria">{{ c.concepto }}</td>
                  <td class="cod">{{ c.ff_of || '—' }}</td>
                  <td class="num">
                    <span *ngIf="!editando">{{ moneda(c.monto) }}</span>
                    <input *ngIf="editando" class="celda-num" type="number" step="0.01"
                           [value]="valor(c, 'monto')"
                           (input)="editar(c, 'monto', $event)">
                  </td>
                  <td class="num">{{ porcentaje(c.porcentaje) }}</td>
                  <td class="num" colspan="4"></td>
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
    .msg-box.error { background: var(--error-fondo); color: var(--error-tinta); padding: 0.7rem 0.9rem; border-radius: var(--radius); margin-bottom: var(--e-2); }
  `],
})
export class PresupuestoRecursosComponent implements OnInit {
  datos: PresupuestoRecursos | null = null;
  cargando = true;
  ocupado = false;
  error = '';
  private techoId: number | null = null;

  editando = false;
  guardando = false;
  /** Cambios sin guardar, por id de fila. Nada se escribe hasta confirmar. */
  private pendientes = new Map<number, Record<string, number | null>>();

  constructor(private servicio: BudgetService, private cdr: ChangeDetectorRef) {}

  ngOnInit(): void { this.cargar(); }

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
        next: d => { this.datos = d; this.cdr.markForCheck(); },
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
    const bruto = (evento.target as HTMLInputElement).value;
    const numero = bruto === '' ? null : Number(bruto);
    const actual = this.pendientes.get(fila.id) ?? {};
    actual[campo] = Number.isNaN(numero as number) ? null : numero;
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

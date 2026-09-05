import { ChangeDetectorRef, Component, OnInit } from '@angular/core';
import { PoauSaldosService } from './poau-saldos.service';
import {
  OpcionCatalogo,
  SaldoUnidadCategoria,
  SaldoUnidadCategoriaForm,
  aFormulario,
  erroresDeFormulario,
  formularioVacio,
  totalDeSaldos,
} from './poau-saldos.model';

interface Unidad {
  id: string;
  codigo: string;
  nombre: string;
}

@Component({
  selector: 'app-poau-saldos-admin',
  // Angular 21 hace standalone por defecto; el resto de los módulos de
  // `features/` se declara en su NgModule y esta pantalla sigue esa convención.
  standalone: false,
  template: `
    <div class="contenedor">
      <header class="cabecera">
        <div>
          <h2>Presupuesto por unidad y categoría</h2>
          <p class="subtitulo">
            Techo disponible para programar en el asistente de recursos del POAU.
          </p>
        </div>
        <button class="btn btn-primary" type="button"
                (click)="abrirNuevo()" [disabled]="cargando">
          Nuevo saldo
        </button>
      </header>

      <div class="alerta alerta-error" *ngIf="error">{{ error }}</div>

      <section class="filtros">
        <label>
          Unidad organizacional
          <select [(ngModel)]="filtroUnidad" (ngModelChange)="cargarSaldos()"
                  [disabled]="cargando">
            <option value="">Todas las unidades</option>
            <option *ngFor="let u of unidades" [value]="u.codigo">
              {{ u.codigo }} — {{ u.nombre }}
            </option>
          </select>
        </label>
        <div class="resumen" *ngIf="!cargando">
          <span><strong>{{ saldos.length }}</strong> filas</span>
          <span><strong>{{ moneda(total) }}</strong> Bs. de techo declarado</span>
          <span class="aviso" *ngIf="sinFuente > 0">
            {{ sinFuente }} sin fuente ni organismo declarados
          </span>
        </div>
      </section>

      <p class="cargando" *ngIf="cargando">Cargando…</p>

      <table class="tabla" *ngIf="!cargando && saldos.length">
        <thead>
          <tr>
            <th>Unidad</th>
            <th>Cat. programática</th>
            <th>Denominación</th>
            <th>Fuente</th>
            <th>Organismo</th>
            <th class="der">Saldo (Bs.)</th>
            <th>Origen</th>
            <th></th>
          </tr>
        </thead>
        <tbody>
          <tr *ngFor="let s of saldos" [class.inactivo]="!s.activo">
            <td>
              <strong>{{ s.unidad_codigo }}</strong>
              <small>{{ s.unidad_nombre }}</small>
            </td>
            <td class="mono">{{ s.categoria_programatica }}</td>
            <td>{{ s.denominacion || '—' }}</td>
            <td>
              <span *ngIf="s.fuente_codigo; else huecoFuente">
                {{ s.fuente_codigo }} — {{ s.fuente_denominacion }}
              </span>
              <ng-template #huecoFuente>
                <span class="hueco" title="Heredado de la planilla, sin fuente declarada">
                  sin declarar
                </span>
              </ng-template>
            </td>
            <td>
              <span *ngIf="s.organismo_codigo; else huecoOrg">
                {{ s.organismo_codigo }} — {{ s.organismo_denominacion }}
              </span>
              <ng-template #huecoOrg>
                <span class="hueco">sin declarar</span>
              </ng-template>
            </td>
            <td class="der mono" [class.negativo]="numero(s.saldo) < 0">
              {{ moneda(numero(s.saldo)) }}
            </td>
            <td>
              <span class="etiqueta" *ngIf="s.filas_origen === 0"
                    title="No viene de la planilla: una regeneración desde el origen la perdería">
                manual
              </span>
              <span *ngIf="s.filas_origen > 0">planilla ({{ s.filas_origen }})</span>
            </td>
            <td class="acciones">
              <button class="btn btn-sm" type="button" (click)="abrirEdicion(s)">
                Editar
              </button>
              <button class="btn btn-sm btn-peligro" type="button" (click)="pedirBorrado(s)">
                Borrar
              </button>
            </td>
          </tr>
        </tbody>
      </table>

      <p class="vacio" *ngIf="!cargando && !saldos.length">
        No hay saldos cargados para este filtro.
      </p>

      <!-- Formulario -->
      <div class="modal" *ngIf="formulario">
        <div class="panel">
          <h3>{{ editandoId ? 'Editar saldo' : 'Nuevo saldo' }}</h3>

          <div class="alerta alerta-error" *ngIf="erroresForm.length">
            <div *ngFor="let e of erroresForm">{{ e }}</div>
          </div>

          <label>
            Unidad organizacional *
            <select [(ngModel)]="formulario.unidad">
              <option value="">Elija una unidad</option>
              <option *ngFor="let u of unidades" [value]="u.id">
                {{ u.codigo }} — {{ u.nombre }}
              </option>
            </select>
          </label>

          <label>
            Categoría programática *
            <input type="text" [(ngModel)]="formulario.categoria_programatica"
                   placeholder="251 0 013" />
          </label>

          <label>
            Denominación
            <input type="text" [(ngModel)]="formulario.denominacion"
                   placeholder="Denominación oficial de la categoría" />
          </label>

          <label>
            Fuente de financiamiento
            <select [(ngModel)]="formulario.fuente">
              <option [ngValue]="null">Sin declarar</option>
              <option *ngFor="let f of fuentes" [ngValue]="f.id">
                {{ f.codigo }} — {{ f.denominacion }}
              </option>
            </select>
          </label>

          <label>
            Organismo financiador
            <select [(ngModel)]="formulario.organismo">
              <option [ngValue]="null">Sin declarar</option>
              <option *ngFor="let o of organismos" [ngValue]="o.id">
                {{ o.codigo }} — {{ o.denominacion }}
              </option>
            </select>
          </label>

          <label>
            Saldo en bolivianos *
            <input type="number" step="0.01" [(ngModel)]="formulario.saldo" />
            <small>
              Se admite negativo: la planilla marca saldos negativos y
              redondearlos a cero inventaría un margen que la unidad no tiene.
            </small>
          </label>

          <label>
            Observación
            <textarea rows="2" [(ngModel)]="formulario.observacion"
                      placeholder="Por qué esta fila se aparta de la planilla, si es el caso"></textarea>
          </label>

          <label class="en-linea">
            <input type="checkbox" [(ngModel)]="formulario.activo" />
            Activo
          </label>

          <div class="pie">
            <button class="btn" type="button" (click)="cerrarFormulario()"
                    [disabled]="guardando">Cancelar</button>
            <button class="btn btn-primary" type="button" (click)="guardar()"
                    [disabled]="guardando">
              {{ guardando ? 'Guardando…' : 'Guardar' }}
            </button>
          </div>
        </div>
      </div>

      <!-- Confirmación de borrado -->
      <div class="modal" *ngIf="porBorrar">
        <div class="panel">
          <h3>Borrar el saldo</h3>
          <p>
            Se va a borrar el techo de
            <strong>{{ porBorrar.unidad_codigo }}</strong> en
            <strong class="mono">{{ porBorrar.categoria_programatica }}</strong>,
            por <strong>{{ moneda(numero(porBorrar.saldo)) }} Bs.</strong>
          </p>
          <p class="advertencia">
            Esa unidad deja de poder programar recursos en esa categoría. Si lo
            que quiere es cambiar el monto, use Editar: borrar no deja historial.
          </p>
          <div class="pie">
            <button class="btn" type="button" (click)="porBorrar = null"
                    [disabled]="guardando">Cancelar</button>
            <button class="btn btn-peligro" type="button" (click)="confirmarBorrado()"
                    [disabled]="guardando">
              {{ guardando ? 'Borrando…' : 'Borrar' }}
            </button>
          </div>
        </div>
      </div>
    </div>
  `,
  styles: [`
    .contenedor { padding: 1rem; }
    .cabecera { display: flex; justify-content: space-between; align-items: flex-start; gap: 1rem; }
    .subtitulo { color: #64748b; margin: .25rem 0 0; font-size: .875rem; }
    .filtros { display: flex; justify-content: space-between; align-items: flex-end;
               gap: 1rem; margin: 1rem 0; flex-wrap: wrap; }
    .filtros label { display: flex; flex-direction: column; gap: .25rem; font-size: .8125rem; }
    .filtros select { min-width: 22rem; padding: .4rem; }
    .resumen { display: flex; gap: 1.25rem; font-size: .875rem; color: #334155; }
    .resumen .aviso { color: #b45309; }
    .tabla { width: 100%; border-collapse: collapse; font-size: .8125rem; }
    .tabla th, .tabla td { border-bottom: 1px solid #e2e8f0; padding: .5rem; text-align: left;
                           vertical-align: top; }
    .tabla th { background: #f8fafc; font-weight: 600; }
    .tabla td small { display: block; color: #64748b; }
    .tabla tr.inactivo { opacity: .55; }
    .der { text-align: right; }
    .mono { font-variant-numeric: tabular-nums; font-family: ui-monospace, monospace; }
    .negativo { color: #b91c1c; }
    .hueco { color: #b45309; font-style: italic; }
    .etiqueta { background: #fef3c7; color: #92400e; padding: .1rem .4rem;
                border-radius: .25rem; font-size: .75rem; }
    .acciones { white-space: nowrap; }
    .vacio, .cargando { color: #64748b; padding: 1rem 0; }
    .alerta-error { background: #fee2e2; color: #991b1b; padding: .625rem .75rem;
                    border-radius: .375rem; margin: .75rem 0; font-size: .875rem; }
    .modal { position: fixed; inset: 0; background: rgba(15,23,42,.45);
             display: flex; align-items: center; justify-content: center; z-index: 50; }
    .panel { background: #fff; border-radius: .5rem; padding: 1.25rem;
             width: min(34rem, 92vw); max-height: 90vh; overflow: auto; }
    .panel label { display: flex; flex-direction: column; gap: .25rem;
                   margin-bottom: .75rem; font-size: .8125rem; }
    .panel label.en-linea { flex-direction: row; align-items: center; gap: .5rem; }
    .panel input, .panel select, .panel textarea { padding: .4rem; font: inherit; }
    .panel small { color: #64748b; font-size: .75rem; }
    .advertencia { color: #b45309; font-size: .875rem; }
    .pie { display: flex; justify-content: flex-end; gap: .5rem; margin-top: 1rem; }
    .btn-peligro { background: #dc2626; color: #fff; }
  `],
})
export class PoauSaldosAdminComponent implements OnInit {
  saldos: SaldoUnidadCategoria[] = [];
  unidades: Unidad[] = [];
  fuentes: OpcionCatalogo[] = [];
  organismos: OpcionCatalogo[] = [];

  filtroUnidad = '';
  cargando = false;
  guardando = false;
  error = '';

  formulario: SaldoUnidadCategoriaForm | null = null;
  editandoId: string | null = null;
  erroresForm: string[] = [];
  porBorrar: SaldoUnidadCategoria | null = null;

  constructor(
    private servicio: PoauSaldosService,
    private cdr: ChangeDetectorRef,
  ) {}

  ngOnInit(): void {
    this.cargarCatalogos();
    this.cargarSaldos();
  }

  get total(): number {
    return totalDeSaldos(this.saldos);
  }

  /** Cuántas filas siguen sin fuente ni organismo: el hueco a completar. */
  get sinFuente(): number {
    return this.saldos.filter(s => !s.fuente_codigo && !s.organismo_codigo).length;
  }

  numero(valor: string): number {
    const n = Number(valor);
    return Number.isFinite(n) ? n : 0;
  }

  moneda(valor: number): string {
    return valor.toLocaleString('es-BO', {
      minimumFractionDigits: 2, maximumFractionDigits: 2,
    });
  }

  private cargarCatalogos(): void {
    this.servicio.unidades().subscribe({
      next: u => { this.unidades = u; this.cdr.markForCheck(); },
      error: () => { this.error = 'No se pudo cargar el catálogo de unidades.'; },
    });
    this.servicio.fuentes().subscribe({
      next: f => { this.fuentes = f; this.cdr.markForCheck(); },
      error: () => { this.error = 'No se pudo cargar el catálogo de fuentes.'; },
    });
    this.servicio.organismos().subscribe({
      next: o => { this.organismos = o; this.cdr.markForCheck(); },
      error: () => { this.error = 'No se pudo cargar el catálogo de organismos.'; },
    });
  }

  cargarSaldos(): void {
    this.cargando = true;
    this.error = '';
    this.servicio.listar(this.filtroUnidad || undefined).subscribe({
      next: filas => {
        this.saldos = filas;
        this.cargando = false;
        this.cdr.markForCheck();
      },
      error: err => {
        this.error = this.mensajeDeError(err, 'No se pudieron cargar los saldos.');
        this.cargando = false;
        this.cdr.markForCheck();
      },
    });
  }

  abrirNuevo(): void {
    this.formulario = formularioVacio();
    this.editandoId = null;
    this.erroresForm = [];
  }

  abrirEdicion(saldo: SaldoUnidadCategoria): void {
    this.formulario = aFormulario(saldo);
    this.editandoId = saldo.id;
    this.erroresForm = [];
  }

  cerrarFormulario(): void {
    this.formulario = null;
    this.editandoId = null;
    this.erroresForm = [];
  }

  guardar(): void {
    if (!this.formulario) { return; }
    this.erroresForm = erroresDeFormulario(this.formulario);
    if (this.erroresForm.length) { return; }

    this.guardando = true;
    const peticion = this.editandoId
      ? this.servicio.editar(this.editandoId, this.formulario)
      : this.servicio.crear(this.formulario);

    peticion.subscribe({
      next: () => {
        this.guardando = false;
        this.cerrarFormulario();
        this.cargarSaldos();
      },
      error: err => {
        this.guardando = false;
        this.erroresForm = this.erroresDeRespuesta(err);
        this.cdr.markForCheck();
      },
    });
  }

  pedirBorrado(saldo: SaldoUnidadCategoria): void {
    this.porBorrar = saldo;
  }

  confirmarBorrado(): void {
    if (!this.porBorrar) { return; }
    this.guardando = true;
    this.servicio.borrar(this.porBorrar.id).subscribe({
      next: () => {
        this.guardando = false;
        this.porBorrar = null;
        this.cargarSaldos();
      },
      error: err => {
        this.guardando = false;
        this.porBorrar = null;
        this.error = this.mensajeDeError(err, 'No se pudo borrar el saldo.');
        this.cdr.markForCheck();
      },
    });
  }

  /**
   * Despliega los errores de campo del backend.
   *
   * `apps.core.exceptions.api_exception_handler` los envuelve en
   * `{ error: {...} }`; leer `err.error` a secas mostraría «[object Object]».
   */
  private erroresDeRespuesta(err: any): string[] {
    const cuerpo = err?.error?.error ?? err?.error ?? {};
    if (typeof cuerpo === 'string') { return [cuerpo]; }
    const mensajes: string[] = [];
    Object.values(cuerpo).forEach(valor => {
      if (Array.isArray(valor)) {
        valor.forEach(v => mensajes.push(String(v)));
      } else if (typeof valor === 'string') {
        mensajes.push(valor);
      }
    });
    return mensajes.length ? mensajes : ['No se pudo guardar el saldo.'];
  }

  private mensajeDeError(err: any, porDefecto: string): string {
    const detalle = err?.error?.error?.detail ?? err?.error?.detail;
    if (err?.status === 403) {
      return 'Esta pantalla es solo para administración.';
    }
    return typeof detalle === 'string' ? detalle : porDefecto;
  }
}

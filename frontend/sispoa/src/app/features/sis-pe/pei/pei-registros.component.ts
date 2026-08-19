import { ChangeDetectorRef, Component, OnInit } from '@angular/core';
import { catchError, finalize, forkJoin, map, of } from 'rxjs';
import { BorradorMatrizPEI, PeiBorradoresService } from './pei-borradores.service';

interface ColumnaMatriz { clave: string; etiqueta: string; }

/** Bloque de cabecera: agrupa columnas bajo un mismo título y color. */
interface BloqueMatriz {
  etiqueta: string;
  clase: string;
  /** Mismo color que la clase CSS: el reporte exportado lo reutiliza. */
  color: string;
  columnas: ColumnaMatriz[];
}

const GESTIONES = ['2026', '2027', '2028', '2029', '2030'];

/**
 * Matriz PEI: 46 columnas en las 8 secciones de la guía, con los mismos
 * bloques y colores que el visualizador del asistente.
 */
const BLOQUES_PEI: BloqueMatriz[] = [
  {
    etiqueta: 'PLANIFICACIÓN NACIONAL', clase: 'g-nacional', color: '#A6291F',
    columnas: [
      { clave: 'cod_eje_pgdesa', etiqueta: 'COD EJE PGDESA (IMPACTO)' },
      { clave: 'objetivo_impacto', etiqueta: 'OBJETIVO DE IMPACTO' },
      { clave: 'cod_componente_pdesa', etiqueta: 'COD COMPONENTE PDESA (EFECTO)' },
      { clave: 'objetivo_efecto', etiqueta: 'OBJETIVO DE EFECTO' },
    ],
  },
  {
    etiqueta: 'ACUERDOS INTERNACIONALES', clase: 'g-acuerdos', color: '#4B7BB5',
    columnas: [
      { clave: 'cod_ods', etiqueta: 'COD ODS' },
      { clave: 'cod_ndc', etiqueta: 'COD NDC' },
      { clave: 'cod_ndt', etiqueta: 'COD NDT' },
      { clave: 'cod_meta_3030', etiqueta: 'COD META 30x30' },
    ],
  },
  {
    etiqueta: 'IDENTIFICACIÓN DEL SECTOR', clase: 'g-sector', color: '#6B1A16',
    columnas: [
      { clave: 'cod_sector', etiqueta: 'COD SECTOR' },
      { clave: 'sector', etiqueta: 'SECTOR' },
    ],
  },
  {
    etiqueta: 'ARTICULACIÓN SECTORIAL', clase: 'g-sectorial', color: '#A8701C',
    columnas: [
      { clave: 'cod_resultado_sectorial', etiqueta: 'COD RESULTADO SECTORIAL PES' },
      { clave: 'resultado_sectorial', etiqueta: 'RESULTADO SECTORIAL' },
    ],
  },
  {
    etiqueta: 'ARTICULACIÓN TERRITORIAL', clase: 'g-territorial', color: '#2E7D32',
    columnas: [
      { clave: 'cod_resultado_territorial', etiqueta: 'COD RESULTADO TERRITORIAL' },
    ],
  },
  {
    etiqueta: 'PLANIFICACIÓN INSTITUCIONAL', clase: 'g-institucional', color: '#1F3864',
    columnas: [
      { clave: 'cod_entidad', etiqueta: 'COD ENTIDAD' },
      { clave: 'entidad', etiqueta: 'ENTIDAD' },
      { clave: 'cod_oei', etiqueta: 'COD OEI' },
      { clave: 'cod_resultado_pei', etiqueta: 'COD RESULTADO PEI' },
      { clave: 'resultado_institucional', etiqueta: 'RESULTADO INSTITUCIONAL' },
      { clave: 'cod_programa_presup', etiqueta: 'COD PROGRAMA PRESUPUESTARIO' },
      { clave: 'programa_presup', etiqueta: 'DESCRIPCIÓN PROGRAMA PRESUPUESTARIO' },
      { clave: 'cod_producto', etiqueta: 'COD PRODUCTO' },
      { clave: 'nombre_producto', etiqueta: 'NOMBRE PRODUCTO' },
    ],
  },
  {
    etiqueta: 'INDICADOR', clase: 'g-indicador', color: '#1565C0',
    columnas: [
      { clave: 'indicador', etiqueta: 'INDICADOR' },
      { clave: 'tipo_indicador', etiqueta: 'TIPO DE INDICADOR' },
      { clave: 'unidad_medida', etiqueta: 'UNIDAD DE MEDIDA' },
      { clave: 'formula', etiqueta: 'FÓRMULA' },
      { clave: 'linea_base', etiqueta: 'LÍNEA BASE' },
      { clave: 'meta_2030', etiqueta: 'META 2030' },
    ],
  },
  {
    etiqueta: 'PROGRAMACIÓN FÍSICA', clase: 'g-fisica', color: '#1565C0',
    columnas: GESTIONES.map(a => ({ clave: `fisica_${a}`, etiqueta: a })),
  },
  {
    etiqueta: 'PRESUPUESTO QUINQUENAL TOTAL', clase: 'g-total', color: '#7B4B12',
    columnas: [{ clave: 'presupuesto_total', etiqueta: 'TOTAL' }],
  },
  {
    etiqueta: 'PROGRAMACIÓN FINANCIERA GASTO DE INVERSIÓN', clase: 'g-financiera',
    color: '#8A5A1A',
    columnas: [
      { clave: 'inversion_total', etiqueta: 'QUINQUENAL INVERSIÓN' },
      ...GESTIONES.map(a => ({ clave: `inversion_${a}`, etiqueta: a })),
    ],
  },
  {
    etiqueta: 'PROGRAMACIÓN FINANCIERA GASTO CORRIENTE', clase: 'g-financiera',
    color: '#8A5A1A',
    columnas: [
      { clave: 'corriente_total', etiqueta: 'QUINQUENAL CORRIENTE' },
      ...GESTIONES.map(a => ({ clave: `corriente_${a}`, etiqueta: a })),
    ],
  },
];

/** Puente de articulación PAD → PEI, a nivel de fila. */
const BLOQUES_ARTICULACION: BloqueMatriz[] = [
  {
    etiqueta: 'ARTICULACIÓN TERRITORIAL', clase: 'g-territorial', color: '#2E7D32',
    columnas: [
      { clave: 'cod_resultado_territorial', etiqueta: 'COD RESULTADO TERRITORIAL (PAD)' },
    ],
  },
  {
    etiqueta: 'PLANIFICACIÓN INSTITUCIONAL', clase: 'g-institucional', color: '#1F3864',
    columnas: [
      { clave: 'cod_resultado_pei', etiqueta: 'COD RESULTADO PEI' },
      { clave: 'resultado_institucional', etiqueta: 'RESULTADO INSTITUCIONAL' },
      { clave: 'cod_producto', etiqueta: 'COD PRODUCTO PEI' },
      { clave: 'nombre_producto', etiqueta: 'NOMBRE PRODUCTO' },
    ],
  },
  {
    etiqueta: 'INDICADOR', clase: 'g-indicador', color: '#1565C0',
    columnas: [
      { clave: 'indicador', etiqueta: 'INDICADOR' },
      { clave: 'tipo_indicador', etiqueta: 'TIPO' },
    ],
  },
  {
    etiqueta: 'PRESUPUESTO', clase: 'g-total', color: '#7B4B12',
    columnas: [{ clave: 'presupuesto_total', etiqueta: 'QUINQUENAL' }],
  },
];

/**
 * Registros de matrices PEI: listado, circuito de revisión, matrices
 * consolidadas de todos los registros y exportación a Excel y PDF.
 */
@Component({
  selector: 'app-pei-registros',
  standalone: false,
  template: `
    <div class="registros">
      <div class="page-header">
        <div>
          <h2>Matrices PEI</h2>
          <p class="text-secondary">
            Registros generados con el asistente. El lápiz abre el registro para modificarlo;
            abajo se consolidan las matrices de todos los registros.
          </p>
        </div>
        <div class="acciones-header">
          <a routerLink="/sis-pe/pei" class="btn btn-outline btn-sm">← Volver</a>
          <a routerLink="/sis-pe/pei/nuevo" class="btn btn-primary btn-sm">+ Registro nuevo</a>
        </div>
      </div>

      <div class="card tabla-card">
        <table class="tabla">
          <thead>
            <tr>
              <th>Quinquenio</th>
              <th>Resultado institucional</th>
              <th>Productos</th>
              <th>Estado</th>
              <th>Revisión</th>
              <th>Última actualización</th>
              <th class="col-acciones">Acciones</th>
            </tr>
          </thead>
          <tbody>
            <tr *ngFor="let r of registros">
              <td class="codigo">{{ quinquenio(r) }}</td>
              <td class="celda-larga">{{ resultadoDe(r) }}</td>
              <td class="num">{{ productosDe(r) }}</td>
              <td>
                <span class="badge" [class.badge-completo]="r.estado === 'COMPLETO'">{{ r.estado }}</span>
              </td>
              <td>
                <span class="badge rev" [ngClass]="claseRevision(r)">
                  {{ r.estado_revision || 'PENDIENTE' }}
                </span>
                <div class="obs" *ngIf="r.observacion" [title]="r.observacion">
                  ⚠ {{ r.observacion | slice:0:60 }}{{ r.observacion.length > 60 ? '…' : '' }}
                </div>
              </td>
              <td class="fecha">{{ fecha(r) }}</td>
              <td class="col-acciones">
                <a *ngIf="puede(r, 'editar')" [routerLink]="['/sis-pe/pei/nuevo', r.id]"
                   class="btn-icono" title="Editar este registro" aria-label="Editar">✎</a>
                <button *ngIf="puede(r, 'validar')" class="btn-icono validar"
                        (click)="validar(r)" [disabled]="ocupado === r.id"
                        title="Validar: doy por revisada la información">✓</button>
                <button *ngIf="puede(r, 'aprobar')" class="btn-icono aprobar"
                        (click)="aprobar(r)" [disabled]="ocupado === r.id"
                        title="Aprobar: el registro queda permanente e inmutable">✔</button>
                <button *ngIf="puede(r, 'observar')" class="btn-icono observar"
                        (click)="abrirObservacion(r)" [disabled]="ocupado === r.id"
                        title="Registrar una observación">✎̶</button>
                <button *ngIf="puede(r, 'borrar')" class="btn-icono borrar"
                        (click)="pedirBorrado(r)" [disabled]="ocupado === r.id"
                        title="Eliminar este registro">🗑</button>
                <span *ngIf="!accionesDisponibles(r)" class="sin-acciones"
                      title="Registro aprobado: permanente e inmutable">🔒</span>
              </td>
            </tr>
            <tr *ngIf="cargando"><td colspan="7" class="vacio">Cargando registros…</td></tr>
            <tr *ngIf="!cargando && !registros.length && !error">
              <td colspan="7" class="vacio">
                Todavía no hay matrices PEI registradas.
                <a routerLink="/sis-pe/pei/nuevo">Formule la primera</a>.
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <div class="msg-box error" *ngIf="error">
        {{ error }}
        <button class="btn btn-sm btn-outline" (click)="cargar()">Reintentar</button>
      </div>

      <!-- CONFIRMACIÓN DE BORRADO -->
      <div class="modal-fondo" *ngIf="porBorrar" (click)="porBorrar = null">
        <div class="modal" (click)="$event.stopPropagation()">
          <h3>¿Eliminar este registro?</h3>
          <p>
            Se eliminará la matriz PEI del quinquenio <strong>{{ quinquenio(porBorrar) }}</strong>
            con {{ productosDe(porBorrar) }} producto(s) institucional(es).
          </p>
          <p class="advertencia">Esta acción no se puede deshacer.</p>
          <div class="modal-acciones">
            <button class="btn btn-outline" (click)="porBorrar = null">Cancelar</button>
            <button class="btn btn-peligro" (click)="confirmarBorrado()"
                    [disabled]="ocupado === porBorrar.id">
              {{ ocupado === porBorrar.id ? 'Eliminando…' : 'Sí, eliminar' }}
            </button>
          </div>
        </div>
      </div>

      <!-- OBSERVACIÓN DE LA JEFATURA -->
      <div class="modal-fondo" *ngIf="porObservar" (click)="cerrarObservacion()">
        <div class="modal" (click)="$event.stopPropagation()">
          <h3>Observación al registro</h3>
          <p>Quinquenio <strong>{{ quinquenio(porObservar) }}</strong> · {{ resultadoDe(porObservar) }}</p>
          <textarea [(ngModel)]="textoObservacion" class="form-control" rows="4"
                    placeholder="Detalle qué debe corregirse antes de aprobar"></textarea>
          <div class="modal-acciones">
            <button class="btn btn-outline" (click)="cerrarObservacion()">Cancelar</button>
            <button class="btn btn-primary" (click)="confirmarObservacion()"
                    [disabled]="!textoObservacion.trim() || ocupado === porObservar.id">
              {{ ocupado === porObservar.id ? 'Registrando…' : 'Registrar observación' }}
            </button>
          </div>
        </div>
      </div>

      <!-- MATRICES CONSOLIDADAS -->
      <div class="matriz-vista card">
        <div class="matriz-tabs">
          <button class="btn" [class.btn-primary]="vista === 'matriz'"
                  (click)="cambiarVista('matriz')">MATRIZ PEI 2026-2030</button>
          <button class="btn" [class.btn-primary]="vista === 'articulacion'"
                  (click)="cambiarVista('articulacion')">ARTICULACIÓN PAD → PEI</button>
          <span class="contexto">
            {{ registros.length }} registro(s) · {{ filas.length }} fila(s)
            <strong *ngIf="seleccionadas.size">· {{ seleccionadas.size }} seleccionada(s)</strong>
            <em *ngIf="!seleccionadas.size">· sin selección: el reporte incluye todo</em>
          </span>
          <button class="btn btn-sm btn-excel" (click)="exportarExcel()" [disabled]="!filas.length">
            ⬇ Excel
          </button>
          <button class="btn btn-sm btn-pdf" (click)="exportarPdf()" [disabled]="!filas.length">
            ⬇ PDF
          </button>
        </div>

        <div class="matriz-scroll" *ngIf="!cargandoMatriz">
          <table class="mz">
            <thead>
              <tr class="grupo">
                <th rowspan="2" class="g-registro col-check">
                  <input type="checkbox" [checked]="todasSeleccionadas"
                         [indeterminate]="algunaSeleccionada && !todasSeleccionadas"
                         (change)="alternarTodas()" title="Seleccionar todas las filas">
                </th>
                <th rowspan="2" class="g-registro">REGISTRO</th>
                <th *ngFor="let b of bloques" [ngClass]="b.clase" [attr.colspan]="b.columnas.length">
                  {{ b.etiqueta }}
                </th>
                <th rowspan="2" class="g-registro">EDITAR</th>
              </tr>
              <tr class="columna">
                <ng-container *ngFor="let b of bloques">
                  <th *ngFor="let c of b.columnas" [ngClass]="b.clase">{{ c.etiqueta }}</th>
                </ng-container>
              </tr>
            </thead>
            <tbody>
              <tr *ngFor="let fila of filas; let i = index"
                  [class.fila-resultado]="fila.tipo_fila === 'resultado'"
                  [class.fila-elegida]="seleccionadas.has(i)">
                <td class="col-check">
                  <input type="checkbox" [checked]="seleccionadas.has(i)" (change)="alternar(i)">
                </td>
                <td class="col-registro">
                  <span class="chip-gestion">{{ fila._gestion }}</span>
                  <span class="chip-estado" [class.completo]="fila._estado === 'COMPLETO'">
                    {{ fila._estado }}
                  </span>
                </td>
                <ng-container *ngFor="let b of bloques">
                  <td *ngFor="let c of b.columnas">{{ celda(fila, c.clave) }}</td>
                </ng-container>
                <td class="col-editar">
                  <a [routerLink]="['/sis-pe/pei/nuevo', fila._borradorId]" class="btn-icono"
                     title="Editar el registro que originó esta fila">✎</a>
                </td>
              </tr>
              <tr *ngIf="!filas.length">
                <td [attr.colspan]="totalColumnas + 3" class="vacio">
                  Todavía no hay filas en esta matriz.
                </td>
              </tr>
            </tbody>
          </table>
        </div>
        <div class="vacio" *ngIf="cargandoMatriz">Consolidando matrices de todos los registros…</div>
        <div class="msg-box error" *ngIf="errorMatriz">{{ errorMatriz }}</div>
      </div>
    </div>
  `,
  styles: [`
    .registros { width: 100%; max-width: none; padding-inline: var(--canal); }
    .page-header { display: flex; justify-content: space-between; align-items: flex-start; gap: 1rem; flex-wrap: wrap; margin-bottom: 1.25rem; }
    .page-header h2 { font-size: 1.25rem; color: var(--primary); margin-bottom: 0.25rem; }
    .text-secondary { color: var(--text-secondary); font-size: 0.8125rem; max-width: 66ch; }
    .acciones-header { display: flex; gap: 0.5rem; }

    .tabla-card { padding: 0; overflow: hidden; }
    .tabla { width: 100%; border-collapse: collapse; font-size: 0.8125rem; }

    
    .codigo { font-family: 'Courier New', monospace; font-weight: 700; }
    .celda-larga { max-width: 340px; }
    .num { text-align: right; }
    .fecha { white-space: nowrap; font-size: 0.75rem; color: var(--text-secondary); }
    .col-acciones { text-align: center; width: 190px; white-space: nowrap; }

    .badge { font-size: 0.6875rem; padding: 0.15rem 0.5rem; border-radius: 999px; background: #FFF8E1; color: #8A6100; font-weight: 700; }
    .badge.badge-completo { background: #E8F5E9; color: var(--success); }
    .badge.rev { font-size: 0.625rem; }
    .badge.rev.pendiente { background: #ECEFF1; color: #455A64; }
    .badge.rev.validado { background: #E3F2FD; color: #0D47A1; }
    .badge.rev.observado { background: #FFF8E1; color: #8A6100; }
    .badge.rev.aprobado { background: #E8F5E9; color: #1B5E20; }
    .obs { font-size: 0.625rem; color: #8A6100; margin-top: 0.15rem; max-width: 220px; }

    .btn-icono { display: inline-flex; align-items: center; justify-content: center; width: 30px; height: 30px; margin: 0 0.1rem; border-radius: 6px; border: 1px solid var(--border); color: var(--primary); background: transparent; text-decoration: none; font-size: 0.9rem; cursor: pointer; }
    .btn-icono:hover { border-color: var(--primary); background: #E8F5E9; }
    .btn-icono.validar { color: #1B5E20; }
    .btn-icono.aprobar { color: #0D47A1; }
    .btn-icono.observar { color: #8A6100; }
    .btn-icono.borrar { color: var(--warn); }
    .btn-icono[disabled] { opacity: 0.4; cursor: not-allowed; }
    .sin-acciones { font-size: 0.9rem; opacity: 0.6; }

    .vacio { text-align: center; color: var(--text-secondary); padding: 2rem; }
    .msg-box { margin-top: 1rem; padding: 0.6rem 0.8rem; border-radius: 6px; font-size: 0.8125rem; display: flex; align-items: center; gap: 0.75rem; flex-wrap: wrap; }
    .msg-box.error { background: #FFEBEE; color: var(--warn); }

    .modal-fondo { position: fixed; inset: 0; background: rgba(0,0,0,.45); display: flex; align-items: center; justify-content: center; z-index: 1000; padding: 1rem; }
    .modal { background: var(--surface, #fff); border-radius: 10px; padding: 1.5rem; max-width: 460px; width: 100%; box-shadow: 0 10px 40px rgba(0,0,0,.25); }
    .modal h3 { margin: 0 0 0.6rem; font-size: 1rem; color: var(--primary); }
    .modal p { font-size: 0.8125rem; color: var(--text-secondary); margin: 0 0 0.6rem; }
    .modal .advertencia { color: var(--warn); font-weight: 600; }
    .modal-acciones { display: flex; justify-content: flex-end; gap: 0.5rem; margin-top: 1rem; }
    .btn-peligro { background: var(--warn); color: #fff; border: none; border-radius: 6px; padding: 0.5rem 1rem; cursor: pointer; font-size: 0.8125rem; font-weight: 600; }

    .matriz-vista { margin-top: 1.5rem; padding: 1.25rem; border: 2px solid var(--primary); }
    .matriz-tabs { display: flex; gap: 0.5rem; margin-bottom: 1rem; align-items: center; flex-wrap: wrap; }
    .matriz-tabs .btn { font-size: 0.75rem; padding: 0.375rem 0.75rem; }
    .contexto { font-size: 0.75rem; color: var(--text-secondary); flex: 1; }
    .contexto em { font-style: normal; opacity: .8; }
    .matriz-scroll { overflow-x: auto; }
    .mz { border-collapse: collapse; font-size: 0.625rem; width: 100%; }
    .mz th { color: #fff; padding: 0.3rem 0.4rem; text-transform: uppercase; border: 1px solid rgba(255,255,255,0.25); font-weight: 700; vertical-align: middle; }
    .mz tr.grupo th { font-size: 0.625rem; letter-spacing: 0.02em; }
    .mz tr.columna th { font-size: 0.5625rem; min-width: 78px; }
    .mz td { padding: 0.25rem 0.4rem; border: 1px solid var(--border); vertical-align: top; max-width: 200px; }

    /* Misma paleta por bloque que el visualizador del asistente */
    .g-nacional { background: #A6291F; }
    .g-acuerdos { background: #4B7BB5; }
    .g-sector { background: #6B1A16; }
    .g-sectorial { background: #A8701C; }
    .g-territorial { background: #2E7D32; }
    .g-institucional { background: #1F3864; }
    .g-indicador { background: #1565C0; }
    .g-fisica { background: #1565C0; }
    .g-total { background: #7B4B12; }
    .g-financiera { background: #8A5A1A; }
    .g-registro { background: var(--primary); }

    .col-check { width: 34px; text-align: center; }
    .col-registro { white-space: nowrap; }
    .col-editar { text-align: center; width: 60px; }
    .chip-gestion { font-family: 'Courier New', monospace; font-weight: 800; margin-right: 0.25rem; }
    .chip-estado { font-size: 0.5rem; padding: 0.05rem 0.3rem; border-radius: 999px; background: #FFF8E1; color: #8A6100; font-weight: 700; }
    .chip-estado.completo { background: #E8F5E9; color: #1B5E20; }
    .mz tbody tr.fila-resultado td { background: #E8F5E9; font-weight: 600; }
    .mz tbody tr.fila-elegida td { background: #FFF8E1; }
    .mz tbody tr.fila-elegida.fila-resultado td { background: #FFF3C4; }
    .mz tbody tr:hover td { background: #F0F7F3; }
    .btn-excel { background: #1B5E20; color: #fff; border: none; }
    .btn-pdf { background: #B3261E; color: #fff; border: none; }
    .btn-excel[disabled], .btn-pdf[disabled] { opacity: .5; cursor: not-allowed; }
  `],
})
export class PeiRegistrosComponent implements OnInit {
  registros: BorradorMatrizPEI[] = [];
  cargando = true;
  error = '';

  vista: 'matriz' | 'articulacion' = 'matriz';
  filasMatriz: any[] = [];
  cargandoMatriz = false;
  errorMatriz = '';

  ocupado: string | null = null;
  porBorrar: BorradorMatrizPEI | null = null;
  porObservar: BorradorMatrizPEI | null = null;
  textoObservacion = '';

  seleccionadas = new Set<number>();

  constructor(
    private borradores: PeiBorradoresService,
    private cdr: ChangeDetectorRef,
  ) {}

  ngOnInit(): void { this.cargar(); }

  /** `finalize` apaga el indicador de carga pase lo que pase. */
  cargar(): void {
    this.cargando = true;
    this.error = '';
    this.cargarPagina();
  }

  /**
   * La API pagina de a 25 y no acepta `page_size`: hay que recorrer las
   * páginas o el listado y las matrices consolidadas omitirían registros.
   */
  private cargarPagina(pagina = 1, acumulado: any[] = []): void {
    this.borradores.listar({ page: pagina })
      .subscribe({
        next: (r: any) => {
          const lote = r?.results || (Array.isArray(r) ? r : []);
          const total = [...acumulado, ...lote];
          if (r?.next) {
            this.cargarPagina(pagina + 1, total);
            return;
          }
          this.registros = total;
          this.cargando = false;
          this.cdr.markForCheck();
          this.consolidarMatrices();
        },
        error: (err: any) => {
          this.cargando = false;
          const detalle = err?.message || err?.status || 'sin detalle';
          this.error = `No se pudieron cargar los registros de matrices PEI (${detalle}).`;
          this.registros = [];
          this.cdr.markForCheck();
        },
      });
  }

  /** Junta las filas de todos los registros, etiquetadas con su origen. */
  private consolidarMatrices(): void {
    if (!this.registros.length) {
      this.filasMatriz = [];
      this.cdr.markForCheck();
      return;
    }
    this.cargandoMatriz = true;
    this.errorMatriz = '';

    forkJoin(this.registros.map(registro =>
      this.borradores.matriz(registro.id).pipe(
        catchError(() => of([])),
        map((respuesta: any) => {
          const filas = respuesta?.filas || (Array.isArray(respuesta) ? respuesta : []);
          return filas.map((fila: any) => ({
            ...fila,
            _borradorId: registro.id,
            _gestion: registro.gestion,
            _estado: registro.estado,
          }));
        }),
      ),
    )).pipe(finalize(() => { this.cargandoMatriz = false; this.cdr.markForCheck(); }))
      .subscribe({
        next: bloques => { this.filasMatriz = bloques.flat(); this.cdr.markForCheck(); },
        error: () => {
          this.errorMatriz = 'No se pudieron consolidar las matrices de los registros.';
          this.cdr.markForCheck();
        },
      });
  }

  // --- Vista ----------------------------------------------------------------

  get bloques(): BloqueMatriz[] {
    return this.vista === 'matriz' ? BLOQUES_PEI : BLOQUES_ARTICULACION;
  }

  get totalColumnas(): number {
    return this.bloques.reduce((n, b) => n + b.columnas.length, 0);
  }

  get filas(): any[] { return this.filasMatriz; }

  /** Los índices seleccionados no son equivalentes entre vistas. */
  cambiarVista(nueva: 'matriz' | 'articulacion'): void {
    if (this.vista === nueva) return;
    this.vista = nueva;
    this.seleccionadas.clear();
  }

  celda(fila: any, clave: string): string {
    const valor = fila?.[clave];
    if (valor === null || valor === undefined || valor === '') return '-';
    if (typeof valor === 'boolean') return valor ? 'SÍ' : 'NO';
    return String(valor);
  }

  // --- Datos del registro ---------------------------------------------------

  private seccion(registro: BorradorMatrizPEI, clave: string): any {
    return (registro?.datos as any)?.[clave] || {};
  }

  private resultados(registro: BorradorMatrizPEI): any[] {
    const datos = (registro?.datos as any) || {};
    return Array.isArray(datos.resultados) ? datos.resultados : [];
  }

  quinquenio(registro: BorradorMatrizPEI): string {
    const institucional = this.seccion(registro, 's5_institucional');
    const desde = institucional.vigencia_desde || registro.gestion;
    const hasta = institucional.vigencia_hasta || 2030;
    return `${desde}-${hasta}`;
  }

  resultadoDe(registro: BorradorMatrizPEI): string {
    const primero = this.resultados(registro)[0];
    return primero?.denominacion || 'Sin resultado institucional';
  }

  productosDe(registro: BorradorMatrizPEI): number {
    return this.resultados(registro).reduce(
      (total, r) => total + ((r?.productos || []).length), 0,
    );
  }

  fecha(registro: BorradorMatrizPEI): string {
    const valor = registro.updated_at || registro.created_at;
    return valor ? new Date(valor).toLocaleString('es-BO') : '-';
  }

  // --- Circuito de revisión -------------------------------------------------

  puede(registro: BorradorMatrizPEI, accion: keyof NonNullable<BorradorMatrizPEI['permisos']>): boolean {
    return !!registro.permisos?.[accion];
  }

  accionesDisponibles(registro: BorradorMatrizPEI): boolean {
    return this.puede(registro, 'editar') || this.puede(registro, 'validar')
      || this.puede(registro, 'aprobar') || this.puede(registro, 'observar')
      || this.puede(registro, 'borrar');
  }

  claseRevision(registro: BorradorMatrizPEI): string {
    return (registro.estado_revision || 'PENDIENTE').toLowerCase();
  }

  private aplicar(actualizado: BorradorMatrizPEI): void {
    const i = this.registros.findIndex(r => r.id === actualizado.id);
    if (i >= 0) this.registros[i] = { ...this.registros[i], ...actualizado };
    this.cdr.markForCheck();
  }

  private fallo(err: any, accion: string): void {
    this.error = `No se pudo ${accion}: ${err?.message || 'error desconocido'}`;
    this.cdr.markForCheck();
  }

  validar(registro: BorradorMatrizPEI): void {
    this.ocupado = registro.id; this.error = '';
    this.borradores.validar(registro.id)
      .pipe(finalize(() => { this.ocupado = null; this.cdr.markForCheck(); }))
      .subscribe({ next: r => this.aplicar(r), error: e => this.fallo(e, 'validar el registro') });
  }

  aprobar(registro: BorradorMatrizPEI): void {
    this.ocupado = registro.id; this.error = '';
    this.borradores.aprobar(registro.id)
      .pipe(finalize(() => { this.ocupado = null; this.cdr.markForCheck(); }))
      .subscribe({ next: r => this.aplicar(r), error: e => this.fallo(e, 'aprobar el registro') });
  }

  abrirObservacion(registro: BorradorMatrizPEI): void {
    this.porObservar = registro;
    this.textoObservacion = registro.observacion || '';
  }

  cerrarObservacion(): void { this.porObservar = null; this.textoObservacion = ''; }

  confirmarObservacion(): void {
    const registro = this.porObservar;
    if (!registro || !this.textoObservacion.trim()) return;
    this.ocupado = registro.id; this.error = '';
    this.borradores.observar(registro.id, this.textoObservacion.trim())
      .pipe(finalize(() => { this.ocupado = null; this.cdr.markForCheck(); }))
      .subscribe({
        next: r => { this.aplicar(r); this.cerrarObservacion(); },
        error: e => this.fallo(e, 'registrar la observación'),
      });
  }

  pedirBorrado(registro: BorradorMatrizPEI): void { this.porBorrar = registro; }

  confirmarBorrado(): void {
    const registro = this.porBorrar;
    if (!registro) return;
    this.ocupado = registro.id; this.error = '';
    this.borradores.eliminar(registro.id)
      .pipe(finalize(() => { this.ocupado = null; this.cdr.markForCheck(); }))
      .subscribe({
        next: () => {
          this.registros = this.registros.filter(r => r.id !== registro.id);
          this.porBorrar = null;
          this.consolidarMatrices();
          this.cdr.markForCheck();
        },
        error: e => { this.fallo(e, 'eliminar el registro'); this.porBorrar = null; },
      });
  }

  // --- Selección y exportación ----------------------------------------------

  alternar(indice: number): void {
    if (this.seleccionadas.has(indice)) this.seleccionadas.delete(indice);
    else this.seleccionadas.add(indice);
  }

  alternarTodas(): void {
    if (this.todasSeleccionadas) this.seleccionadas.clear();
    else this.filas.forEach((_, i) => this.seleccionadas.add(i));
  }

  get todasSeleccionadas(): boolean {
    return this.filas.length > 0 && this.seleccionadas.size === this.filas.length;
  }

  get algunaSeleccionada(): boolean { return this.seleccionadas.size > 0; }

  private filasParaReporte(): any[] {
    if (!this.seleccionadas.size) return this.filas;
    return this.filas.filter((_, i) => this.seleccionadas.has(i));
  }

  private escapar(valor: string): string {
    return String(valor).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
  }

  /** Tabla con los colores embebidos: Excel los conserva y el PDF los imprime. */
  private tablaHtml(): string {
    const bloques = this.bloques;
    const filas = this.filasParaReporte();

    const grupo = bloques.map(b =>
      `<th colspan="${b.columnas.length}" bgcolor="${b.color}" ` +
      `style="background-color:${b.color};color:#FFFFFF;mso-pattern:${b.color} none;` +
      `border:1px solid #FFFFFF;padding:6px;font-size:10px;text-transform:uppercase;` +
      `-webkit-print-color-adjust:exact;print-color-adjust:exact">` +
      `${this.escapar(b.etiqueta)}</th>`).join('');

    const columnas = bloques.flatMap(b => b.columnas.map(c =>
      `<th bgcolor="${b.color}" style="background-color:${b.color};color:#FFFFFF;` +
      `mso-pattern:${b.color} none;border:1px solid #FFFFFF;padding:5px;font-size:9px;` +
      `text-transform:uppercase;-webkit-print-color-adjust:exact;print-color-adjust:exact">` +
      `${this.escapar(c.etiqueta)}</th>`)).join('');

    const cuerpo = filas.map(fila => {
      const celdas = bloques.flatMap(b => b.columnas.map(c =>
        `<td style="border:1px solid #cfd8dc;padding:4px;font-size:9px">` +
        `${this.escapar(this.celda(fila, c.clave))}</td>`)).join('');
      const fondo = fila.tipo_fila === 'resultado'
        ? ' bgcolor="#E8F5E9" style="background-color:#E8F5E9;mso-pattern:#E8F5E9 none;' +
          '-webkit-print-color-adjust:exact;print-color-adjust:exact"'
        : '';
      return `<tr${fondo}>${celdas}</tr>`;
    }).join('');

    const matriz = this.vista === 'matriz' ? 'Matriz PEI' : 'Articulación PAD → PEI';
    const alcance = this.seleccionadas.size
      ? `${filas.length} fila(s) seleccionada(s) de ${this.filas.length}`
      : `matriz completa (${filas.length} fila(s))`;

    return `<table style="border-collapse:collapse;font-family:Arial;margin:0 0 10px">
        <tr><td style="font-size:13px;font-weight:bold;color:#1B5E20;padding:0">
          GOBIERNO AUTÓNOMO MUNICIPAL DE SACABA
        </td></tr>
        <tr><td style="font-size:12px;font-weight:bold;color:#37474F;padding:2px 0 0">
          PLAN ESTRATÉGICO INSTITUCIONAL 2026-2030
        </td></tr>
        <tr><td style="font-size:12px;font-weight:bold;color:#37474F;padding:2px 0 0">
          ${matriz.toUpperCase()}
        </td></tr>
        <tr><td style="font-size:9px;color:#546E7A;padding:6px 0 0">
          ${alcance} · generado el ${new Date().toLocaleString('es-BO')}
        </td></tr>
      </table>
      <table style="border-collapse:collapse;font-family:Arial">
        <thead><tr>${grupo}</tr><tr>${columnas}</tr></thead>
        <tbody>${cuerpo}</tbody>
      </table>`;
  }

  private nombreArchivo(extension: string): string {
    const sello = new Date().toISOString().slice(0, 10);
    return `matriz-pei-${this.vista}-${sello}.${extension}`;
  }

  exportarExcel(): void {
    if (!this.filas.length) return;
    const contenido = `<html xmlns:x="urn:schemas-microsoft-com:office:excel">
      <head><meta charset="utf-8"></head><body>${this.tablaHtml()}</body></html>`;
    const blob = new Blob(['﻿', contenido], {
      type: 'application/vnd.ms-excel;charset=utf-8',
    });
    const url = URL.createObjectURL(blob);
    const enlace = document.createElement('a');
    enlace.href = url;
    enlace.download = this.nombreArchivo('xls');
    enlace.click();
    URL.revokeObjectURL(url);
  }

  exportarPdf(): void {
    if (!this.filas.length) return;
    const ventana = window.open('', '_blank');
    if (!ventana) {
      this.error = 'El navegador bloqueó la ventana del reporte. Habilite las ventanas emergentes.';
      this.cdr.markForCheck();
      return;
    }
    ventana.document.write(`<!doctype html><html><head><meta charset="utf-8">
      <title>${this.nombreArchivo('pdf')}</title>
      <style>@page { size: A3 landscape; margin: 10mm; }
        /* Sin esto el navegador imprime las cabeceras en blanco. */
        * { -webkit-print-color-adjust: exact !important;
            print-color-adjust: exact !important;
            color-adjust: exact !important; }
        body { margin: 0; }
        thead { display: table-header-group; }
        tr { page-break-inside: avoid; }
      </style></head><body>${this.tablaHtml()}</body></html>`);
    ventana.document.close();
    ventana.focus();
    setTimeout(() => ventana.print(), 300);
  }
}

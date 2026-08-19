import { ChangeDetectorRef, Component, OnInit } from '@angular/core';
import { forkJoin, map, of, catchError, finalize } from 'rxjs';
import { BorradorMatrizPAD, MatricesPadService } from '../matrices-pad.service';

interface ColumnaMatriz {
  clave: string;
  etiqueta: string;
}

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
 * Matriz "A" (27 columnas) con los mismos bloques y colores que el
 * visualizador del asistente.
 */
const BLOQUES_A: BloqueMatriz[] = [
  {
    etiqueta: 'PLANIFICACIÓN TERRITORIAL', clase: 'g-territorial', color: '#2E7D32',
    columnas: [
      { clave: 'sector', etiqueta: 'SECTOR' },
      { clave: 'cod_geografico', etiqueta: 'CÓD. GEOGRÁFICO' },
      { clave: 'politica', etiqueta: 'POLÍTICA' },
      { clave: 'cod_lineamiento_pad', etiqueta: 'CÓD. LINEAMIENTO' },
      { clave: '_lineamiento', etiqueta: 'LINEAMIENTO ESTRATÉGICO' },
      { clave: 'codigo_resultado_pad', etiqueta: 'CÓD. RESULTADO TERRITORIAL' },
      { clave: 'resultado_pad', etiqueta: 'RESULTADO TERRITORIAL PAD' },
    ],
  },
  {
    etiqueta: 'PRODUCTO TERRITORIAL', clase: 'g-producto', color: '#1F3864',
    columnas: [
      { clave: 'codigo_producto_pad', etiqueta: 'CÓD. PRODUCTO' },
      { clave: 'producto_pad', etiqueta: 'PRODUCTO (PROYECTO/PROGRAMA)' },
      { clave: 'territorializacion', etiqueta: 'TERRITORIALIZACIÓN' },
      { clave: 'responsable_pad', etiqueta: 'RESPONSABLE' },
    ],
  },
  {
    etiqueta: 'INDICADOR', clase: 'g-indicador', color: '#1565C0',
    columnas: [
      { clave: 'indicador', etiqueta: 'INDICADOR' },
      { clave: 'formula', etiqueta: 'FÓRMULA' },
      { clave: 'linea_base', etiqueta: 'LÍNEA BASE' },
      { clave: 'meta_2030', etiqueta: 'META 2030' },
    ],
  },
  {
    etiqueta: 'PROGRAMACIÓN FÍSICA', clase: 'g-fisica', color: '#1565C0',
    columnas: GESTIONES.map(a => ({ clave: `pf_${a}`, etiqueta: a })),
  },
  {
    etiqueta: 'PROGRAMACIÓN FINANCIERA', clase: 'g-financiera', color: '#8A5A1A',
    columnas: [
      { clave: 'cuenta_con_financiamiento', etiqueta: 'CUENTA CON FINANCIAMIENTO' },
      { clave: 'presupuesto_total', etiqueta: 'PRESUPUESTO TOTAL PAD (Bs.)' },
      ...GESTIONES.map(a => ({ clave: `presupuesto_${a}`, etiqueta: `${a} (Bs.)` })),
    ],
  },
];

/** Matriz "B" (33 columnas): articulación con los instrumentos del SIPEB. */
const BLOQUES_B: BloqueMatriz[] = [
  {
    etiqueta: 'PLANIFICACIÓN NACIONAL', clase: 'g-nacional', color: '#A6291F',
    columnas: [
      { clave: 'cod_eje_pgdesa', etiqueta: 'CÓD. EJE PGDESA (IMPACTO)' },
      { clave: 'objetivo_impacto', etiqueta: 'OBJETIVO DE IMPACTO' },
      { clave: 'cod_componente_pdesa', etiqueta: 'CÓD. COMPONENTE PDESA (EFECTO)' },
      { clave: 'objetivo_efecto', etiqueta: 'OBJETIVO DE EFECTO' },
    ],
  },
  {
    etiqueta: 'ACUERDOS INTERNACIONALES', clase: 'g-acuerdos', color: '#4B7BB5',
    columnas: [
      { clave: 'ods', etiqueta: 'CÓD. ODS' },
      { clave: 'ndc', etiqueta: 'CÓD. META NDC' },
      { clave: 'ndt', etiqueta: 'CÓD. PRINCIPIOS NDT' },
      { clave: 'compromiso_3030', etiqueta: 'COMPROMISOS 30/30' },
    ],
  },
  {
    etiqueta: 'PLANIFICACIÓN SECTORIAL', clase: 'g-sector', color: '#6B1A16',
    columnas: [
      { clave: 'cod_sector', etiqueta: 'CÓD. SECTOR' },
      { clave: 'sector', etiqueta: 'SECTOR' },
      { clave: 'cod_resultado_pds', etiqueta: 'CÓD. RESULTADO SECTORIAL' },
      { clave: 'resultado_pds', etiqueta: 'RESULTADO SECTORIAL' },
    ],
  },
  {
    etiqueta: 'PLANIFICACIÓN TERRITORIAL', clase: 'g-territorial', color: '#2E7D32',
    columnas: [
      { clave: 'cod_geografico', etiqueta: 'CÓD. GEOGRÁFICO' },
      { clave: 'eta', etiqueta: 'DENOMINACIÓN DE LA ETA' },
      { clave: 'cod_lineamiento_pad', etiqueta: 'CÓD. LINEAMIENTO' },
      { clave: '_lineamiento', etiqueta: 'LINEAMIENTO ESTRATÉGICO' },
      { clave: 'codigo_resultado_pad', etiqueta: 'CÓD. RESULTADO TERRITORIAL' },
      { clave: 'resultado_pad', etiqueta: 'RESULTADO TERRITORIAL' },
      { clave: 'indicador', etiqueta: 'INDICADOR' },
      { clave: 'formula', etiqueta: 'FÓRMULA' },
      { clave: 'linea_base', etiqueta: 'LÍNEA BASE' },
      { clave: 'meta_2030', etiqueta: 'META 2030' },
      ...GESTIONES.map(a => ({ clave: `pf_${a}`, etiqueta: `PROG. ${a}` })),
      { clave: 'presupuesto_total', etiqueta: 'PRESUPUESTO REFERENCIAL PAD' },
      ...GESTIONES.map(a => ({ clave: `presupuesto_${a}`, etiqueta: `${a}` })),
    ],
  },
];

/**
 * Registros de matrices PAD: listado de lo formulado, con acceso a la edición
 * y a las Matrices "A" y "B" de cada registro.
 */
@Component({
  selector: 'app-pad-registros',
  standalone: false,
  template: `
    <div class="registros">
      <div class="page-header">
        <div>
          <h2>Matrices PAD</h2>
          <p class="text-secondary">
            Registros generados con el asistente. El lápiz abre el registro para modificarlo;
            "Ver matrices" despliega sus Matrices A y B.
          </p>
        </div>
        <div class="acciones-header">
          <a routerLink="/matrices-pad" class="btn btn-outline btn-sm">← Volver</a>
          <a routerLink="/matrices-pad/nuevo" class="btn btn-primary btn-sm">+ Registro nuevo</a>
        </div>
      </div>

      <div class="card tabla-card">
        <table class="tabla">
          <thead>
            <tr>
              <th>Gestión</th>
              <th>Lineamiento</th>
              <th>Resultados</th>
              <th>Productos</th>
              <th>Estado</th>
              <th>Revisión</th>
              <th>Última actualización</th>
              <th class="col-acciones">Acciones</th>
            </tr>
          </thead>
          <tbody>
            <tr *ngFor="let r of registros">
              <td class="codigo">{{ r.gestion }}</td>
              <td class="celda-larga">{{ lineamientoDe(r) }}</td>
              <td class="num">{{ resultadosDe(r) }}</td>
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
                <a *ngIf="puede(r, 'editar')" [routerLink]="['/matrices-pad/nuevo', r.id]"
                   class="btn-icono" title="Editar este registro" aria-label="Editar">✎</a>
                <button *ngIf="puede(r, 'validar')" class="btn-icono validar"
                        (click)="validar(r)" [disabled]="ocupado === r.id"
                        title="Validar: doy por revisada la información" aria-label="Validar">✓</button>
                <button *ngIf="puede(r, 'aprobar')" class="btn-icono aprobar"
                        (click)="aprobar(r)" [disabled]="ocupado === r.id"
                        title="Aprobar: el registro queda permanente e inmutable"
                        aria-label="Aprobar">✔</button>
                <button *ngIf="puede(r, 'observar')" class="btn-icono observar"
                        (click)="abrirObservacion(r)" [disabled]="ocupado === r.id"
                        title="Registrar una observación" aria-label="Observar">✎̶</button>
                <button *ngIf="puede(r, 'borrar')" class="btn-icono borrar"
                        (click)="pedirBorrado(r)" [disabled]="ocupado === r.id"
                        title="Eliminar este registro" aria-label="Eliminar">🗑</button>
                <span *ngIf="!accionesDisponibles(r)" class="sin-acciones"
                      title="Registro aprobado: permanente e inmutable">🔒</span>
              </td>
            </tr>
            <tr *ngIf="cargando">
              <td colspan="8" class="vacio">Cargando registros…</td>
            </tr>
            <tr *ngIf="!cargando && !registros.length && !error">
              <td colspan="8" class="vacio">
                Todavía no hay matrices PAD registradas.
                <a routerLink="/matrices-pad/nuevo">Formule la primera</a>.
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
            Se eliminará la matriz PAD de la gestión <strong>{{ porBorrar.gestion }}</strong>
            con {{ resultadosDe(porBorrar) }} resultado(s) y {{ productosDe(porBorrar) }} producto(s).
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
          <p>
            Gestión <strong>{{ porObservar.gestion }}</strong> ·
            {{ lineamientoDe(porObservar) }}
          </p>
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

      <!-- MATRICES CONSOLIDADAS DE TODOS LOS REGISTROS -->
      <div class="matriz-vista card">
        <div class="matriz-tabs">
          <button class="btn" [class.btn-primary]="vista === 'a'" (click)="cambiarVista('a')">MATRIZ A</button>
          <button class="btn" [class.btn-primary]="vista === 'b'" (click)="cambiarVista('b')">MATRIZ B</button>
          <span class="contexto">
            {{ registros.length }} registro(s) · {{ filas.length }} fila(s)
            <strong *ngIf="seleccionadas.size">
              · {{ seleccionadas.size }} seleccionada(s)
            </strong>
            <em *ngIf="!seleccionadas.size">· sin selección: el reporte incluye todo</em>
          </span>
          <button class="btn btn-sm btn-excel" (click)="exportarExcel()"
                  [disabled]="!filas.length" title="Descargar la selección en Excel">
            ⬇ Excel
          </button>
          <button class="btn btn-sm btn-pdf" (click)="exportarPdf()"
                  [disabled]="!filas.length" title="Generar el PDF de la selección">
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
                  <a [routerLink]="['/matrices-pad/nuevo', fila._borradorId]" class="btn-icono"
                     title="Editar el registro que originó esta fila" aria-label="Editar">✎</a>
                </td>
              </tr>
              <tr *ngIf="!filas.length">
                <td [attr.colspan]="totalColumnas + 3" class="vacio">
                  Todavía no hay filas en la Matriz {{ vista === 'a' ? 'A' : 'B' }}.
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
    .btn-icono.validar { color: #1B5E20; }
    .btn-icono.aprobar { color: #0D47A1; }
    .btn-icono.observar { color: #8A6100; }
    .btn-icono.borrar { color: var(--warn); }
    .btn-icono[disabled] { opacity: 0.4; cursor: not-allowed; }
    .sin-acciones { font-size: 0.9rem; opacity: 0.6; }
    .badge.rev { font-size: 0.625rem; }
    .badge.rev.pendiente { background: #ECEFF1; color: #455A64; }
    .badge.rev.validado { background: #E3F2FD; color: #0D47A1; }
    .badge.rev.observado { background: #FFF8E1; color: #8A6100; }
    .badge.rev.aprobado { background: #E8F5E9; color: #1B5E20; }
    .obs { font-size: 0.625rem; color: #8A6100; margin-top: 0.15rem; max-width: 220px; }

    .modal-fondo { position: fixed; inset: 0; background: rgba(0,0,0,.45); display: flex; align-items: center; justify-content: center; z-index: 1000; padding: 1rem; }
    .modal { background: var(--surface, #fff); border-radius: 10px; padding: 1.5rem; max-width: 460px; width: 100%; box-shadow: 0 10px 40px rgba(0,0,0,.25); }
    .modal h3 { margin: 0 0 0.6rem; font-size: 1rem; color: var(--primary); }
    .modal p { font-size: 0.8125rem; color: var(--text-secondary); margin: 0 0 0.6rem; }
    .modal .advertencia { color: var(--warn); font-weight: 600; }
    .modal-acciones { display: flex; justify-content: flex-end; gap: 0.5rem; margin-top: 1rem; }
    .btn-peligro { background: var(--warn); color: #fff; border: none; border-radius: 6px; padding: 0.5rem 1rem; cursor: pointer; font-size: 0.8125rem; font-weight: 600; }
    .btn-peligro[disabled] { opacity: 0.6; cursor: not-allowed; }

    .badge { font-size: 0.6875rem; padding: 0.15rem 0.5rem; border-radius: 999px; background: #FFF8E1; color: #8A6100; font-weight: 700; }
    .badge.badge-completo { background: #E8F5E9; color: var(--success); }

    .btn-icono { display: inline-flex; align-items: center; justify-content: center; width: 30px; height: 30px; margin: 0 0.1rem; border-radius: 6px; border: 1px solid var(--border); color: var(--primary); background: transparent; text-decoration: none; font-size: 0.9rem; cursor: pointer; }
    .btn-icono:hover { border-color: var(--primary); background: #E8F5E9; }

    .vacio { text-align: center; color: var(--text-secondary); padding: 2rem; }
    .msg-box { margin-top: 1rem; padding: 0.6rem 0.8rem; border-radius: 6px; font-size: 0.8125rem; display: flex; align-items: center; gap: 0.75rem; flex-wrap: wrap; }
    .msg-box.error { background: #FFEBEE; color: var(--warn); }

    .matriz-vista { margin-top: 1.5rem; padding: 1.25rem; border: 2px solid var(--primary); }
    .matriz-tabs { display: flex; gap: 0.5rem; margin-bottom: 1rem; align-items: center; flex-wrap: wrap; }
    .matriz-tabs .btn { font-size: 0.75rem; padding: 0.375rem 0.75rem; }
    .contexto { font-size: 0.75rem; color: var(--text-secondary); flex: 1; }
    .cerrar { margin-left: auto; }
    .matriz-scroll { overflow-x: auto; }
    .mz { border-collapse: collapse; font-size: 0.625rem; width: 100%; }
    .mz th { color: #fff; padding: 0.3rem 0.4rem; text-transform: uppercase; border: 1px solid rgba(255,255,255,0.25); font-weight: 700; vertical-align: middle; }
    .mz tr.grupo th { font-size: 0.625rem; letter-spacing: 0.02em; }
    .mz tr.columna th { font-size: 0.5625rem; min-width: 78px; }

    /* Misma paleta por bloque que el visualizador del asistente */
    .g-nacional { background: #A6291F; }
    .g-acuerdos { background: #4B7BB5; }
    .g-sector { background: #6B1A16; }
    .g-territorial { background: #2E7D32; }
    .g-producto { background: #1F3864; }
    .g-indicador { background: #1565C0; }
    .g-fisica { background: #1565C0; }
    .g-financiera { background: #8A5A1A; }
    .g-registro { background: var(--primary); }
    .col-check { width: 34px; text-align: center; }
    .mz tbody tr.fila-elegida td { background: #FFF8E1; }
    .mz tbody tr.fila-elegida.fila-resultado td { background: #FFF3C4; }
    .btn-excel { background: #1B5E20; color: #fff; border: none; }
    .btn-pdf { background: #B3261E; color: #fff; border: none; }
    .btn-excel[disabled], .btn-pdf[disabled] { opacity: .5; cursor: not-allowed; }
    .contexto em { font-style: normal; opacity: .8; }
    .mz td { padding: 0.25rem 0.4rem; border: 1px solid var(--border); vertical-align: top; max-width: 200px; }
    .col-registro { white-space: nowrap; }
    .col-editar { text-align: center; width: 60px; }
    .chip-gestion { font-family: 'Courier New', monospace; font-weight: 800; margin-right: 0.25rem; }
    .chip-estado { font-size: 0.5rem; padding: 0.05rem 0.3rem; border-radius: 999px; background: #FFF8E1; color: #8A6100; font-weight: 700; }
    .chip-estado.completo { background: #E8F5E9; color: #1B5E20; }
    .mz tbody tr.fila-resultado td { background: #E8F5E9; font-weight: 600; }
    .mz tbody tr:hover td { background: #F0F7F3; }
  `],
})
export class PadRegistrosComponent implements OnInit {
  registros: BorradorMatrizPAD[] = [];
  cargando = true;
  error = '';

  vista: 'a' | 'b' = 'a';
  filasA: any[] = [];
  filasB: any[] = [];
  cargandoMatriz = false;
  errorMatriz = '';

  /** Registro con una acción en curso, para no dispararla dos veces. */
  ocupado: string | null = null;
  porBorrar: BorradorMatrizPAD | null = null;
  porObservar: BorradorMatrizPAD | null = null;
  textoObservacion = '';

  constructor(
    private matrices: MatricesPadService,
    private cdr: ChangeDetectorRef,
  ) {}

  ngOnInit(): void {
    this.cargar();
  }

  /**
   * `finalize` apaga el indicador de carga pase lo que pase: si el observable
   * completara sin emitir, un `next`/`error` no alcanzaría y la vista quedaría
   * colgada en "Cargando registros".
   */
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
    this.matrices.listar({ page: pagina })
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
          this.error = `No se pudieron cargar los registros de matrices PAD (${detalle}).`;
          this.registros = [];
          this.cdr.markForCheck();
        },
      });
  }

  /** El backend decide qué puede hacer el usuario; el front solo lo refleja. */
  puede(registro: BorradorMatrizPAD, accion: keyof NonNullable<BorradorMatrizPAD['permisos']>): boolean {
    return !!registro.permisos?.[accion];
  }

  accionesDisponibles(registro: BorradorMatrizPAD): boolean {
    return this.puede(registro, 'editar') || this.puede(registro, 'validar')
      || this.puede(registro, 'aprobar') || this.puede(registro, 'observar')
      || this.puede(registro, 'borrar');
  }

  claseRevision(registro: BorradorMatrizPAD): string {
    return (registro.estado_revision || 'PENDIENTE').toLowerCase();
  }

  private aplicar(actualizado: BorradorMatrizPAD): void {
    const i = this.registros.findIndex(r => r.id === actualizado.id);
    if (i >= 0) this.registros[i] = { ...this.registros[i], ...actualizado };
    this.cdr.markForCheck();
  }

  private fallo(err: any, accion: string): void {
    this.error = `No se pudo ${accion}: ${err?.message || 'error desconocido'}`;
    this.cdr.markForCheck();
  }

  validar(registro: BorradorMatrizPAD): void {
    this.ocupado = registro.id;
    this.error = '';
    this.matrices.validar(registro.id)
      .pipe(finalize(() => { this.ocupado = null; this.cdr.markForCheck(); }))
      .subscribe({
        next: r => this.aplicar(r),
        error: e => this.fallo(e, 'validar el registro'),
      });
  }

  aprobar(registro: BorradorMatrizPAD): void {
    this.ocupado = registro.id;
    this.error = '';
    this.matrices.aprobar(registro.id)
      .pipe(finalize(() => { this.ocupado = null; this.cdr.markForCheck(); }))
      .subscribe({
        next: r => this.aplicar(r),
        error: e => this.fallo(e, 'aprobar el registro'),
      });
  }

  abrirObservacion(registro: BorradorMatrizPAD): void {
    this.porObservar = registro;
    this.textoObservacion = registro.observacion || '';
  }

  cerrarObservacion(): void {
    this.porObservar = null;
    this.textoObservacion = '';
  }

  confirmarObservacion(): void {
    const registro = this.porObservar;
    if (!registro || !this.textoObservacion.trim()) return;
    this.ocupado = registro.id;
    this.error = '';
    this.matrices.observar(registro.id, this.textoObservacion.trim())
      .pipe(finalize(() => { this.ocupado = null; this.cdr.markForCheck(); }))
      .subscribe({
        next: r => { this.aplicar(r); this.cerrarObservacion(); },
        error: e => this.fallo(e, 'registrar la observación'),
      });
  }

  pedirBorrado(registro: BorradorMatrizPAD): void {
    this.porBorrar = registro;
  }

  confirmarBorrado(): void {
    const registro = this.porBorrar;
    if (!registro) return;
    this.ocupado = registro.id;
    this.error = '';
    this.matrices.eliminar(registro.id)
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

  // ------------------------------------------------------------------
  // Selección de filas y exportación
  // ------------------------------------------------------------------

  /** Índices de las filas marcadas en la matriz visible. */
  seleccionadas = new Set<number>();

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

  get algunaSeleccionada(): boolean {
    return this.seleccionadas.size > 0;
  }

  /** Sin selección, el reporte abarca toda la matriz. */
  private filasParaReporte(): any[] {
    if (!this.seleccionadas.size) return this.filas;
    return this.filas.filter((_, i) => this.seleccionadas.has(i));
  }

  private escapar(valor: string): string {
    return String(valor)
      .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
  }

  /**
   * Tabla HTML con los colores de cada bloque en estilos embebidos: Excel la
   * abre conservando la cabecera, y el navegador la imprime igual en el PDF.
   */
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

    const matriz = this.vista === 'a' ? 'Matriz A' : 'Matriz B';
    const alcance = this.seleccionadas.size
      ? `${filas.length} fila(s) seleccionada(s) de ${this.filas.length}`
      : `matriz completa (${filas.length} fila(s))`;

    // Encabezado institucional: entidad, instrumento y matriz, en ese orden.
    return `<table style="border-collapse:collapse;font-family:Arial;margin:0 0 10px">
        <tr><td style="font-size:13px;font-weight:bold;color:#1B5E20;padding:0">
          GOBIERNO AUTÓNOMO MUNICIPAL DE SACABA
        </td></tr>
        <tr><td style="font-size:12px;font-weight:bold;color:#37474F;padding:2px 0 0">
          PLAN AUTONÓMICO DE DESARROLLO 2026-2030
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
    return `matriz-${this.vista}-pad-${sello}.${extension}`;
  }

  /** Excel abre la tabla HTML conservando colores y cabecera agrupada. */
  exportarExcel(): void {
    if (!this.filas.length) return;
    const contenido = `<html xmlns:x="urn:schemas-microsoft-com:office:excel">
      <head><meta charset="utf-8"></head><body>${this.tablaHtml()}</body></html>`;
    const blob = new Blob(['\ufeff', contenido], {
      type: 'application/vnd.ms-excel;charset=utf-8',
    });
    const url = URL.createObjectURL(blob);
    const enlace = document.createElement('a');
    enlace.href = url;
    enlace.download = this.nombreArchivo('xls');
    enlace.click();
    URL.revokeObjectURL(url);
  }

  /**
   * Abre la matriz en una ventana lista para imprimir; el destino "Guardar
   * como PDF" del navegador produce el archivo.
   */
  exportarPdf(): void {
    if (!this.filas.length) return;
    const ventana = window.open('', '_blank');
    if (!ventana) {
      this.error = 'El navegador bloqueó la ventana del reporte. Habilite las ventanas emergentes para este sitio.';
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

  get bloques(): BloqueMatriz[] {
    return this.vista === 'a' ? BLOQUES_A : BLOQUES_B;
  }

  /** Los índices seleccionados no son equivalentes entre matrices. */
  cambiarVista(nueva: 'a' | 'b'): void {
    if (this.vista === nueva) return;
    this.vista = nueva;
    this.seleccionadas.clear();
  }

  get totalColumnas(): number {
    return this.bloques.reduce((n, b) => n + b.columnas.length, 0);
  }

  get filas(): any[] {
    return this.vista === 'a' ? this.filasA : this.filasB;
  }

  /**
   * Junta las Matrices A y B de todos los registros en una sola vista. Cada
   * fila se etiqueta con el borrador que la originó para que el lápiz sepa
   * qué registro abrir.
   */
  private consolidarMatrices(): void {
    if (!this.registros.length) {
      this.filasA = [];
      this.filasB = [];
      this.cdr.markForCheck();
      return;
    }
    this.cargandoMatriz = true;
    this.errorMatriz = '';

    const peticiones = this.registros.map(registro =>
      forkJoin({
        a: this.matrices.matrizA(registro.id).pipe(catchError(() => of([]))),
        b: this.matrices.matrizB(registro.id).pipe(catchError(() => of([]))),
      }).pipe(
        map(({ a, b }) => ({
          a: this.etiquetar(a, registro),
          b: this.etiquetar(b, registro),
        })),
      ),
    );

    forkJoin(peticiones)
      .pipe(finalize(() => { this.cargandoMatriz = false; this.cdr.markForCheck(); }))
      .subscribe({
        next: bloques => {
          this.filasA = bloques.flatMap(x => x.a);
          this.filasB = bloques.flatMap(x => x.b);
          this.cdr.markForCheck();
        },
        error: () => {
          this.errorMatriz = 'No se pudieron consolidar las matrices de los registros.';
          this.cdr.markForCheck();
        },
      });
  }

  private etiquetar(respuesta: any, registro: BorradorMatrizPAD): any[] {
    const filas = respuesta?.filas || (Array.isArray(respuesta) ? respuesta : []);
    return filas.map((fila: any) => ({
      ...fila,
      _borradorId: registro.id,
      _gestion: registro.gestion,
      _estado: registro.estado,
      _lineamiento: this.lineamientoDe(registro),
    }));
  }

  celda(fila: any, clave: string): string {
    const valor = fila?.[clave];
    if (valor === null || valor === undefined || valor === '') return '-';
    if (typeof valor === 'boolean') return valor ? 'SÍ' : 'NO';
    return String(valor);
  }

  private seccion(registro: BorradorMatrizPAD, clave: string): any {
    return (registro?.datos as any)?.[clave] || {};
  }

  lineamientoDe(registro: BorradorMatrizPAD): string {
    const lineamiento = this.seccion(registro, 'p5_lineamiento')?.lineamiento || {};
    const codigo = lineamiento.codigo ? `${lineamiento.codigo} — ` : '';
    return `${codigo}${lineamiento.denominacion || 'Sin lineamiento'}`;
  }

  private resultados(registro: BorradorMatrizPAD): any[] {
    const datos = (registro?.datos as any) || {};
    return Array.isArray(datos.resultados) ? datos.resultados : [];
  }

  resultadosDe(registro: BorradorMatrizPAD): number {
    return this.resultados(registro).length;
  }

  productosDe(registro: BorradorMatrizPAD): number {
    return this.resultados(registro).reduce(
      (total, r) => total + ((r?.productos || []).length), 0,
    );
  }

  fecha(registro: BorradorMatrizPAD): string {
    const valor = registro.updated_at || registro.created_at;
    return valor ? new Date(valor).toLocaleString('es-BO') : '-';
  }
}

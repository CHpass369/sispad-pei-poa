import { ChangeDetectorRef, Component, OnInit } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { finalize, forkJoin } from 'rxjs';
import { environment } from '../../../environments/environment';

interface ColumnaFuente { ff_of: string; denominacion: string; }

interface Actividad {
  id: number;
  categoria: string;
  denominacion: string;
  unidad_ejecutora: string;
  direccion_administrativa: string;
  distrito: string;
  codigo_sisin: string;
  actividad: string;
  da_id: string;
  ue_id: string;
  montos: Record<string, string>;
  estado_revision?: string;
  /** Lo que aportaron las actas de priorización a esta fila. */
  priorizaciones?: Priorizacion[];
  monto_priorizado?: number;
}

interface Priorizacion {
  acta: string;
  otb: string;
  distrito: string;
  estado_acta: string;
  proyecto: string;
  par: string;
  monto: number;
}

interface Subprograma {
  codigo: string;
  denominacion: string;
  actividades: Actividad[];
  total: Record<string, string>;
}

interface Programa {
  /** Se codifica con el rango de la directriz: `170-179`. */
  codigo: string;
  denominacion: string;
  finalidad_funcion: string;
  sector_economico: string;
  subprogramas: Subprograma[];
  total: Record<string, string>;
}

interface ArbolGastos {
  gestion: number;
  gestion_id: number | null;
  /** Techo por FF/OF que viene del Presupuesto General de Recursos. */
  techos: Record<string, string>;
  /** Techo menos gastado: lo que queda por asignar de cada fuente. */
  diferencia: Record<string, string>;
  columnas: ColumnaFuente[];
  programas: Programa[];
  total: Record<string, string>;
}

/**
 * Presupuesto General de Gastos.
 *
 * Reproduce la hoja oficial: el árbol Programa → Subprograma → Actividad, con
 * las fuentes de financiamiento como columnas. Dos diferencias con la
 * planilla: los subtotales se derivan en vez de ser fórmulas que alguien pueda
 * romper, y cada categoría programática lleva su propio estado de revisión,
 * porque las unidades presentan su gasto en momentos distintos.
 */
@Component({
  selector: 'app-presupuesto-gastos',
  standalone: false,
  template: `
    <div class="gastos lienzo lienzo-datos">
      <div class="encabezado-pantalla">
        <div>
          <h2>Presupuesto General de Gastos</h2>
          <p class="sub">
            Distribución del gasto por categoría programática y fuente de
            financiamiento, gestión {{ arbol?.gestion || '—' }}.
          </p>
        </div>
        <div class="encabezado-acciones">
          <span class="contador" *ngIf="arbol">
            {{ arbol.programas.length }} programas · {{ totalActividades() }} categorías
          </span>
          <button class="btn btn-outline btn-sm" (click)="expandirTodo(true)">Expandir</button>
          <button class="btn btn-outline btn-sm" (click)="expandirTodo(false)">Contraer</button>
          <button class="btn btn-outline btn-sm" (click)="cargar()" [disabled]="cargando">
            Actualizar
          </button>
          <button class="btn btn-accent btn-sm" *ngIf="!editando" (click)="abrirAlta('PROGRAMA')">
            + Programa
          </button>
          <button class="btn btn-primary btn-sm" *ngIf="!editando" (click)="editando = true">
            Editar montos
          </button>
          <button class="btn btn-outline btn-sm" *ngIf="editando"
                  (click)="cancelarEdicion()" [disabled]="guardando">Cancelar</button>
          <button class="btn btn-accent btn-sm" *ngIf="editando"
                  (click)="guardarMontos()" [disabled]="guardando || !pendientes.size">
            {{ guardando ? 'Guardando…' : 'Guardar (' + pendientes.size + ')' }}
          </button>
        </div>
      </div>

      <div class="msg-box error" *ngIf="error">{{ error }}</div>

      <div class="sin-datos" *ngIf="cargando">
        <div class="esqueleto" style="width:320px"></div>
        <span>Cargando el presupuesto de gastos…</span>
      </div>

      <div class="alta" *ngIf="alta">
        <h4>
          Nuevo {{ alta.nivel === 'PROGRAMA' ? 'programa'
                 : alta.nivel === 'SUBPROGRAMA' ? 'subprograma' : 'actividad' }}
          <span *ngIf="alta.padreDenominacion" class="sub">en {{ alta.padreDenominacion }}</span>
        </h4>
        <div class="campos-alta">
          <input class="form-control cod-input" [(ngModel)]="alta.codigo"
                 [placeholder]="alta.nivel === 'ACTIVIDAD' ? 'Actividad (023)' : 'Código (101)'"
                 maxlength="12">
          <input class="form-control cod-input" *ngIf="alta.nivel === 'ACTIVIDAD'"
                 [(ngModel)]="alta.sisin" placeholder="SISIN WEB" maxlength="20"
                 title="Código SISIN WEB del proyecto">
          <input class="form-control" [(ngModel)]="alta.denominacion"
                 placeholder="Denominación">
          <input class="form-control cod-input" *ngIf="alta.nivel === 'ACTIVIDAD'"
                 [(ngModel)]="alta.unidadEjecutora" placeholder="UE" maxlength="12">
          <button class="btn btn-primary btn-sm" (click)="crear()"
                  [disabled]="!alta.codigo.trim() || !alta.denominacion.trim() || guardando">
            Crear
          </button>
          <button class="btn btn-outline btn-sm" (click)="alta = null">Cancelar</button>
        </div>
        <p class="guia-directriz" *ngIf="alta.codigo.trim()"
           [class.invalida]="!rangoDelAlta()">
          <ng-container *ngIf="rangoDelAlta() as r">
            Rango {{ r.codigo }} · {{ r.denominacion }}
            <span *ngIf="r.sector_economico">— sector {{ r.sector_economico }}</span>
            <span *ngIf="r.finalidad_funcion"> · fin/fun {{ r.finalidad_funcion }}</span>
          </ng-container>
          <ng-container *ngIf="!rangoDelAlta()">
            {{ motivoDelAlta() }}
          </ng-container>
        </p>
      </div>

      <div class="tabla-caja" *ngIf="!cargando && arbol">
        <table class="tabla tabla-compacta">
          <thead>
            <tr>
              <th class="col-cat">Categoría</th>
              <th class="col-den">Denominación</th>
              <th class="col-org">DA</th>
              <th class="col-org">UE</th>
              <th *ngFor="let c of arbol.columnas" class="num" [title]="c.denominacion">
                {{ c.ff_of }}
              </th>
              <th class="num">Total</th>
              <th>Revisión</th>
              <th class="col-acc"></th>
            </tr>
          </thead>
          <tbody>
            <ng-container *ngFor="let p of arbol.programas">
              <tr class="fila-programa" (click)="alternar(p.codigo)">
                <td class="cod">{{ abierto(p.codigo) ? '▾' : '▸' }} {{ p.codigo }}</td>
                <td class="col-den">
                  <strong>{{ p.denominacion }}</strong>
                  <small class="norma" *ngIf="p.sector_economico">
                    sector {{ p.sector_economico }}
                    <span *ngIf="p.finalidad_funcion">
                      · fin/fun {{ p.finalidad_funcion }}</span>
                  </small>
                </td>
                <td></td>
                <td></td>
                <td *ngFor="let c of arbol.columnas" class="num">
                  {{ moneda(p.total[c.ff_of]) }}
                </td>
                <td class="num"><strong>{{ moneda(sumar(p.total)) }}</strong></td>
                <td></td>
                <td class="col-acc">
                  <button class="icono-fila" title="Agregar subprograma"
                          (click)="abrirAlta('SUBPROGRAMA', p); $event.stopPropagation()">+</button>
                </td>
              </tr>

              <ng-container *ngIf="abierto(p.codigo)">
                <ng-container *ngFor="let s of p.subprogramas">
                  <tr class="fila-subprograma" (click)="alternar(p.codigo + s.codigo)">
                    <td class="cod sangria-1">
                      {{ abierto(p.codigo + s.codigo) ? '▾' : '▸' }} {{ s.codigo }}
                    </td>
                    <td class="col-den">{{ s.denominacion }}</td>
                    <td></td>
                    <td></td>
                    <td *ngFor="let c of arbol.columnas" class="num">
                      {{ moneda(s.total[c.ff_of]) }}
                    </td>
                    <td class="num">{{ moneda(sumar(s.total)) }}</td>
                    <td></td>
                    <td class="col-acc">
                      <button class="icono-fila" title="Agregar actividad"
                              (click)="abrirAlta('ACTIVIDAD', p, s); $event.stopPropagation()">+</button>
                    </td>
                  </tr>

                  <tr class="fila-actividad" *ngFor="let a of s.actividades"
                      [class.oculta]="!abierto(p.codigo + s.codigo)">
                    <td class="cod sangria-2">{{ a.categoria }}</td>
                    <td class="col-den">
                      {{ a.denominacion }}
                      <button class="marca-prior" *ngIf="a.monto_priorizado"
                              (click)="alternarPriorizacion(a)"
                              [title]="'Incluye Bs ' + moneda(a.monto_priorizado)
                                       + ' priorizados en actas'">
                        {{ verPriorizacion(a) ? '▾' : '▸' }}
                        priorizado Bs {{ moneda(a.monto_priorizado) }}
                      </button>
                      <ul class="detalle-prior" *ngIf="verPriorizacion(a)">
                        <li *ngFor="let x of a.priorizaciones">
                          <span class="otb">{{ x.otb }}</span>
                          <span class="dist">{{ x.distrito }}</span>
                          <span class="par">{{ x.par }}</span>
                          <span class="monto">Bs {{ moneda(x.monto) }}</span>
                          <span class="pastilla" [ngClass]="'e-' + x.estado_acta">
                            {{ x.estado_acta }}</span>
                        </li>
                      </ul>
                    </td>
                    <td class="col-org">
                      <select class="celda-org" [value]="a.da_id"
                              (change)="elegirOrg(a, 'da', $event)"
                              [title]="nombreDe(direcciones, a.da_id)">
                        <option value="">—</option>
                        <option *ngFor="let d of direcciones" [value]="d.id">
                          {{ d.codigo }} · {{ d.nombre }}
                        </option>
                      </select>
                    </td>
                    <td class="col-org">
                      <select class="celda-org" [value]="a.ue_id"
                              (change)="elegirOrg(a, 'ue', $event)"
                              [title]="nombreDe(ejecutoras, a.ue_id)">
                        <option value="">—</option>
                        <!-- Solo las de la DA elegida: una UE pertenece a una
                             direccion y ofrecerlas todas invita al error. -->
                        <option *ngFor="let u of ejecutorasDe(a.da_id)" [value]="u.id">
                          {{ u.codigo }} · {{ u.nombre }}
                        </option>
                      </select>
                    </td>
                    <td *ngFor="let c of arbol.columnas" class="num">
                      <span *ngIf="!editando || a.estado_revision === 'APROBADO'">
                        {{ moneda(a.montos[c.ff_of]) }}
                      </span>
                      <input *ngIf="editando && a.estado_revision !== 'APROBADO'"
                             class="celda-num" type="number" step="0.01"
                             [value]="valorMonto(a, c.ff_of)"
                             (input)="editarMonto(a, c.ff_of, $event)">
                    </td>
                    <td class="num">{{ moneda(totalVivo(a)) }}</td>
                    <td>
                      <span class="pastilla" [ngClass]="claseRevision(a)">
                        {{ etiquetaRevision(a) }}
                      </span>
                    </td>
                    <td class="col-acc">
                      <button class="icono-fila" title="Validar esta categoría"
                              *ngIf="puedeValidar(a)" (click)="validar(a)"
                              [disabled]="ocupado === a.id">✓</button>
                      <button class="icono-fila aprobar" title="Aprobar"
                              *ngIf="puedeAprobar(a)" (click)="aprobar(a)"
                              [disabled]="ocupado === a.id">✔</button>
                      <button class="icono-fila observar" title="Observar"
                              *ngIf="puedeObservar(a)" (click)="observar(a)"
                              [disabled]="ocupado === a.id">✎̶</button>
                      <span *ngIf="!puedeValidar(a) && !puedeAprobar(a) && !puedeObservar(a)"
                            title="Categoría aprobada">🔒</span>
                    </td>
                  </tr>
                </ng-container>
              </ng-container>
            </ng-container>

            <tr *ngIf="!arbol.programas.length">
              <td [attr.colspan]="arbol.columnas.length + 6">
                <div class="sin-datos">
                  <span class="sin-datos-icono">▤</span>
                  <strong>No hay gasto distribuido en esta gestión</strong>
                  <span>Importe la planilla o registre las categorías programáticas.</span>
                </div>
              </td>
            </tr>
          </tbody>
          <tfoot *ngIf="arbol.programas.length">
            <tr class="fila-total">
              <td colspan="4">TOTAL GASTOS</td>
              <td *ngFor="let c of arbol.columnas" class="num">
                {{ moneda(arbol.total[c.ff_of]) }}
              </td>
              <td class="num">{{ moneda(sumar(arbol.total)) }}</td>
              <td colspan="2"></td>
            </tr>
            <tr class="fila-techo">
              <td colspan="4">TECHO POR FUENTE</td>
              <td *ngFor="let c of arbol.columnas" class="num">
                {{ moneda(arbol.techos[c.ff_of]) }}
              </td>
              <td class="num">{{ moneda(sumar(arbol.techos)) }}</td>
              <td colspan="2"></td>
            </tr>
            <tr class="fila-diferencia">
              <td colspan="4">DIFERENCIA POR ASIGNAR</td>
              <td *ngFor="let c of arbol.columnas" class="num"
                  [class.negativa]="negativa(arbol.diferencia[c.ff_of])"
                  [class.en-cero]="enCero(arbol.diferencia[c.ff_of])">
                {{ moneda(arbol.diferencia[c.ff_of]) }}
              </td>
              <td class="num" [class.negativa]="negativa(sumar(arbol.diferencia))">
                {{ moneda(sumar(arbol.diferencia)) }}
              </td>
              <td colspan="2"></td>
            </tr>
          </tfoot>
        </table>
      </div>
    </div>
  `,
  styles: [`
    .col-cat { min-width: 120px; }
    .col-den { min-width: 300px; max-width: 460px; }
    .col-acc { width: 82px; text-align: center; white-space: nowrap; }
    .contador { font-size: 0.75rem; color: var(--text-secondary); }

    .fila-programa td {
      background: var(--pip-green-100); font-weight: 600; cursor: pointer;
      border-top: 2px solid var(--pip-green-500);
    }
    .guia-directriz {
      margin: 0.35rem 0 0; font-size: 0.6875rem; color: var(--pip-green-700);
    }
    .guia-directriz.invalida { color: #B3261E; font-weight: 600; }
    .norma {
      display: block; font-size: 0.625rem; font-weight: 400;
      color: var(--text-secondary);
    }
    .fila-subprograma td { background: var(--realce); cursor: pointer; }
    .fila-actividad.oculta { display: none; }
    .sangria-1 { padding-left: 1.2rem !important; }
    .sangria-2 { padding-left: 2.4rem !important; color: var(--text-secondary); }
    /* Tres filas de control fijas al pie: gasto, techo y lo que resta. */
    .fila-total td {
      background: var(--primary); color: #fff; font-weight: 700;
      position: sticky; bottom: 3.4rem;
    }
    .fila-techo td {
      background: var(--pip-ink); color: #fff; font-weight: 600;
      position: sticky; bottom: 1.7rem;
    }
    .fila-diferencia td {
      background: var(--pip-gold); color: #2A1E05; font-weight: 700;
      position: sticky; bottom: 0;
    }
    .fila-diferencia .negativa { background: var(--pip-danger); color: #fff; }
    .fila-diferencia .en-cero { opacity: .62; }

    .pastilla {
      display: inline-block; padding: 0.1rem 0.5rem; border-radius: 999px;
      font-size: 0.5625rem; font-weight: 700; letter-spacing: 0.04em;
    }
    .r-borrador { background: var(--neutro-fondo); color: var(--neutro-tinta); }
    .r-validado { background: var(--info-fondo); color: var(--info-tinta); }
    .r-observado { background: var(--aviso-fondo); color: var(--aviso-tinta); }
    .r-aprobado { background: var(--ok-fondo); color: var(--ok-tinta); }

    .icono-fila {
      width: 22px; height: 22px; border-radius: 4px; border: 1px solid var(--border);
      background: transparent; color: var(--text-secondary); cursor: pointer;
      font-size: 0.6875rem; margin: 0 1px;
    }
    .icono-fila:hover { border-color: var(--primary); color: var(--primary); }
    .icono-fila.aprobar:hover { border-color: var(--ok-tinta); color: var(--ok-tinta); }
    .icono-fila.observar:hover { border-color: var(--aviso-tinta); color: var(--aviso-tinta); }
    .col-org { width: 86px; }
    .celda-org {
      width: 100%; border: none; background: transparent; font-size: 0.6875rem;
      padding: 0.15rem; color: var(--text);
    }
    .celda-org:hover { background: var(--realce); }
    .celda-num {
      width: 100%; max-width: 108px; text-align: right; padding: 0.1rem 0.3rem;
      border: 1px solid var(--border); border-radius: 4px; background: var(--surface);
      font-family: var(--font-mono); font-size: 0.625rem;
      font-variant-numeric: tabular-nums; color: var(--text);
    }
    .celda-num:focus { outline: 2px solid var(--pip-green-500); outline-offset: -1px; }
    .alta {
      margin-bottom: var(--e-2); padding: var(--e-3); border-radius: var(--radius);
      background: var(--surface); border: 1px solid var(--pip-green-500);
    }
    .alta h4 { margin: 0 0 0.6rem; font-size: 0.9rem; }
    .alta h4 .sub { font-weight: 400; margin-left: 0.4rem; }
    .campos-alta { display: flex; gap: 0.5rem; flex-wrap: wrap; align-items: center; }
    .campos-alta .form-control { min-width: 220px; flex: 1; }
    .campos-alta .cod-input { min-width: 96px; max-width: 130px; flex: none; font-family: var(--font-mono); }
    .msg-box.error {
      background: var(--error-fondo); color: var(--error-tinta);
      padding: 0.7rem 0.9rem; border-radius: var(--radius); margin-bottom: var(--e-2);
    }
    .marca-prior {
      display: inline-block; margin-left: 0.4rem; border: none; cursor: pointer;
      background: #BBDEFB; color: #0D47A1; border-radius: 999px;
      padding: 0.05rem 0.45rem; font-size: 0.5625rem; font-weight: 700;
    }
    .marca-prior:hover { background: #90CAF9; }
    .detalle-prior { list-style: none; margin: 0.3rem 0 0; padding: 0; }
    .detalle-prior li {
      display: flex; gap: 0.5rem; align-items: center; flex-wrap: wrap;
      font-size: 0.625rem; padding: 0.15rem 0; border-top: 1px dashed rgba(0,0,0,.12);
    }
    .detalle-prior .otb { font-weight: 700; }
    .detalle-prior .dist, .detalle-prior .par { color: var(--text-secondary); }
    .detalle-prior .monto { margin-left: auto; font-variant-numeric: tabular-nums; }
    .e-BORRADOR { background: #E0E0E0; color: #37474F; }
    .e-VALIDADO { background: #BBDEFB; color: #0D47A1; }
    .e-OBSERVADO { background: #FFE0B2; color: #E65100; }
    .e-APROBADO { background: #C8E6C9; color: #1B5E20; }
  `],
})
export class PresupuestoGastosComponent implements OnInit {
  arbol: ArbolGastos | null = null;
  cargando = true;
  error = '';
  ocupado: number | null = null;

  /** Nodos desplegados; arranca todo contraído porque son 28 programas. */
  private expandidos = new Set<string>();

  editando = false;
  guardando = false;
  /** Montos tecleados y aún sin confirmar, por apertura y por par FF/OF. */
  pendientes = new Map<number, Record<string, number>>();

  alta: {
    nivel: 'PROGRAMA' | 'SUBPROGRAMA' | 'ACTIVIDAD';
    codigo: string; sisin: string; denominacion: string; unidadEjecutora: string;
    padreCodigo: string | null; padreDenominacion: string;
  } | null = null;

  /** Catálogos de dirección administrativa y unidad ejecutora. */
  direcciones: { id: string; codigo: string; nombre: string }[] = [];
  ejecutoras: { id: string; codigo: string; nombre: string; da: string }[] = [];

  private base = environment.apiUrlV2 + '/sis-poa/budget';
  /** Gestión fiscal activa; la necesita el alta de categorías y aperturas. */
  private gestionId: number | null = null;

  constructor(private http: HttpClient, private cdr: ChangeDetectorRef) {}

  ngOnInit(): void {
    this.cargar();
    this.cargarOrganizacion();
  }

  /** DA y UE salen del catálogo maestro de organización, no del gasto. */
  private cargarOrganizacion(): void {
    const v1 = environment.apiUrl;
    this.http.get<any>(`${v1}/direcciones-administrativas/?page_size=200`)
      .subscribe({
        next: d => { this.direcciones = d.results ?? d; this.cdr.markForCheck(); },
        error: () => { this.direcciones = []; },
      });
    this.http.get<any>(`${v1}/unidades-ejecutoras/?page_size=500`)
      .subscribe({
        next: d => { this.ejecutoras = d.results ?? d; this.cdr.markForCheck(); },
        error: () => { this.ejecutoras = []; },
      });
  }

  ejecutorasDe(daId: string) {
    // Sin DA elegida se ofrecen todas: obligar a elegir primero la dirección
    // trabaría la carga de lo que ya viene con UE conocida.
    return daId ? this.ejecutoras.filter(u => u.da === daId) : this.ejecutoras;
  }

  nombreDe(catalogo: { id: string; nombre: string }[], id: string): string {
    return catalogo.find(x => x.id === id)?.nombre ?? '';
  }

  /**
   * Guarda la dirección o la unidad en el acto. No se acumula con los montos:
   * son datos de identificación, no cifras que se cuadran de a varias.
   */
  elegirOrg(a: Actividad, campo: 'da' | 'ue', evento: Event): void {
    const valor = (evento.target as HTMLSelectElement).value;
    const previo = campo === 'da' ? a.da_id : a.ue_id;
    if (campo === 'da') {
      a.da_id = valor;
      // La UE pertenece a una DA: si cambia la dirección, la unidad que ya
      // estaba puede no corresponder.
      if (valor && !this.ejecutorasDe(valor).some(u => u.id === a.ue_id)) {
        a.ue_id = '';
      }
    } else {
      a.ue_id = valor;
    }

    const cuerpo: Record<string, string | null> = { [campo]: valor || null };
    if (campo === 'da' && !a.ue_id) { cuerpo['ue'] = null; }

    this.http.patch(`${this.base}/allocations/${a.id}/`, cuerpo).subscribe({
      next: () => {
        a.direccion_administrativa =
          this.direcciones.find(d => d.id === a.da_id)?.codigo ?? '';
        a.unidad_ejecutora =
          this.ejecutoras.find(u => u.id === a.ue_id)?.codigo ?? '';
        this.cdr.markForCheck();
      },
      error: e => {
        // Se devuelve la celda a lo que estaba: dejarla mostrando algo que no
        // se guardó es peor que no haber editado.
        if (campo === 'da') { a.da_id = previo; } else { a.ue_id = previo; }
        this.fallo(e, `guardar la ${campo === 'da' ? 'dirección' : 'unidad'}`);
      },
    });
  }

  cargar(): void {
    this.cargando = true;
    this.error = '';
    // Sin `?gestion=`: el backend responde por la gestión habilitada. El año
    // ya no lo elige la pantalla (ADR-007) — acá estaba clavado en 2027.
    this.http.get<ArbolGastos>(`${this.base}/presupuesto-gastos/`)
      .pipe(finalize(() => { this.cargando = false; this.cdr.markForCheck(); }))
      .subscribe({
        next: d => {
          this.arbol = d;
          this.gestionId = (d as any).gestion_id ?? this.gestionId;
          this.cdr.markForCheck();
        },
        error: () => {
          this.error = 'No se pudo cargar el presupuesto de gastos.';
          this.cdr.markForCheck();
        },
      });
  }

  // --- Árbol ----------------------------------------------------------------

  abierto(clave: string): boolean { return this.expandidos.has(clave); }

  alternar(clave: string): void {
    if (this.expandidos.has(clave)) { this.expandidos.delete(clave); }
    else { this.expandidos.add(clave); }
  }

  expandirTodo(abrir: boolean): void {
    this.expandidos.clear();
    if (!abrir || !this.arbol) { return; }
    for (const p of this.arbol.programas) {
      this.expandidos.add(p.codigo);
      for (const s of p.subprogramas) { this.expandidos.add(p.codigo + s.codigo); }
    }
  }

  /**
   * A qué programa de la directriz cae el código que se está escribiendo. El
   * programa se codifica con el rango (`170-179`), así que basta con ver cuál
   * lo contiene. Se avisa antes de guardar: enterarse por el error del
   * servidor obliga a rehacer la carga.
   */
  rangoDelAlta(): Programa | null {
    const numero = this.programaDelAlta();
    if (numero === null || (numero >= 10 && numero <= 96)) { return null; }
    const candidatos = (this.arbol?.programas ?? []).filter(
      p => this.enRango(p.codigo, numero));
    // Gana el más acotado: la directriz singulariza algún programa dentro de
    // un rango para darle su propio sector.
    return candidatos.length
      ? candidatos.reduce(
          (a, b) => this.anchoRango(a.codigo) <= this.anchoRango(b.codigo) ? a : b)
      : null;
  }

  motivoDelAlta(): string {
    const numero = this.programaDelAlta();
    if (numero === null) { return 'El programa debe ser numérico.'; }
    if (numero >= 10 && numero <= 96) {
      return `El programa ${numero} no se puede usar: la directriz reserva `
        + 'del 10 al 96 y dispone que no sean apropiados ni utilizados.';
    }
    return `El programa ${numero} no corresponde a ningún rango de la `
      + 'directriz cargada.';
  }

  private programaDelAlta(): number | null {
    const crudo = (this.alta?.codigo ?? '').trim().split(' ')[0].split('-')[0];
    return /^\d+$/.test(crudo) ? Number(crudo) : null;
  }

  private limites(codigo: string): [number, number] {
    const [a, b] = codigo.split('-');
    return [Number(a), Number(b ?? a)];
  }

  private enRango(codigo: string, numero: number): boolean {
    const [desde, hasta] = this.limites(codigo);
    return desde <= numero && numero <= hasta;
  }

  private anchoRango(codigo: string): number {
    const [desde, hasta] = this.limites(codigo);
    return hasta - desde;
  }

  totalActividades(): number {
    return (this.arbol?.programas ?? []).reduce(
      (n, p) => n + p.subprogramas.reduce((m, s) => m + s.actividades.length, 0), 0);
  }

  // --- Alta de programa, subprograma y actividad -----------------------------

  abrirAlta(nivel: 'PROGRAMA' | 'SUBPROGRAMA' | 'ACTIVIDAD',
            programa?: Programa, subprograma?: Subprograma): void {
    const padre = subprograma ?? programa;
    this.alta = {
      nivel, codigo: '', sisin: '', denominacion: '', unidadEjecutora: '',
      padreCodigo: padre?.codigo ?? null,
      padreDenominacion: padre?.denominacion ?? '',
    };
    if (programa) { this.expandidos.add(programa.codigo); }
    if (programa && subprograma) { this.expandidos.add(programa.codigo + subprograma.codigo); }
  }

  crear(): void {
    if (!this.alta || this.guardando) { return; }
    this.guardando = true;
    this.error = '';
    const a = this.alta;

    // Programa y subprograma son categorias del clasificador; la actividad es
    // una apertura, que es lo que lleva montos.
    if (a.nivel === 'ACTIVIDAD') {
      this.http.post(`${this.base}/allocations/`, {
        gestion: this.gestionId,
        denominacion: a.denominacion.trim(),
        actividad_codigo: a.codigo.trim(),
        codigo_sisin: a.sisin.trim(),
        fuentes: [],
      }).pipe(finalize(() => { this.guardando = false; this.cdr.markForCheck(); }))
        .subscribe({
          next: () => { this.alta = null; this.cargar(); },
          error: e => this.fallo(e, 'crear la actividad'),
        });
      return;
    }

    this.http.post(`${this.base}/programmatic-categories/`, {
      gestion: this.gestionId,
      codigo: a.codigo.trim(),
      denominacion: a.denominacion.trim(),
      nivel: a.nivel,
      estado: 'ACTIVA',
    }).pipe(finalize(() => { this.guardando = false; this.cdr.markForCheck(); }))
      .subscribe({
        next: () => { this.alta = null; this.cargar(); },
        error: e => this.fallo(e, 'crear la categoría'),
      });
  }

  private fallo(e: any, accion: string): void {
    const detalle = e?.error?.error?.detail?.[0] || e?.error?.codigo?.[0] || e?.error?.detail;
    this.error = detalle || `No se pudo ${accion}.`;
    this.cdr.markForCheck();
  }

  // --- Edición de montos ------------------------------------------------------

  cancelarEdicion(): void {
    this.editando = false;
    this.pendientes.clear();
    this.error = '';
    this.cargar();
  }

  valorMonto(a: Actividad, par: string): string {
    const pendiente = this.pendientes.get(a.id);
    if (pendiente && par in pendiente) { return String(pendiente[par]); }
    const guardado = a.montos?.[par];
    return guardado === undefined ? '' : String(Number(guardado));
  }

  editarMonto(a: Actividad, par: string, evento: Event): void {
    const bruto = (evento.target as HTMLInputElement).value;
    const actual = this.pendientes.get(a.id) ?? {};
    actual[par] = bruto === '' ? 0 : Number(bruto);
    this.pendientes.set(a.id, actual);
  }

  /** Total de la fila mientras se escribe, sin esperar al servidor. */
  totalVivo(a: Actividad): string {
    if (!this.editando) { return this.sumar(a.montos); }
    const pares = new Set([
      ...Object.keys(a.montos ?? {}),
      ...Object.keys(this.pendientes.get(a.id) ?? {}),
    ]);
    let total = 0;
    for (const par of pares) { total += Number(this.valorMonto(a, par) || 0); }
    return total ? String(total) : '';
  }

  /**
   * Se envia una apertura por vez con sus fuentes completas: el backend valida
   * disponibilidad contra el techo y rechaza con BUDGET_EXCEEDED si el gasto
   * supera el recurso.
   */
  guardarMontos(): void {
    if (!this.pendientes.size || this.guardando) { return; }
    this.guardando = true;
    this.error = '';

    const actividades = new Map<number, Actividad>();
    for (const p of this.arbol?.programas ?? []) {
      for (const s of p.subprogramas) {
        for (const a of s.actividades) { actividades.set(a.id, a); }
      }
    }

    const envios = [...this.pendientes.entries()].map(([id, cambios]) => {
      const a = actividades.get(id);
      const montos = { ...(a?.montos ?? {}), ...cambios };
      const fuentes = Object.entries(montos)
        .filter(([, monto]) => Number(monto) > 0)
        .map(([par, monto]) => {
          const [fuente, organismo] = par.split('/');
          return { fuente, organismo, monto: Number(monto) };
        });
      return this.http.patch(`${this.base}/allocations/${id}/`, { fuentes });
    });

    forkJoin(envios)
      .pipe(finalize(() => { this.guardando = false; this.cdr.markForCheck(); }))
      .subscribe({
        next: () => { this.pendientes.clear(); this.editando = false; this.cargar(); },
        error: e => {
          const d = e?.error;
          this.error = d?.code === 'BUDGET_EXCEEDED'
            ? `El gasto supera el recurso disponible: pidió ${d?.details?.requested}, `
              + `hay ${d?.details?.available}.`
            : (d?.error?.detail?.[0] || 'No se pudieron guardar los montos.');
          this.cdr.markForCheck();
        },
      });
  }

  // --- Presentación ---------------------------------------------------------

  /** Filas cuyo aporte de priorización está desplegado. */
  private prioresAbiertas = new Set<number>();

  alternarPriorizacion(a: Actividad): void {
    if (this.prioresAbiertas.has(a.id)) {
      this.prioresAbiertas.delete(a.id);
    } else {
      this.prioresAbiertas.add(a.id);
    }
  }

  verPriorizacion(a: Actividad): boolean {
    return this.prioresAbiertas.has(a.id);
  }

  moneda(valor: string | undefined): string {
    if (valor === undefined || valor === null || valor === '') { return '—'; }
    const n = Number(valor);
    return n ? n.toLocaleString('es-BO', { minimumFractionDigits: 2 }) : '—';
  }

  sumar(montos: Record<string, string>): string {
    const total = Object.values(montos ?? {}).reduce((a, v) => a + Number(v || 0), 0);
    return total ? String(total) : '';
  }

  /** Un saldo negativo significa gasto por encima del recurso disponible. */
  negativa(valor: string | undefined): boolean { return Number(valor ?? 0) < 0; }
  enCero(valor: string | undefined): boolean { return Number(valor ?? 0) === 0; }

  etiquetaRevision(a: Actividad): string {
    const mapa: Record<string, string> = {
      BORRADOR: 'Borrador', VALIDADO: 'Validado',
      OBSERVADO: 'Observado', APROBADO: 'Aprobado',
    };
    return mapa[a.estado_revision || 'BORRADOR'] || 'Borrador';
  }

  claseRevision(a: Actividad): string {
    return 'r-' + (a.estado_revision || 'BORRADOR').toLowerCase();
  }

  // --- Revisión por categoría programática ----------------------------------

  puedeValidar(a: Actividad): boolean {
    return ['BORRADOR', 'OBSERVADO'].includes(a.estado_revision || 'BORRADOR');
  }
  puedeAprobar(a: Actividad): boolean { return a.estado_revision === 'VALIDADO'; }
  puedeObservar(a: Actividad): boolean { return a.estado_revision !== 'APROBADO'; }

  private transicion(a: Actividad, accion: string, cuerpo: unknown = {}): void {
    this.ocupado = a.id;
    this.error = '';
    this.http.post(`${this.base}/allocations/${a.id}/${accion}/`, cuerpo)
      .pipe(finalize(() => { this.ocupado = null; this.cdr.markForCheck(); }))
      .subscribe({
        next: (r: any) => { a.estado_revision = r?.estado_revision; this.cdr.markForCheck(); },
        error: (e: any) => {
          this.error = e?.error?.error?.detail?.[0] || `No se pudo ${accion} la categoría.`;
          this.cdr.markForCheck();
        },
      });
  }

  validar(a: Actividad): void { this.transicion(a, 'validar'); }
  aprobar(a: Actividad): void { this.transicion(a, 'aprobar'); }

  observar(a: Actividad): void {
    const motivo = window.prompt('¿Qué debe corregirse en esta categoría?');
    if (!motivo?.trim()) { return; }
    this.transicion(a, 'observar', { observacion: motivo.trim() });
  }
}

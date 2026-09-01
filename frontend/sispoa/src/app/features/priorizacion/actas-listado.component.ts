import { ChangeDetectorRef, Component, OnDestroy, OnInit } from '@angular/core';
import { finalize } from 'rxjs';
import { GestionHabilitadaService } from '../../core/services/gestion-habilitada.service';
import { ActaPriorizacion, PriorizacionService } from './priorizacion.service';

@Component({
  selector: 'app-actas-listado',
  standalone: false,
  template: `
    <div class="lienzo lienzo-datos">
        <div class="encabezado-pantalla encabezado-actas">

          <div class="encabezado-titulo">
            <h2>Actas de priorización</h2>

            <p class="sub">
              Lo que cada organización territorial priorizó para el POA.
            </p>
          </div>


          <!--
            Temporizador exclusivamente visual.
            No bloquea, no cierra sesión y no modifica registros.
          -->
          <div
            class="registro-countdown"
            [ngClass]="'countdown--' + estadoCuentaRegresiva"
          >

            <div class="countdown-icono">
              ⏳
            </div>

            <div class="countdown-contenido">

              <div class="countdown-titulo">
                CIERRE DE REGISTROS
              </div>

              <div
                class="countdown-tiempo"
                *ngIf="!plazoFinalizado"
              >
                {{ cuentaRegresiva }}
              </div>

              <div
                class="countdown-tiempo countdown-finalizado"
                *ngIf="plazoFinalizado"
              >
                PLAZO FINALIZADO
              </div>

              <div class="countdown-subtitulo">
                HOY · 23:59 · BOLIVIA
              </div>

            </div>

          </div>

        </div>


        <!--
          RESUMEN + NUEVA ACTA + FILTROS
          Una sola fila en escritorio.
        -->
        <div class="barra-actas">

          <!-- IZQUIERDA: RESUMEN -->
          <div class="barra-actas-resumen">

            <div
              class="tarjetas-resumen"
              *ngIf="totales.actas"
            >

              <div class="tarjeta">
                <span>{{ totales.actas }}</span>
                <small>actas</small>
              </div>

              <div class="tarjeta">
                <span>{{ totales.proyectos }}</span>
                <small>proyectos</small>
              </div>

              <div class="tarjeta">
                <span>
                  Bs {{ totales.monto | number:'1.0-0' }}
                </span>
                <small>priorizado</small>
              </div>

            </div>

          </div>


          <!-- CENTRO: NUEVA ACTA -->
          <div class="barra-actas-centro">

            <a
              class="btn btn-sm btn-primary btn-nueva-acta"
              routerLink="/priorizacion/actas/nueva"
            >
              + Nueva acta
            </a>

          </div>


          <!-- DERECHA: FILTROS Y EXPORTACION -->
          <div class="barra-actas-filtros">

            <select
              class="form-control filtro"
              [(ngModel)]="distrito"
              (change)="filtrar()"
            >
              <option value="">
                Todos los distritos
              </option>

              <option
                *ngFor="let d of distritos"
                [value]="d.id"
              >
                {{ d.nombre }}
              </option>
            </select>


            <input
              class="form-control filtro"
              [(ngModel)]="busqueda"
              (keyup.enter)="filtrar()"
              placeholder="OTB o presidente"
            >


            <button
              type="button"
              class="btn btn-sm btn-exportar"
              [disabled]="!!descargando"
              (click)="exportar('xlsx')"
              title="Proyectos programados de lo filtrado, en Excel"
            >
              {{ descargando === 'xlsx' ? 'Generando…' : 'Excel' }}
            </button>


            <button
              type="button"
              class="btn btn-sm btn-exportar"
              [disabled]="!!descargando"
              (click)="exportar('pdf')"
              title="Proyectos programados de lo filtrado, en PDF"
            >
              {{ descargando === 'pdf' ? 'Generando…' : 'PDF' }}
            </button>

          </div>

        </div>


        <div
          class="msg-box error"
          *ngIf="error"
        >
          {{ error }}
        </div>

        <div
          class="msg-box aviso"
          *ngIf="aviso && !error"
        >
          {{ aviso }}
        </div>

      <div class="sin-datos" *ngIf="cargando"><span>Cargando actas…</span></div>

      <div class="tabla-caja" *ngIf="!cargando">
        <table class="tabla tabla-compacta">
          <thead>
            <tr>
              <th *ngFor="let c of columnas" class="ordenable"
                  [class.num]="c.num" [class.activa]="!!indicador(c.clave)"
                  [attr.aria-sort]="direccion(c.clave)" tabindex="0"
                  (click)="ordenar(c.clave)" (keydown.enter)="ordenar(c.clave)">
                {{ c.titulo }}<span class="flecha">{{ indicador(c.clave) }}</span>
              </th>
              <th style="width:200px">Acciones</th>
            </tr>
          </thead>
          <tbody>
            <tr *ngFor="let a of actas">
              <td>{{ a.distrito_nombre }}</td>
              <td class="fuerte">{{ a.otb }}</td>
              <td>{{ a.presidente }}</td>
              <td>{{ a.fecha || '—' }}</td>
              <td class="num">{{ a.proyectos.length }}</td>
              <td class="num">{{ a.monto_total | number:'1.0-0' }}</td>
              <td>
                <span class="estado" [ngClass]="'e-' + a.estado">{{ a.estado }}</span>
                <span class="incompleta" *ngIf="!a.esta_completa"
                      title="Sin fecha o sin proyectos: no se puede emitir">incompleta</span>
              </td>
              <td class="registro">
                {{ (a.fecha_hora_registro | date:'dd/MM/yy HH:mm') || '—' }}
              </td>
              <td>
                <div class="acciones">
                  <a class="acc" [routerLink]="['/priorizacion/actas', a.id]"
                     title="Editar">✎</a>
                  <a class="acc" [routerLink]="['/priorizacion/actas', a.id, 'acta']"
                     title="Ver acta oficial" [class.inhabilitada]="!a.esta_completa">📄</a>
                  <button class="acc" *ngIf="a.estado !== 'VALIDADO'"
                          (click)="revisar(a, 'validar')"
                          title="Validar y adjuntar al presupuesto de gastos">✓</button>
                  <button class="acc" *ngIf="a.estado === 'VALIDADO'"
                          (click)="revisar(a, 'desvalidar')"
                          title="Desvalidar y liberar el techo">↩</button>
                  <button class="acc" (click)="revisar(a, 'aprobar')" title="Aprobar">✓✓</button>
                  <button class="acc" (click)="revisar(a, 'observar')" title="Observar">!</button>
                  <button class="acc peligro" (click)="eliminar(a)" title="Eliminar">✕</button>
                </div>
              </td>
            </tr>
            <tr *ngIf="!actas.length">
              <td colspan="9">
                <div class="sin-datos">
                  <span class="sin-datos-icono">📋</span>
                  <strong>No hay actas registradas para la gestión {{ gestion }}</strong>
                  <span>Empiece por registrar la primera.</span>
                  <a class="btn btn-sm btn-primary" routerLink="/priorizacion/actas/nueva">
                    + Nueva acta
                  </a>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <div class="paginador" *ngIf="!cargando && totalPaginas > 1">
        <button class="btn btn-sm" [disabled]="pagina === 1"
                (click)="irA(pagina - 1)">◀ Anterior</button>
        <span class="cuenta">
          Página {{ pagina }} de {{ totalPaginas }} · {{ count }} actas
        </span>
        <button class="btn btn-sm" [disabled]="pagina === totalPaginas"
                (click)="irA(pagina + 1)">Siguiente ▶</button>
      </div>
    </div>
  `,
  styles: [`

      /*
       * =====================================================
       * CABECERA
       * =====================================================
       */

      .encabezado-actas {
        width: 100%;

        display: flex;
        align-items: flex-start;
        justify-content: space-between;

        gap: 1.25rem;
      }

      .encabezado-titulo {
        flex: 1 1 auto;
        min-width: 0;
      }


      /*
       * =====================================================
       * TEMPORIZADOR
       * =====================================================
       */

      .registro-countdown {
        flex: 0 0 auto;

        min-width: 270px;

        margin-left: auto;

        display: flex;
        align-items: center;

        gap: 0.85rem;

        padding:
          0.8rem
          1.1rem;

        box-sizing: border-box;

        color: #fff;

        border:
          2px solid
          rgba(255,255,255,.90);

        border-radius: 13px;

        box-shadow:
          0 7px 20px rgba(0,0,0,.20),
          0 0 0 1px rgba(0,0,0,.05);

        transition:
          background .25s ease,
          box-shadow .25s ease,
          transform .25s ease;
      }


      .countdown-icono {
        flex: 0 0 auto;

        font-size: 2.1rem;

        line-height: 1;

        filter:
          drop-shadow(
            0 2px 2px
            rgba(0,0,0,.22)
          );
      }


      .countdown-contenido {
        min-width: 0;

        display: flex;
        flex-direction: column;
      }


      .countdown-titulo {
        font-size: .69rem;

        font-weight: 900;

        line-height: 1.1;

        letter-spacing: .08em;

        color: #fff;
      }


      .countdown-tiempo {
        margin-top: .16rem;

        font-size: 1.8rem;

        font-weight: 900;

        line-height: 1;

        letter-spacing: .045em;

        font-variant-numeric:
          tabular-nums;

        color: #fff;

        text-shadow:
          0 2px 3px
          rgba(0,0,0,.20);
      }


      .countdown-finalizado {
        font-size: 1rem;

        line-height: 1.15;
      }


      .countdown-subtitulo {
        margin-top: .3rem;

        font-size: .64rem;

        font-weight: 800;

        line-height: 1;

        letter-spacing: .06em;

        color:
          rgba(255,255,255,.94);
      }


      /*
       * Estado normal:
       * resaltante naranja → rojo.
       */
      .countdown--normal {
        background:
          linear-gradient(
            135deg,
            #f59e0b 0%,
            #f97316 40%,
            #dc2626 100%
          );
      }


      /*
       * Menos de 2 horas.
       */
      .countdown--urgente {
        background:
          linear-gradient(
            135deg,
            #f97316 0%,
            #dc2626 45%,
            #991b1b 100%
          );

        box-shadow:
          0 7px 22px
          rgba(185,28,28,.36),
          0 0 0 2px
          rgba(254,202,202,.22);
      }


      /*
       * Últimos 30 minutos.
       */
      .countdown--critico {
        background:
          linear-gradient(
            135deg,
            #dc2626 0%,
            #b91c1c 50%,
            #7f1d1d 100%
          );

        box-shadow:
          0 8px 25px
          rgba(185,28,28,.48),
          0 0 0 3px
          rgba(254,202,202,.38);

        animation:
          pulso-cierre
          1.7s
          ease-in-out
          infinite;
      }


      /*
       * Luego de las 23:59.
       * Sigue sin realizar ninguna acción funcional.
       */
      .countdown--finalizado {
        background:
          linear-gradient(
            135deg,
            #374151 0%,
            #111827 100%
          );

        animation: none;
      }


      @keyframes pulso-cierre {

        0%,
        100% {
          transform: scale(1);
        }

        50% {
          transform: scale(1.018);
        }

      }


      /*
       * =====================================================
       * NUEVA ACTA
       * =====================================================
       */

      .fila-nueva-acta {
        width: 100%;

        display: flex;
        align-items: center;
        justify-content: center;

        margin:
          .35rem 0
          .65rem;
      }


      .btn-nueva-acta {
        min-width: 165px;

        min-height: 41px;

        display: inline-flex;
        align-items: center;
        justify-content: center;

        padding:
          0 1.25rem;

        font-size: .83rem;

        font-weight: 800;

        box-shadow:
          0 4px 11px
          rgba(0,128,61,.22);
      }


      /*
       * =====================================================
       * FILTROS + EXCEL + PDF
       * =====================================================
       */

      .fila-filtros {
        width: 100%;

        display: flex;
        align-items: center;
        justify-content: center;

        gap: .5rem;

        flex-wrap: wrap;

        margin-bottom: 1rem;
      }


      .fila-filtros .filtro,
      .fila-filtros .btn {
        height: 38px;
        min-height: 38px;

        box-sizing: border-box;
      }


      .fila-filtros .btn {
        display: inline-flex;

        align-items: center;
        justify-content: center;
      }


      /*
       * =====================================================
       * RESPONSIVE
       * =====================================================
       */

      @media (max-width: 900px) {

        .encabezado-actas {
          flex-direction: column;
        }

        .registro-countdown {
          align-self: stretch;

          width: 100%;
          min-width: 0;

          margin-left: 0;
        }

      }


      @media (max-width: 680px) {

        .btn-nueva-acta {
          width: 100%;
        }

        .fila-filtros {
          flex-direction: column;

          align-items: stretch;
        }

        .fila-filtros .filtro,
        .fila-filtros .btn {
          width: 100%;

          max-width: none;
        }

      }

      /*
       * =====================================================
       * FILA PRINCIPAL DE ACTAS
       * =====================================================
       *
       * 1fr / auto / 1fr mantiene el botón Nueva acta
       * geométricamente centrado respecto al contenido.
       */

      .barra-actas {
        width: 100%;

        display: grid;

        grid-template-columns:
          minmax(0, 1fr)
          auto
          minmax(0, 1fr);

        align-items: center;

        column-gap: 1rem;

        margin:
          0.7rem 0
          0.8rem;
      }


      /* IZQUIERDA */

      .barra-actas-resumen {
        min-width: 0;

        display: flex;

        align-items: center;
        justify-content: flex-start;
      }


      .barra-actas-resumen .tarjetas-resumen {
        margin: 0;

        flex-wrap: nowrap;
      }


      .barra-actas-resumen .tarjeta {
        min-height: 64px;

        box-sizing: border-box;
      }


      /* CENTRO */

      .barra-actas-centro {
        display: flex;

        align-items: center;
        justify-content: center;
      }


      .barra-actas-centro .btn-nueva-acta {
        margin: 0;

        min-width: 165px;
        min-height: 38px;
      }


      /* DERECHA */

      .barra-actas-filtros {
        min-width: 0;

        display: flex;

        align-items: center;
        justify-content: flex-end;

        gap: 0.45rem;

        flex-wrap: nowrap;
      }


      .barra-actas-filtros .filtro {
        width: 175px;
        max-width: 175px;

        height: 38px;
        min-height: 38px;

        box-sizing: border-box;
      }


      .barra-actas-filtros .btn {
        height: 38px;
        min-height: 38px;

        display: inline-flex;

        align-items: center;
        justify-content: center;

        box-sizing: border-box;

        white-space: nowrap;
      }


      /*
       * En resoluciones pequeñas dejamos que se reorganice.
       * En escritorio permanece obligatoriamente en una fila.
       */
      @media (max-width: 1250px) {

        .barra-actas {
          grid-template-columns: 1fr;

          row-gap: 0.65rem;

          justify-items: center;
        }


        .barra-actas-resumen {
          justify-content: center;
        }


        .barra-actas-filtros {
          justify-content: center;

          flex-wrap: wrap;
        }

      }


      .filtro {
        max-width: 190px;
        font-size: 0.8125rem;
      }

    .tarjetas-resumen { display: flex; gap: var(--e-2); margin-bottom: var(--e-2); }
    .tarjeta {
      background: var(--surface); border: 1px solid var(--border);
      border-radius: var(--radius); padding: 0.6rem 1rem; min-width: 130px;
    }
    .tarjeta span { display: block; font-size: 1.15rem; font-weight: 700; color: var(--pip-green-700); }
    .tarjeta small { font-size: 0.6875rem; color: var(--text-secondary); }
    .fuerte { font-weight: 600; }
    .num { text-align: right; }
    .registro { font-size: 0.6875rem; color: var(--text-secondary); white-space: nowrap; }
    .ordenable { cursor: pointer; user-select: none; }
    .ordenable:hover, .ordenable:focus-visible { background: rgba(0,0,0,.06); }
    .ordenable.activa { color: var(--pip-green-700); }
    .flecha { font-size: 0.625rem; margin-left: 0.2rem; }
    .paginador {
      display: flex; align-items: center; justify-content: center;
      gap: var(--e-2); margin-top: var(--e-2); font-size: 0.75rem;
    }
    .paginador .cuenta { color: var(--text-secondary); }
    .paginador button[disabled] { opacity: .4; cursor: default; }
    .acciones { display: flex; gap: 0.2rem; }
    .acc {
      border: none; background: rgba(0,0,0,.06); color: var(--text); cursor: pointer;
      border-radius: 3px; padding: 0.15rem 0.35rem; font-size: 0.75rem;
      text-decoration: none; line-height: 1.3;
    }
    .acc:hover { background: rgba(0,0,0,.16); }
    .acc.inhabilitada { opacity: .35; pointer-events: none; }
    .acc.peligro:hover { background: #B3261E; color: #fff; }
    .estado {
      font-size: 0.5625rem; font-weight: 700; padding: 0.05rem 0.35rem;
      border-radius: 999px;
    }
    .e-BORRADOR { background: #E0E0E0; color: #37474F; }
    .e-VALIDADO { background: #BBDEFB; color: #0D47A1; }
    .e-OBSERVADO { background: #FFE0B2; color: #E65100; }
    .e-APROBADO { background: #C8E6C9; color: #1B5E20; }
    .incompleta {
      display: block; font-size: 0.5625rem; color: #B3261E; margin-top: 0.15rem;
    }
    .msg-box.error {
      background: var(--error-fondo); color: var(--error-tinta);
      padding: 0.7rem 0.9rem; border-radius: var(--radius); margin-bottom: var(--e-2);
    }
    /* Exportar es acción secundaria: verde institucional, pero en tinta y no
       en relleno, para no competir con el primario «+ Nueva acta». */
    .btn-exportar {
      background: var(--pip-green-100);
      border: 1px solid var(--pip-green-500);
      color: var(--pip-green-700);
      font-weight: 600;
    }
    .btn-exportar:hover:not(:disabled) {
      background: var(--pip-green-700);
      border-color: var(--pip-green-700);
      color: #fff;
    }
    .btn-exportar:disabled { opacity: 0.55; cursor: progress; }

    .msg-box.aviso {
      background: var(--pip-green-100); color: var(--pip-green-700);
      padding: 0.55rem 0.9rem; border-radius: var(--radius); margin-bottom: var(--e-2);
    }
  `],
})
export class ActasListadoComponent implements OnInit, OnDestroy {
  actas: ActaPriorizacion[] = [];
  distritos: any[] = [];
  /** La gestión la fija el candado de SIS-POA, no un filtro (ADR-007). */
  get gestion(): number | null { return this.gestionActiva.anio(); }
  distrito = '';
  busqueda = '';
  cargando = true;
  error = '';
  aviso = '';

  /**
   * Columnas del encabezado. `clave` viaja tal cual al backend en `ordering`:
   * ordenar acá sería ordenar solo la página recibida, no las actas.
   */
  readonly columnas = [
    { titulo: 'Distrito', clave: 'distrito__codigo', num: false },
    { titulo: 'OTB / Junta vecinal', clave: 'otb', num: false },
    { titulo: 'Presidente', clave: 'presidente', num: false },
    { titulo: 'Fecha', clave: 'fecha', num: false },
    { titulo: 'Proyectos', clave: 'cuenta_proyectos', num: true },
    { titulo: 'Monto Bs', clave: 'suma_monto', num: true },
    { titulo: 'Estado', clave: 'estado', num: false },
    { titulo: 'Registrada', clave: 'created_at', num: false },
  ];

  /** Lo último registrado arriba. Es el mismo default que aplica el backend. */
  orden = '-created_at';

  pagina = 1;
  count = 0;
  /** Lo dice el servidor: clavarlo acá lo desincroniza de `PAGE_SIZE`. */
  pageSize = 25;
  /** Totales de todo lo filtrado, no de la página que se está viendo. */
  totales = { actas: 0, proyectos: 0, monto: 0 };

  /** Qué formato se está generando: deshabilita ambos botones mientras tanto. */
  descargando: '' | 'xlsx' | 'pdf' = '';

  /**
   * Temporizador exclusivamente visual.
   *
   * No controla ninguna operación del sistema.
   */
  cuentaRegresiva = '--:--:--';

  plazoFinalizado = false;

  estadoCuentaRegresiva:
    | 'normal'
    | 'urgente'
    | 'critico'
    | 'finalizado'
    = 'normal';

  /**
   * 1 de septiembre de 2026,
   * 23:59 hora de Bolivia (UTC-4).
   */
  private readonly cierreRegistros =
    new Date(
      '2026-09-01T23:59:00-04:00'
    ).getTime();

  private timerCuentaRegresiva:
    ReturnType<typeof setInterval>
    | null
    = null;

  constructor(private api: PriorizacionService, private cdr: ChangeDetectorRef,
              private gestionActiva: GestionHabilitadaService) {}

  ngOnInit(): void {

    /*
     * AVISO VISUAL SOLAMENTE.
     *
     * No bloquea registros.
     * No deshabilita botones.
     * No realiza llamadas al backend.
     */
    this.actualizarCuentaRegresiva();

    if (!this.plazoFinalizado) {

      this.timerCuentaRegresiva =
        setInterval(
          () => this.actualizarCuentaRegresiva(),
          1000,
        );

    }

    this.api.distritos().subscribe(d => {
      this.distritos = d.results ?? d;
      this.cdr.markForCheck();
    });
    this.cargar();
  }

  ngOnDestroy(): void {

    if (this.timerCuentaRegresiva !== null) {

      clearInterval(
        this.timerCuentaRegresiva
      );

      this.timerCuentaRegresiva = null;

    }

  }


  /**
   * Actualiza únicamente la representación visual
   * del plazo de cierre.
   */
  private actualizarCuentaRegresiva(): void {

    const restante =
      this.cierreRegistros
      - Date.now();


    if (restante <= 0) {

      this.cuentaRegresiva =
        '00:00:00';

      this.plazoFinalizado =
        true;

      this.estadoCuentaRegresiva =
        'finalizado';


      if (
        this.timerCuentaRegresiva
        !== null
      ) {

        clearInterval(
          this.timerCuentaRegresiva
        );

        this.timerCuentaRegresiva =
          null;

      }


      this.cdr.markForCheck();

      return;

    }


    this.plazoFinalizado =
      false;


    const totalSegundos =
      Math.floor(
        restante / 1000
      );


    const horas =
      Math.floor(
        totalSegundos / 3600
      );


    const minutos =
      Math.floor(
        (totalSegundos % 3600)
        / 60
      );


    const segundos =
      totalSegundos % 60;


    this.cuentaRegresiva =
      `${String(horas).padStart(2, '0')}:`
      + `${String(minutos).padStart(2, '0')}:`
      + `${String(segundos).padStart(2, '0')}`;


    /*
     * Cambio solamente visual.
     */
    if (
      restante
      <= 30 * 60 * 1000
    ) {

      this.estadoCuentaRegresiva =
        'critico';

    } else if (
      restante
      <= 2 * 60 * 60 * 1000
    ) {

      this.estadoCuentaRegresiva =
        'urgente';

    } else {

      this.estadoCuentaRegresiva =
        'normal';

    }


    this.cdr.markForCheck();

  }


  get totalPaginas(): number {
    if (!this.pageSize) { return 1; }
    return Math.max(1, Math.ceil(this.count / this.pageSize));
  }

  /** Filtrar u ordenar cambia el conjunto: la página vieja ya no significa nada. */
  filtrar(): void {
    this.pagina = 1;
    this.cargar();
  }

  irA(pagina: number): void {
    if (pagina < 1 || pagina > this.totalPaginas) { return; }
    this.pagina = pagina;
    this.cargar();
  }

  /** Click en el encabezado: misma columna invierte, otra columna arranca asc. */
  ordenar(clave: string): void {
    this.orden = this.orden === clave ? `-${clave}` : clave;
    this.filtrar();
  }

  indicador(clave: string): string {
    if (this.orden === clave) { return '▲'; }
    if (this.orden === `-${clave}`) { return '▼'; }
    return '';
  }

  direccion(clave: string): string {
    if (this.orden === clave) { return 'ascending'; }
    if (this.orden === `-${clave}`) { return 'descending'; }
    return 'none';
  }

  cargar(): void {
    this.cargando = true;
    this.error = '';
    // La gestión no viaja como filtro: la resuelve el candado en el backend.
    this.api.listarActas({ distrito: this.distrito, q: this.busqueda,
                           ordering: this.orden, page: this.pagina })
      .pipe(finalize(() => { this.cargando = false; this.cdr.markForCheck(); }))
      .subscribe({
        next: d => {
          this.actas = d.results ?? d;
          this.count = d.count ?? this.actas.length;
          this.pageSize = d.page_size ?? this.pageSize;
          // Los montos llegan como texto (DRF serializa Decimal así): sin el
          // `+` la tarjeta muestra el string crudo en vez del número formateado.
          this.totales = d.resumen
            ? { actas: +d.resumen.actas, proyectos: +d.resumen.proyectos,
                monto: +d.resumen.monto }
            : this.totalesDeLaPagina();
          this.cdr.markForCheck();
        },
        error: () => {
          this.error = 'No se pudieron cargar las actas.';
          this.cdr.markForCheck();
        },
      });
  }

  /**
   * Descarga el reporte de proyectos programados del recorte actual.
   *
   * Se mandan los filtros y NO la página: lo que se exporta es todo lo
   * filtrado. El total de proyectos ya lo trae el resumen del listado, así que
   * el recorte vacío se corta acá en vez de bajar un archivo con solo el
   * encabezado.
   */
  exportar(formato: 'xlsx' | 'pdf'): void {
    if (!this.totales.proyectos) {
      this.error = 'El recorte actual no tiene proyectos que reportar.';
      return;
    }
    this.descargando = formato;
    this.error = '';
    this.api
      .reporteProyectos(
        { distrito: this.distrito, q: this.busqueda, ordering: this.orden },
        formato)
      .pipe(finalize(() => { this.descargando = ''; this.cdr.markForCheck(); }))
      .subscribe({
        next: blob => {
          const url = URL.createObjectURL(blob);
          const a = document.createElement('a');
          a.href = url;
          a.download = `proyectos-programados-${this.gestion}.${formato}`;
          a.click();
          URL.revokeObjectURL(url);
        },
        error: () => {
          this.error = 'No se pudo generar el reporte.';
          this.cdr.markForCheck();
        },
      });
  }

  /** Respaldo para una respuesta sin paginar: los totales de lo que llegó. */
  private totalesDeLaPagina(): { actas: number; proyectos: number; monto: number } {
    return {
      actas: this.actas.length,
      proyectos: this.actas.reduce((t, a) => t + a.proyectos.length, 0),
      monto: this.actas.reduce((t, a) => t + Number(a.monto_total || 0), 0),
    };
  }

  revisar(acta: ActaPriorizacion, accion: string): void {
    let cuerpo: any = {};
    if (accion === 'observar') {
      const comentario = (window.prompt('Motivo de la observación:') || '').trim();
      if (!comentario) { return; }
      cuerpo = { comentario };
    }
    this.error = '';
    this.api.revisar(acta.id!, accion, cuerpo).subscribe({
      next: r => {
        acta.estado = r.estado;
        this.aviso = this.resumen(r);
        this.cdr.markForCheck();
      },
      error: e => {
        this.error = e?.error?.error || 'No se pudo completar la acción.';
        this.cdr.markForCheck();
      },
    });
  }

  /** Lo que se volcó al gasto —o se liberó— hay que decirlo, no esconderlo. */
  private resumen(r: any): string {
    const partes = [`Acta ${String(r.estado).toLowerCase()}.`];
    const puestos = r.materializacion?.materializados?.length ?? 0;
    const afuera = r.materializacion?.omitidos ?? [];
    const revertidos = r.revertidos?.length ?? 0;
    if (puestos) {
      partes.push(`${puestos} proyecto(s) adjuntados al presupuesto de gastos.`);
      // Dar de alta una categoría programática no es rutina: hay que decirlo.
      const nuevas = (r.materializacion?.materializados ?? [])
        .filter((m: any) => m.categoria_creada);
      for (const m of nuevas) {
        partes.push(`Se dio de alta la categoría ${m.categoria} `
          + `«${m.denominacion_categoria}».`);
      }
    }
    if (revertidos) {
      partes.push(`${revertidos} proyecto(s) liberados del techo.`);
    }
    for (const o of afuera) {
      partes.push(`Sin adjuntar «${o.nombre}»: ${o.motivo}.`);
    }
    return partes.join(' ');
  }

  eliminar(acta: ActaPriorizacion): void {
    if (!window.confirm(`¿Eliminar el acta de ${acta.otb}?`)) { return; }
    this.api.eliminarActa(acta.id!).subscribe({
      next: () => {
        this.aviso = 'Acta eliminada.';
        // Era la única de la página: esa página ya no existe y el servidor
        // responde 404 «Invalid page», no una lista vacía.
        if (this.actas.length === 1 && this.pagina > 1) { this.pagina--; }
        this.cargar();
      },
      error: e => {
        this.error = e?.error?.error || 'No se pudo eliminar el acta.';
        this.cdr.markForCheck();
      },
    });
  }
}

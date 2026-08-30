import { ChangeDetectorRef, Component, OnInit } from '@angular/core';
import { finalize } from 'rxjs';
import { GestionHabilitadaService } from '../../core/services/gestion-habilitada.service';
import { ActaPriorizacion, PriorizacionService } from './priorizacion.service';

@Component({
  selector: 'app-actas-listado',
  standalone: false,
  template: `
    <div class="lienzo lienzo-datos">
      <div class="encabezado-pantalla">
        <div>
          <h2>Actas de priorización</h2>
          <p class="sub">Lo que cada organización territorial priorizó para el POA.</p>
        </div>
        <div class="encabezado-acciones">
          <select class="form-control filtro" [(ngModel)]="distrito" (change)="filtrar()">
            <option value="">Todos los distritos</option>
            <option *ngFor="let d of distritos" [value]="d.id">{{ d.nombre }}</option>
          </select>
          <input class="form-control filtro" [(ngModel)]="busqueda"
                 (keyup.enter)="filtrar()" placeholder="OTB o presidente">
          <button type="button" class="btn btn-sm btn-exportar"
                  [disabled]="!!descargando" (click)="exportar('xlsx')"
                  title="Proyectos programados de lo filtrado, en Excel">
            {{ descargando === 'xlsx' ? 'Generando…' : 'Excel' }}
          </button>
          <button type="button" class="btn btn-sm btn-exportar"
                  [disabled]="!!descargando" (click)="exportar('pdf')"
                  title="Proyectos programados de lo filtrado, en PDF">
            {{ descargando === 'pdf' ? 'Generando…' : 'PDF' }}
          </button>
          <a class="btn btn-sm btn-primary" routerLink="/priorizacion/actas/nueva">
            + Nueva acta
          </a>
        </div>
      </div>

      <div class="msg-box error" *ngIf="error">{{ error }}</div>
      <div class="msg-box aviso" *ngIf="aviso && !error">{{ aviso }}</div>

      <!-- El resumen es de todo lo filtrado, no de la página en pantalla. -->
      <div class="tarjetas-resumen" *ngIf="totales.actas">
        <div class="tarjeta"><span>{{ totales.actas }}</span><small>actas</small></div>
        <div class="tarjeta"><span>{{ totales.proyectos }}</span><small>proyectos</small></div>
        <div class="tarjeta">
          <span>Bs {{ totales.monto | number:'1.0-0' }}</span><small>priorizado</small>
        </div>
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
    .filtro { max-width: 190px; font-size: 0.8125rem; }
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
export class ActasListadoComponent implements OnInit {
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

  constructor(private api: PriorizacionService, private cdr: ChangeDetectorRef,
              private gestionActiva: GestionHabilitadaService) {}

  ngOnInit(): void {
    this.api.distritos().subscribe(d => {
      this.distritos = d.results ?? d;
      this.cdr.markForCheck();
    });
    this.cargar();
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

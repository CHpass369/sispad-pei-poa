import { ChangeDetectorRef, Component, ElementRef, OnInit } from '@angular/core';
import { ActivatedRoute, Router } from '@angular/router';
import { Subject } from 'rxjs';
import {
  AUTOCOMPLETE_CONFIG,
  autocompleteSearch
} from '../../shared/utils/autocomplete.util';
import { GestionHabilitadaService } from '../../core/services/gestion-habilitada.service';
import {
  ActaPriorizacion, OrganizacionTerritorial, PriorizacionService,
  ProyectoCatalogo, ProyectoPriorizado,
} from './priorizacion.service';

@Component({
  selector: 'app-acta-form',
  standalone: false,
  template: `
    <div class="lienzo">
      <div class="encabezado-pantalla">
        <div>
          <h2>{{ id ? 'Editar acta de priorización' : 'Nueva acta de priorización' }}</h2>
          <p class="sub">
            Registro de lo que la organización territorial prioriza para el POA
            {{ acta.gestion }}.
          </p>
        </div>
        <a class="btn btn-sm btn-secondary" routerLink="/priorizacion/actas">Volver</a>
      </div>

      <div class="msg-box error" *ngIf="error">{{ error }}</div>

      <div class="card">
        <h3>Datos del acta</h3>
        <div class="grilla">
          <label>Gestión POA
            <input class="form-control" type="number" [ngModel]="acta.gestion" name="gestion" readonly
                   title="La gestión la fija la habilitación de gestión fiscal">
          </label>
          <label>Distrito
            <select class="form-control" [ngModel]="acta.distrito"
                    (ngModelChange)="cambiarDistrito($event)">
              <option value="">Seleccione…</option>
              <option *ngFor="let d of distritos" [value]="d.id">{{ d.nombre }}</option>
            </select>
          </label>
          <!-- Los dos campos buscan sobre el mismo padrón y se completan
               mutuamente: se puede entrar por la organización o por el
               dirigente. Siguen admitiendo texto libre porque hay
               organizaciones que todavía no están en la tabla maestra y el
               acta no puede quedar trabada por eso. -->
          <!-- Combobox editable no restrictivo: se escribe adentro y la lista
               acota, pero un valor que no está en el padrón también vale. La
               lista va FUERA del <label>: un label no puede contener otro
               control, y un lector de pantalla leería el listbox como parte
               del rótulo. -->
          <div class="campo-padron">
            <label for="buscador-otb">OTB / Junta vecinal</label>
            <input class="form-control" id="buscador-otb" [value]="acta.otb"
                   (input)="buscarOtb($event)" (focus)="abrir('otb')"
                   (blur)="cerrarPadron()" (keydown)="teclaPadron($event, 'otb')"
                   role="combobox" aria-autocomplete="list"
                   aria-controls="sugeridas-otb" autocomplete="off"
                   [attr.aria-expanded]="abiertoPadron === 'otb'"
                   [attr.aria-activedescendant]="opcionActivaId('otb')"
                   placeholder="Escriba y agregue palabras para acotar: ulincate">
            <ul class="sugerencias" id="sugeridas-otb" role="listbox"
                *ngIf="abiertoPadron === 'otb' && sugeridas.length">
              <li *ngFor="let o of sugeridas; let i = index"
                  [id]="'opcion-otb-' + i" role="option"
                  [attr.aria-selected]="i === indiceActivo"
                  [class.activa]="i === indiceActivo"
                  (mousedown)="tomar(o, 'otb')">
                <span class="nombre">{{ o.nombre }}</span>
                <span class="marca">{{ o.tipo_display }}</span>
                <span class="marca" *ngIf="o.distrito_codigo">{{ o.distrito_codigo }}</span>
                <span class="marca dirigente" *ngIf="o.dirigente">{{ o.dirigente }}</span>
              </li>
            </ul>
            <small class="pista">{{ pistaOtb() }}</small>
          </div>

          <div class="campo-padron">
            <label for="buscador-presidente">Presidente</label>
            <input class="form-control" id="buscador-presidente"
                   [value]="acta.presidente"
                   (input)="buscarPresidente($event)" (focus)="abrir('presidente')"
                   (blur)="cerrarPadron()"
                   (keydown)="teclaPadron($event, 'presidente')"
                   role="combobox" aria-autocomplete="list"
                   aria-controls="sugeridas-presidente" autocomplete="off"
                   [attr.aria-expanded]="abiertoPadron === 'presidente'"
                   [attr.aria-activedescendant]="opcionActivaId('presidente')"
                   placeholder="Busque por nombre del dirigente">
            <ul class="sugerencias" id="sugeridas-presidente" role="listbox"
                *ngIf="abiertoPadron === 'presidente' && sugeridas.length">
              <li *ngFor="let o of sugeridas; let i = index"
                  [id]="'opcion-presidente-' + i" role="option"
                  [attr.aria-selected]="i === indiceActivo"
                  [class.activa]="i === indiceActivo"
                  (mousedown)="tomar(o, 'presidente')">
                <span class="nombre">{{ o.dirigente }}</span>
                <span class="marca" *ngIf="o.cargo">{{ o.cargo | lowercase }}</span>
                <span class="marca dirigente">{{ o.nombre }}</span>
              </li>
            </ul>
            <small class="pista" *ngIf="cargoDirigente && cargoDirigente !== 'PRESIDENTE'">
              El padrón lo registra como {{ cargoDirigente | lowercase }}.
            </small>
          </div>

          <label class="pavimento-check">
            <span>Pavimentos</span>

            <div class="check-pavimento">
              <input
                type="checkbox"
                [(ngModel)]="acta.es_pavimento"
              >

              <span>
                Incluir condición especial de combustible en el acta
              </span>
            </div>
          </label>
          <label>Responsable del registro
            <input class="form-control" [(ngModel)]="acta.responsable_registro">
          </label>
          <label>Fecha y hora de registro
            <input
              class="form-control"
              type="text"
              [value]="fechaHoraMostrada()"
              readonly
              title="La fecha y hora se asignan automáticamente al registrar el acta"
            >
          </label>
        </div>
      </div>

      <div class="card">
        <div class="titulo-acciones">
          <h3>Proyectos priorizados</h3>
          <span class="total">Total Bs {{ total | number:'1.2-2' }}</span>
        </div>

        <div class="buscador">
          <label>Nombre del proyecto
            <input class="form-control" [value]="consulta"
                   (input)="buscar($event)" (focus)="abierto = true"
                   (blur)="cerrarProyectos()" (keydown)="teclaProyecto($event)"
                   role="combobox" aria-autocomplete="list"
                   aria-controls="sugerencias-proyecto" autocomplete="off"
                   [attr.aria-expanded]="abierto"
                   [attr.aria-activedescendant]="opcionProyectoActivaId()"
                   placeholder="Escriba y agregue palabras para acotar: lumin distrito 4">
          </label>
          <p class="ayuda">
            Cada palabra que agregue acota más el resultado.
            <span *ngIf="consulta">{{ totalHallado }} coincidencia(s).</span>
          </p>
          <ul class="sugerencias" id="sugerencias-proyecto" role="listbox"
              *ngIf="abierto && sugerencias.length">
            <li *ngFor="let s of sugerencias; let i = index"
                [id]="'opcion-proyecto-' + i" role="option"
                [attr.aria-selected]="i === indiceProyecto"
                [class.activa]="i === indiceProyecto"
                (mousedown)="elegir(s)">
              <span class="nombre">{{ s.nombre }}</span>
              <span class="marca sisin" *ngIf="s.sisin">SISIN {{ s.sisin }}</span>
              <span class="marca" *ngIf="s.categoria_programatica">
                {{ s.categoria_programatica }}</span>
              <span class="marca veces" *ngIf="s.veces_priorizado">
                priorizado {{ s.veces_priorizado }}×</span>
            </li>
          </ul>
          <p class="ayuda" *ngIf="abierto && consulta && !sugerencias.length">
            Sin coincidencias en el catálogo.
            <button class="btn btn-sm btn-secondary" (mousedown)="agregarLibre()">
              Agregar «{{ consulta }}» igual
            </button>
          </p>
        </div>

        <div class="techos" *ngIf="pares.length">
          <span class="rotulo">Saldo por fuente / organismo</span>
          <div class="pares">
            <div class="par" *ngFor="let s of pares"
                 [class.agotado]="saldoTrasCargar(s) <= 0">
              <strong>{{ s.par }}</strong>
              <span class="disp">Bs {{ saldoTrasCargar(s) | number:'1.0-0' }}</span>
              <small>de {{ s.techo | number:'1.0-0' }}</small>
            </div>
          </div>
        </div>

        <table class="tabla tabla-compacta">
          <thead>
            <tr>
              <th style="width:36px">N°</th>
              <th>Proyecto</th>
              <th style="width:130px">SISIN</th>
              <th style="width:230px">Categoría programática</th>
              <th style="width:190px">FF / OF</th>
              <th style="width:130px">Monto Bs</th>
              <th style="width:44px"></th>
            </tr>
          </thead>
          <tbody>
            <tr *ngFor="let p of acta.proyectos; let i = index">
              <td>{{ i + 1 }}</td>
              <td><input class="form-control sin-borde" [(ngModel)]="p.nombre"></td>
              <td><input class="form-control sin-borde" [(ngModel)]="p.sisin"></td>
              <td>
                <!-- La categoría la elige el técnico: solo se autocompleta
                     cuando el proyecto vino del SIGEP. -->
                <select class="form-control sin-borde" [(ngModel)]="p.categoria_programatica">
                  <option value="">— elegir categoría —</option>
                  <option *ngFor="let c of categorias" [value]="c.codigo">
                    {{ c.codigo }} · {{ c.denominacion }}
                  </option>
                </select>
              </td>
              <td>
                <!-- El par decide contra qué techo se descuenta el monto. -->
                <select class="form-control sin-borde" [(ngModel)]="p.par_elegido"
                        (change)="elegirPar(p)">
                  <option value="">— elegir FF/OF —</option>
                  <option *ngFor="let s of pares" [value]="s.par">
                    {{ s.par }} · Bs {{ s.disponible | number:'1.0-0' }}
                  </option>
                </select>
                <small class="saldo" *ngIf="saldoDelProyecto(p) !== null"
                       [class.negativo]="saldoDelProyecto(p)! < 0">
                  queda Bs {{ saldoDelProyecto(p) | number:'1.0-0' }}
                </small>
              </td>
              <td>
                <input class="form-control sin-borde num" type="number"
                       [(ngModel)]="p.monto">
              </td>
              <td>
                <button class="btn btn-sm btn-danger" (click)="quitar(i)">✕</button>
              </td>
            </tr>
            <tr *ngIf="!acta.proyectos.length">
              <td colspan="7">
                <div class="sin-datos">
                  <strong>Todavía no hay proyectos priorizados</strong>
                  <span>Búsquelos por nombre en el campo de arriba.</span>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <div class="pie-acciones">
        <button class="btn btn-primary" (click)="guardar()" [disabled]="!valido() || guardando">
          {{ guardando ? 'Guardando…' : (id ? 'Guardar cambios' : 'Registrar acta') }}
        </button>
        <span class="aviso" *ngIf="!valido()">
          Faltan distrito, OTB o presidente.
        </span>
      </div>
    </div>
  `,
  styles: [`
    .grilla { display: grid; gap: var(--e-2); grid-template-columns: repeat(auto-fit, minmax(230px, 1fr)); }
    label { display: block; font-size: 0.75rem; font-weight: 600; color: var(--text-secondary); }
    label .form-control { margin-top: 0.25rem; font-weight: 400; }
    .titulo-acciones { display: flex; justify-content: space-between; align-items: baseline; }
    .total { font-weight: 700; color: var(--pip-green-700); }
    .buscador { position: relative; margin: var(--e-2) 0; }
    .ayuda { font-size: 0.75rem; color: var(--text-secondary); margin: 0.3rem 0 0; }
    .pista {
      display: block; margin-top: 0.2rem; font-size: 0.6875rem; font-weight: 400;
      color: var(--text-secondary);
    }
    /* La lista de sugerencias se ancla al campo, no a la grilla. Como el
       envoltorio dejó de ser un <label>, repite su estilo de grilla. */
    .campo-padron {
      position: relative; display: block; font-size: 0.75rem;
      font-weight: 600; color: var(--text-secondary);
    }
    .campo-padron .form-control { margin-top: 0.25rem; font-weight: 400; }
    .sugerencias li.activa { background: var(--realce); }
    .sugerencias li[aria-selected="true"] { outline: 2px solid var(--pip-green-700); outline-offset: -2px; }
    .marca.dirigente { background: #FFE0B2; color: #E65100; }
    .sugerencias {
      position: absolute; z-index: 20; left: 0; right: 0; margin: 0.2rem 0 0;
      padding: 0; list-style: none; max-height: 320px; overflow: auto;
      background: var(--surface); border: 1px solid var(--border);
      border-radius: var(--radius); box-shadow: var(--shadow);
    }
    .sugerencias li { padding: 0.5rem 0.7rem; cursor: pointer; border-bottom: 1px solid var(--border); }
    .sugerencias li:hover { background: var(--realce); }
    .nombre { display: block; font-size: 0.8125rem; }
    .marca {
      display: inline-block; font-size: 0.625rem; margin-top: 0.2rem;
      margin-right: 0.3rem; padding: 0.05rem 0.35rem; border-radius: 999px;
      background: var(--realce); color: var(--text-secondary);
    }
    .marca.sisin { background: #C8E6C9; color: #1B5E20; }
    .marca.veces { background: #BBDEFB; color: #0D47A1; }
    .sin-borde { border: none; background: transparent; padding: 0.2rem; }
    .techos { margin: var(--e-2) 0; }
    .techos .rotulo {
      font-size: 0.6875rem; font-weight: 700; color: var(--text-secondary);
      text-transform: uppercase; letter-spacing: .06em;
    }
    .pares { display: flex; flex-wrap: wrap; gap: 0.45rem; margin-top: 0.35rem; }
    .par {
      border: 1px solid var(--border); border-radius: var(--radius);
      padding: 0.35rem 0.6rem; background: var(--surface); min-width: 130px;
    }
    .par strong { display: block; font-size: 0.75rem; }
    .par .disp { display: block; font-size: 0.8125rem; font-weight: 700; color: var(--pip-green-700); }
    .par small { font-size: 0.625rem; color: var(--text-secondary); }
    .par.agotado { border-color: #B3261E; }
    .par.agotado .disp { color: #B3261E; }
    .saldo { display: block; font-size: 0.625rem; color: var(--text-secondary); }
    .saldo.negativo { color: #B3261E; font-weight: 700; }
    .num { text-align: right; }
    .pavimento-check {
      display: flex;
      flex-direction: column;
      gap: 0.35rem;
    }

    .check-pavimento {
      min-height: 38px;

      display: flex;
      align-items: center;

      gap: 0.55rem;

      padding: 0.45rem 0.65rem;

      border: 1px solid var(--border);
      border-radius: var(--radius);

      background: var(--surface);

      font-size: 0.78rem;

      cursor: pointer;
    }

    .check-pavimento input[type="checkbox"] {
      width: 18px;
      height: 18px;

      margin: 0;

      flex: 0 0 auto;

      cursor: pointer;
    }

    .check-pavimento span {
      line-height: 1.25;
    }

    .pie-acciones { display: flex; gap: var(--e-2); align-items: center; margin-top: var(--e-2); }
    .aviso { font-size: 0.75rem; color: var(--text-secondary); }
    .msg-box.error {
      background: var(--error-fondo); color: var(--error-tinta);
      padding: 0.7rem 0.9rem; border-radius: var(--radius); margin-bottom: var(--e-2);
    }
  `],
})
export class ActaFormComponent implements OnInit {
  id = '';
  acta: ActaPriorizacion = {
    // La gestión sale del candado (ADR-007); el backend rechaza cualquier otra.
    gestion: 0, distrito: '', otb: '', unidad_territorial: null, presidente: '',
    responsable_registro: '', fecha: null,
    es_pavimento: false,
    proyectos: [],
  };
  distritos: any[] = [];
  organizaciones: OrganizacionTerritorial[] = [];
  sugeridas: OrganizacionTerritorial[] = [];
  /** Qué buscador del padrón está desplegado: '' | 'otb' | 'presidente'. */
  abiertoPadron = '';
  /** Opción resaltada por teclado. -1 = ninguna, se respeta lo tipeado. */
  indiceActivo = -1;
  cargoDirigente = '';
  /** Lo último que puso el padrón, para saber qué se puede retirar y qué no. */
  private presidenteDelPadron = '';
  categorias: any[] = [];
  pares: any[] = [];
  sugerencias: ProyectoCatalogo[] = [];
  totalHallado = 0;
  consulta = '';
  abierto = false;
  /** Opción resaltada por teclado en el buscador del catálogo. -1 = ninguna. */
  indiceProyecto = -1;
  guardando = false;
  error = '';

  private teclas = new Subject<string>();

  constructor(private api: PriorizacionService, private cdr: ChangeDetectorRef,
              private ruta: ActivatedRoute, private router: Router,
              private gestionActiva: GestionHabilitadaService,
              private anfitrion: ElementRef<HTMLElement>) {}

  ngOnInit(): void {
    // El acta nace en la gestión habilitada y el campo va de solo lectura:
    // no es una decisión del técnico, es el candado de SIS-POA (ADR-007).
    this.acta.gestion = this.gestionActiva.anio() ?? 0;
    this.api.distritos().subscribe(d => {
      this.distritos = d.results ?? d;
      this.cdr.markForCheck();
    });
    this.cargarPadron();
    this.cargarCategorias();
    this.cargarSaldos();

    // El buscador espera a que se deje de escribir: una consulta por tecla
    // satura el backend sin mejorar nada.
    this.teclas.pipe(
      autocompleteSearch(
        q => this.api.buscarProyectos(
          q,
          AUTOCOMPLETE_CONFIG.limit
        ),
        { resultados: [], total: 0 }
      ),
    ).subscribe({
      next: (d: any) => {
        this.sugerencias = d.resultados ?? [];
        this.totalHallado = d.total ?? 0;
        this.indiceProyecto = -1;
        this.cdr.markForCheck();
      },
      error: () => {
        this.sugerencias = [];
        this.indiceProyecto = -1;
        this.cdr.markForCheck();
      },
    });

    this.id = this.ruta.snapshot.paramMap.get('id') || '';
    if (this.id) { this.cargar(this.id); }
  }

  /**
   * Los saldos excluyen el acta que se está editando: si no, sus propios
   * montos se descontarían del techo que se le muestra al técnico.
   */
  private cargarSaldos(): void {
    this.api.saldos(this.id).subscribe({
      next: (d: any) => { this.pares = d.pares ?? []; this.cdr.markForCheck(); },
      error: () => { this.pares = []; },
    });
  }

  /** Lo cargado en este acta contra un par, que todavía no está en el techo. */
  cargadoEn(par: string): number {
    return this.acta.proyectos
      .filter((p: any) => p.par_elegido === par)
      .reduce((t, p) => t + (Number(p.monto) || 0), 0);
  }

  saldoTrasCargar(s: any): number {
    return s.disponible - this.cargadoEn(s.par);
  }

  saldoDelProyecto(p: any): number | null {
    const s = this.pares.find(x => x.par === p.par_elegido);
    return s ? this.saldoTrasCargar(s) : null;
  }

  /** Del par elegido salen los dos identificadores que guarda el acta. */
  elegirPar(p: any): void {
    const s = this.pares.find(x => x.par === p.par_elegido);
    p.fuente = s ? s.fuente_id : null;
    p.organismo = s ? s.organismo_id : null;
    this.cdr.markForCheck();
  }

  private cargarCategorias(): void {
    this.api.categorias().subscribe({
      next: (d: any) => { this.categorias = d.results ?? d; this.cdr.markForCheck(); },
      error: () => { this.categorias = []; },
    });
  }

  private cargar(id: string): void {
    this.api.obtenerActa(id).subscribe({
      next: a => {
        this.acta = { ...a, proyectos: a.proyectos ?? [] };
        // El par vuelve del backend como texto: se reconstruye para que el
        // desplegable muestre lo que ya se había elegido.
        for (const p of this.acta.proyectos as any[]) {
          p.par_elegido = p.par_financiamiento || '';
        }
        this.cargarSaldos();
        this.cdr.markForCheck();
      },
      error: () => { this.error = 'No se pudo cargar el acta.'; this.cdr.markForCheck(); },
    });
  }

  /**
   * Cambiar de distrito limpia lo ya escrito: dejar una OTB del distrito
   * anterior es peor que pedir que se elija de nuevo. El padrón no se vuelve a
   * pedir —está entero en memoria— solo se acota al distrito.
   */
  cambiarDistrito(distritoId: string): void {
    this.acta.distrito = distritoId;
    this.limpiarOrganizacion();
    this.cdr.markForCheck();
  }

  private limpiarOrganizacion(): void {
    this.acta.otb = '';
    this.acta.unidad_territorial = null;
    this.acta.presidente = '';
    this.presidenteDelPadron = '';
    this.cargoDirigente = '';
    this.sugeridas = [];
  }

  /**
   * El padrón se trae entero una sola vez. Son 368 filas con los doce
   * distritos cargados: filtrar en memoria es instantáneo y evita una consulta
   * por tecla.
   */
  private cargarPadron(): void {
    this.api.organizaciones().subscribe({
      next: (d: any) => {
        this.organizaciones = d.resultados ?? [];
        this.cdr.markForCheck();
      },
      error: () => { this.organizaciones = []; this.cdr.markForCheck(); },
    });
  }

  /** Lo que se puede elegir: el distrito del acta acota, si ya se eligió. */
  private get padron(): OrganizacionTerritorial[] {
    return this.acta.distrito
      ? this.organizaciones.filter(o => o.distrito === this.acta.distrito)
      : this.organizaciones;
  }

  abrir(campo: string): void {
    this.abiertoPadron = campo;
    this.indiceActivo = -1;
    // Al enfocar sin haber escrito se ve el padrón entero: es un desplegable
    // además de un buscador.
    const escrito = campo === 'otb' ? this.acta.otb : this.acta.presidente;
    this.sugeridas = this.filtrar(escrito, campo);
    this.cdr.markForCheck();
  }

  buscarOtb(evento: Event): void {
    this.acta.otb = (evento.target as HTMLInputElement).value;
    this.abiertoPadron = 'otb';
    this.indiceActivo = -1;
    this.sugeridas = this.filtrar(this.acta.otb, 'otb');
    this.resolverCoincidencia();
  }

  buscarPresidente(evento: Event): void {
    this.acta.presidente = (evento.target as HTMLInputElement).value;
    this.presidenteDelPadron = '';
    this.abiertoPadron = 'presidente';
    this.indiceActivo = -1;
    this.sugeridas = this.filtrar(this.acta.presidente, 'presidente');
    this.cdr.markForCheck();
  }

  /**
   * Cada palabra acota más —AND de contiene—, igual que el buscador de
   * proyectos. Sin texto devuelve el padrón entero, recortado para que la
   * lista no tape el formulario.
   */
  private filtrar(texto: string, campo: string): OrganizacionTerritorial[] {
    const palabras = this.normalizar(texto).split(' ').filter(Boolean);
    const contra = (o: OrganizacionTerritorial) => this.normalizar(
      campo === 'presidente' ? `${o.dirigente} ${o.nombre}`
                             : `${o.nombre} ${o.dirigente}`);
    return this.padron
      .filter(o => palabras.every(w => contra(o).includes(w)))
      .slice(0, 40);
  }

  /**
   * Escribir el nombre exacto vale lo mismo que elegirlo de la lista. Si se
   * sigue tipeando y se pierde la coincidencia, se suelta el enganche y se
   * retira lo que había puesto el padrón —no lo escrito a mano—.
   */
  private resolverCoincidencia(): void {
    const clave = this.normalizar(this.acta.otb);
    const hallada = this.padron.find(o => this.normalizar(o.nombre) === clave);
    if (hallada) {
      this.tomar(hallada, 'exacto');
      return;
    }
    this.acta.unidad_territorial = null;
    this.cargoDirigente = '';
    if (this.acta.presidente === this.presidenteDelPadron) {
      this.acta.presidente = '';
    }
    this.presidenteDelPadron = '';
    this.cdr.markForCheck();
  }

  /**
   * Elegir del padrón por cualquiera de los dos campos completa los dos.
   *
   * `origen` decide qué pasa con el presidente, y no es un detalle:
   * - `presidente`: se eligió a esa persona de la lista, gana el padrón.
   * - `otb` o `exacto`: se eligió la organización, así que un presidente
   *   escrito a mano se respeta —puede ser un cambio de dirigencia posterior
   *   al padrón, y el acta la firma quien firmó—.
   */
  tomar(o: OrganizacionTerritorial, origen = 'otb'): void {
    // Gana la grafía del padrón: es la que sale impresa en el acta.
    this.acta.otb = o.nombre;
    this.acta.unidad_territorial = o.id;
    this.cargoDirigente = o.cargo;
    // Elegir sin distrito lo resuelve solo: la organización sabe cuál es.
    if (o.distrito) { this.acta.distrito = o.distrito; }
    if (origen === 'presidente' || !this.acta.presidente.trim()
        || this.acta.presidente === this.presidenteDelPadron) {
      this.acta.presidente = o.dirigente;
      this.presidenteDelPadron = o.dirigente;
    }
    if (origen !== 'exacto') { this.cerrarPadron(); }
    this.cdr.markForCheck();
  }

  /**
   * El teclado maneja el combobox entero: flechas recorren, Enter elige,
   * Escape cierra. Quien carga actas todo el día no debería soltar el teclado
   * para ir al mouse por cada OTB.
   */
  teclaPadron(evento: KeyboardEvent, campo: string): void {
    if (this.abiertoPadron !== campo) {
      if (evento.key !== 'ArrowDown') { return; }
      this.abrir(campo);
    }
    switch (evento.key) {
      case 'ArrowDown':
        this.mover(1, campo);
        break;
      case 'ArrowUp':
        this.mover(-1, campo);
        break;
      case 'Enter':
        // Sin opción resaltada no se elige nada: lo tipeado vale como está,
        // que es lo que hace no restrictivo a este combobox.
        if (this.indiceActivo < 0) { return; }
        evento.preventDefault();
        this.tomar(this.sugeridas[this.indiceActivo], campo);
        break;
      case 'Escape':
        evento.preventDefault();
        this.cerrarPadron();
        break;
      case 'Tab':
        this.cerrarPadron();
        return;
      default:
        return;
    }
    // Las flechas no deben mover el cursor dentro del campo. Tab y el resto
    // ya salieron por `return` más arriba.
    evento.preventDefault();
    this.cdr.markForCheck();
  }

  private mover(paso: number, campo: string): void {
    if (!this.sugeridas.length) { return; }
    const total = this.sugeridas.length;
    // Da la vuelta en los extremos, y desde "nada resaltado" bajar lleva a la
    // primera y subir a la última.
    this.indiceActivo = this.indiceActivo < 0
      ? (paso > 0 ? 0 : total - 1)
      : (this.indiceActivo + paso + total) % total;
    this.desplazarAVista(campo);
  }

  /** La lista tiene alto máximo: sin esto la opción resaltada se sale. */
  private desplazarAVista(campo: string): void {
    const opcion = this.anfitrion.nativeElement.querySelector(
      `#opcion-${campo}-${this.indiceActivo}`);
    opcion?.scrollIntoView({ block: 'nearest' });
  }

  cerrarPadron(): void {
    this.abiertoPadron = '';
    this.indiceActivo = -1;
    this.sugeridas = [];
    this.cdr.markForCheck();
  }

  /** Le dice al lector de pantalla cuál opción está resaltada. */
  opcionActivaId(campo: string): string | null {
    return this.abiertoPadron === campo && this.indiceActivo >= 0
      ? `opcion-${campo}-${this.indiceActivo}` : null;
  }

  pistaOtb(): string {
    if (!this.organizaciones.length) { return 'Padrón no disponible: se escribe a mano.'; }
    if (this.acta.otb.trim() && !this.acta.unidad_territorial) {
      return 'No figura en el padrón: se guarda como texto libre.';
    }
    return `${this.padron.length} organizaciones en el padrón`
         + (this.acta.distrito ? ' del distrito.' : '. Elija una y se completa el distrito.');
  }

  /**
   * Espejo de `clave_organizacion` del backend: sin tildes ni puntuación, y
   * las siglas punteadas vueltas a pegar para que `O.T.B. VILLA` reconozca a
   * `OTB VILLA`. Si esto se desalinea, elegir del padrón deja de enganchar.
   */
  private normalizar(texto: string): string {
    const plano = (texto || '').toUpperCase()
      .normalize('NFD').replace(/[\u0300-\u036f]/g, '')
      .replace(/[^A-Z0-9 ]/g, ' ').replace(/\s+/g, ' ').trim();
    // Solo se junta una corrida de dos o más letras sueltas: una letra final
    // —`OTB SAN JOSE B`— es parte del nombre.
    return plano.replace(/\b(?:[A-Z] ){1,}[A-Z]\b/g, c => c.replace(/ /g, ''));
  }

  get total(): number {
    return this.acta.proyectos.reduce((t, p) => t + (Number(p.monto) || 0), 0);
  }

  buscar(evento: Event): void {
    this.consulta = (evento.target as HTMLInputElement).value;
    this.abierto = true;
    this.indiceProyecto = -1;
    if (
      this.consulta.trim().length <
      AUTOCOMPLETE_CONFIG.minChars
    ) {
      this.sugerencias = [];
      this.totalHallado = 0;
    }

    /*
     * Se emite siempre, incluso cuando queda por debajo
     * del mínimo. Así autocompleteSearch() puede cancelar
     * inmediatamente cualquier request anterior.
     */
    this.teclas.next(this.consulta);
  }

  /**
   * El teclado maneja el buscador del catálogo igual que los del padrón:
   * flechas recorren, Enter elige, Escape cierra. Antes la lista era solo
   * mouse: con el tabulador no había forma de alcanzar una sugerencia.
   */
  teclaProyecto(evento: KeyboardEvent): void {
    if (!this.abierto) {
      if (evento.key !== 'ArrowDown' || !this.sugerencias.length) { return; }
      this.abierto = true;
    }
    switch (evento.key) {
      case 'ArrowDown':
        this.moverProyecto(1);
        break;
      case 'ArrowUp':
        this.moverProyecto(-1);
        break;
      case 'Enter':
        // Sin opción resaltada no se agrega nada: el nombre libre sigue
        // saliendo por su botón, que es una decisión y no un descuido.
        if (this.indiceProyecto < 0) { return; }
        evento.preventDefault();
        this.elegir(this.sugerencias[this.indiceProyecto]);
        break;
      case 'Escape':
        evento.preventDefault();
        this.cerrarProyectos();
        break;
      case 'Tab':
        this.cerrarProyectos();
        return;
      default:
        return;
    }
    // Las flechas no deben mover el cursor dentro del campo. Tab y el resto
    // ya salieron por `return` más arriba.
    evento.preventDefault();
    this.cdr.markForCheck();
  }

  private moverProyecto(paso: number): void {
    if (!this.sugerencias.length) { return; }
    const total = this.sugerencias.length;
    // Da la vuelta en los extremos, y desde "nada resaltado" bajar lleva a la
    // primera y subir a la última.
    this.indiceProyecto = this.indiceProyecto < 0
      ? (paso > 0 ? 0 : total - 1)
      : (this.indiceProyecto + paso + total) % total;
    const opcion = this.anfitrion.nativeElement.querySelector(
      `#opcion-proyecto-${this.indiceProyecto}`);
    opcion?.scrollIntoView({ block: 'nearest' });
  }

  /**
   * Cierra sin borrar `sugerencias`: al volver al campo reaparece lo mismo que
   * muestra el texto que quedó escrito, sin repetir la consulta al servidor.
   */
  cerrarProyectos(): void {
    this.abierto = false;
    this.indiceProyecto = -1;
    this.cdr.markForCheck();
  }

  /** Le dice al lector de pantalla cuál opción está resaltada. */
  opcionProyectoActivaId(): string | null {
    return this.abierto && this.indiceProyecto >= 0
      ? `opcion-proyecto-${this.indiceProyecto}` : null;
  }

  elegir(s: ProyectoCatalogo): void {
    this.agregar({
      nombre: s.nombre, catalogo: s.id, sisin: s.sisin,
      categoria_programatica: s.categoria_programatica, monto: null,
    });
  }

  /** Lo priorizado puede no estar en el catálogo: se admite el nombre libre. */
  agregarLibre(): void {
    this.agregar({
      nombre: this.consulta.trim(), catalogo: null, sisin: '',
      categoria_programatica: '', monto: null,
    });
  }

  private agregar(p: ProyectoPriorizado): void {
    this.acta.proyectos.push({ ...p, fuente: null, organismo: null } as any);
    this.consulta = '';
    this.sugerencias = [];
    this.abierto = false;
    this.indiceProyecto = -1;
    this.cdr.markForCheck();
  }

  quitar(i: number): void {
    this.acta.proyectos.splice(i, 1);
    this.cdr.markForCheck();
  }

  fechaHoraMostrada(): string {
    const valor = this.acta.fecha_hora_registro;
    const fecha = valor ? new Date(valor) : new Date();

    return fecha.toLocaleString('es-BO', {
      timeZone: 'America/La_Paz',
      hour12: false,
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit'
    });
  }

  valido(): boolean {
    return !!(
      this.acta.distrito &&
      this.acta.otb.trim() &&
      this.acta.presidente.trim()
    );
  }

  guardar(): void {
    this.guardando = true;
    this.error = '';
    const peticion = this.id
      ? this.api.actualizarActa(this.id, this.acta)
      : this.api.crearActa(this.acta);
    peticion.subscribe({
      next: () => this.router.navigate(['/priorizacion/actas']),
      error: e => {
        this.error = this.mensaje(e);
        this.guardando = false;
        this.cdr.markForCheck();
      },
    });
  }

  private mensaje(e: any): string {
    const cuerpo = e?.error;
    if (typeof cuerpo === 'string') { return cuerpo; }
    if (cuerpo?.error) { return cuerpo.error; }
    // Los errores de validación de DRF vienen por campo.
    if (cuerpo && typeof cuerpo === 'object') {
      const primero = Object.entries(cuerpo)[0];
      if (primero) { return `${primero[0]}: ${[].concat(primero[1] as any).join(' ')}`; }
    }
    return 'No se pudo guardar el acta.';
  }
}

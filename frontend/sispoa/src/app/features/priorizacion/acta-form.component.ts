import { ChangeDetectorRef, Component, OnInit } from '@angular/core';
import { ActivatedRoute, Router } from '@angular/router';
import { Subject, debounceTime, distinctUntilChanged, switchMap } from 'rxjs';
import {
  ActaPriorizacion, PriorizacionService, ProyectoCatalogo, ProyectoPriorizado,
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
            <input class="form-control" type="number" [(ngModel)]="acta.gestion">
          </label>
          <label>Distrito
            <select class="form-control" [(ngModel)]="acta.distrito">
              <option value="">Seleccione…</option>
              <option *ngFor="let d of distritos" [value]="d.id">{{ d.nombre }}</option>
            </select>
          </label>
          <label>OTB / Junta vecinal
            <input class="form-control" [(ngModel)]="acta.otb"
                   placeholder="OTB SAN JOSE DE KORIPILA">
          </label>
          <label>Presidente
            <input class="form-control" [(ngModel)]="acta.presidente">
          </label>
          <label>Responsable del registro
            <input class="form-control" [(ngModel)]="acta.responsable_registro">
          </label>
          <label>Fecha de la priorización
            <input class="form-control" type="date" [(ngModel)]="acta.fecha">
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
                   placeholder="Escriba y agregue palabras para acotar: lumin distrito 4">
          </label>
          <p class="ayuda">
            Cada palabra que agregue acota más el resultado.
            <span *ngIf="consulta">{{ totalHallado }} coincidencia(s).</span>
          </p>
          <ul class="sugerencias" *ngIf="abierto && sugerencias.length">
            <li *ngFor="let s of sugerencias" (click)="elegir(s)">
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
            <button class="btn btn-sm btn-secondary" (click)="agregarLibre()">
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
          Faltan distrito, OTB, presidente o fecha.
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
    gestion: 2027, distrito: '', otb: '', presidente: '',
    responsable_registro: '', fecha: null, proyectos: [],
  };
  distritos: any[] = [];
  categorias: any[] = [];
  pares: any[] = [];
  sugerencias: ProyectoCatalogo[] = [];
  totalHallado = 0;
  consulta = '';
  abierto = false;
  guardando = false;
  error = '';

  private teclas = new Subject<string>();

  constructor(private api: PriorizacionService, private cdr: ChangeDetectorRef,
              private ruta: ActivatedRoute, private router: Router) {}

  ngOnInit(): void {
    this.api.distritos().subscribe(d => {
      this.distritos = d.results ?? d;
      this.cdr.markForCheck();
    });
    this.cargarCategorias();
    this.cargarSaldos();

    // El buscador espera a que se deje de escribir: una consulta por tecla
    // satura el backend sin mejorar nada.
    this.teclas.pipe(
      debounceTime(220),
      distinctUntilChanged(),
      switchMap(q => this.api.buscarProyectos(q)),
    ).subscribe({
      next: (d: any) => {
        this.sugerencias = d.resultados ?? [];
        this.totalHallado = d.total ?? 0;
        this.cdr.markForCheck();
      },
      error: () => { this.sugerencias = []; this.cdr.markForCheck(); },
    });

    this.id = this.ruta.snapshot.paramMap.get('id') || '';
    if (this.id) { this.cargar(this.id); }
  }

  /**
   * Los saldos excluyen el acta que se está editando: si no, sus propios
   * montos se descontarían del techo que se le muestra al técnico.
   */
  private cargarSaldos(): void {
    this.api.saldos(this.acta.gestion, this.id).subscribe({
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

  get total(): number {
    return this.acta.proyectos.reduce((t, p) => t + (Number(p.monto) || 0), 0);
  }

  buscar(evento: Event): void {
    this.consulta = (evento.target as HTMLInputElement).value;
    this.abierto = true;
    if (this.consulta.trim().length < 2) {
      this.sugerencias = [];
      this.totalHallado = 0;
      return;
    }
    this.teclas.next(this.consulta.trim());
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
    this.cdr.markForCheck();
  }

  quitar(i: number): void {
    this.acta.proyectos.splice(i, 1);
    this.cdr.markForCheck();
  }

  valido(): boolean {
    return !!(this.acta.distrito && this.acta.otb.trim()
              && this.acta.presidente.trim() && this.acta.fecha);
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

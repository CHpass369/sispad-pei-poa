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
          <select class="form-control filtro" [(ngModel)]="distrito" (change)="cargar()">
            <option value="">Todos los distritos</option>
            <option *ngFor="let d of distritos" [value]="d.id">{{ d.nombre }}</option>
          </select>
          <input class="form-control filtro" [(ngModel)]="busqueda"
                 (keyup.enter)="cargar()" placeholder="OTB o presidente">
          <a class="btn btn-sm btn-primary" routerLink="/priorizacion/actas/nueva">
            + Nueva acta
          </a>
        </div>
      </div>

      <div class="msg-box error" *ngIf="error">{{ error }}</div>
      <div class="msg-box aviso" *ngIf="aviso && !error">{{ aviso }}</div>

      <div class="tarjetas-resumen" *ngIf="actas.length">
        <div class="tarjeta"><span>{{ actas.length }}</span><small>actas</small></div>
        <div class="tarjeta"><span>{{ totalProyectos }}</span><small>proyectos</small></div>
        <div class="tarjeta">
          <span>Bs {{ montoTotal | number:'1.0-0' }}</span><small>priorizado</small>
        </div>
      </div>

      <div class="sin-datos" *ngIf="cargando"><span>Cargando actas…</span></div>

      <div class="tabla-caja" *ngIf="!cargando">
        <table class="tabla tabla-compacta">
          <thead>
            <tr>
              <th>Distrito</th><th>OTB / Junta vecinal</th><th>Presidente</th>
              <th>Fecha</th><th class="num">Proyectos</th><th class="num">Monto Bs</th>
              <th>Estado</th><th style="width:200px">Acciones</th>
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
              <td colspan="8">
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

  constructor(private api: PriorizacionService, private cdr: ChangeDetectorRef,
              private gestionActiva: GestionHabilitadaService) {}

  ngOnInit(): void {
    this.api.distritos().subscribe(d => {
      this.distritos = d.results ?? d;
      this.cdr.markForCheck();
    });
    this.cargar();
  }

  get totalProyectos(): number {
    return this.actas.reduce((t, a) => t + a.proyectos.length, 0);
  }

  get montoTotal(): number {
    return this.actas.reduce((t, a) => t + Number(a.monto_total || 0), 0);
  }

  cargar(): void {
    this.cargando = true;
    this.error = '';
    // La gestión no viaja como filtro: la resuelve el candado en el backend.
    this.api.listarActas({ distrito: this.distrito, q: this.busqueda })
      .pipe(finalize(() => { this.cargando = false; this.cdr.markForCheck(); }))
      .subscribe({
        next: d => {
          this.actas = d.results ?? d;
          this.cdr.markForCheck();
        },
        error: () => {
          this.error = 'No se pudieron cargar las actas.';
          this.cdr.markForCheck();
        },
      });
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
      next: () => { this.aviso = 'Acta eliminada.'; this.cargar(); },
      error: e => {
        this.error = e?.error?.error || 'No se pudo eliminar el acta.';
        this.cdr.markForCheck();
      },
    });
  }
}

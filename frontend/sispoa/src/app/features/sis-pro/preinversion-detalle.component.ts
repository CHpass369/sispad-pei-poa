import { Component, OnInit } from '@angular/core';
import { ActivatedRoute } from '@angular/router';
import { PermissionsService } from '../../core/services/permissions.service';
import {
  ITCP, PreinversionService, ProyectoPreinversion, ResultadoAccion,
  TDR, EDTP, ValidacionResultado,
} from './preinversion.service';

@Component({
  standalone: false,
  selector: 'app-preinversion-detalle',
  template: `
    <div class="page-header">
      <a routerLink="/sis-pro/preinversion" class="volver">← Preinversión</a>
      <h2>{{ proyecto?.codigo_interno }} — {{ proyecto?.nombre }}</h2>
      <p class="text-secondary" *ngIf="proyecto">
        Estado: <span class="badge estado">{{ service.etiquetaEstadoExpediente(proyecto.estado_preinversion) }}</span>
        · Tipología: <span class="badge">{{ proyecto.tipologia_rm115 ? service.tipologiaNombre(proyecto.tipologia_rm115) : 'Sin clasificar' }}</span>
        · Madurez: <strong>{{ proyecto.puntaje_madurez }}%</strong>
        · POA: {{ proyecto.habilitado_poa ? '✅ habilitado' : '—' }}
      </p>
    </div>
    <div *ngIf="cargando" class="loading">Cargando expediente...</div>
    <div class="alert alert-error" *ngIf="error">{{ error }}</div>
    <div class="alert alert-success" *ngIf="mensaje">{{ mensaje }}</div>

    <div class="card" *ngIf="proyecto && !cargando">
      <h3>Ficha de la iniciativa</h3>
      <form (ngSubmit)="guardarFicha()" class="ficha">
        <label>Problema / necesidad
          <textarea [(ngModel)]="ficha.problema" name="problema" rows="2" class="input"></textarea>
        </label>
        <label>Objetivo general
          <textarea [(ngModel)]="ficha.objetivo_general" name="obj" rows="2" class="input"></textarea>
        </label>
        <div class="fila">
          <label>Distrito
            <input [(ngModel)]="ficha.distrito" name="distrito" class="input" />
          </label>
          <label>Comunidad / OTB
            <input [(ngModel)]="ficha.comunidad" name="comunidad" class="input" />
          </label>
          <label>Localización
            <input [(ngModel)]="ficha.descripcion_localizacion" name="loc" class="input" />
          </label>
        </div>
        <div class="fila">
          <label>Presupuesto estimado (Bs)
            <input type="number" [(ngModel)]="ficha.presupuesto_estimado" name="pe" class="input" />
          </label>
          <label>Presupuesto aprobado (Bs)
            <input type="number" [(ngModel)]="ficha.presupuesto_aprobado" name="pa" class="input" />
          </label>
        </div>
        <div class="acciones">
          <button type="submit" class="btn btn-primary" [disabled]="!puedeEditar">Guardar ficha</button>
          <button type="button" class="btn" (click)="clasificar()" [disabled]="!puedeEditar">🤖 Clasificar RM 115</button>
        </div>
      </form>
    </div>

    <div class="card" *ngIf="proyecto && !cargando">
      <h3>Acciones del expediente</h3>
      <div class="acciones">
        <a class="btn btn-sm btn-wizard" [routerLink]="['/sis-pro/preinversion', proyecto.id, 'wizard']">
          ✨ Abrir wizard de llenado (ITCP → EDTP)
        </a>
      </div>
      <div class="acciones mt">
        <button class="btn btn-sm" (click)="inicializarItcp()" [disabled]="!puedeEditar">
          🚀 Inicializar ITCP
        </button>
        <button class="btn btn-sm" (click)="inicializarEdtp()" [disabled]="!puedeEditar">
          🚀 Inicializar EDTP
        </button>
        <button class="btn btn-sm" (click)="calcularMadurez()" [disabled]="!puedeValidar">
          📊 Calcular madurez
        </button>
        <button class="btn btn-sm" (click)="validar('ITCP')" [disabled]="!puedeValidar">✔ Validar ITCP</button>
        <button class="btn btn-sm" (click)="validar('EDTP')" [disabled]="!puedeValidar">✔ Validar EDTP</button>
        <button class="btn btn-sm" (click)="generar('ITCP')" [disabled]="!puedeValidar">📄 Generar ITCP DOCX</button>
        <button class="btn btn-sm" (click)="generar('EDTP')" [disabled]="!puedeValidar">📄 Generar EDTP DOCX</button>
        <button class="btn btn-sm" (click)="cambiarEstado('enviado_poa')" [disabled]="!puedeValidar">
          ➜ Enviar a SIS-POA
        </button>
      </div>
      <div class="acciones mt">
        <button class="btn btn-sm" (click)="descargarPaquete()">📦 Paquete de transferencia</button>
      </div>
      <div *ngIf="validacion" class="validacion">
        <div [class.ok]="validacion.aprobable" [class.ko]="!validacion.aprobable">
          {{ validacion.aprobable ? '✅ Aprobable' : '❌ No aprobable' }}
        </div>
        <ul *ngIf="validacion.errores.length">
          <li *ngFor="let e of validacion.errores">{{ e }}</li>
        </ul>
      </div>
    </div>

    <div class="card" *ngIf="itcp && !cargando">
      <h3>ITCP <span class="badge">{{ itcp.estado }}</span> v{{ itcp.version }}
        <a class="btn btn-sm float-right" [routerLink]="['/sis-pro/preinversion', proyecto?.id, 'itcp']">Asistente ITCP →</a>
      </h3>
      <div class="resumen">
        <span>Condiciones: <strong>{{ itcp.condiciones.length }}</strong></span>
        <span>Resultado: <strong>{{ itcp.resultado_preliminar || '—' }}</strong></span>
      </div>
    </div>

    <div class="card" *ngIf="tdr && !cargando">
      <h3>TDR del EDTP <span class="badge">{{ tdr.estado }}</span> v{{ tdr.version }}
        <a class="btn btn-sm float-right" [routerLink]="['/sis-pro/preinversion', proyecto?.id, 'tdr']">Asistente TDR →</a>
      </h3>
      <div class="resumen">
        <span>Presupuesto referencial: <strong>Bs {{ tdr.presupuesto_referencial || '—' }}</strong></span>
        <span>Duración: <strong>{{ tdr.duracion_dias ?? '—' }} días</strong></span>
      </div>
    </div>

    <div class="card" *ngIf="edtp && !cargando">
      <h3>EDTP <span class="badge">{{ edtp.estado }}</span> v{{ edtp.version }}
        <a class="btn btn-sm float-right" [routerLink]="['/sis-pro/preinversion', proyecto?.id, 'edtp']">Asistente EDTP →</a>
      </h3>
      <div class="resumen">
        <span>Secciones: <strong>{{ edtp.secciones.length }}</strong></span>
        <span>Viabilidad: <strong>{{ edtp.resultado_viabilidad || '—' }}</strong></span>
        <span>Costo total: <strong>Bs {{ totalCosto }}</strong></span>
        <span>Financiamiento: <strong>Bs {{ totalFinanciamiento }}</strong></span>
      </div>
    </div>
  `,
  styles: [`
    .page-header { margin-bottom: 1.5rem; }
    .volver { display: inline-block; font-size: 0.8125rem; color: var(--text-secondary); text-decoration: none; margin-bottom: 0.25rem; }
    .text-secondary { color: var(--text-secondary); font-size: 0.875rem; }
    .card { background: var(--surface); border: 1px solid var(--border); border-radius: 8px; padding: 1.25rem; margin-bottom: 1rem; }
    .card h3 { margin-top: 0; font-size: 1rem; }
    .ficha { display: flex; flex-direction: column; gap: 0.75rem; }
    .ficha label { display: flex; flex-direction: column; gap: 0.25rem; font-size: 0.75rem; color: var(--text-secondary); }
    .fila { display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 0.75rem; }
    .input { padding: 0.5rem; border: 1px solid var(--border); border-radius: 6px; font-size: 0.875rem; font-family: inherit; }
    .acciones { display: flex; gap: 0.5rem; flex-wrap: wrap; }
    .mt { margin-top: 0.75rem; }
    .btn { display: inline-flex; align-items: center; padding: 0.5rem 0.875rem; border-radius: 6px; border: none; font-size: 0.8125rem; font-weight: 600; cursor: pointer; text-decoration: none; }
    .btn-primary { background: var(--primary); color: white; }
    .btn-sm { background: #E3F2FD; color: #1565C0; }
    .btn-wizard { background: #FFF3E0; color: #E65100; }
    .float-right { margin-left: auto; }
    .badge { display: inline-block; padding: 0.125rem 0.5rem; border-radius: 4px; font-size: 0.6875rem; font-weight: 600; background: #E3F2FD; color: #1565C0; }
    .estado { background: #F3E5F5; color: #6A1B9A; }
    .resumen { display: flex; gap: 1.5rem; flex-wrap: wrap; font-size: 0.8125rem; }
    .validacion { margin-top: 1rem; padding: 0.75rem; border-radius: 6px; font-size: 0.8125rem; }
    .ok { color: #2E7D32; font-weight: 600; }
    .ko { color: #C62828; font-weight: 600; }
    .validacion ul { margin: 0.5rem 0 0; padding-left: 1.25rem; }
    .loading { text-align: center; padding: 2rem; color: var(--text-secondary); }
    .alert { padding: 0.75rem 1rem; border-radius: 6px; margin-bottom: 1rem; }
    .alert-error { background: #FFEBEE; color: var(--warn); }
    .alert-success { background: #E8F5E9; color: #2E7D32; }
  `],
})
export class PreinversionDetalleComponent implements OnInit {
  proyecto: ProyectoPreinversion | null = null;
  itcp: ITCP | null = null;
  tdr: TDR | null = null;
  edtp: EDTP | null = null;
  validacion: ValidacionResultado | null = null;
  cargando = true;
  error = '';
  mensaje = '';
  ficha: Partial<ProyectoPreinversion> = {};

  constructor(
    private route: ActivatedRoute,
    public service: PreinversionService,
    private permissions: PermissionsService,
  ) {}

  get puedeEditar(): boolean {
    return this.permissions.hasAnyCapability(['sis_pro.project.create', 'sis_pro.project.edit']);
  }

  get puedeValidar(): boolean {
    return this.permissions.hasAnyCapability(['sis_pro.preinvestment.validate']);
  }

  get totalCosto(): string {
    return this.edtp?.items_costo.reduce((s, i) => s + (Number(i.subtotal) || 0), 0).toFixed(2) ?? '0.00';
  }

  get totalFinanciamiento(): string {
    return this.edtp?.fuentes_financiamiento.reduce((s, f) => s + (Number(f.monto) || 0), 0).toFixed(2) ?? '0.00';
  }

  ngOnInit(): void {
    const id = this.route.snapshot.paramMap.get('id')!;
    this.cargar(id);
  }

  private cargar(id: string): void {
    this.cargando = true;
    this.service.obtenerProyecto(id).subscribe({
      next: (proyecto) => {
        this.proyecto = proyecto;
        this.ficha = {
          problema: proyecto.problema,
          objetivo_general: proyecto.objetivo_general,
          distrito: proyecto.distrito,
          comunidad: proyecto.comunidad,
          descripcion_localizacion: proyecto.descripcion_localizacion,
          presupuesto_estimado: proyecto.presupuesto_estimado,
          presupuesto_aprobado: proyecto.presupuesto_aprobado,
        };
        this.cargarExpediente(id);
      },
      error: () => { this.error = 'Error al cargar el proyecto'; this.cargando = false; },
    });
  }

  private cargarExpediente(id: string): void {
    this.service.listarItcps({ proyecto: id }).subscribe({
      next: (data) => { this.itcp = data.results[0] ?? null; },
      error: () => undefined,
    });
    this.service.listarTdrs({ proyecto: id }).subscribe({
      next: (data) => { this.tdr = data.results[0] ?? null; },
      error: () => undefined,
    });
    this.service.listarEdtps({ proyecto: id }).subscribe({
      next: (data) => { this.edtp = data.results[0] ?? null; this.cargando = false; },
      error: () => { this.cargando = false; },
    });
  }

  private notificar(accion: ResultadoAccion | string): void {
    this.mensaje = typeof accion === 'string' ? accion : JSON.stringify(accion);
    if (this.proyecto) this.cargar(this.proyecto.id);
  }

  private manejarError(msg: string): void {
    this.error = msg;
  }

  guardarFicha(): void {
    if (!this.proyecto) return;
    this.error = '';
    this.service.actualizarProyecto(this.proyecto.id, this.ficha).subscribe({
      next: () => { this.mensaje = 'Ficha actualizada'; },
      error: () => this.manejarError('Error al guardar la ficha'),
    });
  }

  clasificar(): void {
    if (!this.proyecto) return;
    this.service.clasificar(this.proyecto.id).subscribe({
      next: (r) => this.notificar(`Tipología sugerida: ${r.tipologia_sugerida}`),
      error: () => this.manejarError('Error al clasificar'),
    });
  }

  inicializarItcp(): void {
    if (!this.proyecto) return;
    this.service.inicializarItcp(this.proyecto.id).subscribe({
      next: (r) => this.notificar(`ITCP inicializado (${r.condiciones} condiciones)`),
      error: () => this.manejarError('Error al inicializar ITCP'),
    });
  }

  inicializarEdtp(): void {
    if (!this.proyecto) return;
    this.service.inicializarEdtp(this.proyecto.id).subscribe({
      next: (r) => this.notificar(`EDTP inicializado (${r.secciones} secciones)`),
      error: (e) => this.manejarError(e?.error?.detail ?? 'Error: el ITCP debe estar aprobado con TDR y presupuesto'),
    });
  }

  calcularMadurez(): void {
    if (!this.proyecto) return;
    this.service.calcularMadurez(this.proyecto.id).subscribe({
      next: (r) => this.notificar(
        `Madurez: ${r.puntaje_madurez}% — ${r.habilitado_poa ? 'habilitado para POA' : 'aún no habilitado'}`,
      ),
      error: () => this.manejarError('Error al calcular madurez'),
    });
  }

  validar(documento: 'ITCP' | 'EDTP'): void {
    if (!this.proyecto) return;
    this.validacion = null;
    this.service.validarAprobacion(this.proyecto.id, documento).subscribe({
      next: (r) => { this.validacion = r; },
      error: () => this.manejarError('Error al validar aprobación'),
    });
  }

  generar(documento: 'ITCP' | 'EDTP'): void {
    if (!this.proyecto) return;
    this.service.generarDocumento(this.proyecto.id, documento).subscribe({
      next: () => this.notificar(`${documento} encolado para generación DOCX`),
      error: (e) => this.manejarError(e?.error?.error ?? `Error al generar ${documento}`),
    });
  }

  cambiarEstado(estado: string): void {
    if (!this.proyecto) return;
    this.service.cambiarEstado(this.proyecto.id, estado).subscribe({
      next: () => this.notificar(`Estado cambiado a ${this.service.etiquetaEstadoExpediente(estado)}`),
      error: () => this.manejarError('Error al cambiar el estado'),
    });
  }

  descargarPaquete(): void {
    if (!this.proyecto) return;
    this.service.paqueteTransferencia(this.proyecto.id).subscribe({
      next: (paquete) => {
        const blob = new Blob([JSON.stringify(paquete, null, 2)], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `${paquete.project_code}_transferencia.json`;
        a.click();
        URL.revokeObjectURL(url);
      },
      error: () => this.manejarError('Error al generar el paquete de transferencia'),
    });
  }
}

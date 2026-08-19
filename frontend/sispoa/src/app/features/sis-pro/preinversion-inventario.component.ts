import { Component, OnInit } from '@angular/core';
import { PermissionsService } from '../../core/services/permissions.service';
import {
  DocumentoGenerado, PreinversionService, ProyectoPreinversion,
} from './preinversion.service';

@Component({
  standalone: false,
  selector: 'app-preinversion-inventario',
  template: `
    <div class="page-header">
      <h2>Inventario Documental — Preinversión</h2>
      <p class="text-secondary">Seleccione un proyecto y genere el ITCP o EDTP desde su expediente</p>
    </div>
    @if (error) {
      <div class="alert alert-error">{{ error }}</div>
    }
    @if (mensaje) {
      <div class="alert alert-success">{{ mensaje }}</div>
    }
    
    @if (proyectos.length && !cargando) {
      <div class="card">
        <h3>1. Seleccionar proyecto</h3>
        <div class="toolbar">
          <label>Gestión
            <input type="number" [(ngModel)]="filtro.gestion" (change)="cargarProyectos()" class="input" />
          </label>
          <label>Tipología
            <select [(ngModel)]="filtro.tipologia_rm115" (change)="cargarProyectos()" class="input">
              <option value="">Todas</option>
              <option value="I">I — Empresarial Productivo</option>
              <option value="II">II — Apoyo Productivo</option>
              <option value="III">III — Desarrollo Social</option>
              <option value="IV">IV — Fortalecimiento Institucional</option>
              <option value="V">V — Investigación y Tecnología</option>
            </select>
          </label>
        </div>
        <table class="data-table">
          <thead>
            <tr><th></th><th>Código</th><th>Proyecto</th><th>Tipología</th><th>Estado</th><th>Madurez</th></tr>
          </thead>
          <tbody>
            @for (p of proyectos; track p) {
              <tr
                [class.fila-seleccionada]="seleccionado?.id === p.id"
                (click)="seleccionar(p)" class="fila">
                <td><input type="radio" [checked]="seleccionado?.id === p.id" (change)="seleccionar(p)" /></td>
                <td>{{ p.codigo_interno }}</td>
                <td>{{ p.nombre }}</td>
                <td><span class="badge">{{ p.tipologia_rm115 || '—' }}</span></td>
                <td><span class="badge estado">{{ service.etiquetaEstadoExpediente(p.estado_preinversion) }}</span></td>
                <td>{{ p.puntaje_madurez }}%</td>
              </tr>
            }
          </tbody>
        </table>
      </div>
    }
    @if (!cargando && proyectos.length === 0) {
      <div class="empty">No hay proyectos. Créelos desde la cartera.</div>
    }
    
    @if (seleccionado) {
      <div class="card">
        <h3>2. Generar documentos — {{ seleccionado.codigo_interno }}</h3>
        <p class="text-secondary">
          ITCP: <span class="badge">{{ itcpEstado }}</span> ·
          EDTP: <span class="badge">{{ edtpEstado }}</span>
        </p>
        <div class="botones">
          @if (!tieneItcp) {
            <button class="btn btn-primary" (click)="inicializar('itcp')" [disabled]="!puedeEditar">
              🚀 Inicializar ITCP
            </button>
          }
          <button class="btn btn-primary" (click)="generar('ITCP')" [disabled]="!puedeValidar">
            📄 Generar ITCP DOCX
          </button>
          @if (!tieneEdtp) {
            <button class="btn btn-primary" (click)="inicializar('edtp')" [disabled]="!puedeEditar">
              🚀 Inicializar EDTP
            </button>
          }
          <button class="btn btn-primary" (click)="generar('EDTP')" [disabled]="!puedeValidar">
            📄 Generar EDTP DOCX
          </button>
          <a class="btn" [routerLink]="['/sis-pro/preinversion', seleccionado.id, 'wizard']">Wizard de llenado →</a>
        </div>
      </div>
    }
    
    @if (historial.length) {
      <div class="card">
        <h3>3. Historial de documentos generados</h3>
        <table class="data-table">
          <thead>
            <tr><th>Proyecto</th><th>Tipo</th><th>Estado</th><th>Fecha</th><th>Descargar</th></tr>
          </thead>
          <tbody>
            @for (g of historial; track g) {
              <tr>
                <td>{{ proyectoNombre(g.proyecto) }}</td>
                <td>{{ g.tipo_documento }}</td>
                <td><span class="badge" [class.verde]="g.estado === 'completado'" [class.rojo]="g.estado === 'fallido'">{{ g.estado }}</span></td>
                <td>{{ g.created_at | date: 'short' }}</td>
                <td>
                  @if (g.archivo_docx) {
                    <a class="btn btn-sm" [href]="service.urlArchivo(g.archivo_docx)" target="_blank">DOCX</a>
                  }
                  @if (g.archivo_pdf) {
                    <a class="btn btn-sm" [href]="service.urlArchivo(g.archivo_pdf)" target="_blank">PDF</a>
                  }
                </td>
              </tr>
            }
          </tbody>
        </table>
      </div>
    }
    `,
  styles: [`
    .page-header { margin-bottom: 1.5rem; }
    .text-secondary { color: var(--text-secondary); font-size: 0.875rem; }
    .card { background: var(--surface); border: 1px solid var(--border); border-radius: 8px; padding: 1.25rem; margin-bottom: 1rem; }
    .card h3 { margin-top: 0; font-size: 1rem; }
    .toolbar { display: flex; gap: 1rem; align-items: flex-end; margin-bottom: 1rem; flex-wrap: wrap; }
    .toolbar label { display: flex; flex-direction: column; gap: 0.25rem; font-size: 0.75rem; color: var(--text-secondary); }
    .input { padding: 0.5rem; border: 1px solid var(--border); border-radius: 6px; font-size: 0.875rem; }
    .data-table { width: 100%; border-collapse: collapse; font-size: 0.8125rem; }
    .data-table th, 
    .fila { cursor: pointer; }
    .fila:hover { background: #F5F7FA; }
    .fila-seleccionada { background: var(--mdc-blue-50) !important; }
    .badge { display: inline-block; padding: 0.125rem 0.5rem; border-radius: 4px; font-size: 0.6875rem; font-weight: 600; background: var(--mdc-blue-50); color: var(--mdc-blue-800); }
    .estado { background: #F3E5F5; color: #6A1B9A; }
    .verde { background: var(--mdc-green-50); color: var(--mdc-green-800); }
    .rojo { background: var(--mdc-red-50); color: var(--mdc-red-800); }
    .botones { display: flex; gap: 0.5rem; flex-wrap: wrap; }
    .btn { display: inline-flex; align-items: center; padding: 0.5rem 0.875rem; border-radius: 6px; border: none; font-size: 0.8125rem; font-weight: 600; cursor: pointer; text-decoration: none; }
    .btn-primary { background: var(--primary); color: white; }
    .btn-sm { background: var(--mdc-blue-50); color: var(--mdc-blue-800); padding: 0.375rem 0.625rem; }
    .empty { text-align: center; padding: 2rem; color: var(--text-secondary); }
    .alert { padding: 0.75rem 1rem; border-radius: 6px; margin-bottom: 1rem; }
    .alert-error { background: var(--mdc-red-50); color: var(--warn); }
    .alert-success { background: var(--mdc-green-50); color: var(--mdc-green-800); }
  `],
})
export class PreinversionInventarioComponent implements OnInit {
  cargando = true;
  error = '';
  mensaje = '';
  proyectos: ProyectoPreinversion[] = [];
  seleccionado: ProyectoPreinversion | null = null;
  historial: DocumentoGenerado[] = [];
  tieneItcp = false;
  tieneEdtp = false;
  itcpEstado = '—';
  edtpEstado = '—';
  filtro: { gestion?: number; tipologia_rm115?: string } = {};

  constructor(
    public service: PreinversionService,
    private permissions: PermissionsService,
  ) {}

  get puedeEditar(): boolean {
    return this.permissions.hasAnyCapability(['sis_pro.project.create', 'sis_pro.project.edit']);
  }

  get puedeValidar(): boolean {
    return this.permissions.hasAnyCapability(['sis_pro.preinvestment.validate']);
  }

  ngOnInit(): void {
    this.cargarProyectos();
    this.service.listarDocumentosGenerados().subscribe({
      next: (data) => { this.historial = data.results; },
      error: () => undefined,
    });
  }

  cargarProyectos(): void {
    this.cargando = true;
    this.error = '';
    const params: Record<string, string | number> = {};
    if (this.filtro.gestion) params['gestion'] = this.filtro.gestion;
    if (this.filtro.tipologia_rm115) params['tipologia_rm115'] = this.filtro.tipologia_rm115;
    this.service.listarProyectos(params).subscribe({
      next: (data) => {
        this.proyectos = data.results;
        this.cargando = false;
        if (this.seleccionado) {
          const vigente = this.proyectos.find(p => p.id === this.seleccionado!.id);
          this.seleccionado = vigente ?? null;
        }
      },
      error: () => { this.error = 'Error al cargar proyectos'; this.cargando = false; },
    });
  }

  seleccionar(p: ProyectoPreinversion): void {
    this.seleccionado = p;
    this.error = '';
    this.mensaje = '';
    this.tieneItcp = false;
    this.tieneEdtp = false;
    this.itcpEstado = '—';
    this.edtpEstado = '—';
    this.service.listarItcps({ proyecto: p.id }).subscribe({
      next: (data) => {
        const itcp = data.results[0];
        if (itcp) {
          this.tieneItcp = true;
          this.itcpEstado = itcp.estado;
        }
      },
      error: () => undefined,
    });
    this.service.listarEdtps({ proyecto: p.id }).subscribe({
      next: (data) => {
        const edtp = data.results[0];
        if (edtp) {
          this.tieneEdtp = true;
          this.edtpEstado = edtp.estado;
        }
      },
      error: () => undefined,
    });
  }

  inicializar(tipo: 'itcp' | 'edtp'): void {
    if (!this.seleccionado) return;
    const obs = tipo === 'itcp'
      ? this.service.inicializarItcp(this.seleccionado.id)
      : this.service.inicializarEdtp(this.seleccionado.id);
    obs.subscribe({
      next: (r) => {
        this.mensaje = tipo === 'itcp'
          ? `ITCP inicializado (${r.condiciones} condiciones)`
          : `EDTP inicializado (${r.secciones} secciones)`;
        this.seleccionar(this.seleccionado!);
      },
      error: (e) => this.error = e?.error?.detail
        ?? e?.error?.error
        ?? `Error al inicializar ${tipo.toUpperCase()}`,
    });
  }

  generar(tipo: 'ITCP' | 'EDTP'): void {
    if (!this.seleccionado) return;
    this.service.generarDocumento(this.seleccionado.id, tipo).subscribe({
      next: () => {
        this.mensaje = `${tipo} encolado para generación DOCX`;
        this.service.listarDocumentosGenerados().subscribe({
          next: (data) => { this.historial = data.results; },
          error: () => undefined,
        });
      },
      error: (e) => this.error = e?.error?.error ?? `Error al generar ${tipo}`,
    });
  }

  proyectoNombre(id: string): string {
    const p = this.proyectos.find(x => x.id === id);
    return p ? `${p.codigo_interno} — ${p.nombre}` : id;
  }
}

import { Component, OnInit } from '@angular/core';
import { ActivatedRoute } from '@angular/router';
import { PermissionsService } from '../../core/services/permissions.service';
import { CondicionITCP, ITCP, PreinversionService } from './preinversion.service';

@Component({
  standalone: false,
  selector: 'app-preinversion-itcp',
  template: `
    <div class="page-header">
      <a [routerLink]="['/sis-pro/preinversion', proyectoId]" class="volver">← Expediente</a>
      <h2>Asistente ITCP — Condiciones Previas</h2>
      <p class="text-secondary">RM 115 · Informe Técnico de Condiciones Previas</p>
    </div>
    @if (cargando) {
      <div class="loading">Cargando ITCP...</div>
    }
    @if (error) {
      <div class="alert alert-error">{{ error }}</div>
    }
    @if (mensaje) {
      <div class="alert alert-success">{{ mensaje }}</div>
    }
    
    @if (itcp && !cargando) {
      <div class="card">
        <h3>Información general
          <span class="badge estado">{{ itcp.estado }}</span> v{{ itcp.version }}
        </h3>
        <div class="grid">
          <label>Justificación de la iniciativa
            <textarea [(ngModel)]="itcp.justificacion_iniciativa" name="ji" rows="3" class="input" (change)="guardarItcp()"></textarea>
          </label>
          <label>Idea del proyecto
            <textarea [(ngModel)]="itcp.idea_proyecto" name="idea" rows="3" class="input" (change)="guardarItcp()"></textarea>
          </label>
          <label>Resultado preliminar
            <select [(ngModel)]="itcp.resultado_preliminar" name="rp" class="input" (change)="guardarItcp()">
              <option value="">— Seleccionar —</option>
              <option value="viable_edtp">Viable para elaborar EDTP</option>
              <option value="viable_condiciones">Viable con condiciones</option>
              <option value="no_viable">No viable</option>
              <option value="informacion_insuficiente">Información insuficiente</option>
            </select>
          </label>
          <label>Conclusiones
            <textarea [(ngModel)]="itcp.conclusiones" name="concl" rows="3" class="input" (change)="guardarItcp()"></textarea>
          </label>
          <label>Recomendaciones
            <textarea [(ngModel)]="itcp.recomendaciones" name="recom" rows="3" class="input" (change)="guardarItcp()"></textarea>
          </label>
        </div>
      </div>
    }
    
    @if (condiciones.length && !cargando) {
      <div class="card">
        <h3>Matriz de condiciones previas</h3>
        <div class="semafaro">
          <span class="chip verde">{{ resueltas }} resueltas</span>
          <span class="chip rojo">{{ pendientes }} pendientes</span>
          <span class="chip gris">{{ criticas }} críticas</span>
        </div>
        <table class="data-table">
          <thead>
            <tr><th>Categoría</th><th>Condición</th><th>Estado</th><th>Hallazgo / Plan de acción</th><th>Crítica</th><th></th></tr>
          </thead>
          <tbody>
            @for (c of condiciones; track c) {
              <tr [class.no-aplica]="c.estado === 'no_aplica'">
                <td>{{ service.condicionCategoria(c.categoria) }}</td>
                <td>
                  <strong>{{ c.titulo }}</strong>
                  @if (editando === c.id) {
                    <textarea [(ngModel)]="c.hallazgo" name="h" rows="2" class="input" placeholder="Hallazgo"></textarea>
                  }
                  @if (editando === c.id) {
                    <textarea [(ngModel)]="c.plan_accion" name="pa" rows="2" class="input" placeholder="Plan de acción"></textarea>
                  }
                  @if (editando === c.id && c.estado === 'no_aplica') {
                    <textarea [(ngModel)]="c.justificacion_no_aplica" name="jna" rows="2" class="input" placeholder="Justificación de no aplica"></textarea>
                  }
                </td>
                <td>
                  <select [(ngModel)]="c.estado" name="est" class="input" (change)="guardarCondicion(c)">
                    @for (e of service.estadosCondicion; track e) {
                      <option [value]="e">{{ etiquetaEstado(e) }}</option>
                    }
                  </select>
                </td>
                <td>
                  @if (editando !== c.id) {
                    <span class="texto">{{ c.hallazgo || '—' }}</span>
                  }
                </td>
                <td>{{ c.critica ? '🔴' : '—' }}</td>
                <td>
                  <button class="btn btn-sm" (click)="toggleEditar(c)" [disabled]="!puedeEditar">
                    {{ editando === c.id ? 'Cerrar' : '✎' }}
                  </button>
                  @if (editando === c.id) {
                    <button class="btn btn-sm" (click)="guardarCondicion(c)" [disabled]="!puedeEditar">Guardar</button>
                  }
                </td>
              </tr>
            }
          </tbody>
        </table>
      </div>
    }
    
    @if (itcp && !cargando) {
      <div class="card">
        <div class="acciones">
          <button class="btn" (click)="validar()" [disabled]="!puedeValidar">✔ Validar aprobación</button>
          <button class="btn btn-primary" (click)="generar()" [disabled]="!puedeValidar">📄 Generar ITCP DOCX</button>
          <button class="btn" (click)="aprobar()" [disabled]="!puedeValidar">✅ Marcar ITCP aprobado</button>
        </div>
        @if (errores.length) {
          <div class="errores">
            <strong>No aprobable:</strong>
            <ul>@for (e of errores; track e) {
              <li>{{ e }}</li>
            }</ul>
          </div>
        }
      </div>
    }
    `,
  styles: [`
    .page-header { margin-bottom: 1.5rem; }
    .volver { display: inline-block; font-size: 0.8125rem; color: var(--text-secondary); text-decoration: none; margin-bottom: 0.25rem; }
    .text-secondary { color: var(--text-secondary); font-size: 0.875rem; }
    .card { background: var(--surface); border: 1px solid var(--border); border-radius: 8px; padding: 1.25rem; margin-bottom: 1rem; }
    .card h3 { margin-top: 0; font-size: 1rem; }
    .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 0.75rem; }
    .grid label { display: flex; flex-direction: column; gap: 0.25rem; font-size: 0.75rem; color: var(--text-secondary); }
    .input { padding: 0.5rem; border: 1px solid var(--border); border-radius: 6px; font-size: 0.875rem; font-family: inherit; }
    .semafaro { display: flex; gap: 0.5rem; margin-bottom: 1rem; }
    .chip { padding: 0.25rem 0.625rem; border-radius: 999px; font-size: 0.75rem; font-weight: 600; }
    .verde { background: var(--mdc-green-50); color: var(--mdc-green-800); }
    .rojo { background: var(--mdc-red-50); color: var(--mdc-red-800); }
    .gris { background: var(--mdc-amber-50); color: #E65100; }
    .data-table { width: 100%; border-collapse: collapse; font-size: 0.8125rem; }
    .data-table th, .data-table td { padding: 0.5rem 0.625rem; text-align: left; border-bottom: 1px solid var(--border); vertical-align: top; }
    .no-aplica td { opacity: 0.6; }
    .texto { white-space: pre-wrap; }
    .badge { display: inline-block; padding: 0.125rem 0.5rem; border-radius: 4px; font-size: 0.6875rem; font-weight: 600; background: var(--mdc-blue-50); color: var(--mdc-blue-800); }
    .estado { background: #F3E5F5; color: #6A1B9A; }
    .acciones { display: flex; gap: 0.5rem; flex-wrap: wrap; }
    .btn { display: inline-flex; align-items: center; padding: 0.5rem 0.875rem; border-radius: 6px; border: none; font-size: 0.8125rem; font-weight: 600; cursor: pointer; }
    .btn-primary { background: var(--primary); color: white; }
    .btn-sm { background: var(--mdc-blue-50); color: var(--mdc-blue-800); }
    .errores { margin-top: 1rem; padding: 0.75rem; background: var(--mdc-red-50); border-radius: 6px; font-size: 0.8125rem; color: var(--mdc-red-800); }
    .errores ul { margin: 0.25rem 0 0; padding-left: 1.25rem; }
    .loading { text-align: center; padding: 2rem; color: var(--text-secondary); }
    .alert { padding: 0.75rem 1rem; border-radius: 6px; margin-bottom: 1rem; }
    .alert-error { background: var(--mdc-red-50); color: var(--warn); }
    .alert-success { background: var(--mdc-green-50); color: var(--mdc-green-800); }
  `],
})
export class PreinversionItcpComponent implements OnInit {
  proyectoId = '';
  itcp: ITCP | null = null;
  condiciones: CondicionITCP[] = [];
  editando: string | null = null;
  errores: string[] = [];
  cargando = true;
  error = '';
  mensaje = '';

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

  get resueltas(): number {
    return this.condiciones.filter(c => ['cumple', 'aprobada', 'no_aplica'].includes(c.estado)).length;
  }

  get pendientes(): number {
    return this.condiciones.filter(c => !['cumple', 'aprobada', 'no_aplica'].includes(c.estado)).length;
  }

  get criticas(): number {
    return this.condiciones.filter(c => c.critica && !['cumple', 'aprobada', 'no_aplica'].includes(c.estado)).length;
  }

  ngOnInit(): void {
    this.proyectoId = this.route.snapshot.paramMap.get('id')!;
    this.service.listarItcps({ proyecto: this.proyectoId }).subscribe({
      next: (data) => {
        const itcp = data.results[0];
        if (!itcp) {
          this.error = 'Este proyecto no tiene ITCP. Inicialícelo desde el expediente.';
          this.cargando = false;
          return;
        }
        this.itcp = itcp;
        this.cargarCondiciones(itcp.id);
      },
      error: () => { this.error = 'Error al cargar el ITCP'; this.cargando = false; },
    });
  }

  private cargarCondiciones(itcpId: string): void {
    this.service.listarCondiciones({ itcp: itcpId }).subscribe({
      next: (condiciones) => {
        this.condiciones = condiciones;
        this.cargando = false;
      },
      error: () => { this.error = 'Error al cargar las condiciones'; this.cargando = false; },
    });
  }

  etiquetaEstado(estado: string): string {
    const mapa: Record<string, string> = {
      pendiente: 'Pendiente', en_elaboracion: 'En elaboración',
      observada: 'Observada', subsanada: 'Subsanada',
      cumple: 'Cumple', no_aplica: 'No aplica', aprobada: 'Aprobada',
    };
    return mapa[estado] ?? estado;
  }

  toggleEditar(c: CondicionITCP): void {
    this.editando = this.editando === c.id ? null : c.id;
  }

  guardarCondicion(c: CondicionITCP): void {
    this.error = '';
    if (c.estado === 'no_aplica' && !c.justificacion_no_aplica) {
      this.error = 'Debe justificar por qué la condición no aplica';
      return;
    }
    this.service.actualizarCondicion(c.id, {
      estado: c.estado,
      hallazgo: c.hallazgo,
      plan_accion: c.plan_accion,
      justificacion_no_aplica: c.justificacion_no_aplica,
    }).subscribe({
      next: () => { this.mensaje = 'Condición guardada'; this.editando = null; },
      error: () => this.error = 'Error al guardar la condición',
    });
  }

  guardarItcp(): void {
    if (!this.itcp) return;
    this.service.actualizarItcp(this.itcp.id, {
      justificacion_iniciativa: this.itcp.justificacion_iniciativa,
      idea_proyecto: this.itcp.idea_proyecto,
      resultado_preliminar: this.itcp.resultado_preliminar,
      conclusiones: this.itcp.conclusiones,
      recomendaciones: this.itcp.recomendaciones,
    }).subscribe({
      next: () => { this.mensaje = 'ITCP guardado'; },
      error: () => this.error = 'Error al guardar el ITCP',
    });
  }

  validar(): void {
    this.errores = [];
    this.service.validarAprobacion(this.proyectoId, 'ITCP').subscribe({
      next: (r) => {
        this.errores = r.errores ?? [];
        if (!this.errores.length) this.mensaje = '✅ ITCP aprobable';
      },
      error: () => this.error = 'Error al validar el ITCP',
    });
  }

  generar(): void {
    this.service.generarDocumento(this.proyectoId, 'ITCP').subscribe({
      next: () => this.mensaje = 'ITCP encolado para generación DOCX',
      error: (e) => this.error = e?.error?.error ?? 'Error al generar el ITCP',
    });
  }

  aprobar(): void {
    if (!this.itcp) return;
    this.service.actualizarItcp(this.itcp.id, { estado: 'aprobado' }).subscribe({
      next: () => {
        this.mensaje = 'ITCP aprobado';
        this.service.cambiarEstado(this.proyectoId, 'itcp_aprobado').subscribe({
          next: () => undefined,
          error: () => undefined,
        });
      },
      error: () => this.error = 'Error al aprobar el ITCP',
    });
  }
}

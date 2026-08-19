import { Component, OnInit } from '@angular/core';
import { ActivatedRoute } from '@angular/router';
import { PermissionsService } from '../../core/services/permissions.service';
import {
  ComponenteProyecto, EDTP, EstudioTecnico, FuenteFinanciamientoEDTP,
  ItemCostoEDTP, PreinversionService, SeccionEDTP,
} from './preinversion.service';

@Component({
  standalone: false,
  selector: 'app-preinversion-edtp',
  template: `
    <div class="page-header">
      <a [routerLink]="['/sis-pro/preinversion', proyectoId]" class="volver">← Expediente</a>
      <h2>Asistente EDTP — Estudio de Diseño Técnico de Preinversión</h2>
      <p class="text-secondary">RM 115 · secciones dinámicas por tipología</p>
    </div>
    @if (cargando) {
      <div class="loading">Cargando EDTP...</div>
    }
    @if (error) {
      <div class="alert alert-error">{{ error }}</div>
    }
    @if (mensaje) {
      <div class="alert alert-success">{{ mensaje }}</div>
    }
    
    @if (edtp && !cargando) {
      <div class="card">
        <h3>Información general <span class="badge">{{ edtp.estado }}</span> v{{ edtp.version }}</h3>
        <div class="grid">
          <label>Resumen ejecutivo
            <textarea [(ngModel)]="edtp.resumen_ejecutivo" name="re" rows="3" class="input" (change)="guardar()"></textarea>
          </label>
          <label>Método de evaluación
            <select [(ngModel)]="edtp.metodo_evaluacion" name="me" class="input" (change)="guardar()">
              <option value="">— Seleccionar —</option>
              <option value="costo_beneficio">Costo / Beneficio</option>
              <option value="costo_efectividad">Costo / Efectividad</option>
              <option value="multicriterio">Multicriterio</option>
            </select>
          </label>
          <label>Resultado de viabilidad
            <select [(ngModel)]="edtp.resultado_viabilidad" name="rv" class="input" (change)="guardar()">
              <option value="">— Seleccionar —</option>
              <option value="viable">Viable</option>
              <option value="viable_condiciones">Viable con condiciones</option>
              <option value="no_viable">No viable</option>
              <option value="suspendido">Suspendido</option>
            </select>
          </label>
          <label>Conclusiones
            <textarea [(ngModel)]="edtp.conclusiones" name="c" rows="3" class="input" (change)="guardar()"></textarea>
          </label>
          <label>Recomendaciones
            <textarea [(ngModel)]="edtp.recomendaciones" name="r" rows="3" class="input" (change)="guardar()"></textarea>
          </label>
        </div>
      </div>
    }
    
    @if (edtp && !cargando) {
      <div class="card">
        <h3>Componentes</h3>
        @if (puedeEditar) {
          <form (ngSubmit)="agregarComponente()" class="form-inline">
            <input [(ngModel)]="componente.codigo" name="cc" placeholder="Código" required class="input" />
            <input [(ngModel)]="componente.nombre" name="cn" placeholder="Nombre" required class="input" />
            <input [(ngModel)]="componente.presupuesto" name="cp" type="number" placeholder="Presupuesto" class="input" />
            <button type="submit" class="btn btn-primary">+ Componente</button>
          </form>
        }
        <table class="data-table">
          <tbody>
            @for (c of componentes; track c) {
              <tr>
                <td><span class="badge">{{ c.codigo }}</span></td>
                <td>{{ c.nombre }}</td>
                <td>Bs {{ c.presupuesto }}</td>
              </tr>
            }
          </tbody>
        </table>
      </div>
    }
    
    @if (edtp && !cargando) {
      <div class="card">
        <h3>Secciones del estudio</h3>
        <div class="semafaro">
          <span class="chip verde">{{ seccionesAprobadas }} aprobadas</span>
          <span class="chip gris">{{ seccionesPendientes }} pendientes</span>
        </div>
        <table class="data-table">
          <thead>
            <tr><th>Cód.</th><th>Sección</th><th>Requerida</th><th>Aplica</th><th>Estado</th><th>Contenido</th><th></th></tr>
          </thead>
          <tbody>
            @for (s of edtp.secciones; track s) {
              <tr>
                <td><span class="badge">{{ s.codigo }}</span></td>
                <td>{{ s.titulo }}</td>
                <td>{{ s.requerida ? '✔' : '—' }}</td>
                <td>
                  <select [(ngModel)]="s.aplicable" name="ap" class="input" (change)="guardarSeccion(s)">
                    <option [ngValue]="true">Sí</option>
                    <option [ngValue]="false">No</option>
                  </select>
                </td>
                <td>
                  <select [(ngModel)]="s.estado" name="es" class="input" (change)="guardarSeccion(s)">
                    @for (e of service.estadosDocumento; track e) {
                      <option [value]="e">{{ etiquetaEstado(e) }}</option>
                    }
                  </select>
                </td>
                <td>
                  <textarea [(ngModel)]="s.contenido" name="con" rows="2" class="input" (change)="guardarSeccion(s)" placeholder="Contenido de la sección"></textarea>
                  @if (!s.aplicable) {
                    <input [(ngModel)]="s.justificacion_no_aplica" name="jna" class="input" placeholder="Justificación de no aplica" (change)="guardarSeccion(s)" />
                  }
                </td>
                <td><span class="chip" [class.gris]="s.estado !== 'aprobado'" [class.verde]="s.estado === 'aprobado'">{{ s.porcentaje_avance }}%</span></td>
              </tr>
            }
          </tbody>
        </table>
      </div>
    }
    
    @if (edtp && !cargando) {
      <div class="card">
        <h3>Estudios técnicos</h3>
        @if (puedeEditar) {
          <form (ngSubmit)="agregarEstudio()" class="form-inline">
            <input [(ngModel)]="estudio.tipo_estudio" name="te" placeholder="Tipo (topografía, suelos...)" required class="input" />
            <input [(ngModel)]="estudio.titulo" name="tt" placeholder="Título" required class="input" />
            <button type="submit" class="btn btn-primary">+ Estudio</button>
          </form>
        }
        <table class="data-table">
          <tbody>
            @for (e of edtp.estudios_tecnicos; track e) {
              <tr>
                <td>{{ e.tipo_estudio }}</td>
                <td>{{ e.titulo }}</td>
                <td>{{ e.profesional || '—' }}</td>
                <td>
                  <select [(ngModel)]="e.estado" name="ee" class="input" (change)="actualizarEstudio(e)">
                    @for (st of service.estadosDocumento; track st) {
                      <option [value]="st">{{ etiquetaEstado(st) }}</option>
                    }
                  </select>
                </td>
              </tr>
            }
          </tbody>
        </table>
      </div>
    }
    
    @if (edtp && !cargando) {
      <div class="card">
        <h3>Costos de inversión</h3>
        @if (puedeEditar) {
          <form (ngSubmit)="agregarCosto()" class="form-inline">
            <input [(ngModel)]="costo.codigo" name="k" placeholder="Código" required class="input" />
            <input [(ngModel)]="costo.descripcion" name="d" placeholder="Descripción" required class="input" />
            <input [(ngModel)]="costo.unidad" name="u" placeholder="Unidad" required class="input" />
            <input [(ngModel)]="costo.cantidad" name="q" type="number" placeholder="Cantidad" required class="input" />
            <input [(ngModel)]="costo.precio_unitario" name="pu" type="number" placeholder="Precio unitario" required class="input" />
            <button type="submit" class="btn btn-primary">+ Item costo</button>
          </form>
        }
        <table class="data-table">
          <thead>
            <tr><th>Cód.</th><th>Descripción</th><th>Unidad</th><th>Cant.</th><th>P.U.</th><th>Subtotal</th></tr>
          </thead>
          <tbody>
            @for (i of edtp.items_costo; track i) {
              <tr>
                <td>{{ i.codigo }}</td><td>{{ i.descripcion }}</td><td>{{ i.unidad }}</td>
                <td>{{ i.cantidad }}</td><td>Bs {{ i.precio_unitario }}</td>
                <td><strong>Bs {{ i.subtotal }}</strong></td>
              </tr>
            }
          </tbody>
        </table>
        <div class="total"><strong>Total inversión: Bs {{ totalCosto }}</strong></div>
      </div>
    }
    
    @if (edtp && !cargando) {
      <div class="card">
        <h3>Financiamiento</h3>
        @if (puedeEditar) {
          <form (ngSubmit)="agregarFinanciamiento()" class="form-inline">
            <input [(ngModel)]="financiamiento.codigo_fuente" name="fc" placeholder="Código fuente" required class="input" />
            <input [(ngModel)]="financiamiento.nombre_fuente" name="fn" placeholder="Nombre fuente" required class="input" />
            <input [(ngModel)]="financiamiento.monto" name="fm" type="number" placeholder="Monto" required class="input" />
            <button type="submit" class="btn btn-primary">+ Fuente</button>
          </form>
        }
        <table class="data-table">
          <tbody>
            @for (f of edtp.fuentes_financiamiento; track f) {
              <tr>
                <td>{{ f.codigo_fuente }}</td><td>{{ f.nombre_fuente }}</td>
                <td><strong>Bs {{ f.monto }}</strong></td><td>{{ f.confirmada ? '✅' : '—' }}</td>
              </tr>
            }
          </tbody>
        </table>
        <div class="total"><strong>Total financiamiento: Bs {{ totalFinanciamiento }}</strong></div>
      </div>
    }
    
    @if (edtp && !cargando) {
      <div class="card">
        <div class="acciones">
          <button class="btn" (click)="validar()" [disabled]="!puedeValidar">✔ Validar aprobación</button>
          <button class="btn btn-primary" (click)="generar()" [disabled]="!puedeValidar">📄 Generar EDTP DOCX</button>
          <button class="btn" (click)="aprobar()" [disabled]="!puedeValidar">✅ Marcar EDTP aprobado</button>
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
    .form-inline { display: flex; gap: 0.5rem; margin-bottom: 1rem; flex-wrap: wrap; }
    .data-table { width: 100%; border-collapse: collapse; font-size: 0.8125rem; }
    .data-table th, 
    .badge { display: inline-block; padding: 0.125rem 0.5rem; border-radius: 4px; font-size: 0.6875rem; font-weight: 600; background: var(--mdc-blue-50); color: var(--mdc-blue-800); }
    .semafaro { display: flex; gap: 0.5rem; margin-bottom: 1rem; }
    .chip { display: inline-block; padding: 0.25rem 0.625rem; border-radius: 999px; font-size: 0.75rem; font-weight: 600; }
    .verde { background: var(--mdc-green-50); color: var(--mdc-green-800); }
    .gris { background: var(--mdc-grey-50); color: var(--text-secondary); }
    .total { margin-top: 0.75rem; font-size: 0.875rem; text-align: right; }
    .acciones { display: flex; gap: 0.5rem; flex-wrap: wrap; }
    .btn { display: inline-flex; align-items: center; padding: 0.5rem 0.875rem; border-radius: 6px; border: none; font-size: 0.8125rem; font-weight: 600; cursor: pointer; }
    .btn-primary { background: var(--primary); color: white; }
    .errores { margin-top: 1rem; padding: 0.75rem; background: var(--mdc-red-50); border-radius: 6px; font-size: 0.8125rem; color: var(--mdc-red-800); }
    .errores ul { margin: 0.25rem 0 0; padding-left: 1.25rem; }
    .loading { text-align: center; padding: 2rem; color: var(--text-secondary); }
    .alert { padding: 0.75rem 1rem; border-radius: 6px; margin-bottom: 1rem; }
    .alert-error { background: var(--mdc-red-50); color: var(--warn); }
    .alert-success { background: var(--mdc-green-50); color: var(--mdc-green-800); }
  `],
})
export class PreinversionEdtpComponent implements OnInit {
  proyectoId = '';
  edtp: EDTP | null = null;
  componentes: ComponenteProyecto[] = [];
  errores: string[] = [];
  cargando = true;
  error = '';
  mensaje = '';
  componente: Partial<ComponenteProyecto> = {};
  estudio: Partial<EstudioTecnico> = {};
  costo: Partial<ItemCostoEDTP> = {};
  financiamiento: Partial<FuenteFinanciamientoEDTP> = {};

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

  get seccionesAprobadas(): number {
    return this.edtp?.secciones.filter(s => s.estado === 'aprobado').length ?? 0;
  }

  get seccionesPendientes(): number {
    return this.edtp ? this.edtp.secciones.length - this.seccionesAprobadas : 0;
  }

  get totalCosto(): string {
    return this.edtp?.items_costo.reduce((s, i) => s + (Number(i.subtotal) || 0), 0).toFixed(2) ?? '0.00';
  }

  get totalFinanciamiento(): string {
    return this.edtp?.fuentes_financiamiento.reduce((s, f) => s + (Number(f.monto) || 0), 0).toFixed(2) ?? '0.00';
  }

  ngOnInit(): void {
    this.proyectoId = this.route.snapshot.paramMap.get('id')!;
    this.service.listarEdtps({ proyecto: this.proyectoId }).subscribe({
      next: (data) => {
        const edtp = data.results[0];
        if (!edtp) {
          this.error = 'Este proyecto no tiene EDTP. Inicialícelo desde el expediente.';
          this.cargando = false;
          return;
        }
        this.edtp = edtp;
        this.cargarComponentes();
      },
      error: () => { this.error = 'Error al cargar el EDTP'; this.cargando = false; },
    });
  }

  private cargarComponentes(): void {
    this.service.listarComponentes(this.proyectoId).subscribe({
      next: (componentes) => { this.componentes = componentes; this.cargando = false; },
      error: () => { this.cargando = false; },
    });
  }

  etiquetaEstado(estado: string): string {
    const mapa: Record<string, string> = {
      borrador: 'Borrador', en_revision: 'En revisión',
      observado: 'Observado', aprobado: 'Aprobado', rechazado: 'Rechazado',
    };
    return mapa[estado] ?? estado;
  }

  guardar(): void {
    if (!this.edtp) return;
    this.service.actualizarEdtp(this.edtp.id, {
      resumen_ejecutivo: this.edtp.resumen_ejecutivo,
      metodo_evaluacion: this.edtp.metodo_evaluacion,
      resultado_viabilidad: this.edtp.resultado_viabilidad,
      conclusiones: this.edtp.conclusiones,
      recomendaciones: this.edtp.recomendaciones,
    }).subscribe({
      next: () => { this.mensaje = 'EDTP guardado'; },
      error: () => this.error = 'Error al guardar el EDTP',
    });
  }

  guardarSeccion(s: SeccionEDTP): void {
    this.error = '';
    if (!s.aplicable && !s.justificacion_no_aplica) {
      this.error = 'Debe justificar la no aplicabilidad de la sección';
      return;
    }
    this.service.actualizarSeccion(s.id, {
      aplicable: s.aplicable,
      estado: s.estado,
      contenido: s.contenido,
      justificacion_no_aplica: s.justificacion_no_aplica,
      porcentaje_avance: s.estado === 'aprobado' ? 100 : s.porcentaje_avance,
    }).subscribe({
      next: () => { this.mensaje = 'Sección guardada'; },
      error: () => this.error = 'Error al guardar la sección',
    });
  }

  actualizarEstudio(e: EstudioTecnico): void {
    this.service.actualizarEstudioTecnico(e.id, { estado: e.estado }).subscribe({
      next: () => { this.mensaje = 'Estudio técnico actualizado'; },
      error: () => this.error = 'Error al actualizar el estudio técnico',
    });
  }

  agregarComponente(): void {
    if (!this.componente.codigo || !this.componente.nombre) return;
    this.service.crearComponente({
      proyecto: this.proyectoId, codigo: this.componente.codigo,
      nombre: this.componente.nombre,
      presupuesto: String(this.componente.presupuesto ?? '0'),
    }).subscribe({
      next: () => {
        this.componente = {};
        this.cargarComponentes();
      },
      error: () => this.error = 'Error al agregar el componente',
    });
  }

  agregarEstudio(): void {
    if (!this.edtp || !this.estudio.tipo_estudio || !this.estudio.titulo) return;
    this.service.crearEstudioTecnico({
      edtp: this.edtp.id, tipo_estudio: this.estudio.tipo_estudio,
      titulo: this.estudio.titulo,
    }).subscribe({
      next: () => {
        this.estudio = {};
        this.recargar();
      },
      error: () => this.error = 'Error al agregar el estudio técnico',
    });
  }

  agregarCosto(): void {
    if (!this.edtp || !this.costo.descripcion) return;
    this.service.crearItemCosto({
      edtp: this.edtp.id, categoria: 'infraestructura',
      codigo: this.costo.codigo ?? 'N/A', descripcion: this.costo.descripcion,
      unidad: this.costo.unidad ?? 'global',
      cantidad: String(this.costo.cantidad ?? '1'),
      precio_unitario: String(this.costo.precio_unitario ?? '0'),
    }).subscribe({
      next: () => {
        this.costo = {};
        this.recargar();
      },
      error: () => this.error = 'Error al agregar el item de costo',
    });
  }

  agregarFinanciamiento(): void {
    if (!this.edtp || !this.financiamiento.codigo_fuente) return;
    this.service.crearFinanciamiento({
      edtp: this.edtp.id, codigo_fuente: this.financiamiento.codigo_fuente,
      nombre_fuente: this.financiamiento.nombre_fuente ?? '',
      monto: String(this.financiamiento.monto ?? '0'),
    }).subscribe({
      next: () => {
        this.financiamiento = {};
        this.recargar();
      },
      error: () => this.error = 'Error al agregar la fuente de financiamiento',
    });
  }

  private recargar(): void {
    if (!this.edtp) return;
    this.service.obtenerEdtp(this.edtp.id).subscribe({
      next: (edtp) => { this.edtp = edtp; },
      error: () => undefined,
    });
  }

  validar(): void {
    this.errores = [];
    this.service.validarAprobacion(this.proyectoId, 'EDTP').subscribe({
      next: (r) => {
        this.errores = r.errores ?? [];
        if (!this.errores.length) this.mensaje = '✅ EDTP aprobable';
      },
      error: () => this.error = 'Error al validar el EDTP',
    });
  }

  generar(): void {
    this.service.generarDocumento(this.proyectoId, 'EDTP').subscribe({
      next: () => this.mensaje = 'EDTP encolado para generación DOCX',
      error: (e) => this.error = e?.error?.error ?? 'Error al generar el EDTP',
    });
  }

  aprobar(): void {
    if (!this.edtp) return;
    this.service.actualizarEdtp(this.edtp.id, { estado: 'aprobado' }).subscribe({
      next: () => {
        this.mensaje = 'EDTP aprobado';
        this.service.cambiarEstado(this.proyectoId, 'edtp_aprobado').subscribe({
          next: () => undefined,
          error: () => undefined,
        });
      },
      error: () => this.error = 'Error al aprobar el EDTP',
    });
  }
}

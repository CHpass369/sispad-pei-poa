import { Component, OnInit } from '@angular/core';
import { ActivatedRoute } from '@angular/router';
import { PermissionsService } from '../../core/services/permissions.service';
import {
  CondicionITCP, EDTP, ITCP, PreinversionService, ProyectoPreinversion,
  ResultadoAccion, SeccionEDTP, TDR, ValidacionResultado,
} from './preinversion.service';

@Component({
  standalone: false,
  selector: 'app-preinversion-wizard',
  template: `
    <div class="page-header">
      <a [routerLink]="['/sis-pro/preinversion', proyectoId]" class="volver">← Expediente</a>
      <h2>Wizard de Preinversión — {{ proyecto?.codigo_interno }}</h2>
      <p class="text-secondary">{{ proyecto?.nombre }}</p>
    </div>
    <div class="alert alert-error" *ngIf="error">{{ error }}</div>
    <div class="alert alert-success" *ngIf="mensaje">{{ mensaje }}</div>

    <!-- Barra de progreso -->
    <div class="stepper">
      <div class="step" *ngFor="let s of pasos; let i = index"
           [class.active]="pasoActual === i + 1"
           [class.completed]="pasoActual > i + 1"
           (click)="irAPaso(i + 1)">
        <div class="step-circle">{{ pasoActual > i + 1 ? '✓' : i + 1 }}</div>
        <div class="step-label">{{ s }}</div>
      </div>
    </div>

    <div class="card">
      <!-- ======= PASO 1: Ficha del proyecto ======= -->
      <div *ngIf="pasoActual === 1">
        <h3 class="step-title">Paso 1: Ficha del proyecto</h3>
        <div class="form-grid">
          <div class="field-full">
            <label>Nombre oficial</label>
            <input [(ngModel)]="ficha.nombre" name="nombre" class="form-control" (change)="guardarFicha()" />
          </div>
          <div class="field">
            <label>Problema / necesidad</label>
            <textarea [(ngModel)]="ficha.problema" name="problema" rows="3" class="form-control" (change)="guardarFicha()"></textarea>
          </div>
          <div class="field">
            <label>Objetivo general</label>
            <textarea [(ngModel)]="ficha.objetivo_general" name="obj" rows="3" class="form-control" (change)="guardarFicha()"></textarea>
          </div>
          <div class="field">
            <label>Distrito</label>
            <input [(ngModel)]="ficha.distrito" name="distrito" class="form-control" (change)="guardarFicha()" />
          </div>
          <div class="field">
            <label>Comunidad / OTB</label>
            <input [(ngModel)]="ficha.comunidad" name="comunidad" class="form-control" (change)="guardarFicha()" />
          </div>
          <div class="field">
            <label>Localización</label>
            <input [(ngModel)]="ficha.descripcion_localizacion" name="loc" class="form-control" (change)="guardarFicha()" />
          </div>
          <div class="field">
            <label>Presupuesto estimado (Bs)</label>
            <input type="number" [(ngModel)]="ficha.presupuesto_estimado" name="pe" class="form-control" (change)="guardarFicha()" />
          </div>
          <div class="field">
            <label>Presupuesto aprobado (Bs)</label>
            <input type="number" [(ngModel)]="ficha.presupuesto_aprobado" name="pa" class="form-control" (change)="guardarFicha()" />
          </div>
          <div class="field">
            <label>Tipología RM 115</label>
            <div class="tipologia-row">
              <span class="badge" *ngIf="proyecto?.tipologia_rm115">{{ service.tipologiaNombre(proyecto!.tipologia_rm115) }}</span>
              <button class="btn btn-sm" (click)="clasificar()" [disabled]="!puedeEditar">🤖 Clasificar</button>
            </div>
          </div>
        </div>
      </div>

      <!-- ======= PASO 2: Condiciones previas (ITCP) ======= -->
      <div *ngIf="pasoActual === 2">
        <h3 class="step-title">Paso 2: Condiciones previas (ITCP)</h3>
        <p class="text-secondary">Marque el estado de cada condición; las críticas bloquean la aprobación.</p>
        <div class="semafaro">
          <span class="chip verde">{{ condicionesResueltas }} resueltas</span>
          <span class="chip rojo">{{ condicionesPendientes }} pendientes</span>
        </div>
        <div class="condiciones">
          <div class="condicion" *ngFor="let c of condiciones" [class.recuadro-critica]="c.critica && c.estado !== 'cumple'">
            <div class="condicion-cab">
              <span class="badge">{{ service.condicionCategoria(c.categoria) }}</span>
              <span class="critica" *ngIf="c.critica" title="Condición crítica">🔴</span>
            </div>
            <div class="condicion-titulo">{{ c.titulo }}</div>
            <div class="condicion-fila">
              <select [(ngModel)]="c.estado" name="est{{ c.id }}" class="form-control" (change)="guardarCondicion(c)">
                <option *ngFor="let e of service.estadosCondicion" [value]="e">{{ etiquetaCondicion(e) }}</option>
              </select>
            </div>
            <textarea *ngIf="c.estado !== 'cumple' && c.estado !== 'aprobada'" [(ngModel)]="c.hallazgo" name="h{{ c.id }}" rows="2" class="form-control" placeholder="Hallazgo / evidencia" (change)="guardarCondicion(c)"></textarea>
            <textarea *ngIf="c.estado === 'no_aplica'" [(ngModel)]="c.justificacion_no_aplica" name="j{{ c.id }}" rows="2" class="form-control" placeholder="Justificación de no aplica" (change)="guardarCondicion(c)"></textarea>
          </div>
        </div>
      </div>

      <!-- ======= PASO 3: ITCP ======= -->
      <div *ngIf="pasoActual === 3">
        <h3 class="step-title">Paso 3: Contenido del ITCP</h3>
        <div class="form-grid">
          <div class="field-full">
            <label>Justificación de la iniciativa (principios, planificación, competencias, priorización)</label>
            <textarea [(ngModel)]="itcp.justificacion_iniciativa" name="ji" rows="4" class="form-control" (change)="guardarItcp()"></textarea>
          </div>
          <div class="field-full">
            <label>Idea del proyecto (necesidad, objetivos, beneficios, alternativas, localización)</label>
            <textarea [(ngModel)]="itcp.idea_proyecto" name="idea" rows="4" class="form-control" (change)="guardarItcp()"></textarea>
          </div>
          <div class="field">
            <label>Resultado preliminar</label>
            <select [(ngModel)]="itcp.resultado_preliminar" name="rp" class="form-control" (change)="guardarItcp()">
              <option value="">— Seleccionar —</option>
              <option value="viable_edtp">Viable para elaborar EDTP</option>
              <option value="viable_condiciones">Viable con condiciones</option>
              <option value="no_viable">No viable</option>
              <option value="informacion_insuficiente">Información insuficiente</option>
            </select>
          </div>
          <div class="field-full">
            <label>Conclusiones</label>
            <textarea [(ngModel)]="itcp.conclusiones" name="concl" rows="3" class="form-control" (change)="guardarItcp()"></textarea>
          </div>
          <div class="field-full">
            <label>Recomendaciones</label>
            <textarea [(ngModel)]="itcp.recomendaciones" name="recom" rows="3" class="form-control" (change)="guardarItcp()"></textarea>
          </div>
        </div>
        <div class="acciones">
          <button class="btn" (click)="validar('ITCP')" [disabled]="!puedeValidar">✔ Validar ITCP</button>
          <div *ngIf="erroresItcp.length" class="errores">
            <ul><li *ngFor="let e of erroresItcp">{{ e }}</li></ul>
          </div>
        </div>
      </div>

      <!-- ======= PASO 4: TDR ======= -->
      <div *ngIf="pasoActual === 4">
        <h3 class="step-title">Paso 4: TDR y presupuesto referencial del EDTP</h3>
        <div class="form-grid">
          <div class="field-full">
            <label>Objetivos del estudio</label>
            <textarea [(ngModel)]="tdr.objetivos" name="to" rows="3" class="form-control" (change)="guardarTdr()"></textarea>
          </div>
          <div class="field-full">
            <label>Alcance</label>
            <textarea [(ngModel)]="tdr.alcance" name="ta" rows="3" class="form-control" (change)="guardarTdr()"></textarea>
          </div>
          <div class="field-full">
            <label>Metodología</label>
            <textarea [(ngModel)]="tdr.metodologia" name="tm" rows="3" class="form-control" (change)="guardarTdr()"></textarea>
          </div>
          <div class="field">
            <label>Duración (días)</label>
            <input type="number" [(ngModel)]="tdr.duracion_dias" name="td" class="form-control" (change)="guardarTdr()" />
          </div>
          <div class="field">
            <label>Presupuesto referencial (Bs)</label>
            <input type="number" [(ngModel)]="tdr.presupuesto_referencial" name="tpr" class="form-control" (change)="guardarTdr()" />
          </div>
        </div>
        <div class="sub-block">
          <h4>Actividades del estudio</h4>
          <div class="fila-form">
            <input [(ngModel)]="actividad.codigo" name="ac" placeholder="Código" class="form-control" />
            <input [(ngModel)]="actividad.descripcion" name="ad" placeholder="Descripción" class="form-control" />
            <input [(ngModel)]="actividad.duracion_dias" name="add" type="number" placeholder="Días" class="form-control" />
            <button class="btn btn-primary" (click)="agregarActividad()" [disabled]="!puedeEditar">+</button>
          </div>
          <ul class="mini-lista">
            <li *ngFor="let a of tdr.actividades"><span class="badge">{{ a.codigo }}</span> {{ a.descripcion }} ({{ a.duracion_dias }} días)</li>
          </ul>
        </div>
        <div class="sub-block">
          <h4>Presupuesto referencial (memoria de cálculo)</h4>
          <div class="fila-form">
            <input [(ngModel)]="item.categoria" name="ic" placeholder="Categoría" class="form-control" />
            <input [(ngModel)]="item.descripcion" name="id" placeholder="Descripción" class="form-control" />
            <input [(ngModel)]="item.cantidad" name="iq" type="number" placeholder="Cantidad" class="form-control" />
            <input [(ngModel)]="item.costo_unitario" name="icu" type="number" placeholder="Costo unitario" class="form-control" />
            <button class="btn btn-primary" (click)="agregarItem()" [disabled]="!puedeEditar">+</button>
          </div>
          <ul class="mini-lista">
            <li *ngFor="let i of tdr.items_presupuesto"><span class="badge">{{ i.categoria }}</span> {{ i.descripcion }} — Bs {{ i.subtotal }}</li>
          </ul>
          <div class="total"><strong>Total referencial: Bs {{ totalReferencial }}</strong></div>
        </div>
      </div>

      <!-- ======= PASO 5: EDTP ======= -->
      <div *ngIf="pasoActual === 5">
        <h3 class="step-title">Paso 5: Contenido del EDTP</h3>
        <div class="form-grid">
          <div class="field-full">
            <label>Resumen ejecutivo</label>
            <textarea [(ngModel)]="edtp.resumen_ejecutivo" name="re" rows="3" class="form-control" (change)="guardarEdtp()"></textarea>
          </div>
          <div class="field">
            <label>Método de evaluación</label>
            <select [(ngModel)]="edtp.metodo_evaluacion" name="me" class="form-control" (change)="guardarEdtp()">
              <option value="">— Seleccionar —</option>
              <option value="costo_beneficio">Costo / Beneficio</option>
              <option value="costo_efectividad">Costo / Efectividad</option>
              <option value="multicriterio">Multicriterio</option>
            </select>
          </div>
          <div class="field">
            <label>Resultado de viabilidad</label>
            <select [(ngModel)]="edtp.resultado_viabilidad" name="rv" class="form-control" (change)="guardarEdtp()">
              <option value="">— Seleccionar —</option>
              <option value="viable">Viable</option>
              <option value="viable_condiciones">Viable con condiciones</option>
              <option value="no_viable">No viable</option>
              <option value="suspendido">Suspendido</option>
            </select>
          </div>
          <div class="field-full">
            <label>Conclusiones</label>
            <textarea [(ngModel)]="edtp.conclusiones" name="ec" rows="3" class="form-control" (change)="guardarEdtp()"></textarea>
          </div>
          <div class="field-full">
            <label>Recomendaciones</label>
            <textarea [(ngModel)]="edtp.recomendaciones" name="er" rows="3" class="form-control" (change)="guardarEdtp()"></textarea>
          </div>
        </div>
        <div class="acciones">
          <button class="btn" (click)="validar('EDTP')" [disabled]="!puedeValidar">✔ Validar EDTP</button>
          <div *ngIf="erroresEdtp.length" class="errores">
            <ul><li *ngFor="let e of erroresEdtp">{{ e }}</li></ul>
          </div>
        </div>
      </div>

      <!-- ======= PASO 6: Secciones EDTP ======= -->
      <div *ngIf="pasoActual === 6">
        <h3 class="step-title">Paso 6: Secciones del EDTP por tipología</h3>
        <p class="text-secondary">Complete el contenido y el estado de cada sección obligatoria.</p>
        <div class="semafaro">
          <span class="chip verde">{{ seccionesAprobadas }} aprobadas</span>
          <span class="chip gris">{{ seccionesPendientes }} pendientes</span>
        </div>
        <div class="secciones">
          <div class="seccion" *ngFor="let s of edtp.secciones">
            <div class="seccion-cab">
              <span class="badge">{{ s.codigo }}</span>
              <strong>{{ s.titulo }}</strong>
              <span class="chip" [class.verde]="s.estado === 'aprobado'" [class.gris]="s.estado !== 'aprobado'">{{ s.porcentaje_avance }}%</span>
            </div>
            <div class="seccion-fila">
              <select [(ngModel)]="s.estado" name="es{{ s.id }}" class="form-control" (change)="guardarSeccion(s)">
                <option *ngFor="let e of service.estadosDocumento" [value]="e">{{ etiquetaDocumento(e) }}</option>
              </select>
              <select [(ngModel)]="s.aplicable" name="ea{{ s.id }}" class="form-control" (change)="guardarSeccion(s)">
                <option [ngValue]="true">Aplica</option>
                <option [ngValue]="false">No aplica</option>
              </select>
            </div>
            <textarea [(ngModel)]="s.contenido" name="sc{{ s.id }}" rows="2" class="form-control" placeholder="Contenido de la sección" (change)="guardarSeccion(s)"></textarea>
            <input *ngIf="!s.aplicable" [(ngModel)]="s.justificacion_no_aplica" name="sj{{ s.id }}" class="form-control" placeholder="Justificación de no aplica" (change)="guardarSeccion(s)" />
          </div>
        </div>
      </div>

      <!-- ======= PASO 7: Generación de documentos ======= -->
      <div *ngIf="pasoActual === 7">
        <h3 class="step-title">Paso 7: Generar documentos del expediente</h3>
        <p class="text-secondary">Valide primero y genere el documento desde el expediente estructurado.</p>
        <div class="documentos">
          <div class="doc-card">
            <h4>📄 ITCP — Informe Técnico de Condiciones Previas</h4>
            <p>Condiciones: {{ condicionesResueltas }}/{{ condiciones.length }} · Conclusiones: {{ itcp.conclusiones ? '✔' : '✘' }}</p>
            <button class="btn btn-primary" (click)="generar('ITCP')" [disabled]="!puedeValidar">Generar ITCP DOCX</button>
          </div>
          <div class="doc-card">
            <h4>📄 EDTP — Estudio de Diseño Técnico de Preinversión</h4>
            <p>Secciones aprobadas: {{ seccionesAprobadas }}/{{ edtp.secciones.length }} · Presupuesto referencial: Bs {{ tdr.presupuesto_referencial || '—' }}</p>
            <button class="btn btn-primary" (click)="generar('EDTP')" [disabled]="!puedeValidar">Generar EDTP DOCX</button>
          </div>
        </div>
        <div *ngIf="generados.length" class="historial">
          <h4>Historial de documentos generados</h4>
          <table class="data-table">
            <thead>
              <tr><th>Tipo</th><th>Estado</th><th>Fecha</th><th>Descargar</th></tr>
            </thead>
            <tbody>
              <tr *ngFor="let g of generados">
                <td>{{ g.tipo_documento }}</td>
                <td><span class="badge" [class.verde]="g.estado === 'completado'" [class.rojo]="g.estado === 'fallido'">{{ g.estado }}</span></td>
                <td>{{ g.created_at | date: 'short' }}</td>
                <td>
                  <a *ngIf="g.archivo_docx" class="btn btn-sm" [href]="service.urlArchivo(g.archivo_docx)" target="_blank">DOCX</a>
                  <a *ngIf="g.archivo_pdf" class="btn btn-sm" [href]="service.urlArchivo(g.archivo_pdf)" target="_blank">PDF</a>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>

    <!-- Navegación -->
    <div class="wizard-nav">
      <button class="btn" (click)="irAPaso(pasoActual - 1)" [disabled]="pasoActual === 1">← Anterior</button>
      <span class="nav-info">Paso {{ pasoActual }} de {{ pasos.length }}</span>
      <button class="btn btn-primary" (click)="irAPaso(pasoActual + 1)" [disabled]="pasoActual === pasos.length">Siguiente →</button>
    </div>
  `,
  styles: [`
    .page-header { margin-bottom: 1.5rem; }
    .volver { display: inline-block; font-size: 0.8125rem; color: var(--text-secondary); text-decoration: none; margin-bottom: 0.25rem; }
    .text-secondary { color: var(--text-secondary); font-size: 0.875rem; }
    .stepper { display: flex; gap: 0.25rem; margin-bottom: 1.5rem; overflow-x: auto; padding: 0.5rem 0; }
    .step { display: flex; flex-direction: column; align-items: center; gap: 0.25rem; padding: 0.375rem 0.75rem; cursor: pointer; min-width: 80px; border-radius: 8px; }
    .step:hover { background: #F5F5F5; }
    .step-circle { width: 1.75rem; height: 1.75rem; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 0.8125rem; font-weight: 700; background: #E0E0E0; color: var(--text-secondary); }
    .step.active .step-circle { background: var(--primary); color: white; }
    .step.completed .step-circle { background: #2E7D32; color: white; }
    .step-label { font-size: 0.6875rem; color: var(--text-secondary); text-align: center; white-space: nowrap; }
    .card { background: var(--surface); border: 1px solid var(--border); border-radius: 8px; padding: 1.5rem; margin-bottom: 1rem; }
    .step-title { margin-top: 0; font-size: 1.125rem; }
    .form-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 1rem; }
    .field, .field-full { display: flex; flex-direction: column; gap: 0.25rem; }
    .field-full { grid-column: 1 / -1; }
    .field label, .field-full label { font-size: 0.75rem; color: var(--text-secondary); }
    .form-control { padding: 0.5rem; border: 1px solid var(--border); border-radius: 6px; font-size: 0.875rem; font-family: inherit; }
    .tipologia-row { display: flex; align-items: center; gap: 0.5rem; }
    .semafaro { display: flex; gap: 0.5rem; margin-bottom: 1rem; flex-wrap: wrap; }
    .chip { display: inline-block; padding: 0.25rem 0.625rem; border-radius: 999px; font-size: 0.75rem; font-weight: 600; }
    .verde { background: #E8F5E9; color: #2E7D32; }
    .rojo { background: #FFEBEE; color: #C62828; }
    .gris { background: #F5F5F5; color: var(--text-secondary); }
    .badge { display: inline-block; padding: 0.125rem 0.5rem; border-radius: 4px; font-size: 0.6875rem; font-weight: 600; background: #E3F2FD; color: #1565C0; }
    .condiciones, .secciones { display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 0.75rem; }
    .condicion, .seccion { border: 1px solid var(--border); border-radius: 8px; padding: 0.75rem; display: flex; flex-direction: column; gap: 0.5rem; }
    .recuadro-critica { border-color: #EF9A9A; background: #FFF8F8; }
    .condicion-cab, .seccion-cab { display: flex; align-items: center; gap: 0.375rem; }
    .condicion-titulo { font-size: 0.8125rem; font-weight: 600; }
    .condicion-fila, .seccion-fila { display: flex; gap: 0.5rem; }
    .critica { font-size: 0.875rem; }
    .sub-block { margin-top: 1.25rem; border-top: 1px solid var(--border); padding-top: 1rem; }
    .sub-block h4 { margin: 0 0 0.5rem; font-size: 0.9375rem; }
    .fila-form { display: flex; gap: 0.5rem; margin-bottom: 0.5rem; flex-wrap: wrap; }
    .mini-lista { list-style: none; margin: 0 0 0.5rem; padding: 0; font-size: 0.8125rem; }
    .mini-lista li { padding: 0.25rem 0; border-bottom: 1px solid var(--border); }
    .total { text-align: right; font-size: 0.875rem; }
    .acciones { margin-top: 1rem; display: flex; flex-direction: column; gap: 0.5rem; align-items: flex-start; }
    .errores { padding: 0.75rem; background: #FFEBEE; border-radius: 6px; font-size: 0.8125rem; color: #C62828; }
    .errores ul { margin: 0.25rem 0 0; padding-left: 1.25rem; }
    .documentos { display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 1rem; }
    .doc-card { border: 1px solid var(--border); border-radius: 8px; padding: 1rem; display: flex; flex-direction: column; gap: 0.5rem; }
    .doc-card h4 { margin: 0; }
    .doc-card p { margin: 0; font-size: 0.8125rem; color: var(--text-secondary); }
    .historial { margin-top: 1.5rem; }
    .historial h4 { font-size: 0.9375rem; }
    .data-table { width: 100%; border-collapse: collapse; font-size: 0.8125rem; }
    .data-table th, .data-table td { padding: 0.5rem 0.625rem; text-align: left; border-bottom: 1px solid var(--border); }
    .wizard-nav { display: flex; justify-content: space-between; align-items: center; }
    .nav-info { font-size: 0.8125rem; color: var(--text-secondary); }
    .btn { display: inline-flex; align-items: center; padding: 0.5rem 0.875rem; border-radius: 6px; border: none; font-size: 0.8125rem; font-weight: 600; cursor: pointer; text-decoration: none; }
    .btn-primary { background: var(--primary); color: white; }
    .btn-sm { background: #E3F2FD; color: #1565C0; padding: 0.375rem 0.625rem; }
    .alert { padding: 0.75rem 1rem; border-radius: 6px; margin-bottom: 1rem; }
    .alert-error { background: #FFEBEE; color: var(--warn); }
    .alert-success { background: #E8F5E9; color: #2E7D32; }
    @media (max-width: 640px) { .stepper { gap: 0; } .step { min-width: 60px; padding: 0.25rem 0.375rem; } }
  `],
})
export class PreinversionWizardComponent implements OnInit {
  pasos = [
    'Ficha del proyecto', 'Condiciones previas', 'ITCP', 'TDR',
    'EDTP', 'Secciones EDTP', 'Generar documentos',
  ];
  pasoActual = 1;
  proyectoId = '';
  proyecto: ProyectoPreinversion | null = null;
  ficha: Partial<ProyectoPreinversion> = {};
  itcp: ITCP | null = null;
  condiciones: CondicionITCP[] = [];
  tdr: TDR | null = null;
  edtp: EDTP | null = null;
  erroresItcp: string[] = [];
  erroresEdtp: string[] = [];
  generados: import('./preinversion.service').DocumentoGenerado[] = [];
  actividad: { codigo: string; descripcion: string; duracion_dias: number } = { codigo: '', descripcion: '', duracion_dias: 0 };
  item: { categoria: string; descripcion: string; cantidad: string; costo_unitario: string } = { categoria: '', descripcion: '', cantidad: '1', costo_unitario: '0' };
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

  get condicionesResueltas(): number {
    return this.condiciones.filter(c => ['cumple', 'aprobada', 'no_aplica'].includes(c.estado)).length;
  }

  get condicionesPendientes(): number {
    return this.condiciones.length - this.condicionesResueltas;
  }

  get seccionesAprobadas(): number {
    return this.edtp?.secciones.filter(s => s.estado === 'aprobado').length ?? 0;
  }

  get seccionesPendientes(): number {
    return this.edtp ? this.edtp.secciones.length - this.seccionesAprobadas : 0;
  }

  get totalReferencial(): string {
    return this.tdr?.items_presupuesto.reduce((s, i) => s + (Number(i.subtotal) || 0), 0).toFixed(2) ?? '0.00';
  }

  ngOnInit(): void {
    this.proyectoId = this.route.snapshot.paramMap.get('id')!;
    this.service.obtenerProyecto(this.proyectoId).subscribe({
      next: (proyecto) => {
        this.proyecto = proyecto;
        this.ficha = {
          nombre: proyecto.nombre,
          problema: proyecto.problema,
          objetivo_general: proyecto.objetivo_general,
          distrito: proyecto.distrito,
          comunidad: proyecto.comunidad,
          descripcion_localizacion: proyecto.descripcion_localizacion,
          presupuesto_estimado: proyecto.presupuesto_estimado,
          presupuesto_aprobado: proyecto.presupuesto_aprobado,
        };
        this.cargarExpediente();
      },
      error: () => this.error = 'Error al cargar el proyecto',
    });
  }

  private cargarExpediente(): void {
    this.service.listarItcps({ proyecto: this.proyectoId }).subscribe({
      next: (data) => {
        this.itcp = data.results[0] ?? null;
        if (this.itcp) this.cargarCondiciones(this.itcp.id);
      },
      error: () => undefined,
    });
    this.service.listarTdrs({ proyecto: this.proyectoId }).subscribe({
      next: (data) => { this.tdr = data.results[0] ?? null; },
      error: () => undefined,
    });
    this.service.listarEdtps({ proyecto: this.proyectoId }).subscribe({
      next: (data) => { this.edtp = data.results[0] ?? null; },
      error: () => undefined,
    });
    this.service.listarDocumentosGenerados({ proyecto: this.proyectoId }).subscribe({
      next: (data) => { this.generados = data.results; },
      error: () => undefined,
    });
  }

  private cargarCondiciones(itcpId: string): void {
    this.service.listarCondiciones({ itcp: itcpId }).subscribe({
      next: (c) => { this.condiciones = c; },
      error: () => undefined,
    });
  }

  irAPaso(nuevo: number): void {
    if (nuevo < 1 || nuevo > this.pasos.length) return;
    if (nuevo > this.pasoActual) this.guardarPasoActual();
    this.pasoActual = nuevo;
    this.error = '';
  }

  private guardarPasoActual(): void {
    switch (this.pasoActual) {
      case 1: this.guardarFicha(); break;
      case 2: break; // las condiciones se guardan al cambiar
      case 3: this.guardarItcp(); break;
      case 4: this.guardarTdr(); break;
      case 5: this.guardarEdtp(); break;
      case 6: break; // las secciones se guardan al cambiar
    }
  }

  guardarFicha(): void {
    if (!this.ficha.nombre?.trim()) return;
    this.service.actualizarProyecto(this.proyectoId, this.ficha).subscribe({
      next: () => { this.mensaje = 'Ficha guardada'; },
      error: () => this.error = 'Error al guardar la ficha',
    });
  }

  clasificar(): void {
    this.service.clasificar(this.proyectoId).subscribe({
      next: (r) => {
        this.mensaje = `Tipología sugerida: ${this.service.tipologiaNombre(r.tipologia_sugerida ?? '')}`;
        if (this.proyecto) {
          this.proyecto.tipologia_rm115 = r.tipologia_sugerida ?? '';
        }
      },
      error: () => this.error = 'Error al clasificar',
    });
  }

  guardarCondicion(c: CondicionITCP): void {
    this.error = '';
    if (c.estado === 'no_aplica' && !c.justificacion_no_aplica) {
      this.error = 'Debe justificar por qué la condición no aplica';
      return;
    }
    this.service.actualizarCondicion(c.id, {
      estado: c.estado, hallazgo: c.hallazgo,
      plan_accion: c.plan_accion, justificacion_no_aplica: c.justificacion_no_aplica,
    }).subscribe({
      next: () => { this.mensaje = 'Condición guardada'; },
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

  guardarTdr(): void {
    if (!this.tdr) return;
    this.service.actualizarTdr(this.tdr.id, {
      objetivos: this.tdr.objetivos, alcance: this.tdr.alcance,
      metodologia: this.tdr.metodologia, duracion_dias: this.tdr.duracion_dias,
      presupuesto_referencial: this.tdr.presupuesto_referencial,
    }).subscribe({
      next: () => { this.mensaje = 'TDR guardado'; },
      error: () => this.error = 'Error al guardar el TDR',
    });
  }

  guardarEdtp(): void {
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
      this.error = 'Debe justificar la no aplicabilidad';
      return;
    }
    this.service.actualizarSeccion(s.id, {
      estado: s.estado, aplicable: s.aplicable,
      contenido: s.contenido, justificacion_no_aplica: s.justificacion_no_aplica,
      porcentaje_avance: s.estado === 'aprobado' ? 100 : s.porcentaje_avance,
    }).subscribe({
      next: () => { this.mensaje = 'Sección guardada'; },
      error: () => this.error = 'Error al guardar la sección',
    });
  }

  agregarActividad(): void {
    if (!this.tdr || !this.actividad.codigo || !this.actividad.descripcion) return;
    this.service.crearActividadTdr({
      tdr: this.tdr.id, codigo: this.actividad.codigo,
      descripcion: this.actividad.descripcion, duracion_dias: this.actividad.duracion_dias,
    }).subscribe({
      next: () => {
        this.actividad = { codigo: '', descripcion: '', duracion_dias: 0 };
        this.recargarTdr();
      },
      error: () => this.error = 'Error al agregar la actividad',
    });
  }

  agregarItem(): void {
    if (!this.tdr || !this.item.descripcion) return;
    this.service.crearItemPresupuestoTdr({
      tdr: this.tdr.id, categoria: this.item.categoria || 'general',
      descripcion: this.item.descripcion, cantidad: this.item.cantidad,
      costo_unitario: this.item.costo_unitario,
    }).subscribe({
      next: () => {
        this.item = { categoria: '', descripcion: '', cantidad: '1', costo_unitario: '0' };
        this.recargarTdr();
      },
      error: () => this.error = 'Error al agregar el item',
    });
  }

  private recargarTdr(): void {
    if (!this.tdr) return;
    this.service.obtenerTdr(this.tdr.id).subscribe({
      next: (tdr) => { this.tdr = tdr; },
      error: () => undefined,
    });
  }

  validar(tipo: 'ITCP' | 'EDTP'): void {
    if (tipo === 'ITCP') this.erroresItcp = [];
    else this.erroresEdtp = [];
    this.service.validarAprobacion(this.proyectoId, tipo).subscribe({
      next: (r: ValidacionResultado) => {
        if (tipo === 'ITCP') this.erroresItcp = r.errores ?? [];
        else this.erroresEdtp = r.errores ?? [];
        if (!r.errores?.length) this.mensaje = `✅ ${tipo} aprobable`;
      },
      error: () => this.error = `Error al validar ${tipo}`,
    });
  }

  generar(tipo: 'ITCP' | 'EDTP'): void {
    this.service.generarDocumento(this.proyectoId, tipo).subscribe({
      next: () => {
        this.mensaje = `${tipo} encolado para generación DOCX`;
        this.service.listarDocumentosGenerados({ proyecto: this.proyectoId }).subscribe({
          next: (data) => { this.generados = data.results; },
          error: () => undefined,
        });
      },
      error: (e) => this.error = e?.error?.error ?? `Error al generar ${tipo}`,
    });
  }

  etiquetaCondicion(estado: string): string {
    const mapa: Record<string, string> = {
      pendiente: 'Pendiente', en_elaboracion: 'En elaboración',
      observada: 'Observada', subsanada: 'Subsanada',
      cumple: 'Cumple', no_aplica: 'No aplica', aprobada: 'Aprobada',
    };
    return mapa[estado] ?? estado;
  }

  etiquetaDocumento(estado: string): string {
    const mapa: Record<string, string> = {
      borrador: 'Borrador', en_revision: 'En revisión',
      observado: 'Observado', aprobado: 'Aprobado', rechazado: 'Rechazado',
    };
    return mapa[estado] ?? estado;
  }
}

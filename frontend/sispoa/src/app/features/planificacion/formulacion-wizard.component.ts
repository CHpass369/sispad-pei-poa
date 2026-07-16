import { Component, OnInit, OnDestroy } from '@angular/core';
import { FormBuilder, FormArray, Validators } from '@angular/forms';
import { ActivatedRoute, Router } from '@angular/router';
import { ApiService } from '../../core/services/api.service';

@Component({
  standalone: false,
  selector: 'app-formulacion-wizard',
  template: `
    <div class="wizard">
      <div class="wizard-header">
        <h2>Formulación POA {{ gestion }}</h2>
        <p class="text-secondary" *ngIf="unidad">{{ unidad.nombre }}</p>
      </div>

      <!-- Progress Steps -->
      <div class="steps-bar">
        <div *ngFor="let step of steps; let i = index"
             class="step" [class.active]="i === currentStep"
             [class.completed]="i < currentStep"
             (click)="goToStep(i)">
          <div class="step-circle">{{ i < currentStep ? '✓' : i + 1 }}</div>
          <div class="step-label">{{ step }}</div>
        </div>
      </div>

      <!-- Step Content -->
      <div class="step-content card">
        <!-- Paso 1: Articulación estratégica -->
        <div *ngIf="currentStep === 0">
          <h3>Articulación Estratégica</h3>
          <p class="text-secondary">Vincule la acción de corto plazo con el PEI y planes superiores</p>
          <form [formGroup]="form.controls.articulacion">
            <div class="field">
              <label>Plan / PEI</label>
              <select formControlName="pei" class="form-control">
                <option value="">Seleccione...</option>
                <option *ngFor="let p of planes" [value]="p.id">{{ p.nombre }}</option>
              </select>
            </div>
            <div class="field">
              <label>Acción de mediano plazo</label>
              <select formControlName="accion_mediano" class="form-control">
                <option value="">Seleccione...</option>
                <option *ngFor="let amp of accionesMediano" [value]="amp.id">{{ amp.codigo }} - {{ amp.nombre }}</option>
              </select>
            </div>
            <div class="field">
              <label>Programa presupuestario</label>
              <select formControlName="programa" class="form-control">
                <option value="">Seleccione...</option>
                <option *ngFor="let p of programas" [value]="p.id">{{ p.codigo }} - {{ p.nombre }}</option>
              </select>
            </div>
          </form>
        </div>

        <!-- Paso 2: Acción de corto plazo -->
        <div *ngIf="currentStep === 1">
          <h3>Acción de Corto Plazo</h3>
          <form [formGroup]="form.controls.accion">
            <div class="field">
              <label>Código</label>
              <input formControlName="codigo" class="form-control" placeholder="ACP-001">
            </div>
            <div class="field">
              <label>Nombre de la acción</label>
              <input formControlName="nombre" class="form-control"
                     placeholder="Ej: Mantenimiento de vías urbanas">
            </div>
            <div class="field">
              <label>Justificación / Problema atendido</label>
              <textarea formControlName="justificacion" class="form-control" rows="3"
                        placeholder="Describa el problema o necesidad que atiende esta acción"></textarea>
            </div>
            <div class="row">
              <div class="field half">
                <label>Fecha inicio</label>
                <input formControlName="fecha_inicio" type="date" class="form-control">
              </div>
              <div class="field half">
                <label>Fecha fin</label>
                <input formControlName="fecha_fin" type="date" class="form-control">
              </div>
            </div>
          </form>
        </div>

        <!-- Paso 3: Productos e indicadores -->
        <div *ngIf="currentStep === 2">
          <h3>Productos e Indicadores</h3>
          <form [formGroup]="form.controls.producto">
            <div class="field">
              <label>Tipo de producto</label>
              <select formControlName="tipo" class="form-control">
                <option value="terminal">Terminal</option>
                <option value="intermedio">Intermedio</option>
              </select>
            </div>
            <div class="field">
              <label>Producto esperado (bien, servicio o norma)</label>
              <input formControlName="nombre" class="form-control" placeholder="Ej: 5 km de vía asfaltada">
            </div>
            <h4 style="margin: 1.5rem 0 0.75rem;">Indicador</h4>
            <div class="field">
              <label>Nombre del indicador</label>
              <input formControlName="indicador_nombre" class="form-control">
            </div>
            <div class="field">
              <label>Fórmula</label>
              <input formControlName="indicador_formula" class="form-control" placeholder="Ej: (km ejecutados / km programados) * 100">
            </div>
            <div class="row">
              <div class="field third">
                <label>Línea base</label>
                <input formControlName="linea_base" type="number" class="form-control">
              </div>
              <div class="field third">
                <label>Meta anual</label>
                <input formControlName="meta_anual" type="number" class="form-control">
              </div>
              <div class="field third">
                <label>Unidad medida</label>
                <select formControlName="unidad_medida" class="form-control">
                  <option *ngFor="let u of unidadesMedida" [value]="u.id">{{ u.codigo }} - {{ u.denominacion }}</option>
                </select>
              </div>
            </div>
            <h4 style="margin: 1.5rem 0 0.75rem;">Programación trimestral</h4>
            <div class="row">
              <div class="field fourth" *ngFor="let t of [1,2,3,4]">
                <label>Trimestre {{ t }}</label>
                <input [formControlName]="'trimestre' + t" type="number" class="form-control">
              </div>
            </div>
          </form>
        </div>

        <!-- Paso 4: Operaciones y requerimientos -->
        <div *ngIf="currentStep === 3">
          <h3>Operaciones y Requerimientos</h3>
          <form [formGroup]="operacionesFormGroup">
            <div class="operations-list">
              <div *ngFor="let op of operacionesForm.controls; let i = index" class="operation-item card">
                <div [formGroupName]="i">
                  <div class="row">
                    <div class="field half">
                      <label>Operación</label>
                      <input formControlName="nombre" class="form-control" placeholder="Ej: fiscalización de obra">
                    </div>
                    <div class="field quarter">
                      <label>Cantidad</label>
                      <input formControlName="cantidad" type="number" class="form-control">
                    </div>
                    <div class="field quarter">
                      <label>P. Unitario (Bs)</label>
                      <input formControlName="precio_unitario" type="number" class="form-control">
                    </div>
                  </div>
                  <div class="field">
                    <label>Objeto del gasto</label>
                    <select formControlName="objeto_gasto" class="form-control">
                      <option *ngFor="let og of objetosGasto" [value]="og.id">{{ og.codigo }} - {{ og.denominacion }}</option>
                    </select>
                  </div>
                  <div style="text-align: right; font-weight: 600; margin-top: 0.5rem;">
                    Subtotal: Bs {{ (op.value.cantidad || 0) * (op.value.precio_unitario || 0) | number }}
                  </div>
                </div>
                <button class="btn btn-outline btn-sm" (click)="eliminarOperacion(i)" *ngIf="operacionesForm.length > 1">
                  Eliminar
                </button>
              </div>
            </div>
            <button class="btn btn-outline" (click)="agregarOperacion()" style="margin-top: 1rem;">
              + Agregar operación
            </button>
          </form>
        </div>

        <!-- Paso 5: Resumen y envío -->
        <div *ngIf="currentStep === 4">
          <h3>Resumen y Envío</h3>
          <div class="summary-grid">
            <div class="summary-item">
              <strong>Acción:</strong> {{ form.value.accion?.nombre || '—' }}
            </div>
            <div class="summary-item">
              <strong>Producto:</strong> {{ form.value.producto?.nombre || '—' }}
            </div>
            <div class="summary-item">
              <strong>Indicador:</strong> {{ form.value.producto?.indicador_nombre || '—' }}
            </div>
            <div class="summary-item">
              <strong>Meta anual:</strong> {{ form.value.producto?.meta_anual || '—' }}
            </div>
            <div class="summary-item">
              <strong>Total operaciones:</strong> {{ totalOperaciones | number }} Bs
            </div>
          </div>

          <div class="field" style="margin-top: 1.5rem;">
            <label>Comentario (opcional)</label>
            <textarea [(ngModel)]="comentarioEnvio" class="form-control" rows="2"
                      placeholder="Notas para el revisor"></textarea>
          </div>

          <div *ngIf="mensajeError" class="alert alert-error">{{ mensajeError }}</div>
          <div *ngIf="mensajeExito" class="alert alert-success">{{ mensajeExito }}</div>
        </div>
      </div>

      <!-- Navigation -->
      <div class="step-nav">
        <button class="btn btn-outline" (click)="prevStep()" [disabled]="currentStep === 0 || enviando">
          Anterior
        </button>
        <span class="step-indicator">Paso {{ currentStep + 1 }} de {{ steps.length }}</span>
        <button *ngIf="currentStep < steps.length - 1" class="btn btn-primary" (click)="nextStep()">
          Siguiente
        </button>
        <button *ngIf="currentStep === steps.length - 1" class="btn btn-accent"
                (click)="enviarFormulacion()" [disabled]="enviando">
          {{ enviando ? 'Enviando...' : 'Enviar formulación' }}
        </button>
      </div>
    </div>
  `,
  styles: [`
    .steps-bar { display: flex; gap: 0.5rem; margin-bottom: 2rem; overflow-x: auto; }
    .step { display: flex; align-items: center; gap: 0.5rem; cursor: pointer; opacity: 0.5; white-space: nowrap; }
    .step.active, .step.completed { opacity: 1; }
    .step-circle {
      width: 28px; height: 28px; border-radius: 50%; display: flex; align-items: center;
      justify-content: center; font-size: 0.75rem; font-weight: 700;
      background: var(--border); color: var(--text-secondary);
    }
    .step.active .step-circle { background: var(--primary); color: white; }
    .step.completed .step-circle { background: var(--success); color: white; }
    .step-label { font-size: 0.8125rem; font-weight: 500; }
    .step-content { min-height: 300px; }
    .step-nav {
      display: flex; justify-content: space-between; align-items: center;
      margin-top: 1.5rem; padding-top: 1rem; border-top: 1px solid var(--border);
    }
    .step-indicator { font-size: 0.8125rem; color: var(--text-secondary); }
    .row { display: flex; gap: 1rem; margin-bottom: 1rem; }
    .field { margin-bottom: 1rem; }
    .field label { display: block; margin-bottom: 0.375rem; font-weight: 500; font-size: 0.8125rem; }
    .half { flex: 1; }
    .third { flex: 1; }
    .fourth { flex: 1; }
    .text-secondary { color: var(--text-secondary); margin-bottom: 1.5rem; }
    .operation-item { margin-bottom: 1rem; padding: 1rem; border: 1px solid var(--border); border-radius: 8px; }
    .summary-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; }
    .summary-item { padding: 0.75rem; background: var(--bg); border-radius: 6px; }
    .summary-item strong { display: block; font-size: 0.75rem; color: var(--text-secondary); margin-bottom: 0.25rem; }
    .alert { padding: 0.75rem 1rem; border-radius: 6px; margin-top: 1rem; font-size: 0.875rem; }
    .alert-error { background: #FFEBEE; color: var(--warn); }
    .alert-success { background: #E8F5E9; color: var(--success); }
    .btn-sm { padding: 0.25rem 0.625rem; font-size: 0.75rem; }
    @media (max-width: 768px) {
      .row { flex-direction: column; gap: 0; }
      .summary-grid { grid-template-columns: 1fr; }
      .steps-bar { gap: 0.25rem; }
      .step-label { display: none; }
    }
  `]
})
export class FormulacionWizardComponent implements OnInit {
  steps = ['Articulación', 'Acción', 'Indicadores', 'Operaciones', 'Envío'];
  currentStep = 0;
  gestion = 2026;
  enviando = false;
  comentarioEnvio = '';
  mensajeError = '';
  mensajeExito = '';
  unidad: any = null;

  // Data from API
  planes: any[] = [];
  accionesMediano: any[] = [];
  programas: any[] = [];
  unidadesMedida: any[] = [];
  objetosGasto: any[] = [];

  form = this.fb.group({
    articulacion: this.fb.group({
      pei: [''],
      accion_mediano: ['', Validators.required],
      programa: ['', Validators.required],
    }),
    accion: this.fb.group({
      codigo: ['', Validators.required],
      nombre: ['', Validators.required],
      justificacion: [''],
      fecha_inicio: [''],
      fecha_fin: [''],
    }),
    producto: this.fb.group({
      tipo: ['terminal'],
      nombre: ['', Validators.required],
      indicador_nombre: ['', Validators.required],
      indicador_formula: [''],
      linea_base: [0],
      meta_anual: [0, Validators.required],
      unidad_medida: ['', Validators.required],
      trimestre1: [0],
      trimestre2: [0],
      trimestre3: [0],
      trimestre4: [0],
    }),
    operaciones: this.fb.array([]),
  });

  constructor(
    private fb: FormBuilder,
    private api: ApiService,
    private route: ActivatedRoute,
    private router: Router,
  ) {}

  get operacionesForm() { return this.form.controls.operaciones as FormArray; }
  get operacionesFormGroup() { return this.form.controls.operaciones as any; }

  get totalOperaciones(): number {
    return this.operacionesForm.controls.reduce((sum, c) => {
      const q = Number(c.value.cantidad || 0);
      const p = Number(c.value.precio_unitario || 0);
      return sum + q * p;
    }, 0);
  }

  ngOnInit(): void {
    this.route.params.subscribe(params => {
      if (params['unidadId']) {
        this.api.get<any>(`/unidades/${params['unidadId']}/`).subscribe({
          next: u => this.unidad = u
        });
      }
    });
    this.loadCatalogos();
    this.agregarOperacion();
  }

  loadCatalogos(): void {
    this.api.get<any>('/planes/', { tipo: 'pei', activo: true }).subscribe(r => this.planes = (r as any).results || r);
    this.api.get<any>('/acciones-mediano-plazo/').subscribe(r => this.accionesMediano = (r as any).results || r);
    this.api.get<any>('/programas/', { gestion: this.gestion, activo: true }).subscribe(r => this.programas = (r as any).results || r);
    this.api.get<any>('/unidades-medida/', { gestion: this.gestion }).subscribe(r => this.unidadesMedida = (r as any).results || r);
    this.api.get<any>('/objetos-gasto/', { gestion: this.gestion }).subscribe(r => this.objetosGasto = (r as any).results || r);
  }

  agregarOperacion(): void {
    this.operacionesForm.push(this.fb.group({
      nombre: ['', Validators.required],
      cantidad: [1],
      precio_unitario: [0],
      objeto_gasto: ['', Validators.required],
    }));
  }

  eliminarOperacion(index: number): void {
    this.operacionesForm.removeAt(index);
  }

  goToStep(step: number): void {
    if (step < this.currentStep) { this.currentStep = step; }
  }

  nextStep(): void {
    if (this.currentStep < this.steps.length - 1) {
      this.currentStep++;
      window.scrollTo(0, 0);
    }
  }

  prevStep(): void {
    if (this.currentStep > 0) {
      this.currentStep--;
      window.scrollTo(0, 0);
    }
  }

  enviarFormulacion(): void {
    this.enviando = true;
    this.mensajeError = '';
    this.mensajeExito = '';

    const payload = {
      gestion: this.gestion,
      unidad_id: this.unidad?.id || this.route.snapshot.params['unidadId'],
      articulacion: this.form.value.articulacion,
      accion: this.form.value.accion,
      producto: this.form.value.producto,
      operaciones: this.form.value.operaciones,
      comentario: this.comentarioEnvio,
    };

    this.api.post('/formulacion/enviar/', payload).subscribe({
      next: (res: any) => {
        this.mensajeExito = res.mensaje || 'Formulación enviada correctamente';
        this.enviando = false;
      },
      error: (err) => {
        this.mensajeError = err.message || 'Error al enviar la formulación';
        this.enviando = false;
      },
    });
  }
}

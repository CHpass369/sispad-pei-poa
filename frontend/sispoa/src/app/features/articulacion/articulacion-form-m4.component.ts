import { Component, OnInit } from '@angular/core';
import { ApiService } from '../../core/services/api.service';
import { Router } from '@angular/router';

@Component({
  selector: 'app-articulacion-form-m4',
  standalone: false,
  template: `
    <div class="form-page">
      <div class="page-header">
        <h2>Nuevo Seguimiento Presupuestario</h2>
        <p class="text-secondary">Registre el seguimiento presupuestario de una actividad</p>
      </div>
    
      @if (mensajeExito) {
        <div class="alert alert-success">{{ mensajeExito }}</div>
      }
      @if (mensajeError) {
        <div class="alert alert-danger">{{ mensajeError }}</div>
      }
    
      <div class="card form-card">
        <h3 class="step-title">Datos del Seguimiento</h3>
    
        <div class="form-grid">
          <!-- Seleccionar Actividad desde árbol M3 -->
          <div class="field-full">
            <label>Actividad *</label>
            <select [(ngModel)]="form.actividad" class="form-control">
              <option value="">Seleccionar actividad...</option>
              @for (a of actividades; track a) {
                <option [value]="a.id">
                  {{ a.codigo_actividad }} — {{ a.denominacion }}
                  @if (a.operacion_nombre) {
                    ({{ a.operacion_nombre }})
                  }
                </option>
              }
            </select>
          </div>
    
          <!-- Gestión -->
          <div class="field">
            <label>Gestión *</label>
            <select [(ngModel)]="form.gestion" class="form-control">
              <option value="">Seleccionar...</option>
              @for (g of gestiones; track g) {
                <option [value]="g">{{ g }}</option>
              }
            </select>
          </div>
          <div class="field">
            <label>Fecha de Actualización</label>
            <input type="date" [(ngModel)]="form.fecha_actualizacion" class="form-control">
          </div>
    
          <h4 class="section-subtitle">Presupuesto</h4>
    
          <div class="field">
            <label>Presupuesto Inicial (Bs.)</label>
            <input type="number" step="0.01" [(ngModel)]="form.presupuesto_inicial" class="form-control" placeholder="0.00">
          </div>
          <div class="field">
            <label>Modificaciones (Bs.)</label>
            <input type="number" step="0.01" [(ngModel)]="form.modificaciones" class="form-control" placeholder="0.00">
          </div>
          <div class="field">
            <label>Presupuesto Vigente (Bs.)</label>
            <input type="number" step="0.01" [(ngModel)]="form.presupuesto_vigente" class="form-control" placeholder="Calculado automáticamente">
          </div>
          <div class="field">
            <label>Devengado Total (Bs.)</label>
            <input type="number" step="0.01" [(ngModel)]="form.devengado_total" class="form-control" placeholder="0.00">
          </div>
    
          <h4 class="section-subtitle">Ejecución Mensual (Devengado)</h4>
          <div class="field-full">
            <div class="mensual-grid">
              @for (m of meses; track m; let i = $index) {
                <div class="field">
                  <label>{{ m }}</label>
                  <input type="number" step="0.01" [(ngModel)]="form['ejecucion_' + (i + 1)]" class="form-control" placeholder="0.00">
                </div>
              }
            </div>
          </div>
    
          <h4 class="section-subtitle">Ejecución Física</h4>
    
          <div class="field">
            <label>Meta Física</label>
            <input type="number" step="0.01" [(ngModel)]="form.meta_fisica" class="form-control" placeholder="Meta">
          </div>
          <div class="field">
            <label>Ejecución Física</label>
            <input type="number" step="0.01" [(ngModel)]="form.ejecucion_fisica" class="form-control" placeholder="Ejecutado">
          </div>
          <div class="field">
            <label>Desviación (%)</label>
            <input type="number" step="0.01" [(ngModel)]="form.desviacion" class="form-control" placeholder="% desviación">
          </div>
          <div class="field">
            <label>Eficacia (%)</label>
            <input type="number" step="0.01" [(ngModel)]="form.eficacia" class="form-control" placeholder="% eficacia">
          </div>
    
          <!-- Acción correctiva -->
          <div class="field-full">
            <label>Acción Correctiva</label>
            <textarea [(ngModel)]="form.accion_correctiva" class="form-control" rows="2" placeholder="Acciones correctivas implementadas"></textarea>
          </div>
    
          <!-- Evidencia -->
          <div class="field-full">
            <label>Evidencia / Observaciones</label>
            <textarea [(ngModel)]="form.evidencia" class="form-control" rows="2" placeholder="Evidencias, observaciones o notas"></textarea>
          </div>
        </div>
    
        <div class="form-nav">
          <button class="btn btn-outline" (click)="cancelar()">← Cancelar</button>
          <button class="btn btn-primary btn-guardar" (click)="guardar()" [disabled]="guardando">
            {{ guardando ? 'Guardando...' : '💾 Guardar Seguimiento' }}
          </button>
        </div>
      </div>
    </div>
    `,
  styles: [`
    .form-page { padding-bottom: 2rem; max-width: 800px; margin: 0 auto; }
    .page-header { margin-bottom: 1rem; }
    .page-header h2 { font-size: 1.25rem; color: var(--primary); margin-bottom: 0.25rem; }
    .text-secondary { color: var(--text-secondary); font-size: 0.8125rem; }

    .form-card { padding: 1.5rem; }
    .step-title { font-size: 1.125rem; color: var(--primary); margin-bottom: 0.75rem; padding-bottom: 0.5rem; border-bottom: 2px solid var(--border); }
    .section-subtitle { font-size: 0.875rem; color: var(--primary-dark); margin: 1rem 0 0.5rem; grid-column: 1 / -1; padding-top: 0.5rem; border-top: 1px solid var(--border); }

    .form-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 0.75rem; }
    .field-full { grid-column: 1 / -1; }
    .field label { display: block; font-size: 0.6875rem; font-weight: 600; color: var(--text-secondary); margin-bottom: 0.25rem; }
    .field { min-width: 0; }

    .mensual-grid { display: grid; grid-template-columns: repeat(6, 1fr); gap: 0.375rem; }
    .mensual-grid .field label { font-size: 0.625rem; }

    .form-nav { display: flex; align-items: center; justify-content: space-between; margin-top: 1.5rem; padding-top: 1rem; border-top: 1px solid var(--border); }
    .btn-guardar { background: var(--success); }
    .btn-guardar:hover { background: var(--mdc-green-800); }

    .alert { padding: 0.75rem 1rem; border-radius: 6px; font-size: 0.8125rem; margin-bottom: 1rem; }
    .alert-success { background: var(--mdc-green-50); color: var(--mdc-green-800); border: 1px solid #A5D6A7; }
    .alert-danger { background: var(--mdc-red-50); color: var(--mdc-red-800); border: 1px solid #EF9A9A; }

    @media (max-width: 768px) {
      .form-grid { grid-template-columns: 1fr; }
      .mensual-grid { grid-template-columns: repeat(3, 1fr); }
    }
  `],
})
export class ArticulacionFormM4Component implements OnInit {
  guardando = false;
  mensajeExito = '';
  mensajeError = '';
  meses = ['ENE', 'FEB', 'MAR', 'ABR', 'MAY', 'JUN', 'JUL', 'AGO', 'SEP', 'OCT', 'NOV', 'DIC'];
  gestiones: number[] = [];
  actividades: any[] = [];

  form: any = {
    actividad: '',
    gestion: null,
    fecha_actualizacion: '',
    presupuesto_inicial: null,
    modificaciones: null,
    presupuesto_vigente: null,
    devengado_total: null,
    ejecucion_1: null, ejecucion_2: null, ejecucion_3: null,
    ejecucion_4: null, ejecucion_5: null, ejecucion_6: null,
    ejecucion_7: null, ejecucion_8: null, ejecucion_9: null,
    ejecucion_10: null, ejecucion_11: null, ejecucion_12: null,
    meta_fisica: null,
    ejecucion_fisica: null,
    desviacion: null,
    eficacia: null,
    accion_correctiva: '',
    evidencia: '',
    estado: 'REFERENCIAL',
  };

  constructor(private api: ApiService, private router: Router) {}

  ngOnInit(): void {
    this.cargarCatalogos();
  }

  private cargarCatalogos(): void {
    // Cargar actividades con datos de operación para contexto
    this.api.get<any>('/articulacion/actividades/').subscribe({
      next: (r) => {
        const acts = r.results || r || [];
        // Si hay operaciones disponibles, enriquecer nombres
        this.api.get<any>('/articulacion/operaciones/').subscribe({
          next: (rOps) => {
            const ops = this.buildMap(rOps.results || rOps || [], 'id');
            this.actividades = acts.map((a: any) => ({
              ...a,
              operacion_nombre: ops.get(a.operacion)?.denominacion || '',
            }));
          },
          error: () => { this.actividades = acts; },
        });
      },
      error: () => {},
    });

    const year = new Date().getFullYear();
    this.gestiones = [year - 1, year, year + 1];
  }

  private buildMap(list: any[], key: string): Map<string, any> {
    const m = new Map<string, any>();
    (list || []).forEach((item: any) => m.set(item[key], item));
    return m;
  }

  cancelar(): void {
    this.router.navigate(['/articulacion/presupuesto-seguimiento']);
  }

  guardar(): void {
    if (!this.validar()) return;

    this.guardando = true;
    this.mensajeError = '';

    this.api.post<any>('/articulacion/seguimientos/', this.form).subscribe({
      next: () => {
        this.mensajeExito = '✅ Seguimiento presupuestario registrado exitosamente. Redirigiendo...';
        this.guardando = false;
        setTimeout(() => this.router.navigate(['/articulacion/presupuesto-seguimiento']), 2000);
      },
      error: (err) => {
        console.error('Error al crear seguimiento', err);
        this.mensajeError = '❌ Error al guardar el seguimiento. Verifique los datos.';
        this.guardando = false;
      },
    });
  }

  private validar(): boolean {
    this.mensajeError = '';
    if (!this.form.actividad) { this.mensajeError = 'Debe seleccionar una actividad.'; return false; }
    if (!this.form.gestion) { this.mensajeError = 'Debe seleccionar la gestión.'; return false; }
    return true;
  }
}

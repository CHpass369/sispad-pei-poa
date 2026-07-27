import { Component, OnInit } from '@angular/core';
import { ApiService } from '../../core/services/api.service';
import { Router } from '@angular/router';

@Component({
  selector: 'app-articulacion-form-m3',
  standalone: false,
  template: `
    <div class="form-page">
      <div class="page-header">
        <h2>Nueva Articulación POA → POAU</h2>
        <p class="text-secondary">Cree la jerarquía Operación → Actividad → Tarea</p>
      </div>

      <div class="alert alert-success" *ngIf="mensajeExito">{{ mensajeExito }}</div>
      <div class="alert alert-danger" *ngIf="mensajeError">{{ mensajeError }}</div>

      <!-- Seleccionar Acción POA -->
      <div class="card form-card">
        <h3 class="step-title">1. Seleccionar Acción POA</h3>
        <div class="field-full">
          <label>Acción POA *</label>
          <select [(ngModel)]="accionPoaSeleccionada" class="form-control" (change)="onAccionChange()">
            <option value="">Seleccionar acción POA...</option>
            <option *ngFor="let a of accionesPOA" [value]="a.id">{{ a.codigo_accion }} — {{ a.denominacion }}</option>
          </select>
        </div>
      </div>

      <ng-container *ngIf="accionPoaSeleccionada">
        <!-- Operación -->
        <div class="card form-card">
          <h3 class="step-title">2. Operación</h3>
          <div class="form-grid">
            <div class="field">
              <label>Código Operación *</label>
              <input [(ngModel)]="operacion.codigo_operacion" class="form-control" placeholder="Ej: OP-001">
            </div>
            <div class="field">
              <label>Tipo Operación</label>
              <select [(ngModel)]="operacion.tipo_operacion" class="form-control">
                <option value="">Seleccionar...</option>
                <option value="FUNCIONAMIENTO">Funcionamiento</option>
                <option value="INVERSION">Inversión</option>
              </select>
            </div>
            <div class="field-full">
              <label>Denominación Operación *</label>
              <textarea [(ngModel)]="operacion.denominacion" class="form-control" rows="2" placeholder="Descripción de la operación"></textarea>
            </div>
            <div class="field">
              <label>Unidad de Medida</label>
              <select [(ngModel)]="operacion.unidad_medida" class="form-control">
                <option value="">Seleccionar...</option>
                <option value="Unidad">Unidad</option>
                <option value="Porcentaje">Porcentaje</option>
                <option value="Persona">Persona</option>
                <option value="Familia">Familia</option>
                <option value="Obra">Obra</option>
              </select>
            </div>
            <div class="field">
              <label>Meta Anual</label>
              <input type="number" step="0.01" [(ngModel)]="operacion.meta_anual" class="form-control" placeholder="Meta">
            </div>
            <div class="field">
              <label>Fecha Inicio</label>
              <input type="date" [(ngModel)]="operacion.fecha_inicio" class="form-control">
            </div>
            <div class="field">
              <label>Fecha Fin</label>
              <input type="date" [(ngModel)]="operacion.fecha_fin" class="form-control">
            </div>
            <div class="field">
              <label>Responsable</label>
              <input [(ngModel)]="operacion.responsable" class="form-control" placeholder="Responsable">
            </div>
            <div class="field">
              <label>Cargo</label>
              <input [(ngModel)]="operacion.cargo" class="form-control" placeholder="Cargo">
            </div>
          </div>
        </div>

        <!-- Actividades -->
        <div class="card form-card">
          <div class="section-header">
            <h3 class="step-title">3. Actividades</h3>
            <button class="btn btn-sm btn-outline" (click)="agregarActividad()">+ Agregar Actividad</button>
          </div>

          <div *ngFor="let act of actividades; let i = index" class="sub-form">
            <h4 class="section-subtitle">Actividad {{ i + 1 }}</h4>
            <div class="form-grid">
              <div class="field">
                <label>Código Actividad *</label>
                <input [(ngModel)]="act.codigo_actividad" class="form-control" placeholder="Ej: ACT-001">
              </div>
              <div class="field">
                <label>Unidad de Medida</label>
                <select [(ngModel)]="act.unidad_medida" class="form-control">
                  <option value="">Seleccionar...</option>
                  <option value="Unidad">Unidad</option>
                  <option value="Porcentaje">Porcentaje</option>
                  <option value="Persona">Persona</option>
                  <option value="Obra">Obra</option>
                </select>
              </div>
              <div class="field-full">
                <label>Denominación *</label>
                <textarea [(ngModel)]="act.denominacion" class="form-control" rows="2" placeholder="Descripción de la actividad"></textarea>
              </div>
              <div class="field">
                <label>Meta Anual</label>
                <input type="number" step="0.01" [(ngModel)]="act.meta_anual" class="form-control" placeholder="Meta anual">
              </div>
              <div class="field">
                <label>Ponderación (%)</label>
                <input type="number" [(ngModel)]="act.ponderacion" class="form-control" min="0" max="100" placeholder="%">
              </div>
              <div class="field-full">
                <label>Programación Mensual</label>
                <div class="mensual-grid">
                  <div class="field" *ngFor="let m of meses; let mi = index">
                    <label>{{ m }}</label>
                    <input type="number" step="0.01" [(ngModel)]="act.programacion_mensual[mi]" class="form-control" placeholder="0">
                  </div>
                </div>
              </div>
            </div>

            <!-- Tareas dentro de la actividad -->
            <div class="tareas-section">
              <div class="section-header">
                <label class="tareas-label">Tareas</label>
                <button class="btn btn-xs btn-outline" (click)="agregarTarea(i)">+ Tarea</button>
              </div>

              <div *ngFor="let tar of act.tareas; let tj = index" class="sub-form tarea-form">
                <h5 class="tarea-title">Tarea {{ tj + 1 }}
                  <button class="btn btn-xs btn-outline-danger" (click)="eliminarTarea(i, tj)">✕</button>
                </h5>
                <div class="form-grid">
                  <div class="field">
                    <label>Código Tarea *</label>
                    <input [(ngModel)]="tar.codigo_tarea" class="form-control" placeholder="Ej: TAR-001">
                  </div>
                  <div class="field">
                    <label>Responsable</label>
                    <input [(ngModel)]="tar.responsable" class="form-control" placeholder="Responsable">
                  </div>
                  <div class="field-full">
                    <label>Denominación *</label>
                    <textarea [(ngModel)]="tar.denominacion" class="form-control" rows="1" placeholder="Descripción"></textarea>
                  </div>
                  <div class="field">
                    <label>Fecha Inicio</label>
                    <input type="date" [(ngModel)]="tar.fecha_inicio" class="form-control">
                  </div>
                  <div class="field">
                    <label>Fecha Fin</label>
                    <input type="date" [(ngModel)]="tar.fecha_fin" class="form-control">
                  </div>
                  <div class="field">
                    <label>Meta</label>
                    <input type="number" step="0.01" [(ngModel)]="tar.metas" class="form-control" placeholder="Meta">
                  </div>
                  <div class="field">
                    <label>Orden</label>
                    <input type="number" [(ngModel)]="tar.orden" class="form-control" placeholder="Orden">
                  </div>
                </div>
              </div>
            </div>

            <div class="sub-form-actions">
              <button class="btn btn-xs btn-outline-danger" (click)="eliminarActividad(i)" *ngIf="actividades.length > 1">Eliminar actividad</button>
            </div>
          </div>
        </div>

        <!-- Normativas -->
        <div class="card form-card">
          <h3 class="step-title">4. Normativas Aplicables</h3>
          <div class="field-full">
            <div class="checkbox-grid">
              <label *ngFor="let n of normativas" class="checkbox-item">
                <input type="checkbox" [value]="n.id"
                       [checked]="normativasSeleccionadas.includes(n.id)"
                       (change)="toggleNormativa(n.id)">
                <span>{{ n.codigo || n.normativa }} — {{ n.descripcion || n.denominacion }}</span>
              </label>
            </div>
          </div>
        </div>

        <!-- Botón guardar -->
        <div class="form-nav">
          <button class="btn btn-outline" (click)="cancelar()">← Cancelar</button>
          <button class="btn btn-primary btn-guardar" (click)="guardarTodo()" [disabled]="guardando">
            {{ guardando ? 'Guardando...' : '💾 Guardar Jerarquía Completa' }}
          </button>
        </div>
      </ng-container>
    </div>
  `,
  styles: [`
    .form-page { padding-bottom: 2rem; max-width: 900px; margin: 0 auto; }
    .page-header { margin-bottom: 1rem; }
    .page-header h2 { font-size: 1.25rem; color: var(--primary); margin-bottom: 0.25rem; }
    .text-secondary { color: var(--text-secondary); font-size: 0.8125rem; }

    .form-card { padding: 1.5rem; margin-bottom: 1rem; }
    .step-title { font-size: 1rem; color: var(--primary); margin-bottom: 0.75rem; padding-bottom: 0.5rem; border-bottom: 2px solid var(--border); }
    .section-subtitle { font-size: 0.875rem; color: var(--primary-dark); margin: 0.75rem 0 0.5rem; }
    .section-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 0.75rem; }
    .section-header .step-title { margin-bottom: 0; }

    .form-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 0.75rem; }
    .field-full { grid-column: 1 / -1; }
    .field label { display: block; font-size: 0.6875rem; font-weight: 600; color: var(--text-secondary); margin-bottom: 0.25rem; }
    .field { min-width: 0; }

    .sub-form { background: var(--bg); border-radius: 8px; padding: 1rem; margin-bottom: 0.75rem; border: 1px solid var(--border); }
    .sub-form-actions { margin-top: 0.5rem; text-align: right; }

    .btn-sm { font-size: 0.75rem; padding: 0.375rem 0.75rem; }
    .btn-xs { font-size: 0.6875rem; padding: 0.25rem 0.5rem; }
    .btn-outline-danger { background: transparent; border: 1px solid var(--warn); color: var(--warn); }
    .btn-outline-danger:hover { background: var(--warn); color: white; }

    .tareas-section { margin-top: 0.75rem; padding-top: 0.75rem; border-top: 1px solid var(--border); }
    .tareas-label { font-size: 0.75rem; font-weight: 600; color: var(--text-secondary); }
    .tareas-section .section-header { margin-bottom: 0.5rem; }
    .tarea-form { margin-bottom: 0.5rem; }
    .tarea-title { display: flex; align-items: center; justify-content: space-between; font-size: 0.8125rem; color: var(--primary); margin-bottom: 0.5rem; }

    .mensual-grid { display: grid; grid-template-columns: repeat(6, 1fr); gap: 0.375rem; }
    .mensual-grid .field label { font-size: 0.625rem; }

    .checkbox-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 0.375rem; background: var(--bg); padding: 0.75rem; border-radius: 6px; max-height: 250px; overflow-y: auto; }
    .checkbox-item { display: flex; align-items: flex-start; gap: 0.5rem; font-size: 0.75rem; cursor: pointer; padding: 0.25rem; }
    .checkbox-item input[type="checkbox"] { accent-color: var(--primary); margin-top: 2px; }

    .form-nav { display: flex; align-items: center; justify-content: space-between; margin-top: 1rem; padding-top: 1rem; border-top: 1px solid var(--border); }
    .btn-guardar { background: var(--success); }
    .btn-guardar:hover { background: #1B5E3B; }

    .alert { padding: 0.75rem 1rem; border-radius: 6px; font-size: 0.8125rem; margin-bottom: 1rem; }
    .alert-success { background: #E8F5E9; color: #1B5E3B; border: 1px solid #A5D6A7; }
    .alert-danger { background: #FFEBEE; color: #C62828; border: 1px solid #EF9A9A; }

    @media (max-width: 768px) {
      .form-grid { grid-template-columns: 1fr; }
      .mensual-grid { grid-template-columns: repeat(3, 1fr); }
    }
  `],
})
export class ArticulacionFormM3Component implements OnInit {
  guardando = false;
  mensajeExito = '';
  mensajeError = '';
  meses = ['ENE', 'FEB', 'MAR', 'ABR', 'MAY', 'JUN', 'JUL', 'AGO', 'SEP', 'OCT', 'NOV', 'DIC'];

  accionesPOA: any[] = [];
  normativas: any[] = [];
  accionPoaSeleccionada = '';

  operacion: any = {
    codigo_operacion: '',
    denominacion: '',
    tipo_operacion: '',
    unidad_medida: '',
    meta_anual: null,
    fecha_inicio: '',
    fecha_fin: '',
    responsable: '',
    cargo: '',
  };

  actividades: any[] = [];
  normativasSeleccionadas: number[] = [];

  constructor(private api: ApiService, private router: Router) {}

  ngOnInit(): void {
    this.cargarCatalogos();
  }

  private cargarCatalogos(): void {
    this.api.get<any>('/articulacion/acciones-poa/').subscribe({
      next: (r) => { this.accionesPOA = r.results || r || []; },
      error: () => {},
    });

    this.api.get<any>('/articulacion/normativas/').subscribe({
      next: (r) => { this.normativas = r.results || r || []; },
      error: () => {},
    });
  }

  onAccionChange(): void {
    this.operacion = {
      codigo_operacion: '',
      denominacion: '',
      tipo_operacion: '',
      unidad_medida: '',
      meta_anual: null,
      fecha_inicio: '',
      fecha_fin: '',
      responsable: '',
      cargo: '',
    };
    this.actividades = [];
    this.normativasSeleccionadas = [];
    this.mensajeError = '';
    this.mensajeExito = '';
  }

  agregarActividad(): void {
    this.actividades.push(this.nuevaActividad());
  }

  private nuevaActividad(): any {
    return {
      codigo_actividad: '',
      denominacion: '',
      unidad_medida: '',
      meta_anual: null,
      ponderacion: null,
      programacion_mensual: Array(12).fill(null),
      tareas: [],
    };
  }

  eliminarActividad(i: number): void {
    this.actividades.splice(i, 1);
  }

  agregarTarea(actIdx: number): void {
    this.actividades[actIdx].tareas.push(this.nuevaTarea());
  }

  private nuevaTarea(): any {
    return {
      codigo_tarea: '',
      denominacion: '',
      responsable: '',
      fecha_inicio: '',
      fecha_fin: '',
      metas: null,
      orden: null,
    };
  }

  eliminarTarea(actIdx: number, tarIdx: number): void {
    this.actividades[actIdx].tareas.splice(tarIdx, 1);
  }

  toggleNormativa(id: number): void {
    const idx = this.normativasSeleccionadas.indexOf(id);
    if (idx >= 0) {
      this.normativasSeleccionadas.splice(idx, 1);
    } else {
      this.normativasSeleccionadas.push(id);
    }
  }

  cancelar(): void {
    this.router.navigate(['/articulacion/poa-poau']);
  }

  guardarTodo(): void {
    if (!this.validar()) return;

    this.guardando = true;
    this.mensajeError = '';
    this.mensajeExito = '';

    // Crear operación vinculada a la acción POA
    this.api.post<any>('/articulacion/operaciones/', {
      ...this.operacion,
      accion_poa: this.accionPoaSeleccionada,
      estado: 'REFERENCIAL',
    }).subscribe({
      next: (opRes) => {
        const operacionId = opRes.id || opRes;

        // Crear actividades secuencialmente
        let actPromises: Promise<any>[] = this.actividades.map((act) => {
          return new Promise((resolve, reject) => {
            this.api.post<any>('/articulacion/actividades/', {
              ...act,
              operacion: operacionId,
              estado: 'REFERENCIAL',
            }).subscribe({
              next: (actRes) => {
                const actividadId = actRes.id || actRes;

                // Crear tareas de esta actividad
                if (act.tareas.length === 0) {
                  resolve(true);
                  return;
                }

                let tarPromises = act.tareas.map((tar: any) => {
                  return new Promise<void>((resT, rejT) => {
                    this.api.post<any>('/articulacion/tareas/', {
                      ...tar,
                      actividad: actividadId,
                      estado: 'REFERENCIAL',
                    }).subscribe({
                      next: () => resT(),
                      error: (err) => rejT(err),
                    });
                  });
                });

                Promise.all(tarPromises)
                  .then(() => resolve(true))
                  .catch((err) => reject(err));
              },
              error: (err) => reject(err),
            });
          });
        });

        Promise.all(actPromises)
          .then(() => {
            this.mensajeExito = '✅ Jerarquía POA→POAU creada exitosamente. Redirigiendo...';
            this.guardando = false;
            setTimeout(() => this.router.navigate(['/articulacion/poa-poau']), 2000);
          })
          .catch((err) => {
            this.onError(err, 'Error al crear actividades o tareas');
          });
      },
      error: (err) => {
        this.onError(err, 'Error al crear la operación');
      },
    });
  }

  private validar(): boolean {
    this.mensajeError = '';
    if (!this.accionPoaSeleccionada) { this.mensajeError = 'Debe seleccionar una Acción POA.'; return false; }
    if (!this.operacion.codigo_operacion) { this.mensajeError = 'Debe ingresar el código de operación.'; return false; }
    if (!this.operacion.denominacion) { this.mensajeError = 'Debe ingresar la denominación de la operación.'; return false; }
    if (this.actividades.length === 0) { this.mensajeError = 'Debe agregar al menos una actividad.'; return false; }
    for (let i = 0; i < this.actividades.length; i++) {
      if (!this.actividades[i].codigo_actividad) { this.mensajeError = `Actividad ${i + 1}: debe ingresar el código.`; return false; }
      if (!this.actividades[i].denominacion) { this.mensajeError = `Actividad ${i + 1}: debe ingresar la denominación.`; return false; }
    }
    return true;
  }

  private onError(err: any, msg: string): void {
    console.error(msg, err);
    this.mensajeError = `❌ ${msg}. Verifique los datos e intente nuevamente.`;
    this.guardando = false;
  }
}

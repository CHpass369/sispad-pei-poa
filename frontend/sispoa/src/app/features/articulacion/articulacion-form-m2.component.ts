import { Component, OnInit } from '@angular/core';
import { ApiService } from '../../core/services/api.service';
import { Router } from '@angular/router';

@Component({
  selector: 'app-articulacion-form-m2',
  standalone: false,
  template: `
    <div class="form-page">
      <div class="page-header">
        <h2>Nueva Articulación PEI → POA</h2>
        <p class="text-secondary">Cree una Acción POA vinculada a un Producto PEI</p>
      </div>
    
      @if (mensajeExito) {
        <div class="alert alert-success">{{ mensajeExito }}</div>
      }
      @if (mensajeError) {
        <div class="alert alert-danger">{{ mensajeError }}</div>
      }
    
      <div class="card form-card">
        <h3 class="step-title">Datos de la Acción POA</h3>
    
        <div class="form-grid">
          <!-- Producto PEI -->
          <div class="field-full">
            <label>Producto PEI *</label>
            <select [(ngModel)]="form.producto_pei" class="form-control">
              <option value="">Seleccionar producto PEI...</option>
              @for (p of productosPEI; track p) {
                <option [value]="p.id">
                  {{ p.codigo_producto }} — {{ p.denominacion }}
                </option>
              }
            </select>
          </div>
    
          <!-- Código Acción POA -->
          <div class="field">
            <label>Código Acción POA *</label>
            <input [(ngModel)]="form.codigo_accion" class="form-control" placeholder="Ej: POA-2026-001">
          </div>
          <div class="field">
            <label>Gestión *</label>
            <select [(ngModel)]="form.gestion" class="form-control">
              <option value="">Seleccionar...</option>
              @for (g of gestiones; track g) {
                <option [value]="g">{{ g }}</option>
              }
            </select>
          </div>
    
          <!-- Denominación -->
          <div class="field-full">
            <label>Denominación *</label>
            <textarea [(ngModel)]="form.denominacion" class="form-control" rows="3" placeholder="Descripción de la acción POA"></textarea>
          </div>
    
          <!-- Resultado esperado -->
          <div class="field-full">
            <label>Resultado Esperado</label>
            <textarea [(ngModel)]="form.resultado_esperado" class="form-control" rows="2" placeholder="Resultado esperado de la acción"></textarea>
          </div>
    
          <!-- Indicador -->
          <div class="field-full">
            <label>Indicador</label>
            <textarea [(ngModel)]="form.indicador" class="form-control" rows="2" placeholder="Indicador de la acción"></textarea>
          </div>
          <div class="field">
            <label>Fórmula del Indicador</label>
            <input [(ngModel)]="form.formula_indicador" class="form-control" placeholder="Ej: (A/B)*100">
          </div>
          <div class="field">
            <label>Unidad de Medida</label>
            <select [(ngModel)]="form.unidad_medida" class="form-control">
              <option value="">Seleccionar...</option>
              <option value="Porcentaje">Porcentaje</option>
              <option value="Número">Número</option>
              <option value="Unidad">Unidad</option>
              <option value="Persona">Persona</option>
              <option value="Familia">Familia</option>
              <option value="Hectárea">Hectárea</option>
              <option value="Metro">Metro</option>
              <option value="Obra">Obra</option>
              <option value="Proyecto">Proyecto</option>
            </select>
          </div>
    
          <!-- Línea base y meta -->
          <div class="field">
            <label>Línea Base</label>
            <input type="number" step="0.01" [(ngModel)]="form.linea_base" class="form-control" placeholder="Valor línea base">
          </div>
          <div class="field">
            <label>Meta Gestión</label>
            <input type="number" step="0.01" [(ngModel)]="form.meta_gestion" class="form-control" placeholder="Meta de la gestión">
          </div>
    
          <!-- Responsable -->
          <div class="field">
            <label>Código REACP</label>
            <input [(ngModel)]="form.codigo_reacp" class="form-control" placeholder="Ej: REACP-001">
          </div>
          <div class="field">
            <label>Cargo Responsable</label>
            <input [(ngModel)]="form.cargo_responsable" class="form-control" placeholder="Ej: Jefe de Unidad">
          </div>
    
          <!-- Fechas -->
          <div class="field">
            <label>Fecha Inicio</label>
            <input type="date" [(ngModel)]="form.fecha_inicio" class="form-control">
          </div>
          <div class="field">
            <label>Fecha Fin</label>
            <input type="date" [(ngModel)]="form.fecha_fin" class="form-control">
          </div>
    
          <!-- Tipo operación -->
          <div class="field">
            <label>Tipo de Operación</label>
            <select [(ngModel)]="form.tipo_operacion" class="form-control">
              <option value="">Seleccionar...</option>
              <option value="FUNCIONAMIENTO">Funcionamiento</option>
              <option value="INVERSION">Inversión</option>
            </select>
          </div>
          <div class="field">
            <label>Categoría Programática</label>
            <input [(ngModel)]="form.categoria_programatica" class="form-control" placeholder="Cat. programática">
          </div>
    
          <!-- Programa y Proyecto -->
          <div class="field">
            <label>Programa</label>
            <input [(ngModel)]="form.programa" class="form-control" placeholder="Programa">
          </div>
          <div class="field">
            <label>Proyecto SISIN</label>
            <input [(ngModel)]="form.proyecto_sisin" class="form-control" placeholder="Código SISIN">
          </div>
    
          <!-- Actividad presupuestaria -->
          <div class="field-full">
            <label>Actividad Presupuestaria</label>
            <input [(ngModel)]="form.actividad_presupuestaria" class="form-control" placeholder="Actividad presupuestaria">
          </div>
    
          <!-- Presupuesto -->
          <div class="field">
            <label>Presupuesto Programado (Bs.) *</label>
            <input type="number" step="0.01" [(ngModel)]="form.presupuesto_programado" class="form-control" placeholder="0.00">
          </div>
          <div class="field">
            <label>Fuente de Financiamiento</label>
            <input [(ngModel)]="form.fuente_financiamiento" class="form-control" placeholder="Ej: TGN, HIPC, etc.">
          </div>
    
          <!-- Organismo -->
          <div class="field">
            <label>Organismo Financiador</label>
            <input [(ngModel)]="form.organismo_financiador" class="form-control" placeholder="Ej: Gobierno Central">
          </div>
          <div class="field">
            <label>Medio de Verificación</label>
            <input [(ngModel)]="form.medio_verificacion" class="form-control" placeholder="Medio de verificación">
          </div>
    
          <!-- Riesgo -->
          <div class="field-full">
            <label>Riesgo</label>
            <textarea [(ngModel)]="form.riesgo" class="form-control" rows="2" placeholder="Identificación de riesgos"></textarea>
          </div>
        </div>
    
        <div class="form-nav">
          <button class="btn btn-outline" (click)="cancelar()">← Cancelar</button>
          <button class="btn btn-primary btn-guardar" (click)="guardar()" [disabled]="guardando">
            {{ guardando ? 'Guardando...' : '💾 Guardar Acción POA' }}
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
    .step-title { font-size: 1.125rem; color: var(--primary); margin-bottom: 1rem; padding-bottom: 0.5rem; border-bottom: 2px solid var(--border); }

    .form-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 0.75rem; }
    .field-full { grid-column: 1 / -1; }
    .field label { display: block; font-size: 0.6875rem; font-weight: 600; color: var(--text-secondary); margin-bottom: 0.25rem; }
    .field { min-width: 0; }

    .form-nav { display: flex; align-items: center; justify-content: space-between; margin-top: 1.5rem; padding-top: 1rem; border-top: 1px solid var(--border); }
    .btn-guardar { background: var(--success); }
    .btn-guardar:hover { background: var(--mdc-green-800); }

    .alert { padding: 0.75rem 1rem; border-radius: 6px; font-size: 0.8125rem; margin-bottom: 1rem; }
    .alert-success { background: var(--mdc-green-50); color: var(--mdc-green-800); border: 1px solid #A5D6A7; }
    .alert-danger { background: var(--mdc-red-50); color: var(--mdc-red-800); border: 1px solid #EF9A9A; }

    @media (max-width: 768px) {
      .form-grid { grid-template-columns: 1fr; }
    }
  `],
})
export class ArticulacionFormM2Component implements OnInit {
  guardando = false;
  mensajeExito = '';
  mensajeError = '';
  gestiones: number[] = [];

  productosPEI: any[] = [];

  form: any = {
    producto_pei: '',
    codigo_accion: '',
    gestion: null,
    denominacion: '',
    resultado_esperado: '',
    indicador: '',
    formula_indicador: '',
    unidad_medida: '',
    linea_base: null,
    meta_gestion: null,
    codigo_reacp: '',
    cargo_responsable: '',
    fecha_inicio: '',
    fecha_fin: '',
    tipo_operacion: '',
    categoria_programatica: '',
    programa: '',
    proyecto_sisin: '',
    actividad_presupuestaria: '',
    presupuesto_programado: null,
    fuente_financiamiento: '',
    organismo_financiador: '',
    medio_verificacion: '',
    riesgo: '',
  };

  constructor(private api: ApiService, private router: Router) {}

  ngOnInit(): void {
    this.cargarCatalogos();
  }

  private cargarCatalogos(): void {
    this.api.get<any>('/articulacion/productos-pei/').subscribe({
      next: (r) => { this.productosPEI = r.results || r || []; },
      error: () => {},
    });

    const year = new Date().getFullYear();
    this.gestiones = Array.from({ length: 6 }, (_, i) => year + i);
  }

  cancelar(): void {
    this.router.navigate(['/articulacion/pei-poa']);
  }

  guardar(): void {
    if (!this.validar()) return;

    this.guardando = true;
    this.mensajeError = '';
    this.mensajeExito = '';

    this.api.post<any>('/articulacion/acciones-poa/', this.form).subscribe({
      next: () => {
        this.mensajeExito = '✅ Acción POA creada exitosamente. Redirigiendo...';
        this.guardando = false;
        setTimeout(() => this.router.navigate(['/articulacion/pei-poa']), 2000);
      },
      error: (err) => {
        console.error('Error al crear acción POA', err);
        this.mensajeError = '❌ Error al guardar la Acción POA. Verifique los datos.';
        this.guardando = false;
      },
    });
  }

  private validar(): boolean {
    this.mensajeError = '';
    if (!this.form.producto_pei) { this.mensajeError = 'Debe seleccionar un Producto PEI.'; return false; }
    if (!this.form.codigo_accion) { this.mensajeError = 'Debe ingresar el código de la acción POA.'; return false; }
    if (!this.form.denominacion) { this.mensajeError = 'Debe ingresar la denominación.'; return false; }
    if (!this.form.gestion) { this.mensajeError = 'Debe seleccionar la gestión.'; return false; }
    return true;
  }
}

import { Component, OnInit } from '@angular/core';
import { ApiService } from '../../core/services/api.service';
import { Router } from '@angular/router';

@Component({
  selector: 'app-articulacion-form-m1',
  standalone: false,
  template: `
    <div class="form-page">
      <div class="page-header">
        <h2>Nueva Articulación PAD → PEI</h2>
        <p class="text-secondary">Complete los pasos para crear una cadena completa de articulación</p>
      </div>
    
      <!-- Barra de progreso -->
      <div class="stepper">
        @for (s of pasos; track s; let i = $index) {
          <div class="step"
            [class.active]="pasoActual === i + 1"
            [class.completed]="pasoActual > i + 1"
            (click)="irAPaso(i + 1)">
            <div class="step-circle">{{ pasoActual > i + 1 ? '✓' : i + 1 }}</div>
            <div class="step-label">{{ s }}</div>
          </div>
        }
      </div>
    
      <!-- Mensajes -->
      @if (mensajeExito) {
        <div class="alert alert-success">{{ mensajeExito }}</div>
      }
      @if (mensajeError) {
        <div class="alert alert-danger">{{ mensajeError }}</div>
      }
    
      <div class="card form-card">
        <!-- ======= PASO 1: Planificación Nacional ======= -->
        @if (pasoActual === 1) {
          <div>
            <h3 class="step-title">Paso 1: Planificación Nacional</h3>
            <div class="form-grid">
              <div class="field">
                <label>Eje PGDESA</label>
                <select [(ngModel)]="form.eje_pgdesa" class="form-control">
                  <option value="">Seleccionar...</option>
                  <option value="EJE 1 - Reconstrucción Económica">EJE 1 - Reconstrucción Económica</option>
                  <option value="EJE 2 - Desarrollo Social">EJE 2 - Desarrollo Social</option>
                  <option value="EJE 3 - Medio Ambiente y Cambio Climático">EJE 3 - Medio Ambiente y Cambio Climático</option>
                  <option value="EJE 4 - Descentralización y Autonomías">EJE 4 - Descentralización y Autonomías</option>
                </select>
              </div>
              <div class="field">
                <label>Componente PDESA</label>
                <select [(ngModel)]="form.componente_pdesa" class="form-control">
                  <option value="">Seleccionar...</option>
                  <option value="CP-01 - Fortalecimiento Productivo">CP-01 - Fortalecimiento Productivo</option>
                  <option value="CP-02 - Infraestructura y Servicios">CP-02 - Infraestructura y Servicios</option>
                  <option value="CP-03 - Desarrollo Humano">CP-03 - Desarrollo Humano</option>
                  <option value="CP-04 - Gestión Ambiental">CP-04 - Gestión Ambiental</option>
                  <option value="CP-05 - Fortalecimiento Institucional">CP-05 - Fortalecimiento Institucional</option>
                </select>
              </div>
              <div class="field">
                <label>Objetivo de Impacto</label>
                <input [(ngModel)]="form.objetivo_impacto" class="form-control" placeholder="Objetivo de impacto del PGDESA">
              </div>
              <div class="field">
                <label>Efecto</label>
                <input [(ngModel)]="form.efecto" class="form-control" placeholder="Efecto esperado">
              </div>
            </div>
          </div>
        }
    
        <!-- ======= PASO 2: Acuerdos Internacionales ======= -->
        @if (pasoActual === 2) {
          <div>
            <h3 class="step-title">Paso 2: Acuerdos Internacionales</h3>
            <div class="form-grid">
              <div class="field-full">
                <label>ODS (Objetivos de Desarrollo Sostenible)</label>
                <div class="checkbox-grid">
                  @for (ods of catalogoODS; track ods) {
                    <label class="checkbox-item">
                      <input type="checkbox" [value]="ods.id"
                        [checked]="form.ods_seleccionados.includes(ods.id)"
                        (change)="toggleODS(ods.id)">
                        <span>{{ ods.codigo || ods.nombre }}</span>
                      </label>
                    }
                  </div>
                </div>
                <div class="field">
                  <label>NDC (Contribución Nacional Determinada)</label>
                  <input [(ngModel)]="form.ndc" class="form-control" placeholder="NDC">
                </div>
                <div class="field">
                  <label>NDT</label>
                  <input [(ngModel)]="form.ndt" class="form-control" placeholder="NDT">
                </div>
                <div class="field">
                  <label>30/30</label>
                  <input [(ngModel)]="form.meta_3030" class="form-control" placeholder="Meta 30/30">
                </div>
              </div>
            </div>
          }
    
          <!-- ======= PASO 3: Planificación Sectorial ======= -->
          @if (pasoActual === 3) {
            <div>
              <h3 class="step-title">Paso 3: Planificación Sectorial</h3>
              <div class="form-grid">
                <div class="field">
                  <label>Sector</label>
                  <select [(ngModel)]="form.sector" class="form-control">
                    <option value="">Seleccionar sector...</option>
                    <option value="SALUD">Salud</option>
                    <option value="EDUCACION">Educación</option>
                    <option value="INFRAESTRUCTURA">Infraestructura</option>
                    <option value="DESARROLLO_PRODUCTIVO">Desarrollo Productivo</option>
                    <option value="MEDIO_AMBIENTE">Medio Ambiente</option>
                    <option value="DESARROLLO_SOCIAL">Desarrollo Social</option>
                    <option value="INSTITUCIONAL">Institucional</option>
                  </select>
                </div>
                <div class="field">
                  <label>Código Resultado PDS</label>
                  <input [(ngModel)]="form.codigo_resultado_pds" class="form-control" placeholder="Ej: R-PDS-01">
                </div>
                <div class="field-full">
                  <label>Nombre Resultado PDS</label>
                  <input [(ngModel)]="form.nombre_resultado_pds" class="form-control" placeholder="Denominación del resultado PDS">
                </div>
              </div>
            </div>
          }
    
          <!-- ======= PASO 4: PAD ======= -->
          @if (pasoActual === 4) {
            <div>
              <h3 class="step-title">Paso 4: Plan de Acción Departamental (PAD)</h3>
              <div class="form-grid">
                <div class="field">
                  <label>Código Geográfico</label>
                  <input [(ngModel)]="form.codigo_geografico" class="form-control" placeholder="Código municipio/departamento">
                </div>
                <div class="field">
                  <label>ETA (Estructura Territorial de Apoyo)</label>
                  <input [(ngModel)]="form.eta" class="form-control" placeholder="ETA">
                </div>
                <h4 class="section-subtitle">Resultado PAD</h4>
                <div class="field">
                  <label>Código Resultado PAD</label>
                  <input [(ngModel)]="form.codigo_resultado_pad" class="form-control" placeholder="Ej: RPAD-01">
                </div>
                <div class="field-full">
                  <label>Denominación Resultado PAD</label>
                  <textarea [(ngModel)]="form.denominacion_resultado_pad" class="form-control" rows="2" placeholder="Descripción del resultado PAD"></textarea>
                </div>
                <h4 class="section-subtitle">Producto PAD</h4>
                <div class="field">
                  <label>Código Producto PAD</label>
                  <input [(ngModel)]="form.codigo_producto_pad" class="form-control" placeholder="Ej: PPAD-01">
                </div>
                <div class="field-full">
                  <label>Denominación Producto PAD</label>
                  <textarea [(ngModel)]="form.denominacion_producto_pad" class="form-control" rows="2" placeholder="Descripción del producto PAD"></textarea>
                </div>
              </div>
            </div>
          }
    
          <!-- ======= PASO 5: PEI ======= -->
          @if (pasoActual === 5) {
            <div>
              <h3 class="step-title">Paso 5: Plan Estratégico Institucional (PEI)</h3>
              <div class="form-grid">
                <div class="field">
                  <label>Código Entidad</label>
                  <input [(ngModel)]="form.codigo_entidad" class="form-control" placeholder="Código de la entidad">
                </div>
                <h4 class="section-subtitle">Resultado PEI</h4>
                <div class="field">
                  <label>Código Resultado PEI</label>
                  <input [(ngModel)]="form.codigo_resultado_pei" class="form-control" placeholder="Ej: RPEI-01">
                </div>
                <div class="field-full">
                  <label>Denominación Resultado PEI</label>
                  <textarea [(ngModel)]="form.denominacion_resultado_pei" class="form-control" rows="2" placeholder="Descripción del resultado PEI"></textarea>
                </div>
                <h4 class="section-subtitle">Producto PEI</h4>
                <div class="field">
                  <label>Código Producto PEI</label>
                  <input [(ngModel)]="form.codigo_producto_pei" class="form-control" placeholder="Ej: PPEI-01">
                </div>
                <div class="field-full">
                  <label>Denominación Producto PEI</label>
                  <textarea [(ngModel)]="form.denominacion_producto_pei" class="form-control" rows="2" placeholder="Descripción del producto PEI"></textarea>
                </div>
              </div>
            </div>
          }
    
          <!-- ======= PASO 6: Articulación ======= -->
          @if (pasoActual === 6) {
            <div>
              <h3 class="step-title">Paso 6: Articulación PAD → PEI</h3>
              <div class="form-grid">
                <div class="field">
                  <label>Tipo de Contribución</label>
                  <select [(ngModel)]="form.tipo_contribucion" class="form-control">
                    <option value="">Seleccionar...</option>
                    <option value="DIRECTA">Directa</option>
                    <option value="INDIRECTA">Indirecta</option>
                    <option value="COMPLEMENTARIA">Complementaria</option>
                  </select>
                </div>
                <div class="field">
                  <label>Ponderación (%)</label>
                  <input type="number" [(ngModel)]="form.ponderacion" class="form-control" min="0" max="100" placeholder="0-100">
                </div>
              </div>
            </div>
          }
    
          <!-- ======= PASO 7: Indicador ======= -->
          @if (pasoActual === 7) {
            <div>
              <h3 class="step-title">Paso 7: Indicador de Cadena</h3>
              <div class="form-grid">
                <div class="field-full">
                  <label>Indicador</label>
                  <textarea [(ngModel)]="form.indicador" class="form-control" rows="2" placeholder="Nombre del indicador"></textarea>
                </div>
                <div class="field-full">
                  <label>Fórmula</label>
                  <input [(ngModel)]="form.formula" class="form-control" placeholder="Ej: (A/B)*100">
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
                    <option value="Metro cuadrado">Metro cuadrado</option>
                    <option value="Kilómetro">Kilómetro</option>
                    <option value="Obra">Obra</option>
                    <option value="Proyecto">Proyecto</option>
                  </select>
                </div>
                <div class="field">
                  <label>Línea Base</label>
                  <input type="number" step="0.01" [(ngModel)]="form.linea_base" class="form-control" placeholder="Valor línea base">
                </div>
                <div class="field">
                  <label>Meta 2030</label>
                  <input type="number" step="0.01" [(ngModel)]="form.meta_2030" class="form-control" placeholder="Meta al 2030">
                </div>
                <div class="field">
                  <label>Fuente del Indicador</label>
                  <input [(ngModel)]="form.fuente_indicador" class="form-control" placeholder="Fuente">
                </div>
              </div>
            </div>
          }
    
          <!-- ======= PASO 8: Programación Física ======= -->
          @if (pasoActual === 8) {
            <div>
              <h3 class="step-title">Paso 8: Programación Física</h3>
              <p class="field-hint">Metas físicas anuales del quinquenio</p>
              <div class="quinquenio-grid">
                @for (year of quinquenio; track year) {
                  <div class="field">
                    <label>{{ year }}</label>
                    <input type="number" step="0.01"
                      [(ngModel)]="form['pf_' + year]"
                      class="form-control"
                      [placeholder]="'Meta ' + year">
                    </div>
                  }
                </div>
              </div>
            }
    
            <!-- ======= PASO 9: Presupuesto Quinquenal ======= -->
            @if (pasoActual === 9) {
              <div>
                <h3 class="step-title">Paso 9: Presupuesto Quinquenal</h3>
                <div class="presupuesto-grid">
                  <div class="budget-section">
                    <h4>Inversión</h4>
                    @for (year of aniosPresupuesto; track year) {
                      <div class="field">
                        <label>Inversión {{ year }}</label>
                        <input type="number" step="0.01" [(ngModel)]="form['inversion_' + year]" class="form-control" placeholder="Bs.">
                      </div>
                    }
                  </div>
                  <div class="budget-section">
                    <h4>Corriente</h4>
                    @for (year of aniosPresupuesto; track year) {
                      <div class="field">
                        <label>Corriente {{ year }}</label>
                        <input type="number" step="0.01" [(ngModel)]="form['corriente_' + year]" class="form-control" placeholder="Bs.">
                      </div>
                    }
                  </div>
                </div>
              </div>
            }
    
            <!-- ======= PASO 10: Guardar todo ======= -->
            @if (pasoActual === 10) {
              <div>
                <h3 class="step-title">Paso 10: Revisión y Guardado</h3>
                <div class="resumen-card">
                  <p>Revise los datos ingresados antes de guardar. Todos los registros se crearán en una sola operación.</p>
                  <div class="resumen-grid">
                    <div class="resumen-item"><strong>Eje PGDESA:</strong> {{ form.eje_pgdesa || '—' }}</div>
                    <div class="resumen-item"><strong>Comp. PDESA:</strong> {{ form.componente_pdesa || '—' }}</div>
                    <div class="resumen-item"><strong>Objetivo Impacto:</strong> {{ form.objetivo_impacto || '—' }}</div>
                    <div class="resumen-item"><strong>Efecto:</strong> {{ form.efecto || '—' }}</div>
                    <div class="resumen-item"><strong>Resultado PAD:</strong> {{ form.codigo_resultado_pad }} — {{ form.denominacion_resultado_pad || '—' }}</div>
                    <div class="resumen-item"><strong>Producto PAD:</strong> {{ form.codigo_producto_pad }} — {{ form.denominacion_producto_pad || '—' }}</div>
                    <div class="resumen-item"><strong>Resultado PEI:</strong> {{ form.codigo_resultado_pei }} — {{ form.denominacion_resultado_pei || '—' }}</div>
                    <div class="resumen-item"><strong>Producto PEI:</strong> {{ form.codigo_producto_pei }} — {{ form.denominacion_producto_pei || '—' }}</div>
                    <div class="resumen-item"><strong>Tipo Contribución:</strong> {{ form.tipo_contribucion || '—' }}</div>
                    <div class="resumen-item"><strong>Ponderación:</strong> {{ form.ponderacion || '—' }}%</div>
                  </div>
                </div>
              </div>
            }
    
            <!-- Navegación -->
            <div class="form-nav">
              <button class="btn btn-outline" (click)="pasoAnterior()" [disabled]="pasoActual === 1">
                ← Anterior
              </button>
              <span class="step-counter">Paso {{ pasoActual }} de 10</span>
              @if (pasoActual < 10) {
                <button class="btn btn-primary" (click)="pasoSiguiente()">
                  Siguiente →
                </button>
              }
              @if (pasoActual === 10) {
                <button class="btn btn-primary btn-guardar" (click)="guardarTodo()" [disabled]="guardando">
                  {{ guardando ? 'Guardando...' : '💾 Guardar Articulación Completa' }}
                </button>
              }
            </div>
          </div>
        </div>
    `,
  styles: [`
    .form-page { padding-bottom: 2rem; max-width: 960px; margin: 0 auto; }
    .page-header { margin-bottom: 1rem; }
    .page-header h2 { font-size: 1.25rem; color: var(--primary); margin-bottom: 0.25rem; }
    .text-secondary { color: var(--text-secondary); font-size: 0.8125rem; }

    .stepper { display: flex; gap: 0.25rem; margin-bottom: 1.5rem; overflow-x: auto; padding: 0.5rem 0; }
    .step { display: flex; align-items: center; gap: 0.375rem; cursor: pointer; padding: 0.25rem 0.5rem; border-radius: 6px; font-size: 0.6875rem; white-space: nowrap; opacity: 0.5; }
    .step.active { opacity: 1; background: var(--mdc-green-50); }
    .step.completed { opacity: 0.8; color: var(--primary); }
    .step-circle { width: 22px; height: 22px; border-radius: 50%; background: var(--border); display: flex; align-items: center; justify-content: center; font-weight: 700; font-size: 0.6875rem; color: var(--text-secondary); }
    .step.active .step-circle { background: var(--primary); color: white; }
    .step.completed .step-circle { background: var(--success); color: white; }
    .step-label { font-weight: 500; }

    .form-card { padding: 1.5rem; }
    .step-title { font-size: 1.125rem; color: var(--primary); margin-bottom: 1rem; padding-bottom: 0.5rem; border-bottom: 2px solid var(--border); }
    .section-subtitle { font-size: 0.875rem; color: var(--primary-dark); margin: 0.75rem 0 0.5rem; grid-column: 1 / -1; padding-top: 0.5rem; border-top: 1px solid var(--border); }

    .form-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 0.75rem; }
    .field-full { grid-column: 1 / -1; }
    .field label { display: block; font-size: 0.6875rem; font-weight: 600; color: var(--text-secondary); margin-bottom: 0.25rem; }
    .field-hint { font-size: 0.75rem; color: var(--text-secondary); margin-bottom: 0.75rem; }
    .field { min-width: 0; }

    .checkbox-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(200px, 1fr)); gap: 0.375rem; background: var(--bg); padding: 0.75rem; border-radius: 6px; max-height: 200px; overflow-y: auto; }
    .checkbox-item { display: flex; align-items: center; gap: 0.5rem; font-size: 0.8125rem; cursor: pointer; }
    .checkbox-item input[type="checkbox"] { accent-color: var(--primary); }

    .quinquenio-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(140px, 1fr)); gap: 0.75rem; }
    .presupuesto-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 1.5rem; }
    .budget-section h4 { font-size: 0.875rem; color: var(--primary); margin-bottom: 0.75rem; }

    .resumen-card { background: var(--bg); padding: 1rem; border-radius: 8px; margin-bottom: 1rem; }
    .resumen-card p { font-size: 0.8125rem; color: var(--text-secondary); margin-bottom: 0.75rem; }
    .resumen-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 0.5rem; }
    .resumen-item { font-size: 0.75rem; padding: 0.25rem 0; }
    .resumen-item strong { color: var(--primary-dark); }

    .form-nav { display: flex; align-items: center; justify-content: space-between; margin-top: 1.5rem; padding-top: 1rem; border-top: 1px solid var(--border); }
    .step-counter { font-size: 0.75rem; color: var(--text-secondary); font-weight: 500; }
    .btn-guardar { background: var(--success); }
    .btn-guardar:hover { background: var(--mdc-green-800); }

    .alert { padding: 0.75rem 1rem; border-radius: 6px; font-size: 0.8125rem; margin-bottom: 1rem; }
    .alert-success { background: var(--mdc-green-50); color: var(--mdc-green-800); border: 1px solid #A5D6A7; }
    .alert-danger { background: var(--mdc-red-50); color: var(--mdc-red-800); border: 1px solid #EF9A9A; }

    @media (max-width: 768px) {
      .form-grid { grid-template-columns: 1fr; }
      .presupuesto-grid { grid-template-columns: 1fr; }
      .stepper { gap: 0; }
      .step-label { display: none; }
    }
  `],
})
export class ArticulacionFormM1Component implements OnInit {
  pasos = ['Planif. Nacional', 'Acuerdos Intl.', 'Planif. Sectorial', 'PAD', 'PEI', 'Articulación', 'Indicador', 'Prog. Física', 'Presupuesto', 'Guardar'];
  pasoActual = 1;
  guardando = false;
  mensajeExito = '';
  mensajeError = '';
  quinquenio = [2026, 2027, 2028, 2029, 2030];
  aniosPresupuesto = [2026, 2027, 2028, 2029, 2030, 2031];

  catalogoODS: any[] = [];

  form: any = {
    eje_pgdesa: '',
    componente_pdesa: '',
    objetivo_impacto: '',
    efecto: '',
    ods_seleccionados: [] as number[],
    ndc: '',
    ndt: '',
    meta_3030: '',
    sector: '',
    codigo_resultado_pds: '',
    nombre_resultado_pds: '',
    codigo_geografico: '',
    eta: '',
    codigo_resultado_pad: '',
    denominacion_resultado_pad: '',
    codigo_producto_pad: '',
    denominacion_producto_pad: '',
    codigo_entidad: '',
    codigo_resultado_pei: '',
    denominacion_resultado_pei: '',
    codigo_producto_pei: '',
    denominacion_producto_pei: '',
    tipo_contribucion: '',
    ponderacion: null,
    indicador: '',
    formula: '',
    unidad_medida: '',
    linea_base: null,
    meta_2030: null,
    fuente_indicador: '',
    pf_2026: null, pf_2027: null, pf_2028: null, pf_2029: null, pf_2030: null,
    inversion_2026: null, inversion_2027: null, inversion_2028: null,
    inversion_2029: null, inversion_2030: null, inversion_2031: null,
    corriente_2026: null, corriente_2027: null, corriente_2028: null,
    corriente_2029: null, corriente_2030: null, corriente_2031: null,
  };

  constructor(private api: ApiService, private router: Router) {}

  ngOnInit(): void {
    this.cargarODS();
  }

  private cargarODS(): void {
    this.api.get<any>('/articulacion/acuerdos/', { tipo_acuerdo: 'ODS' }).subscribe({
      next: (r) => { this.catalogoODS = r.results || r || []; },
      error: () => {
        // Catálogo hardcodeado si falla API
        this.catalogoODS = [
          { id: 1, codigo: 'ODS 1', nombre: 'Fin de la Pobreza' },
          { id: 2, codigo: 'ODS 2', nombre: 'Hambre Cero' },
          { id: 3, codigo: 'ODS 3', nombre: 'Salud y Bienestar' },
          { id: 4, codigo: 'ODS 4', nombre: 'Educación de Calidad' },
          { id: 5, codigo: 'ODS 5', nombre: 'Igualdad de Género' },
          { id: 6, codigo: 'ODS 6', nombre: 'Agua Limpia y Saneamiento' },
          { id: 7, codigo: 'ODS 7', nombre: 'Energía Asequible y No Contaminante' },
          { id: 8, codigo: 'ODS 8', nombre: 'Trabajo Decente y Crecimiento Económico' },
          { id: 9, codigo: 'ODS 9', nombre: 'Industria, Innovación e Infraestructura' },
          { id: 10, codigo: 'ODS 10', nombre: 'Reducción de las Desigualdades' },
          { id: 11, codigo: 'ODS 11', nombre: 'Ciudades y Comunidades Sostenibles' },
          { id: 12, codigo: 'ODS 12', nombre: 'Producción y Consumo Responsables' },
          { id: 13, codigo: 'ODS 13', nombre: 'Acción por el Clima' },
          { id: 14, codigo: 'ODS 14', nombre: 'Vida Submarina' },
          { id: 15, codigo: 'ODS 15', nombre: 'Vida de Ecosistemas Terrestres' },
          { id: 16, codigo: 'ODS 16', nombre: 'Paz, Justicia e Instituciones Sólidas' },
          { id: 17, codigo: 'ODS 17', nombre: 'Alianzas para Lograr los Objetivos' },
        ];
      },
    });
  }

  toggleODS(odsId: number): void {
    const idx = this.form.ods_seleccionados.indexOf(odsId);
    if (idx >= 0) {
      this.form.ods_seleccionados.splice(idx, 1);
    } else {
      this.form.ods_seleccionados.push(odsId);
    }
  }

  irAPaso(paso: number): void {
    if (paso >= 1 && paso <= 10) {
      this.pasoActual = paso;
      this.mensajeError = '';
      this.mensajeExito = '';
    }
  }

  pasoAnterior(): void {
    if (this.pasoActual > 1) {
      this.pasoActual--;
      this.mensajeError = '';
      this.mensajeExito = '';
    }
  }

  pasoSiguiente(): void {
    if (this.validarPasoActual()) {
      this.pasoActual++;
      this.mensajeError = '';
    }
  }

  private validarPasoActual(): boolean {
    this.mensajeError = '';
    // Validaciones básicas por paso
    if (this.pasoActual === 4) {
      if (!this.form.codigo_resultado_pad || !this.form.denominacion_resultado_pad) {
        this.mensajeError = 'Debe completar los datos del Resultado PAD.';
        return false;
      }
      if (!this.form.codigo_producto_pad || !this.form.denominacion_producto_pad) {
        this.mensajeError = 'Debe completar los datos del Producto PAD.';
        return false;
      }
    }
    if (this.pasoActual === 5) {
      if (!this.form.codigo_resultado_pei || !this.form.denominacion_resultado_pei) {
        this.mensajeError = 'Debe completar los datos del Resultado PEI.';
        return false;
      }
      if (!this.form.codigo_producto_pei || !this.form.denominacion_producto_pei) {
        this.mensajeError = 'Debe completar los datos del Producto PEI.';
        return false;
      }
    }
    return true;
  }

  guardarTodo(): void {
    this.guardando = true;
    this.mensajeError = '';
    this.mensajeExito = '';

    // 1. Crear Resultado PAD
    this.api.post<any>('/articulacion/resultados-pad/', {
      codigo_resultado: this.form.codigo_resultado_pad,
      denominacion: this.form.denominacion_resultado_pad,
      codigo_geografico: this.form.codigo_geografico,
      eta: this.form.eta,
      sector: this.form.sector,
      codigo_resultado_pds: this.form.codigo_resultado_pds,
      nombre_resultado_pds: this.form.nombre_resultado_pds,
      eje_pgdesa: this.form.eje_pgdesa,
      componente_pdesa: this.form.componente_pdesa,
      objetivo_impacto: this.form.objetivo_impacto,
      efecto: this.form.efecto,
      ndc: this.form.ndc,
      ndt: this.form.ndt,
      meta_3030: this.form.meta_3030,
    }).subscribe({
      next: (resPad) => {
        const resultadoPadId = resPad.id || resPad;

        // 2. Crear Producto PAD vinculado
        this.api.post<any>('/articulacion/productos-pad/', {
          codigo_producto: this.form.codigo_producto_pad,
          denominacion: this.form.denominacion_producto_pad,
          resultado_pad: resultadoPadId,
        }).subscribe({
          next: (prodPad) => {
            const productoPadId = prodPad.id || prodPad;

            // 3. Crear Resultado PEI
            this.api.post<any>('/articulacion/resultados-pei/', {
              codigo_resultado: this.form.codigo_resultado_pei,
              denominacion: this.form.denominacion_resultado_pei,
              codigo_entidad: this.form.codigo_entidad,
            }).subscribe({
              next: (resPei) => {
                const resultadoPeiId = resPei.id || resPei;

                // 4. Crear Producto PEI vinculado
                this.api.post<any>('/articulacion/productos-pei/', {
                  codigo_producto: this.form.codigo_producto_pei,
                  denominacion: this.form.denominacion_producto_pei,
                  resultado_pei: resultadoPeiId,
                }).subscribe({
                  next: (prodPei) => {
                    const productoPeiId = prodPei.id || prodPei;

                    // 5. Crear Articulación PAD→PEI
                    this.api.post<any>('/articulacion/articulaciones-pad-pei/', {
                      producto_pad: productoPadId,
                      producto_pei: productoPeiId,
                      tipo_contribucion: this.form.tipo_contribucion,
                      ponderacion: this.form.ponderacion,
                      estado: 'REFERENCIAL',
                    }).subscribe({
                      next: (art) => {
                        const articulacionId = art.id || art;

                        // 6. Crear Indicador
                        this.api.post<any>('/articulacion/indicadores/', {
                          indicador: this.form.indicador,
                          formula: this.form.formula,
                          unidad_medida: this.form.unidad_medida,
                          linea_base: this.form.linea_base,
                          meta_2030: this.form.meta_2030,
                          fuente: this.form.fuente_indicador,
                          articulacion_pad_pei: articulacionId,
                        }).subscribe({
                          next: () => {
                            this.mensajeExito = '✅ Articulación PAD→PEI creada exitosamente. Redirigiendo...';
                            this.guardando = false;
                            setTimeout(() => this.router.navigate(['/articulacion/pad-pei']), 2000);
                          },
                          error: (err) => { this.onError(err, 'Error al crear el indicador'); },
                        });
                      },
                      error: (err) => { this.onError(err, 'Error al crear la articulación'); },
                    });
                  },
                  error: (err) => { this.onError(err, 'Error al crear el producto PEI'); },
                });
              },
              error: (err) => { this.onError(err, 'Error al crear el resultado PEI'); },
            });
          },
          error: (err) => { this.onError(err, 'Error al crear el producto PAD'); },
        });
      },
      error: (err) => { this.onError(err, 'Error al crear el resultado PAD'); },
    });
  }

  private onError(err: any, msg: string): void {
    console.error(msg, err);
    this.mensajeError = `❌ ${msg}. Verifique los datos e intente nuevamente.`;
    this.guardando = false;
  }
}

import { Component, OnInit } from '@angular/core';
import { ApiService } from '../../core/services/api.service';
import { Router } from '@angular/router';

@Component({
  selector: 'app-articulacion-form-m5',
  standalone: false,
  template: `
    <div class="form-page">
      <div class="page-header">
        <h2>Nueva Asignación de Objeto de Gasto</h2>
        <p class="text-secondary">Asigne un objeto de gasto a una actividad</p>
      </div>
    
      @if (mensajeExito) {
        <div class="alert alert-success">{{ mensajeExito }}</div>
      }
      @if (mensajeError) {
        <div class="alert alert-danger">{{ mensajeError }}</div>
      }
    
      <div class="card form-card">
        <h3 class="step-title">Datos de la Asignación</h3>
    
        <div class="form-grid">
          <!-- Actividad -->
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
            <label>Código Asignación</label>
            <input [(ngModel)]="form.codigo_asignacion" class="form-control" placeholder="Ej: ASIG-001">
          </div>
    
          <!-- Objeto de Gasto -->
          <div class="field-full">
            <label>Objeto de Gasto *</label>
            <div class="search-select">
              <input [(ngModel)]="busquedaObjeto" class="form-control" placeholder="Buscar objeto de gasto..."
                (input)="filtrarObjetos()" (focus)="filtrarObjetos()">
                @if (busquedaObjeto && objetosFiltrados.length > 0) {
                  <div class="search-results">
                    @for (obj of objetosFiltrados; track obj) {
                      <div class="search-item" (click)="seleccionarObjeto(obj)">
                        <span class="obj-codigo">{{ obj.codigo || obj.cod_objeto_gasto }}</span>
                        <span class="obj-desc">{{ obj.descripcion || obj.denominacion }}</span>
                      </div>
                    }
                  </div>
                }
                @if (busquedaObjeto && objetosFiltrados.length === 0 && objetosCargados) {
                  <div class="search-results empty">
                    Sin resultados
                  </div>
                }
              </div>
              @if (objetoSeleccionado) {
                <div class="selected-objeto">
                  <span class="badge badge-success">{{ objetoSeleccionado.codigo || objetoSeleccionado.cod_objeto_gasto }}</span>
                  <span>{{ objetoSeleccionado.descripcion || objetoSeleccionado.denominacion }}</span>
                  <button class="btn btn-xs btn-outline" (click)="limpiarObjeto()">✕</button>
                </div>
              }
            </div>
    
            <!-- Grupo y Tipo -->
            <div class="field">
              <label>Grupo de Gasto</label>
              <select [(ngModel)]="form.grupo_gasto" class="form-control">
                <option value="">Seleccionar...</option>
                <option value="SERVICIOS_PERSONALES">Servicios Personales</option>
                <option value="SERVICIOS_NO_PERSONALES">Servicios No Personales</option>
                <option value="MATERIALES Y SUMINISTROS">Materiales y Suministros</option>
                <option value="ACTIVOS_REALES">Activos Reales</option>
                <option value="TRANSFERENCIAS">Transferencias</option>
                <option value="DEUDA">Deuda</option>
              </select>
            </div>
            <div class="field">
              <label>Tipo de Gasto</label>
              <select [(ngModel)]="form.tipo_gasto" class="form-control">
                <option value="">Seleccionar...</option>
                <option value="CORRIENTE">Corriente</option>
                <option value="INVERSION">Inversión</option>
              </select>
            </div>
    
            <!-- Fuente y Organismo -->
            <div class="field">
              <label>Fuente de Financiamiento</label>
              <select [(ngModel)]="form.fuente_financiamiento" class="form-control">
                <option value="">Seleccionar...</option>
                <option value="TGN">TGN - Tesoro General de la Nación</option>
                <option value="HIPC">HIPC - Alivio Deuda</option>
                <option value="IDH">IDH - Impuesto Directo Hidrocarburos</option>
                <option value="RECURSOS_PROPIOS">Recursos Propios</option>
                <option value="DONACION">Donación</option>
                <option value="CREDITO">Crédito</option>
              </select>
            </div>
            <div class="field">
              <label>Organismo Financiador</label>
              <input [(ngModel)]="form.organismo_financiador" class="form-control" placeholder="Ej: Gobierno Municipal">
            </div>
    
            <!-- Monto -->
            <div class="field">
              <label>Monto Programado (Bs.) *</label>
              <input type="number" step="0.01" [(ngModel)]="form.monto_programado" class="form-control" placeholder="0.00">
            </div>
            <div class="field">
              <label>Monto Vigente (Bs.)</label>
              <input type="number" step="0.01" [(ngModel)]="form.monto_vigente" class="form-control" placeholder="0.00">
            </div>
    
            <!-- Justificación y Memoria -->
            <div class="field-full">
              <label>Justificación</label>
              <textarea [(ngModel)]="form.justificacion" class="form-control" rows="2" placeholder="Justificación de la asignación"></textarea>
            </div>
            <div class="field-full">
              <label>Memoria de Cálculo</label>
              <textarea [(ngModel)]="form.memoria_calculo" class="form-control" rows="3" placeholder="Detalle del cálculo del monto programado"></textarea>
            </div>
          </div>
    
          <div class="form-nav">
            <button class="btn btn-outline" (click)="cancelar()">← Cancelar</button>
            <button class="btn btn-primary btn-guardar" (click)="guardar()" [disabled]="guardando">
              {{ guardando ? 'Guardando...' : '💾 Guardar Asignación' }}
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

    .form-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 0.75rem; }
    .field-full { grid-column: 1 / -1; }
    .field label { display: block; font-size: 0.6875rem; font-weight: 600; color: var(--text-secondary); margin-bottom: 0.25rem; }
    .field { min-width: 0; }

    .search-select { position: relative; }
    .search-results {
      position: absolute; top: 100%; left: 0; right: 0; z-index: 100;
      background: white; border: 1px solid var(--border);
      border-radius: 0 0 6px 6px; max-height: 200px; overflow-y: auto;
      box-shadow: 0 4px 12px rgba(0,0,0,0.1);
    }
    .search-results.empty { padding: 0.5rem 0.75rem; color: var(--text-secondary); font-size: 0.75rem; }
    .search-item {
      display: flex; align-items: center; gap: 0.5rem;
      padding: 0.5rem 0.75rem; cursor: pointer; font-size: 0.75rem;
      border-bottom: 1px solid var(--border);
    }
    .search-item:last-child { border-bottom: none; }
    .search-item:hover { background: #F0F7F3; }
    .obj-codigo { font-family: 'Courier New', monospace; font-weight: 600; font-size: 0.6875rem; color: var(--primary); white-space: nowrap; }
    .obj-desc { color: var(--text-secondary); }

    .selected-objeto { display: flex; align-items: center; gap: 0.5rem; margin-top: 0.5rem; padding: 0.5rem; background: #E8F5E9; border-radius: 6px; font-size: 0.8125rem; }
    .btn-xs { font-size: 0.6875rem; padding: 0.125rem 0.375rem; margin-left: auto; }
    .btn-outline { background: transparent; border: 1px solid var(--border); color: var(--text); }
    .btn-outline:hover { border-color: var(--primary); color: var(--primary); }

    .form-nav { display: flex; align-items: center; justify-content: space-between; margin-top: 1.5rem; padding-top: 1rem; border-top: 1px solid var(--border); }
    .btn-guardar { background: var(--success); }
    .btn-guardar:hover { background: #1B5E3B; }

    .alert { padding: 0.75rem 1rem; border-radius: 6px; font-size: 0.8125rem; margin-bottom: 1rem; }
    .alert-success { background: #E8F5E9; color: #1B5E3B; border: 1px solid #A5D6A7; }
    .alert-danger { background: #FFEBEE; color: #C62828; border: 1px solid #EF9A9A; }

    @media (max-width: 768px) {
      .form-grid { grid-template-columns: 1fr; }
    }
  `],
})
export class ArticulacionFormM5Component implements OnInit {
  guardando = false;
  mensajeExito = '';
  mensajeError = '';
  gestiones: number[] = [];
  actividades: any[] = [];
  objetosGasto: any[] = [];
  objetosFiltrados: any[] = [];
  objetosCargados = false;
  busquedaObjeto = '';
  objetoSeleccionado: any = null;

  form: any = {
    actividad: '',
    gestion: null,
    codigo_asignacion: '',
    cod_objeto_gasto: '',
    descripcion_objeto: '',
    grupo_gasto: '',
    tipo_gasto: '',
    fuente_financiamiento: '',
    organismo_financiador: '',
    monto_programado: null,
    monto_vigente: null,
    justificacion: '',
    memoria_calculo: '',
    estado: 'REFERENCIAL',
  };

  constructor(private api: ApiService, private router: Router) {}

  ngOnInit(): void {
    this.cargarCatalogos();
  }

  private cargarCatalogos(): void {
    // Cargar actividades
    this.api.get<any>('/articulacion/actividades/').subscribe({
      next: (r) => {
        const acts = r.results || r || [];
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

    // Cargar objetos de gasto — intentar desde catálogo
    this.api.get<any>('/articulacion/acuerdos/').subscribe({
      next: (r) => {
        // Este endpoint podría no tener objetos de gasto, es un intento
        this.objetosCargados = true;
      },
      error: () => { this.objetosCargados = true; },
    });

    // Objetos de gasto hardcodeados como fallback
    this.objetosGasto = [
      { codigo: '11100', descripcion: 'Sueldos y Salarios del Personal Permanente' },
      { codigo: '11200', descripcion: 'Sueldos y Salarios del Personal Eventual' },
      { codigo: '11300', descripcion: 'Sueldos y Salarios del Personal a Contrato' },
      { codigo: '12100', descripcion: 'Aportes Patronales a la Seguridad Social' },
      { codigo: '21100', descripcion: 'Energía Eléctrica' },
      { codigo: '21200', descripcion: 'Agua y Alcantarillado' },
      { codigo: '21300', descripcion: 'Telecomunicaciones' },
      { codigo: '21400', descripcion: 'Servicio de Imprenta y Publicaciones' },
      { codigo: '21500', descripcion: 'Servicio de Aseo y Limpieza' },
      { codigo: '21600', descripcion: 'Servicio de Vigilancia y Seguridad' },
      { codigo: '21700', descripcion: 'Pasajes y Viáticos' },
      { codigo: '21800', descripcion: 'Combustibles y Lubricantes' },
      { codigo: '22100', descripcion: 'Material de Escritorio y Oficina' },
      { codigo: '22200', descripcion: 'Material de Limpieza' },
      { codigo: '22300', descripcion: 'Material de Construcción' },
      { codigo: '23100', descripcion: 'Alimentos y Bebidas' },
      { codigo: '24100', descripcion: 'Medicamentos y Productos Farmacéuticos' },
      { codigo: '31100', descripcion: 'Maquinaria y Equipo en General' },
      { codigo: '31200', descripcion: 'Equipo de Transporte' },
      { codigo: '31300', descripcion: 'Equipo de Computación' },
      { codigo: '31400', descripcion: 'Muebles y Enseres' },
      { codigo: '32100', descripcion: 'Bienes Inmuebles' },
      { codigo: '33100', descripcion: 'Activos Intangibles' },
      { codigo: '41100', descripcion: 'Transferencias Corrientes al Sector Privado' },
      { codigo: '41200', descripcion: 'Transferencias Corrientes al Sector Público' },
      { codigo: '42100', descripcion: 'Transferencias de Capital' },
    ];
    this.objetosCargados = true;
  }

  private buildMap(list: any[], key: string): Map<string, any> {
    const m = new Map<string, any>();
    (list || []).forEach((item: any) => m.set(item[key], item));
    return m;
  }

  filtrarObjetos(): void {
    const q = this.busquedaObjeto.toLowerCase().trim();
    if (!q) {
      this.objetosFiltrados = [];
      return;
    }
    this.objetosFiltrados = this.objetosGasto.filter(
      (o) =>
        o.codigo.toLowerCase().includes(q) ||
        o.descripcion.toLowerCase().includes(q)
    ).slice(0, 15);
  }

  seleccionarObjeto(obj: any): void {
    this.objetoSeleccionado = obj;
    this.form.cod_objeto_gasto = obj.codigo;
    this.form.descripcion_objeto = obj.descripcion;
    this.busquedaObjeto = `${obj.codigo} — ${obj.descripcion}`;
    this.objetosFiltrados = [];
  }

  limpiarObjeto(): void {
    this.objetoSeleccionado = null;
    this.form.cod_objeto_gasto = '';
    this.form.descripcion_objeto = '';
    this.busquedaObjeto = '';
    this.objetosFiltrados = [];
  }

  cancelar(): void {
    this.router.navigate(['/articulacion/objetos-gasto']);
  }

  guardar(): void {
    if (!this.validar()) return;

    this.guardando = true;
    this.mensajeError = '';

    this.api.post<any>('/articulacion/asignaciones-gasto/', this.form).subscribe({
      next: () => {
        this.mensajeExito = '✅ Asignación de objeto de gasto creada exitosamente. Redirigiendo...';
        this.guardando = false;
        setTimeout(() => this.router.navigate(['/articulacion/objetos-gasto']), 2000);
      },
      error: (err) => {
        console.error('Error al crear asignación', err);
        this.mensajeError = '❌ Error al guardar la asignación. Verifique los datos.';
        this.guardando = false;
      },
    });
  }

  private validar(): boolean {
    this.mensajeError = '';
    if (!this.form.actividad) { this.mensajeError = 'Debe seleccionar una actividad.'; return false; }
    if (!this.form.gestion) { this.mensajeError = 'Debe seleccionar la gestión.'; return false; }
    if (!this.form.cod_objeto_gasto) { this.mensajeError = 'Debe seleccionar un objeto de gasto.'; return false; }
    if (!this.form.monto_programado || this.form.monto_programado <= 0) {
      this.mensajeError = 'Debe ingresar un monto programado válido mayor a 0.';
      return false;
    }
    return true;
  }
}

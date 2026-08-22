import { Component, OnInit } from '@angular/core';
import { BudgetService, CategoriaProgramaticaTecho, CategoriaNodo } from './budget.service';
import { GestionHabilitadaService } from '../../../core/services/gestion-habilitada.service';

@Component({
  standalone: false,
  selector: 'app-programmatic-categories',
  template: `
    <div class="page-header">
      <h2>Categorías Programáticas</h2>
      <div class="page-header-actions">
        <span class="pastilla-gestion">Gestión {{ gestionAnio }}</span>
        <button class="btn btn-primary" (click)="mostrarFormulario = !mostrarFormulario">
          {{ mostrarFormulario ? 'Cancelar' : 'Nueva categoría' }}
        </button>
      </div>
    </div>
    
    @if (mostrarFormulario) {
      <div class="card">
        <div class="card-body">
          <h4>Nueva categoría</h4>
          <div class="form-row">
            <div class="form-group">
              <label>Código</label>
              <input class="form-control" [(ngModel)]="nueva.codigo" placeholder="097" />
            </div>
            <div class="form-group">
              <label>Denominación</label>
              <input class="form-control" [(ngModel)]="nueva.denominacion" />
            </div>
            <div class="form-group">
              <label>Nivel</label>
              <select class="form-control" [(ngModel)]="nueva.nivel">
                <option value="PROGRAMA">Programa</option>
                <option value="SUBPROGRAMA">Subprograma</option>
                <option value="PROYECTO">Proyecto</option>
                <option value="ACTIVIDAD">Actividad</option>
              </select>
            </div>
            <div class="form-group">
              <label>Padre</label>
              <select class="form-control" [(ngModel)]="nueva.parent">
                <option [ngValue]="null">— raíz —</option>
                @for (c of categorias; track c) {
                  <option [ngValue]="c.id">{{ c.codigo_compuesto }} — {{ c.denominacion }}</option>
                }
              </select>
            </div>
            <div class="form-group">
              <button class="btn btn-primary" (click)="crear()" [disabled]="guardando">Guardar</button>
            </div>
          </div>
          @if (error) {
            <div class="alert-error">{{ error }}</div>
          }
        </div>
      </div>
    }
    
    <div class="card">
      <div class="card-body">
        @if (cargando) {
          <div class="loading">Cargando…</div>
        }
        @if (!cargando && categorias.length === 0) {
          <div class="empty">Sin categorías para esta gestión.</div>
        }
        @if (!cargando && categorias.length > 0) {
          <table class="data-table">
            <thead>
              <tr>
                <th>Código compuesto</th>
                <th>Denominación</th>
                <th>Nivel</th>
                <th>Estado</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              @for (c of categorias; track c) {
                <tr>
                  <td>{{ c.codigo_compuesto }}</td>
                  <td>{{ c.denominacion }}</td>
                  <td><span class="badge badge-info">{{ c.nivel_display }}</span></td>
                  <td><span class="badge" [ngClass]="c.estado === 'ACTIVA' ? 'badge-success' : 'badge-warning'">{{ c.estado }}</span></td>
                  <td>
                    <button class="btn btn-sm" title="Duplicar a otra gestión" (click)="duplicar(c)">⧉</button>
                  </td>
                </tr>
              }
            </tbody>
          </table>
        }
      </div>
    </div>
    `,
})
export class ProgrammaticCategoriesComponent implements OnInit {
  /** Id de la gestión habilitada. Era `Number(g.id)` sobre un UUID: NaN. */
  gestionSeleccionada: string | null = null;
  categorias: CategoriaProgramaticaTecho[] = [];
  cargando = false;
  guardando = false;
  mostrarFormulario = false;
  error = '';

  nueva = { codigo: '', denominacion: '', nivel: 'PROGRAMA', parent: null as number | null };

  constructor(private budget: BudgetService,
              private gestionActiva: GestionHabilitadaService) {}

  ngOnInit(): void {
    // El catálogo programático es de la gestión habilitada (ADR-007). El
    // selector anterior hacía `Number(g.id)` sobre un UUID y mandaba NaN.
    const habilitada = this.gestionActiva.gestion();
    if (!habilitada) {
      this.error = 'No hay una gestión fiscal habilitada.';
      return;
    }
    this.cargar(habilitada.id);
  }

  /** Año de la gestión habilitada, para el encabezado. */
  get gestionAnio(): number | null {
    return this.gestionActiva.anio();
  }

  cargar(gestionId: string): void {
    this.gestionSeleccionada = gestionId;
    this.cargando = true;
    this.error = '';
    this.budget.listarCategorias({ gestion: gestionId }).subscribe({
      next: (res) => {
        this.categorias = res.results;
        this.cargando = false;
      },
      error: (e) => {
        this.error = e?.error?.error?.detail ?? 'Error cargando categorías';
        this.cargando = false;
      },
    });
  }

  crear(): void {
    if (!this.gestionSeleccionada || !this.nueva.codigo || !this.nueva.denominacion) {
      this.error = 'Código y denominación son obligatorios.';
      return;
    }
    this.guardando = true;
    this.error = '';
    this.budget.crearCategoria({
      gestion: this.gestionSeleccionada,
      codigo: this.nueva.codigo,
      denominacion: this.nueva.denominacion,
      nivel: this.nueva.nivel,
      parent: this.nueva.parent,
    }).subscribe({
      next: () => {
        this.guardando = false;
        this.mostrarFormulario = false;
        this.nueva = { codigo: '', denominacion: '', nivel: 'PROGRAMA', parent: null };
        this.cargar(this.gestionSeleccionada!);
      },
      error: (e) => {
        this.guardando = false;
        const detail = e?.error?.error?.detail;
        this.error = Array.isArray(detail) ? detail.join(', ') : (detail ?? 'Error al crear');
      },
    });
  }

  /**
   * Duplica la categoría a otra gestión.
   *
   * Es la excepción deliberada al candado: así se siembra el catálogo de la
   * gestión SIGUIENTE antes de habilitarla. La gestión destino se resuelve
   * contra la API en vez de contra una lista local, que era lo único que
   * seguía obligando a esta pantalla a traerse todas las gestiones.
   */
  duplicar(c: CategoriaProgramaticaTecho): void {
    const destino = prompt('Gestión destino (año):', '');
    if (!destino) return;
    const anio = Number(destino);
    if (!Number.isInteger(anio)) {
      this.error = `«${destino}» no es un año válido.`;
      return;
    }
    this.budget.listar({ anio }).subscribe({
      next: (res) => {
        const gestionDestino = res.results[0]?.id;
        if (!gestionDestino) {
          this.error = `No existe gestión ${destino}.`;
          return;
        }
        this.budget.duplicarCategoria(c.id, gestionDestino).subscribe({
          next: () => this.cargar(this.gestionSeleccionada!),
          error: (e) => (this.error = e?.error?.error?.detail ?? 'Error al duplicar'),
        });
      },
      error: () => (this.error = `No se pudo resolver la gestión ${destino}.`),
    });
  }
}

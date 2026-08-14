import { Component, OnInit } from '@angular/core';
import { BudgetService, ProgrammaticCategory, CategoriaNodo } from './budget.service';

@Component({
  standalone: false,
  selector: 'app-programmatic-categories',
  template: `
    <div class="page-header">
      <h2>Categorías Programáticas</h2>
      <div class="page-header-actions">
        <select class="form-control" [ngModel]="gestionSeleccionada" (ngModelChange)="cargar($event)" style="width:auto">
          <option [ngValue]="g.id" *ngFor="let g of gestiones">{{ g.anio }}</option>
        </select>
        <button class="btn btn-primary" (click)="mostrarFormulario = !mostrarFormulario">
          {{ mostrarFormulario ? 'Cancelar' : 'Nueva categoría' }}
        </button>
      </div>
    </div>

    <div class="card" *ngIf="mostrarFormulario">
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
              <option [ngValue]="c.id" *ngFor="let c of categorias">{{ c.codigo_compuesto }} — {{ c.denominacion }}</option>
            </select>
          </div>
          <div class="form-group">
            <button class="btn btn-primary" (click)="crear()" [disabled]="guardando">Guardar</button>
          </div>
        </div>
        <div class="alert-error" *ngIf="error">{{ error }}</div>
      </div>
    </div>

    <div class="card">
      <div class="card-body">
        <div class="loading" *ngIf="cargando">Cargando…</div>
        <div class="empty" *ngIf="!cargando && categorias.length === 0">Sin categorías para esta gestión.</div>
        <table class="data-table" *ngIf="!cargando && categorias.length > 0">
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
            <tr *ngFor="let c of categorias">
              <td>{{ c.codigo_compuesto }}</td>
              <td>{{ c.denominacion }}</td>
              <td><span class="badge badge-info">{{ c.nivel_display }}</span></td>
              <td><span class="badge" [ngClass]="c.estado === 'ACTIVA' ? 'badge-success' : 'badge-warning'">{{ c.estado }}</span></td>
              <td>
                <button class="btn btn-sm" title="Duplicar a otra gestión" (click)="duplicar(c)">⧉</button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  `,
})
export class ProgrammaticCategoriesComponent implements OnInit {
  gestiones: { id: number; anio: number }[] = [];
  gestionSeleccionada: number | null = null;
  categorias: ProgrammaticCategory[] = [];
  cargando = false;
  guardando = false;
  mostrarFormulario = false;
  error = '';

  nueva = { codigo: '', denominacion: '', nivel: 'PROGRAMA', parent: null as number | null };

  constructor(private budget: BudgetService) {}

  ngOnInit(): void {
    this.budget.listar({}).subscribe((res) => {
      this.gestiones = res.results.map((g) => ({ id: Number(g.id), anio: g.anio }));
      if (this.gestiones.length) {
        this.gestionSeleccionada = this.gestiones[0].id;
        this.cargar(this.gestionSeleccionada);
      }
    });
  }

  cargar(gestionId: number): void {
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

  duplicar(c: ProgrammaticCategory): void {
    const destino = prompt('Gestión destino (año):', '');
    if (!destino) return;
    const gestionDestino = this.gestiones.find((g) => String(g.anio) === destino)?.id;
    if (!gestionDestino) {
      this.error = `No existe gestión ${destino}.`;
      return;
    }
    this.budget.duplicarCategoria(c.id, gestionDestino).subscribe({
      next: () => this.cargar(this.gestionSeleccionada!),
      error: (e) => (this.error = e?.error?.error?.detail ?? 'Error al duplicar'),
    });
  }
}

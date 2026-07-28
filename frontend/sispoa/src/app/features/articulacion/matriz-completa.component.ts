import { Component, OnInit, ViewChild, ChangeDetectionStrategy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import {
  MatrizCompletaService,
  NodoArbol,
  MatrizResponse,
} from './matriz-completa.service';
import { MatrizCompletaTreeComponent } from './matriz-completa-tree.component';

@Component({
  selector: 'app-matriz-completa',
  standalone: true,
  imports: [CommonModule, FormsModule, MatrizCompletaTreeComponent],
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <div class="matriz-page">
      <div class="page-header">
        <h2>Matriz de Articulación Completa</h2>
        <p class="text-secondary">
          Cadena PGDESA → PDESA → PAD → PEI → POA
        </p>
      </div>

      <!-- Filters & controls -->
      <div class="card filtros-card">
        <div class="filtros">
          <div class="field">
            <label>Gestión</label>
            <select
              [(ngModel)]="gestion"
              class="form-control"
              (change)="cargarArbol()"
            >
              <option *ngFor="let g of gestionesDisponibles" [value]="g">{{ g }}</option>
            </select>
          </div>
          <div class="field">
            <label>&nbsp;</label>
            <button
              class="btn btn-sm btn-outline-secondary"
              (click)="toggleTodos()"
            >
              {{ todosExpandidos ? '🔽 Colapsar todo' : '▶ Expandir todo' }}
            </button>
          </div>
          <div class="field stats" *ngIf="!cargando && !error && totalNodos > 0">
            <label>&nbsp;</label>
            <span class="badge badge-info">{{ totalNodos }} nodos en la gestión</span>
          </div>
          <div class="field export-field">
            <label>&nbsp;</label>
            <button class="btn btn-sm btn-outline-success" (click)="exportarXLSX()">
              ⬇ Exportar XLSX
            </button>
          </div>
        </div>
      </div>

      <!-- Loading state -->
      <div *ngIf="cargando" class="card estado-card">
        <div class="estado-content">
          <div class="spinner"></div>
          <span>Cargando árbol de articulación completa...</span>
        </div>
      </div>

      <!-- Error state -->
      <div *ngIf="!cargando && error" class="card estado-card error">
        <div class="estado-content">
          <span class="error-icon">⚠</span>
          <div>
            <strong>Error al cargar datos</strong>
            <p class="error-detail">{{ errorMensaje }}</p>
            <button class="btn btn-sm btn-primary" (click)="cargarArbol()">Reintentar</button>
          </div>
        </div>
      </div>

      <!-- Empty state -->
      <div
        *ngIf="!cargando && !error && (!arbolData || arbolData.length === 0)"
        class="card estado-card"
      >
        <div class="estado-content">
          <span>No se encontraron nodos de planificación para la gestión {{ gestion }}</span>
        </div>
      </div>

      <!-- Tree -->
      <div *ngIf="!cargando && !error && arbolData && arbolData.length > 0" class="card table-card">
        <div class="table-scroll">
          <app-matriz-completa-tree
            #treeComponent
            [nodos]="arbolData"
            [level]="0"
            [resultadosPad]="resultadosPad"
            (bridgeUpdated)="onBridgeUpdated()"
          ></app-matriz-completa-tree>
        </div>
      </div>
    </div>
  `,
  styles: [
    `
    .matriz-page { padding-bottom: 2rem; }
    .page-header { margin-bottom: 1rem; }
    .page-header h2 { font-size: 1.25rem; color: var(--primary); margin-bottom: 0.25rem; }
    .text-secondary { color: var(--text-secondary); font-size: 0.8125rem; }

    .filtros-card { padding: 1rem; margin-bottom: 1rem; }
    .filtros { display: flex; gap: 1rem; align-items: flex-end; flex-wrap: wrap; }
    .filtros .field { min-width: 140px; }
    .filtros .field label { display: block; font-size: 0.6875rem; font-weight: 600; color: var(--text-secondary); margin-bottom: 0.25rem; }
    .filtros .field.stats { min-width: auto; }
    .export-field { margin-left: auto; }

    .estado-card {
      padding: 2rem;
      text-align: center;
      margin-bottom: 1rem;
    }
    .estado-content {
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 0.75rem;
      font-size: 0.875rem;
      color: var(--text-secondary);
    }
    .estado-card.error .estado-content {
      color: #C62828;
    }
    .error-icon { font-size: 1.5rem; }
    .error-detail {
      font-size: 0.75rem;
      margin: 0.25rem 0 0.5rem;
      color: var(--text-secondary);
    }

    .spinner {
      width: 20px;
      height: 20px;
      border: 2px solid var(--border);
      border-top-color: var(--primary);
      border-radius: 50%;
      animation: spin 0.6s linear infinite;
    }
    @keyframes spin { to { transform: rotate(360deg); } }

    .table-card { padding: 0; overflow: hidden; }
    .table-scroll { overflow-x: auto; }

    .badge { font-size: 0.6875rem; }
    .btn-outline-success {
      border: 1px solid var(--primary);
      color: var(--primary);
      background: transparent;
      padding: 0.375rem 0.75rem;
      border-radius: 4px;
      cursor: pointer;
      font-size: 0.75rem;
    }
    .btn-outline-success:hover { background: var(--primary); color: white; }
    .btn-outline-secondary {
      border: 1px solid var(--border);
      color: var(--text-secondary);
      background: transparent;
      padding: 0.375rem 0.75rem;
      border-radius: 4px;
      cursor: pointer;
      font-size: 0.75rem;
    }
    .btn-outline-secondary:hover { background: #f0f0f0; color: var(--text); }
  `],
})
export class MatrizCompletaComponent implements OnInit {
  @ViewChild('treeComponent')
  treeComponent?: MatrizCompletaTreeComponent;

  gestion = 2026;
  gestionesDisponibles: number[] = [2026, 2027];
  cargando = true;
  error = false;
  errorMensaje = '';
  arbolData: NodoArbol[] = [];
  resultadosPad: any[] = [];
  totalNodos = 0;
  todosExpandidos = false;

  constructor(private service: MatrizCompletaService) {}

  ngOnInit(): void {
    this.cargarArbol();
  }

  cargarArbol(): void {
    this.cargando = true;
    this.error = false;
    this.errorMensaje = '';
    this.arbolData = [];
    this.totalNodos = 0;

    this.service.getArbol(this.gestion).subscribe({
      next: (res: MatrizResponse) => {
        this.arbolData = res.data || [];
        this.totalNodos = res.stats?.total || 0;
        this.cargando = false;
        this.cargarResultadosPAD();
      },
      error: (err) => {
        this.cargando = false;
        this.error = true;
        this.errorMensaje =
          err.status === 0
            ? 'No se puede conectar con el servidor'
            : err.status === 404
              ? 'Endpoint no encontrado'
              : err.status === 500
                ? 'Error interno del servidor'
                : `Error ${err.status || 'desconocido'}`;
      },
    });
  }

  private cargarResultadosPAD(): void {
    this.service.getResultadosPAD(this.gestion).subscribe({
      next: (res) => {
        this.resultadosPad = res.results || res || [];
      },
      error: () => {
        this.resultadosPad = [];
      },
    });
  }

  toggleTodos(): void {
    this.todosExpandidos = !this.todosExpandidos;
    if (this.treeComponent) {
      this.treeComponent.setAllExpanded(this.todosExpandidos);
    }
  }

  exportarXLSX(): void {
    this.service.exportXLSX(this.gestion);
  }

  onBridgeUpdated(): void {
    // After a bridge update, leave tree as-is (the update is already persisted)
  }
}

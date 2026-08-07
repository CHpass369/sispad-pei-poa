import {
  Component,
  Input,
  Output,
  EventEmitter,
  ChangeDetectionStrategy,
  ChangeDetectorRef,
} from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { NodoArbol } from './matrices-contracts';
import { MatrizCompletaService } from './matriz-completa.service';

const NIVEL_COLORS: Record<string, string> = {
  eje: '#1565C0',
  meta: '#42A5F5',
  resultado: '#90CAF9',
  componente: '#2E7D32',
  accion: '#66BB6A',
  pad: '#EF6C00',
  pei: '#7B1FA2',
  poa: '#C62828',
};

const NIVEL_LABELS: Record<string, string> = {
  eje: 'PGDESA Eje',
  meta: 'PGDESA Meta',
  resultado: 'PGDESA Resultado',
  componente: 'PDESA Componente',
  accion: 'PDESA Acción',
  pad: 'PAD',
  pei: 'PEI',
  poa: 'POA',
};

@Component({
  selector: 'app-matriz-completa-tree',
  standalone: true,
  imports: [CommonModule, FormsModule],
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <table class="matriz-tree-table" [class.is-root]="level === 0">
      <thead *ngIf="level === 0">
        <tr>
          <th class="th-codigo">Código</th>
          <th class="th-nivel">Nivel</th>
          <th class="th-nombre">Nombre</th>
          <th class="th-plan">Plan</th>
          <th class="th-acciones">Articulación PAD</th>
        </tr>
      </thead>
      <tbody>
        <ng-container *ngFor="let nodo of nodos; trackBy: trackByFn">
          <!-- Main row -->
          <tr class="tr-nodo" [class.tr-expanded]="nodo._expanded">
            <td class="td-codigo" [style.padding-left.px]="24 + level * 24">
              <button
                *ngIf="nodo.hijos && nodo.hijos.length > 0"
                class="btn-expand"
                (click)="toggle(nodo); $event.stopPropagation()"
                [title]="nodo._expanded ? 'Colapsar' : 'Expandir'"
              >
                {{ nodo._expanded ? '▼' : '▶' }}
              </button>
              <span
                class="codigo"
                [class.no-children]="!nodo.hijos || nodo.hijos.length === 0"
              >{{ nodo.codigo_completo }}</span>
            </td>
            <td class="td-nivel">
              <span
                class="badge-nivel"
                [style.background-color]="colorNivel(nodo.nivel)"
              >{{ labelNivel(nodo.nivel) }}</span>
            </td>
            <td class="td-nombre">
              <span class="nombre-text">{{ nodo.nombre }}</span>
              <!-- Articulaciones chips -->
              <div *ngIf="nodo.articulaciones && nodo.articulaciones.length > 0" class="artic-chips">
                <span
                  *ngFor="let art of nodo.articulaciones"
                  class="chip"
                  [title]="art.nombre"
                >🔗 {{ art.codigo_completo }} · {{ art.tipo_plan?.toUpperCase() }}</span>
              </div>
            </td>
            <td class="td-plan">{{ nodo.plan_nombre || '—' }}</td>
            <td class="td-acciones">
              <button
                *ngIf="nodo.nivel === 'accion'"
                class="btn-articular"
                (click)="iniciarEdicion(nodo); $event.stopPropagation()"
              >
                ⚡ Articular
              </button>
            </td>
          </tr>

          <!-- Inline edit picker -->
          <tr *ngIf="editandoId === nodo.id" class="tr-picker">
            <td [attr.colspan]="5" class="td-picker">
              <div class="picker-container">
                <div class="picker-header">
                  <strong>Articular PDESA Acción → Resultado PAD</strong>
                  <button class="btn-cerrar" (click)="cancelarEdicion()">✕</button>
                </div>
                <div class="picker-search">
                  <input
                    [(ngModel)]="searchTerm"
                    (input)="filtrarResultados()"
                    class="form-control picker-input"
                    placeholder="Buscar resultado PAD por código o denominación..."
                    autofocus
                  />
                </div>
                <div class="picker-results" *ngIf="!pickerCargando; else pickerLoading">
                  <div
                    *ngIf="resultadosFiltrados.length === 0"
                    class="picker-empty"
                  >No se encontraron resultados PAD</div>
                  <div
                    *ngFor="let r of resultadosFiltrados"
                    class="picker-item"
                    [class.picker-item-selected]="nodo._padSeleccionado === r.id"
                    (click)="seleccionarResultado(nodo, r)"
                  >
                    <span class="picker-item-codigo">{{ r.codigo_resultado || r.codigo || '—' }}</span>
                    <span class="picker-item-nombre">{{ r.denominacion || r.nombre || '—' }}</span>
                    <span *ngIf="nodo._padSeleccionado === r.id" class="picker-item-check">✓</span>
                  </div>
                </div>
                <ng-template #pickerLoading>
                  <div class="picker-loader">Cargando resultados PAD...</div>
                </ng-template>
                <div *ngIf="mensajeFeedback" class="picker-feedback" [class.success]="feedbackTipo === 'success'" [class.error]="feedbackTipo === 'error'">
                  {{ mensajeFeedback }}
                </div>
              </div>
            </td>
          </tr>

          <!-- Children (recursive) -->
          <ng-container *ngIf="nodo._expanded && nodo.hijos && nodo.hijos.length > 0">
            <tr class="tr-children">
              <td [attr.colspan]="5" class="td-children">
                <app-matriz-completa-tree
                  [nodos]="nodo.hijos!"
                  [level]="level + 1"
                  [resultadosPad]="resultadosPad"
                  (bridgeUpdated)="onBridgeUpdated($event)"
                ></app-matriz-completa-tree>
              </td>
            </tr>
          </ng-container>
        </ng-container>
      </tbody>
    </table>
  `,
  styles: [
    `
    .matriz-tree-table {
      width: 100%;
      border-collapse: collapse;
      font-size: 0.8125rem;
    }
    .matriz-tree-table.is-root {
      border: 0;
    }
    .matriz-tree-table th {
      background: var(--primary);
      color: white;
      padding: 0.5rem 0.75rem;
      text-align: left;
      font-size: 0.6875rem;
      text-transform: uppercase;
      letter-spacing: 0.04em;
      white-space: nowrap;
    }
    .th-codigo { min-width: 140px; }
    .th-nivel { min-width: 130px; }
    .th-nombre { min-width: 200px; }
    .th-plan { min-width: 120px; }
    .th-acciones { min-width: 130px; text-align: center; }

    .matriz-tree-table td {
      padding: 0.375rem 0.5rem;
      border-bottom: 1px solid var(--border);
      vertical-align: middle;
    }
    .tr-nodo:hover td { background: #F0F7F3; }
    .tr-nodo:nth-child(even) td { background: #FAFCFA; }
    .tr-nodo:nth-child(even):hover td { background: #F0F7F3; }

    .td-codigo { white-space: nowrap; }
    .btn-expand {
      background: none;
      border: none;
      cursor: pointer;
      font-size: 0.625rem;
      padding: 2px 4px;
      margin-right: 2px;
      color: var(--primary);
      vertical-align: middle;
      line-height: 1;
    }
    .btn-expand:hover { color: var(--primary-dark); }
    .codigo {
      font-family: 'Courier New', monospace;
      font-weight: 700;
      font-size: 0.75rem;
      color: var(--primary-dark);
      vertical-align: middle;
    }
    .codigo.no-children { margin-left: 18px; }

    .badge-nivel {
      display: inline-block;
      font-size: 0.625rem;
      font-weight: 700;
      color: white;
      padding: 2px 8px;
      border-radius: 10px;
      text-transform: uppercase;
      letter-spacing: 0.03em;
      white-space: nowrap;
    }

    .td-nombre { max-width: 300px; }
    .nombre-text {
      display: block;
      line-height: 1.3;
    }
    .artic-chips {
      display: flex;
      flex-wrap: wrap;
      gap: 4px;
      margin-top: 4px;
    }
    .chip {
      font-size: 0.625rem;
      background: #E8F5E9;
      color: #2E7D32;
      padding: 1px 6px;
      border-radius: 8px;
      white-space: nowrap;
      cursor: default;
    }

    .td-plan { font-size: 0.75rem; color: var(--text-secondary); }
    .td-acciones { text-align: center; }

    .btn-articular {
      background: #FFF3E0;
      border: 1px solid #FFCC80;
      color: #E65100;
      padding: 0.25rem 0.5rem;
      border-radius: 4px;
      cursor: pointer;
      font-size: 0.6875rem;
      font-weight: 600;
      transition: all 0.15s;
      white-space: nowrap;
    }
    .btn-articular:hover {
      background: #FFE0B2;
      border-color: #FFB74D;
    }

    /* Inline picker */
    .tr-picker td {
      padding: 0 !important;
      background: #FFFDE7;
      border-bottom: 2px solid #FFE082;
    }
    .picker-container {
      padding: 0.75rem 1rem;
    }
    .picker-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 0.5rem;
      font-size: 0.8125rem;
      color: var(--primary-dark);
    }
    .btn-cerrar {
      background: none;
      border: none;
      font-size: 1rem;
      cursor: pointer;
      color: var(--text-secondary);
      padding: 2px 6px;
    }
    .btn-cerrar:hover { color: #C62828; }
    .picker-search { margin-bottom: 0.5rem; }
    .picker-input {
      width: 100%;
      padding: 0.5rem 0.75rem;
      border: 1px solid var(--border);
      border-radius: 4px;
      font-size: 0.8125rem;
      box-sizing: border-box;
    }
    .picker-input:focus {
      outline: none;
      border-color: var(--primary);
      box-shadow: 0 0 0 2px rgba(21, 101, 192, 0.15);
    }
    .picker-results {
      max-height: 200px;
      overflow-y: auto;
      border: 1px solid var(--border);
      border-radius: 4px;
      background: white;
    }
    .picker-item {
      display: flex;
      align-items: center;
      gap: 0.75rem;
      padding: 0.5rem 0.75rem;
      cursor: pointer;
      border-bottom: 1px solid #f0f0f0;
      transition: background 0.1s;
    }
    .picker-item:last-child { border-bottom: none; }
    .picker-item:hover { background: #E3F2FD; }
    .picker-item-selected { background: #E8F5E9; }
    .picker-item-codigo {
      font-family: 'Courier New', monospace;
      font-weight: 700;
      font-size: 0.75rem;
      color: var(--primary-dark);
      min-width: 80px;
    }
    .picker-item-nombre { flex: 1; font-size: 0.8125rem; }
    .picker-item-check {
      color: #2E7D32;
      font-weight: 700;
      font-size: 1rem;
    }
    .picker-empty {
      padding: 1rem;
      text-align: center;
      color: var(--text-secondary);
      font-size: 0.8125rem;
    }
    .picker-loader {
      padding: 1rem;
      text-align: center;
      color: var(--text-secondary);
      font-size: 0.8125rem;
    }
    .picker-feedback {
      margin-top: 0.5rem;
      padding: 0.5rem;
      border-radius: 4px;
      font-size: 0.75rem;
      font-weight: 600;
      text-align: center;
    }
    .picker-feedback.success {
      background: #E8F5E9;
      color: #2E7D32;
    }
    .picker-feedback.error {
      background: #FFEBEE;
      color: #C62828;
    }

    .td-children {
      padding: 0 !important;
      border: none !important;
      background: transparent;
    }
    .tr-children td {
      padding: 0 !important;
      border: none;
    }
    `,
  ],
})
export class MatrizCompletaTreeComponent {
  @Input() nodos: NodoArbol[] = [];
  @Input() level = 0;
  @Input() resultadosPad: any[] = [];
  @Output() bridgeUpdated = new EventEmitter<void>();

  editandoId: string | null = null;
  searchTerm = '';
  resultadosFiltrados: any[] = [];
  pickerCargando = false;
  mensajeFeedback = '';
  feedbackTipo: 'success' | 'error' = 'success';
  guardando = false;

  constructor(
    private cdr: ChangeDetectorRef,
    private service: MatrizCompletaService,
  ) {}

  trackByFn(_index: number, nodo: NodoArbol): string {
    return nodo.id;
  }

  colorNivel(nivel: string): string {
    return NIVEL_COLORS[nivel] || '#78909C';
  }

  labelNivel(nivel: string): string {
    return NIVEL_LABELS[nivel] || nivel;
  }

  toggle(nodo: NodoArbol): void {
    (nodo as any)._expanded = !(nodo as any)._expanded;
  }

  /** Set expand/collapse on all nodes recursively */
  setAllExpanded(expand: boolean): void {
    const visit = (nodes: NodoArbol[]) => {
      for (const n of nodes) {
        (n as any)._expanded = expand && !!n.hijos && n.hijos.length > 0;
        if (n.hijos) visit(n.hijos);
      }
    };
    visit(this.nodos);
    this.cdr.markForCheck();
  }

  iniciarEdicion(nodo: NodoArbol): void {
    // If picker already open for this node, close instead
    if (this.editandoId === nodo.id) {
      this.cancelarEdicion();
      return;
    }

    this.editandoId = nodo.id;
    this.searchTerm = '';
    this.mensajeFeedback = '';
    this.resultadosFiltrados = [...this.resultadosPad];
    this.cdr.markForCheck();
  }

  cancelarEdicion(): void {
    this.editandoId = null;
    this.searchTerm = '';
    this.mensajeFeedback = '';
    this.resultadosFiltrados = [];
    this.cdr.markForCheck();
  }

  filtrarResultados(): void {
    const q = this.searchTerm.trim().toLowerCase();
    if (!q) {
      this.resultadosFiltrados = [...this.resultadosPad];
    } else {
      this.resultadosFiltrados = this.resultadosPad.filter(
        (r: any) =>
          (r.codigo_resultado || r.codigo || '')
            .toLowerCase()
            .includes(q) ||
          (r.denominacion || r.nombre || '').toLowerCase().includes(q),
      );
    }
    this.cdr.markForCheck();
  }

  seleccionarResultado(nodo: NodoArbol, resultado: any): void {
    if (this.guardando) return;
    this.guardando = true;
    this.mensajeFeedback = 'Guardando...';
    this.feedbackTipo = 'success';
    this.cdr.markForCheck();

    this.service.updateBridgePAD(resultado.id, nodo.id).subscribe({
      next: () => {
        (nodo as any)._padSeleccionado = resultado.id;
        this.mensajeFeedback = `✓ Vinculado con ${resultado.codigo_resultado || resultado.codigo || ''}`;
        this.feedbackTipo = 'success';
        this.guardando = false;
        this.bridgeUpdated.emit();
        this.cdr.markForCheck();
      },
      error: (err) => {
        this.mensajeFeedback = `✗ Error al vincular: ${err.status === 404 ? 'endpoint no encontrado' : err.status === 400 ? 'datos inválidos' : 'error de servidor'}`;
        this.feedbackTipo = 'error';
        this.guardando = false;
        this.cdr.markForCheck();
      },
    });
  }

  onBridgeUpdated(): void {
    this.bridgeUpdated.emit();
  }
}

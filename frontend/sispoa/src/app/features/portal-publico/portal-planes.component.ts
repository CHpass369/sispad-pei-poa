import { Component, OnInit } from '@angular/core';
import { PortalPublicoService, PdeSaPublico } from './portal-publico.service';

interface PlanNodo {
  id: number;
  nombre: string;
  tipo: string;
  descripcion?: string;
  estado?: string;
  gestion?: number;
  expanded: boolean;
  children: PlanNodo[];
}

@Component({
  standalone: false,
  selector: 'app-portal-planes',
  template: `
    <div class="page-header">
      <h2>Planes Institucionales</h2>
      <p class="text-secondary">Jerarquía de planificación: PDESA → PTDI → PEI → PAD</p>
    </div>
    
    <div class="acciones-superior">
      <button class="btn btn-outline" (click)="expandirTodo()">Expandir Todo</button>
      <button class="btn btn-outline" (click)="colapsarTodo()">Colapsar Todo</button>
    </div>
    
    @if (!cargando) {
      <div class="planes-container">
        @for (nodo of arbol; track nodo) {
          <div>
            <ng-container *ngTemplateOutlet="nodeTpl; context: { $implicit: nodo, level: 0 }"></ng-container>
          </div>
        }
        <ng-template #nodeTpl let-nodo let-level="level">
          <div class="plan-item" [style.margin-left.px]="level * 28"
            [class.tipo-pdesa]="nodo.tipo === 'pdesa'"
            [class.tipo-ptdi]="nodo.tipo === 'ptdi'"
            [class.tipo-pei]="nodo.tipo === 'pei'"
            [class.tipo-pad]="nodo.tipo === 'pad'">
            @if (nodo.children.length > 0) {
              <span class="plan-toggle" (click)="toggleNodo(nodo)">
                {{ nodo.expanded ? '▼' : '▶' }}
              </span>
            }
            @if (nodo.children.length === 0) {
              <span class="plan-toggle">&nbsp;&nbsp;&nbsp;</span>
            }
            <span class="badge badge-tipo" [ngClass]="'badge-' + nodo.tipo">{{ nodo.tipo | uppercase }}</span>
            <span class="plan-nombre">{{ nodo.nombre }}</span>
            @if (nodo.estado) {
              <span class="plan-estado">
                <span class="badge" [ngClass]="'badge-estado-' + nodo.estado">{{ nodo.estado }}</span>
              </span>
            }
            @if (nodo.gestion) {
              <span class="plan-gestion">{{ nodo.gestion }}</span>
            }
          </div>
          @if (nodo.expanded && nodo.descripcion) {
            <div class="plan-desc" [style.margin-left.px]="level * 28 + 40">
              {{ nodo.descripcion }}
            </div>
          }
          @if (nodo.expanded && nodo.children.length > 0) {
            <div>
              @for (hijo of nodo.children; track hijo) {
                <ng-container *ngTemplateOutlet="nodeTpl; context: { $implicit: hijo, level: level + 1 }"></ng-container>
              }
            </div>
          }
        </ng-template>
        @if (arbol.length === 0) {
          <div class="empty">No hay planes disponibles para consulta pública</div>
        }
      </div>
    }
    
    @if (cargando) {
      <div class="loading">Cargando planes...</div>
    }
    @if (error) {
      <div class="alert alert-error">{{ error }}</div>
    }
    `,
  styles: [`
    .page-header { margin-bottom: 1rem; }
    .page-header h2 { font-size: 1.5rem; margin-bottom: 0.25rem; }
    .text-secondary { color: var(--text-secondary); font-size: 0.875rem; }
    .acciones-superior { display: flex; gap: 0.75rem; margin-bottom: 1.5rem; }
    .planes-container { background: var(--surface); border: 1px solid var(--border); border-radius: 8px; padding: 1rem; }
    .plan-item { display: flex; align-items: center; gap: 0.5rem; padding: 0.625rem 0.75rem; border-radius: 4px; margin-bottom: 2px; font-size: 0.875rem; }
    .plan-item:hover { background: var(--hover, #fafafa); }
    .plan-item.tipo-pdesa { border-left: 3px solid var(--mdc-blue-800); font-weight: 700; font-size: 1rem; }
    .plan-item.tipo-ptdi { border-left: 3px solid #6A1B9A; font-weight: 600; }
    .plan-item.tipo-pei { border-left: 3px solid var(--mdc-green-800); }
    .plan-item.tipo-pad { border-left: 3px solid #E65100; }
    .plan-toggle { cursor: pointer; user-select: none; font-size: 0.75rem; color: var(--text-secondary); min-width: 16px; }
    .plan-nombre { flex: 1; }
    .plan-estado { margin-left: 0.5rem; }
    .plan-gestion { font-size: 0.8125rem; color: var(--text-secondary); }
    .plan-desc { padding: 0.25rem 0.75rem 0.5rem 40px; font-size: 0.8125rem; color: var(--text-secondary); line-height: 1.4; }
    .badge { display: inline-block; padding: 0.125rem 0.5rem; border-radius: 4px; font-size: 0.6875rem; font-weight: 600; }
    .badge-tipo { text-transform: uppercase; }
    .badge-pdesa { background: var(--mdc-blue-50); color: var(--mdc-blue-800); }
    .badge-ptdi { background: #F3E5F5; color: #6A1B9A; }
    .badge-pei { background: var(--mdc-green-50); color: var(--mdc-green-800); }
    .badge-pad { background: var(--mdc-amber-50); color: #E65100; }
    .badge-estado-completo, .badge-estado-aprobado { background: var(--mdc-green-50); color: var(--mdc-green-800); }
    .badge-estado-en_curso, .badge-estado-en-curso { background: var(--mdc-amber-50); color: #E65100; }
    .badge-estado-borrador, .badge-estado-pendiente { background: var(--mdc-grey-50); color: #616161; }
    .btn { display: inline-flex; align-items: center; padding: 0.5rem 1rem; border-radius: 6px; border: none; font-size: 0.875rem; font-weight: 600; cursor: pointer; }
    .btn-outline { background: transparent; border: 1px solid var(--border); color: var(--text-primary); }
    .btn-outline:hover { background: var(--hover, var(--neutro-fondo)); }
    .empty { text-align: center; padding: 2rem; color: var(--text-secondary); }
    .loading { text-align: center; padding: 2rem; color: var(--text-secondary); }
    .alert { padding: 0.75rem 1rem; border-radius: 6px; margin-top: 1rem; }
    .alert-error { background: var(--mdc-red-50); color: var(--warn); }
  `]
})
export class PortalPlanesComponent implements OnInit {
  arbol: PlanNodo[] = [];
  cargando = true;
  error = '';

  constructor(private portalService: PortalPublicoService) {}

  ngOnInit(): void {
    this.portalService.listarPdeSa().subscribe({
      next: (data: any) => {
        const pdesaList = (data.results || data) as PdeSaPublico[];
        this.arbol = pdesaList.map(p => ({
          id: p.id || 0,
          nombre: p.nombre || '',
          tipo: 'pdesa',
          descripcion: p.descripcion,
          estado: p.estado,
          gestion: p.gestion,
          expanded: true,
          children: [],
        }));
        this.cargando = false;
      },
      error: () => {
        this.error = 'Error al cargar planes';
        this.cargando = false;
      },
    });
  }

  toggleNodo(nodo: PlanNodo): void {
    nodo.expanded = !nodo.expanded;
  }

  expandirTodo(): void {
    this.recExpandir(this.arbol, true);
  }

  colapsarTodo(): void {
    this.recExpandir(this.arbol, false);
  }

  private recExpandir(nodos: PlanNodo[], expanded: boolean): void {
    nodos.forEach(n => {
      n.expanded = expanded;
      if (n.children.length > 0) this.recExpandir(n.children, expanded);
    });
  }
}

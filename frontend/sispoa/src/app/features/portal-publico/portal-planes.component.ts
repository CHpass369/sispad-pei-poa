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

    <div class="planes-container" *ngIf="!cargando">
      <div *ngFor="let nodo of arbol">
        <ng-container *ngTemplateOutlet="nodeTpl; context: { $implicit: nodo, level: 0 }"></ng-container>
      </div>

      <ng-template #nodeTpl let-nodo let-level="level">
        <div class="plan-item" [style.margin-left.px]="level * 28"
             [class.tipo-pdesa]="nodo.tipo === 'pdesa'"
             [class.tipo-ptdi]="nodo.tipo === 'ptdi'"
             [class.tipo-pei]="nodo.tipo === 'pei'"
             [class.tipo-pad]="nodo.tipo === 'pad'">
          <span class="plan-toggle" *ngIf="nodo.children.length > 0" (click)="toggleNodo(nodo)">
            {{ nodo.expanded ? '▼' : '▶' }}
          </span>
          <span class="plan-toggle" *ngIf="nodo.children.length === 0">&nbsp;&nbsp;&nbsp;</span>
          <span class="badge badge-tipo" [ngClass]="'badge-' + nodo.tipo">{{ nodo.tipo | uppercase }}</span>
          <span class="plan-nombre">{{ nodo.nombre }}</span>
          <span class="plan-estado" *ngIf="nodo.estado">
            <span class="badge" [ngClass]="'badge-estado-' + nodo.estado">{{ nodo.estado }}</span>
          </span>
          <span class="plan-gestion" *ngIf="nodo.gestion">{{ nodo.gestion }}</span>
        </div>
        <div class="plan-desc" *ngIf="nodo.expanded && nodo.descripcion" [style.margin-left.px]="level * 28 + 40">
          {{ nodo.descripcion }}
        </div>
        <div *ngIf="nodo.expanded && nodo.children.length > 0">
          <ng-container *ngFor="let hijo of nodo.children">
            <ng-container *ngTemplateOutlet="nodeTpl; context: { $implicit: hijo, level: level + 1 }"></ng-container>
          </ng-container>
        </div>
      </ng-template>

      <div *ngIf="arbol.length === 0" class="empty">No hay planes disponibles para consulta pública</div>
    </div>

    <div class="loading" *ngIf="cargando">Cargando planes...</div>
    <div class="alert alert-error" *ngIf="error">{{ error }}</div>
  `,
  styles: [`
    .page-header { margin-bottom: 1rem; }
    .page-header h2 { font-size: 1.5rem; margin-bottom: 0.25rem; }
    .text-secondary { color: var(--text-secondary); font-size: 0.875rem; }
    .acciones-superior { display: flex; gap: 0.75rem; margin-bottom: 1.5rem; }
    .planes-container { background: var(--surface); border: 1px solid var(--border); border-radius: 8px; padding: 1rem; }
    .plan-item { display: flex; align-items: center; gap: 0.5rem; padding: 0.625rem 0.75rem; border-radius: 4px; margin-bottom: 2px; font-size: 0.875rem; }
    .plan-item:hover { background: var(--hover, #fafafa); }
    .plan-item.tipo-pdesa { border-left: 3px solid #1565C0; font-weight: 700; font-size: 1rem; }
    .plan-item.tipo-ptdi { border-left: 3px solid #6A1B9A; font-weight: 600; }
    .plan-item.tipo-pei { border-left: 3px solid #2E7D32; }
    .plan-item.tipo-pad { border-left: 3px solid #E65100; }
    .plan-toggle { cursor: pointer; user-select: none; font-size: 0.75rem; color: var(--text-secondary); min-width: 16px; }
    .plan-nombre { flex: 1; }
    .plan-estado { margin-left: 0.5rem; }
    .plan-gestion { font-size: 0.8125rem; color: var(--text-secondary); }
    .plan-desc { padding: 0.25rem 0.75rem 0.5rem 40px; font-size: 0.8125rem; color: var(--text-secondary); line-height: 1.4; }
    .badge { display: inline-block; padding: 0.125rem 0.5rem; border-radius: 4px; font-size: 0.6875rem; font-weight: 600; }
    .badge-tipo { text-transform: uppercase; }
    .badge-pdesa { background: #E3F2FD; color: #1565C0; }
    .badge-ptdi { background: #F3E5F5; color: #6A1B9A; }
    .badge-pei { background: #E8F5E9; color: #2E7D32; }
    .badge-pad { background: #FFF3E0; color: #E65100; }
    .badge-estado-completo, .badge-estado-aprobado { background: #E8F5E9; color: #2E7D32; }
    .badge-estado-en_curso, .badge-estado-en-curso { background: #FFF3E0; color: #E65100; }
    .badge-estado-borrador, .badge-estado-pendiente { background: #F5F5F5; color: #616161; }
    .btn { display: inline-flex; align-items: center; padding: 0.5rem 1rem; border-radius: 6px; border: none; font-size: 0.875rem; font-weight: 600; cursor: pointer; }
    .btn-outline { background: transparent; border: 1px solid var(--border); color: var(--text-primary); }
    .btn-outline:hover { background: var(--hover, #f5f5f5); }
    .empty { text-align: center; padding: 2rem; color: var(--text-secondary); }
    .loading { text-align: center; padding: 2rem; color: var(--text-secondary); }
    .alert { padding: 0.75rem 1rem; border-radius: 6px; margin-top: 1rem; }
    .alert-error { background: #FFEBEE; color: var(--warn); }
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

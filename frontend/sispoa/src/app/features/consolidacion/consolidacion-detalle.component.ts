import { Component, OnInit } from '@angular/core';
import { ActivatedRoute } from '@angular/router';
import { ConsolidacionService, PdeSa, Ptdi, Pei, ResultadoPad, Poau } from './consolidacion.service';

interface TreeNode {
  id: number;
  nombre: string;
  tipo: string;
  expanded: boolean;
  children: TreeNode[];
  data: any;
}

@Component({
  standalone: false,
  selector: 'app-consolidacion-detalle',
  template: `
    <div class="page-header">
      <h2>Detalle de Consolidación - UE {{ gestionId }}</h2>
      <p class="text-secondary">Jerarquía completa PDESA → PTDI → PEI → PAD → POAU</p>
    </div>
    
    <div class="acciones-superior">
      <button class="btn btn-outline" (click)="expandirTodo()">Expandir Todo</button>
      <button class="btn btn-outline" (click)="colapsarTodo()">Colapsar Todo</button>
      <button class="btn btn-outline" (click)="cargarDatos()">Recargar</button>
    </div>
    
    @if (!cargando) {
      <div class="tree-container">
        @for (nodo of arbol; track nodo) {
          <div class="tree-node">
            <ng-container *ngTemplateOutlet="nodeTpl; context: { $implicit: nodo, level: 0 }"></ng-container>
          </div>
        }
        <ng-template #nodeTpl let-nodo let-level="level">
          <div class="tree-item" [style.margin-left.px]="level * 24"
            [class.tipo-pdesa]="nodo.tipo === 'pdesa'"
            [class.tipo-ptdi]="nodo.tipo === 'ptdi'"
            [class.tipo-pei]="nodo.tipo === 'pei'"
            [class.tipo-pad]="nodo.tipo === 'pad'"
            [class.tipo-poau]="nodo.tipo === 'poau'">
            @if (nodo.children.length > 0) {
              <span class="tree-toggle" (click)="toggleNode(nodo)">
                {{ nodo.expanded ? '▼' : '▶' }}
              </span>
            }
            @if (nodo.children.length === 0) {
              <span class="tree-toggle">&nbsp;&nbsp;&nbsp;</span>
            }
            <span class="badge badge-tipo" [ngClass]="'badge-' + nodo.tipo">{{ nodo.tipo | uppercase }}</span>
            <span class="tree-nombre">{{ nodo.nombre }}</span>
            @if (nodo.data?.avance_porcentual !== undefined) {
              <span class="tree-avance">
                Avance: {{ nodo.data.avance_porcentual }}%
              </span>
            }
            @if (nodo.data?.estado) {
              <span class="tree-estado">
                <span class="badge" [ngClass]="'badge-' + nodo.data.estado">{{ nodo.data.estado }}</span>
              </span>
            }
            @if (nodo.data?.monto_total !== undefined) {
              <span class="tree-monto">
                Bs {{ nodo.data.monto_total | number:'1.2-2' }}
              </span>
            }
          </div>
          @if (nodo.expanded && nodo.children.length > 0) {
            <div>
              @for (hijo of nodo.children; track hijo) {
                <ng-container *ngTemplateOutlet="nodeTpl; context: { $implicit: hijo, level: level + 1 }"></ng-container>
              }
            </div>
          }
        </ng-template>
        @if (arbol.length === 0) {
          <div class="empty">No hay datos de planificación para esta UE y gestión</div>
        }
      </div>
    }
    
    @if (cargando) {
      <div class="loading">Cargando jerarquía...</div>
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
    .tree-container { background: var(--surface); border: 1px solid var(--border); border-radius: 8px; padding: 1rem; }
    .tree-item { display: flex; align-items: center; gap: 0.5rem; padding: 0.5rem 0.75rem; border-radius: 4px; margin-bottom: 2px; font-size: 0.875rem; }
    .tree-item:hover { background: var(--hover, #fafafa); }
    .tree-item.tipo-pdesa { border-left: 3px solid var(--mdc-blue-800); font-weight: 600; }
    .tree-item.tipo-ptdi { border-left: 3px solid #6A1B9A; }
    .tree-item.tipo-pei { border-left: 3px solid var(--mdc-green-800); }
    .tree-item.tipo-pad { border-left: 3px solid #E65100; }
    .tree-item.tipo-poau { border-left: 3px solid #00838F; }
    .tree-toggle { cursor: pointer; user-select: none; font-size: 0.75rem; color: var(--text-secondary); min-width: 16px; }
    .tree-nombre { flex: 1; }
    .tree-avance { font-size: 0.8125rem; color: var(--text-secondary); margin-left: auto; }
    .tree-estado { margin-left: 0.5rem; }
    .tree-monto { font-size: 0.8125rem; font-weight: 600; margin-left: 0.5rem; }
    .badge { display: inline-block; padding: 0.125rem 0.5rem; border-radius: 4px; font-size: 0.6875rem; font-weight: 600; }
    .badge-tipo { text-transform: uppercase; }
    .badge-pdesa { background: var(--mdc-blue-50); color: var(--mdc-blue-800); }
    .badge-ptdi { background: #F3E5F5; color: #6A1B9A; }
    .badge-pei { background: var(--mdc-green-50); color: var(--mdc-green-800); }
    .badge-pad { background: var(--mdc-amber-50); color: #E65100; }
    .badge-poau { background: #E0F7FA; color: #00838F; }
    .badge-completo, .badge-aprobado { background: var(--mdc-green-50); color: var(--mdc-green-800); }
    .badge-en_curso, .badge-en-curso { background: var(--mdc-amber-50); color: #E65100; }
    .badge-pendiente, .badge-borrador { background: var(--mdc-grey-50); color: #616161; }
    .btn { display: inline-flex; align-items: center; padding: 0.5rem 1rem; border-radius: 6px; border: none; font-size: 0.875rem; font-weight: 600; cursor: pointer; }
    .btn-outline { background: transparent; border: 1px solid var(--border); color: var(--text-primary); }
    .btn-outline:hover { background: var(--hover, var(--neutro-fondo)); }
    .empty { text-align: center; padding: 2rem; color: var(--text-secondary); }
    .loading { text-align: center; padding: 2rem; color: var(--text-secondary); }
    .alert { padding: 0.75rem 1rem; border-radius: 6px; margin-top: 1rem; }
    .alert-error { background: var(--mdc-red-50); color: var(--warn); }
  `]
})
export class ConsolidacionDetalleComponent implements OnInit {
  gestionId = '';
  arbol: TreeNode[] = [];
  cargando = true;
  error = '';

  constructor(
    private consolidacionService: ConsolidacionService,
    private route: ActivatedRoute,
  ) {}

  ngOnInit(): void {
    this.gestionId = this.route.snapshot.paramMap.get('gestion_id') || '';
    this.cargarDatos();
  }

  cargarDatos(): void {
    this.cargando = true;
    this.error = '';
    const params: Record<string, string | number | boolean> = {};
    if (this.gestionId) params.gestion = this.gestionId;

    this.consolidacionService.listarPdeSa(params).subscribe({
      next: (pdesaData: any) => {
        const pdesaList = (pdesaData.results || pdesaData) as PdeSa[];
        this.arbol = pdesaList.map(p => this.crearNodoPdesa(p));
        this.cargarPtdi(params);
      },
      error: () => {
        this.error = 'Error al cargar PDESA';
        this.cargando = false;
      },
    });
  }

  private cargarPtdi(params: Record<string, string | number | boolean>): void {
    this.consolidacionService.listarPtdi(params).subscribe({
      next: (ptdiData: any) => {
        const ptdiList = (ptdiData.results || ptdiData) as Ptdi[];
        ptdiList.forEach(ptdi => {
          const nodo = this.arbol.find(n => n.id === ptdi.pde_sa);
          if (nodo) {
            nodo.children.push(this.crearNodoPtdi(ptdi));
          }
        });
        this.cargarPei(params);
      },
      error: () => {
        this.cargarPei(params);
      },
    });
  }

  private cargarPei(params: Record<string, string | number | boolean>): void {
    this.consolidacionService.listarPei(params).subscribe({
      next: (peiData: any) => {
        const peiList = (peiData.results || peiData) as Pei[];
        peiList.forEach(pei => {
          this.agregarPeiATree(pei);
        });
        this.cargarPad(params);
      },
      error: () => {
        this.cargarPad(params);
      },
    });
  }

  private cargarPad(params: Record<string, string | number | boolean>): void {
    this.consolidacionService.listarResultadosPad(params).subscribe({
      next: (padData: any) => {
        const padList = (padData.results || padData) as ResultadoPad[];
        padList.forEach(pad => {
          this.agregarPadATree(pad);
        });
        this.cargarPoau(params);
      },
      error: () => {
        this.cargarPoau(params);
      },
    });
  }

  private cargarPoau(params: Record<string, string | number | boolean>): void {
    this.consolidacionService.listarPoau(params).subscribe({
      next: (poauData: any) => {
        const poauList = (poauData.results || poauData) as Poau[];
        poauList.forEach(poau => {
          this.agregarPoauATree(poau);
        });
        this.cargando = false;
      },
      error: () => {
        this.cargando = false;
      },
    });
  }

  private agregarPeiATree(pei: Pei): void {
    for (const pdesa of this.arbol) {
      for (const ptdi of pdesa.children) {
        if (ptdi.id === pei.ptdi) {
          ptdi.children.push(this.crearNodoPei(pei));
          return;
        }
      }
    }
  }

  private agregarPadATree(pad: ResultadoPad): void {
    for (const pdesa of this.arbol) {
      for (const ptdi of pdesa.children) {
        for (const pei of ptdi.children) {
          if (pei.id === pad.pei) {
            pei.children.push(this.crearNodoPad(pad));
            return;
          }
        }
      }
    }
  }

  private agregarPoauATree(poau: Poau): void {
    for (const pdesa of this.arbol) {
      for (const ptdi of pdesa.children) {
        for (const pei of ptdi.children) {
          for (const pad of pei.children) {
            if (pad.id === poau.resultado_pad) {
              pad.children.push(this.crearNodoPoau(poau));
              return;
            }
          }
        }
      }
    }
  }

  private crearNodoPdesa(p: PdeSa): TreeNode {
    return { id: p.id || 0, nombre: p.nombre || '', tipo: 'pdesa', expanded: true, children: [], data: p };
  }

  private crearNodoPtdi(p: Ptdi): TreeNode {
    return { id: p.id || 0, nombre: p.nombre || '', tipo: 'ptdi', expanded: false, children: [], data: p };
  }

  private crearNodoPei(p: Pei): TreeNode {
    return { id: p.id || 0, nombre: p.unidad_ejecutora_nombre || `PEI ${p.id}`, tipo: 'pei', expanded: false, children: [], data: p };
  }

  private crearNodoPad(p: ResultadoPad): TreeNode {
    return { id: p.id || 0, nombre: p.programa || `PAD ${p.id}`, tipo: 'pad', expanded: false, children: [], data: p };
  }

  private crearNodoPoau(p: Poau): TreeNode {
    return { id: p.id || 0, nombre: `POAU ${p.id}`, tipo: 'poau', expanded: false, children: [], data: p };
  }

  toggleNode(nodo: TreeNode): void {
    nodo.expanded = !nodo.expanded;
  }

  expandirTodo(): void {
    this.recursivoExpandir(this.arbol, true);
  }

  colapsarTodo(): void {
    this.recursivoExpandir(this.arbol, false);
  }

  private recursivoExpandir(nodos: TreeNode[], expanded: boolean): void {
    nodos.forEach(n => {
      n.expanded = expanded;
      if (n.children.length > 0) {
        this.recursivoExpandir(n.children, expanded);
      }
    });
  }
}

import { Component, Input } from '@angular/core';
import { NodoV2 } from './sis-pe.service';

@Component({
  standalone: false,
  selector: 'app-sis-pe-arbol',
  template: `
    <ul class="tree">
      <li *ngFor="let nodo of nodos">
        <div class="node">
          <span class="code">{{ nodo.codigo }}</span>
          <span class="name">{{ nodo.nombre }}</span>
          <span class="tipo">{{ nodo.tipo_nodo_denominacion }}</span>
        </div>
        <app-sis-pe-arbol *ngIf="nodo.hijos?.length" [nodos]="nodo.hijos"></app-sis-pe-arbol>
      </li>
    </ul>
  `,
  styles: [`
    .tree { list-style: none; padding-left: 1.25rem; margin: 0; }
    .node { display: flex; gap: 0.5rem; align-items: baseline; padding: 0.25rem 0; font-size: 0.8125rem; }
    .code { font-weight: 700; color: var(--primary); min-width: 90px; }
    .name { flex: 1; }
    .tipo { font-size: 0.6875rem; color: var(--text-secondary); background: #F5F5F5; padding: 0.125rem 0.375rem; border-radius: 4px; }
  `],
})
export class SisPeArbolComponent {
  @Input() nodos: NodoV2[] = [];
}

import { Component, Input, Output, EventEmitter } from '@angular/core';
import { CommonModule } from '@angular/common';
import { UnidadOrganizacional } from './models/unidad.model';

@Component({
  selector: 'app-organizacion-tree-node',
  standalone: false,
  templateUrl: './organizacion-tree-node.component.html',
})
export class OrganizacionTreeNodeComponent {
  @Input({ required: true }) nodo!: UnidadOrganizacional;
  @Input() seleccionado = false;
  @Input() nivel = 0;
  @Output() seleccionar = new EventEmitter<UnidadOrganizacional>();

  expandido = false;

  toggleExpandir(event: MouseEvent): void {
    event.stopPropagation();
    this.expandido = !this.expandido;
  }

  onClick(): void {
    this.seleccionar.emit(this.nodo);
  }

  trackByFn(_index: number, item: UnidadOrganizacional): number {
    return item.id;
  }
}

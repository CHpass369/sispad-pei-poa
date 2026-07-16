import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ApiService } from '../../core/services/api.service';
import { UnidadOrganizacional } from './models/unidad.model';

@Component({
  selector: 'app-organizacion-tree',
  standalone: false,
  templateUrl: './organizacion-tree.component.html',
})
export class OrganizacionTreeComponent implements OnInit {
  arbol: UnidadOrganizacional[] = [];
  unidadSeleccionada: UnidadOrganizacional | null = null;
  cargando = true;
  error = '';

  constructor(private api: ApiService) {}

  ngOnInit(): void {
    this.cargarArbol();
  }

  cargarArbol(): void {
    this.cargando = true;
    this.api.get<UnidadOrganizacional[]>('/api/v1/unidades/arbol/').subscribe({
      next: (data) => {
        this.arbol = data;
        this.cargando = false;
      },
      error: () => {
        this.error = 'Error al cargar el árbol organizacional';
        this.cargando = false;
      },
    });
  }

  seleccionar(unidad: UnidadOrganizacional): void {
    this.unidadSeleccionada = unidad;
  }

  limpiarSeleccion(): void {
    this.unidadSeleccionada = null;
  }

  trackByFn(_index: number, item: UnidadOrganizacional): number {
    return item.id;
  }

  tieneHijos(unidad: UnidadOrganizacional): boolean {
    return unidad.hijos && unidad.hijos.length > 0;
  }
}

import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ApiService } from '../../core/services/api.service';
import { UnidadEjecutora, UnidadEjecutoraRequest } from './models/unidad.model';

@Component({
  selector: 'app-organizacion-ue',
  standalone: false,
  templateUrl: './organizacion-ue.component.html',
})
export class OrganizacionUeComponent implements OnInit {
  unidades: UnidadEjecutora[] = [];
  cargando = true;
  error = '';
  mostrarFormulario = false;
  editando = false;
  idEditar: number | null = null;

  form: UnidadEjecutoraRequest = {
    codigo: '',
    nombre: '',
    sigla: '',
    responsable: '',
  };

  constructor(private api: ApiService) {}

  ngOnInit(): void {
    this.cargar();
  }

  cargar(): void {
    this.cargando = true;
    this.api.get<UnidadEjecutora[]>('/api/v1/unidades-ejecutoras/').subscribe({
      next: (data) => {
        this.unidades = data;
        this.cargando = false;
      },
      error: () => {
        this.error = 'Error al cargar unidades ejecutoras';
        this.cargando = false;
      },
    });
  }

  abrirFormulario(): void {
    this.editando = false;
    this.idEditar = null;
    this.form = { codigo: '', nombre: '', sigla: '', responsable: '' };
    this.mostrarFormulario = true;
  }

  editar(item: UnidadEjecutora): void {
    this.editando = true;
    this.idEditar = item.id;
    this.form = {
      codigo: item.codigo,
      nombre: item.nombre,
      sigla: item.sigla,
      responsable: item.responsable,
    };
    this.mostrarFormulario = true;
  }

  cerrarFormulario(): void {
    this.mostrarFormulario = false;
    this.error = '';
  }

  guardar(): void {
    if (!this.form.codigo || !this.form.nombre) {
      this.error = 'Código y nombre son obligatorios';
      return;
    }

    const obs = this.editando && this.idEditar
      ? this.api.put<UnidadEjecutora>(`/api/v1/unidades-ejecutoras/${this.idEditar}/`, this.form)
      : this.api.post<UnidadEjecutora>('/api/v1/unidades-ejecutoras/', this.form);

    obs.subscribe({
      next: () => {
        this.cerrarFormulario();
        this.cargar();
      },
      error: () => (this.error = 'Error al guardar unidad ejecutora'),
    });
  }

  eliminar(id: number): void {
    if (!confirm('¿Eliminar esta unidad ejecutora?')) return;
    this.api.delete(`/api/v1/unidades-ejecutoras/${id}/`).subscribe({
      next: () => this.cargar(),
      error: () => (this.error = 'Error al eliminar'),
    });
  }
}

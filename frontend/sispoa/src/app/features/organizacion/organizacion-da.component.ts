import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ApiService } from '../../core/services/api.service';
import { DireccionAdministrativa, DireccionAdministrativaRequest } from './models/unidad.model';

@Component({
  selector: 'app-organizacion-da',
  standalone: false,
  templateUrl: './organizacion-da.component.html',
})
export class OrganizacionDaComponent implements OnInit {
  direcciones: DireccionAdministrativa[] = [];
  cargando = true;
  error = '';
  mostrarFormulario = false;
  editando = false;
  idEditar: number | null = null;

  form: DireccionAdministrativaRequest = {
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
    this.api.get<DireccionAdministrativa[]>('/api/v1/direcciones-administrativas/').subscribe({
      next: (data) => {
        this.direcciones = data;
        this.cargando = false;
      },
      error: () => {
        this.error = 'Error al cargar direcciones administrativas';
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

  editar(item: DireccionAdministrativa): void {
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
      ? this.api.put<DireccionAdministrativa>(`/api/v1/direcciones-administrativas/${this.idEditar}/`, this.form)
      : this.api.post<DireccionAdministrativa>('/api/v1/direcciones-administrativas/', this.form);

    obs.subscribe({
      next: () => {
        this.cerrarFormulario();
        this.cargar();
      },
      error: () => (this.error = 'Error al guardar dirección administrativa'),
    });
  }

  eliminar(id: number): void {
    if (!confirm('¿Eliminar esta dirección administrativa?')) return;
    this.api.delete(`/api/v1/direcciones-administrativas/${id}/`).subscribe({
      next: () => this.cargar(),
      error: () => (this.error = 'Error al eliminar'),
    });
  }
}

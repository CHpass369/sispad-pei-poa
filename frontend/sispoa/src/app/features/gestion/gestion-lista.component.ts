import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { RouterModule } from '@angular/router';
import { ApiService } from '../../core/services/api.service';
import { Gestion, GestionRequest, ESTADOS_GESTION } from './models/gestion.model';

@Component({
  selector: 'app-gestion-lista',
  standalone: false,
  templateUrl: './gestion-lista.component.html',
})
export class GestionListaComponent implements OnInit {
  gestiones: Gestion[] = [];
  mostrarFormulario = false;
  editando = false;
  gestionIdEditar: number | null = null;
  error = '';
  cargando = true;

  form: GestionRequest = {
    anio: new Date().getFullYear(),
    fecha_inicio: '',
    fecha_fin: '',
  };

  readonly estados = ESTADOS_GESTION;
  readonly estadoKeys = Object.keys(ESTADOS_GESTION);

  constructor(private api: ApiService) {}

  ngOnInit(): void {
    this.cargarGestiones();
  }

  cargarGestiones(): void {
    this.cargando = true;
    this.api.get<Gestion[]>('/api/v1/gestiones/').subscribe({
      next: (data) => {
        this.gestiones = data;
        this.cargando = false;
      },
      error: () => {
        this.error = 'Error al cargar gestiones';
        this.cargando = false;
      },
    });
  }

  abrirFormulario(): void {
    this.editando = false;
    this.gestionIdEditar = null;
    this.form = { anio: new Date().getFullYear(), fecha_inicio: '', fecha_fin: '' };
    this.mostrarFormulario = true;
  }

  cerrarFormulario(): void {
    this.mostrarFormulario = false;
    this.error = '';
  }

  guardar(): void {
    this.error = '';
    if (!this.form.anio || !this.form.fecha_inicio || !this.form.fecha_fin) {
      this.error = 'Todos los campos son obligatorios';
      return;
    }

    if (this.editando && this.gestionIdEditar) {
      this.api.put<Gestion>(`/api/v1/gestiones/${this.gestionIdEditar}/`, this.form).subscribe({
        next: () => {
          this.cerrarFormulario();
          this.cargarGestiones();
        },
        error: () => (this.error = 'Error al actualizar gestión'),
      });
    } else {
      this.api.post<Gestion>('/api/v1/gestiones/', this.form).subscribe({
        next: () => {
          this.cerrarFormulario();
          this.cargarGestiones();
        },
        error: () => (this.error = 'Error al crear gestión'),
      });
    }
  }

  editar(gestion: Gestion): void {
    this.editando = true;
    this.gestionIdEditar = gestion.id;
    this.form = {
      anio: gestion.anio,
      fecha_inicio: gestion.fecha_inicio,
      fecha_fin: gestion.fecha_fin,
    };
    this.mostrarFormulario = true;
  }

  obtenerClaseEstado(estado: string): string {
    const clases: Record<string, string> = {
      planificacion: 'bg-blue-100 text-blue-800',
      formulacion: 'bg-yellow-100 text-yellow-800',
      revision: 'bg-purple-100 text-purple-800',
      aprobado: 'bg-green-100 text-green-800',
      ejecucion: 'bg-indigo-100 text-indigo-800',
      cerrado: 'bg-gray-100 text-gray-800',
    };
    return clases[estado] || 'bg-gray-100 text-gray-800';
  }
}

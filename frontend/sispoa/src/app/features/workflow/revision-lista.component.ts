import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ApiService } from '../../core/services/api.service';
import { Revision, TIPOS_REVISION, ESTADOS_REVISION } from './models/workflow.model';

@Component({
  selector: 'app-revision-lista',
  standalone: false,
  templateUrl: './revision-lista.component.html',
})
export class RevisionListaComponent implements OnInit {
  revisiones: Revision[] = [];
  filtradas: Revision[] = [];
  cargando = true;
  error = '';

  filtroEstado = '';
  filtroTipo = '';

  readonly tipos = TIPOS_REVISION;
  readonly estados = ESTADOS_REVISION;
  readonly tipoKeys = Object.keys(TIPOS_REVISION);
  readonly estadoKeys = Object.keys(ESTADOS_REVISION);

  constructor(private api: ApiService) {}

  ngOnInit(): void {
    this.cargar();
  }

  cargar(): void {
    this.cargando = true;
    this.api.get<Revision[]>('/api/v1/revisiones/').subscribe({
      next: (data) => {
        this.revisiones = data;
        this.aplicarFiltros();
        this.cargando = false;
      },
      error: () => {
        this.error = 'Error al cargar revisiones';
        this.cargando = false;
      },
    });
  }

  aplicarFiltros(): void {
    this.filtradas = this.revisiones.filter((r) => {
      const porEstado = !this.filtroEstado || r.estado === this.filtroEstado;
      const porTipo = !this.filtroTipo || r.tipo === this.filtroTipo;
      return porEstado && porTipo;
    });
  }

  obtenerClaseEstado(estado: string): string {
    const clases: Record<string, string> = {
      pendiente: 'bg-gray-100 text-gray-700',
      en_revision: 'bg-blue-100 text-blue-700',
      observado: 'bg-yellow-100 text-yellow-700',
      aprobado: 'bg-green-100 text-green-700',
      rechazado: 'bg-red-100 text-red-700',
    };
    return clases[estado] || 'bg-gray-100 text-gray-700';
  }

  obtenerClaseTipo(tipo: string): string {
    return tipo === 'envio'
      ? 'bg-purple-100 text-purple-700'
      : 'bg-indigo-100 text-indigo-700';
  }
}

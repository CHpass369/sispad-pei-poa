import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ApiService } from '../../core/services/api.service';
import { Aprobacion, TIPOS_APROBACION, ESTADOS_APROBACION } from './models/workflow.model';

@Component({
  selector: 'app-aprobacion-lista',
  standalone: false,
  templateUrl: './aprobacion-lista.component.html',
})
export class AprobacionListaComponent implements OnInit {
  aprobaciones: Aprobacion[] = [];
  filtradas: Aprobacion[] = [];
  cargando = true;
  error = '';

  filtroEstado = '';
  filtroTipo = '';

  readonly tipos = TIPOS_APROBACION;
  readonly estados = ESTADOS_APROBACION;
  readonly tipoKeys = Object.keys(TIPOS_APROBACION);
  readonly estadoKeys = Object.keys(ESTADOS_APROBACION);

  constructor(private api: ApiService) {}

  ngOnInit(): void {
    this.cargar();
  }

  cargar(): void {
    this.cargando = true;
    this.api.get<Aprobacion[]>('/aprobaciones/').subscribe({
      next: (data) => {
        this.aprobaciones = data;
        this.aplicarFiltros();
        this.cargando = false;
      },
      error: () => {
        this.error = 'Error al cargar aprobaciones';
        this.cargando = false;
      },
    });
  }

  aplicarFiltros(): void {
    this.filtradas = this.aprobaciones.filter((a) => {
      const porEstado = !this.filtroEstado || a.estado === this.filtroEstado;
      const porTipo = !this.filtroTipo || a.tipo === this.filtroTipo;
      return porEstado && porTipo;
    });
  }

  obtenerClaseEstado(estado: string): string {
    const clases: Record<string, string> = {
      pendiente: 'bg-gray-100 text-gray-700',
      aprobado: 'bg-green-100 text-green-700',
      rechazado: 'bg-red-100 text-red-700',
    };
    return clases[estado] || 'bg-gray-100 text-gray-700';
  }

  obtenerClaseTipo(tipo: string): string {
    const clases: Record<string, string> = {
      formulacion: 'bg-blue-100 text-blue-700',
      presupuesto: 'bg-purple-100 text-purple-700',
      cierre: 'bg-orange-100 text-orange-700',
    };
    return clases[tipo] || 'bg-gray-100 text-gray-700';
  }
}

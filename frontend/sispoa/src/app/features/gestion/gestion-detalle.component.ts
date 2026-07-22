import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ActivatedRoute, RouterModule } from '@angular/router';
import { ApiService } from '../../core/services/api.service';
import { Gestion, ESTADOS_GESTION } from './models/gestion.model';

@Component({
  selector: 'app-gestion-detalle',
  standalone: false,
  templateUrl: './gestion-detalle.component.html',
})
export class GestionDetalleComponent implements OnInit {
  gestion: Gestion | null = null;
  cargando = true;
  error = '';

  readonly estados = ESTADOS_GESTION;

  constructor(
    private route: ActivatedRoute,
    private api: ApiService,
  ) {}

  ngOnInit(): void {
    const id = this.route.snapshot.paramMap.get('id');
    if (id) {
      this.cargarGestion(Number(id));
    }
  }

  cargarGestion(id: number): void {
    this.cargando = true;
    this.api.get<Gestion>(`/gestiones/${id}/`).subscribe({
      next: (data) => {
        this.gestion = data;
        this.cargando = false;
      },
      error: () => {
        this.error = 'Error al cargar detalle de la gestión';
        this.cargando = false;
      },
    });
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

  obtenerClaseEtapa(completada: boolean): string {
    return completada
      ? 'bg-green-100 text-green-700 border-green-300'
      : 'bg-gray-100 text-gray-500 border-gray-300';
  }
}

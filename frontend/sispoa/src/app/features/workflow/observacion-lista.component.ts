import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ApiService } from '../../core/services/api.service';
import { Observacion, SEVERIDADES } from './models/workflow.model';

@Component({
  selector: 'app-observacion-lista',
  standalone: false,
  templateUrl: './observacion-lista.component.html',
})
export class ObservacionListaComponent implements OnInit {
  observaciones: Observacion[] = [];
  filtradas: Observacion[] = [];
  cargando = true;
  error = '';
  soloPendientes = false;

  readonly severidades = SEVERIDADES;

  constructor(private api: ApiService) {}

  ngOnInit(): void {
    this.cargar();
  }

  cargar(): void {
    this.cargando = true;
    this.api.get<Observacion[]>('/observaciones/').subscribe({
      next: (data) => {
        this.observaciones = data;
        this.aplicarFiltros();
        this.cargando = false;
      },
      error: () => {
        this.error = 'Error al cargar observaciones';
        this.cargando = false;
      },
    });
  }

  aplicarFiltros(): void {
    this.filtradas = this.soloPendientes
      ? this.observaciones.filter((o) => !o.resuelta)
      : [...this.observaciones];
  }

  obtenerClaseSeveridad(severidad: string): string {
    const clases: Record<string, string> = {
      grave: 'bg-red-100 text-red-700 ring-1 ring-red-300',
      moderada: 'bg-yellow-100 text-yellow-700 ring-1 ring-yellow-300',
      leve: 'bg-green-100 text-green-700 ring-1 ring-green-300',
    };
    return clases[severidad] || 'bg-gray-100 text-gray-700';
  }
}
